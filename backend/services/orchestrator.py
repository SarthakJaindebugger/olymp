from __future__ import annotations

import time
from dataclasses import asdict
from typing import Any, Dict, List

from .aggregator import AggregationService
from .query_optimizer import (
    AdaptiveQueryPlanner,
    ClarificationEngine,
    ParsedIntent,
    QueryCache,
    QueryIntentParser,
    RLHooks,
    Strategy,
    TelemetrySink,
)


class ConversationalQueryOrchestrator:
    def __init__(self, aggregator: AggregationService) -> None:
        self.aggregator = aggregator
        self.parser = QueryIntentParser()
        self.clarifier = ClarificationEngine()
        self.cache = QueryCache(default_ttl_seconds=45)
        self.planner = AdaptiveQueryPlanner()
        self.telemetry = TelemetrySink()
        self.rl_hooks = RLHooks()

    def execute(self, message: str) -> Dict[str, Any]:
        started = time.perf_counter()
        stages: List[str] = ["Understanding query..."]

        intent: ParsedIntent = self.parser.parse(message)
        needs_clarification, confidence, clarification_prompt = self.clarifier.evaluate(message)
        key = self.cache.fingerprint(intent)
        cached_payload = self.cache.get(key)
        cache_hit = cached_payload is not None

        stages.append("Planning execution strategy...")
        plan = self.planner.plan(
            intent=intent,
            cache_hit=cache_hit,
            estimated_rows=50,
            clarification_needed=needs_clarification,
            clarification_prompt=clarification_prompt,
        )

        if plan.strategy == Strategy.ASK_CLARIFICATION:
            latency_ms = int((time.perf_counter() - started) * 1000)
            self.telemetry.record(
                {
                    "event": "query_execution",
                    "strategy": plan.strategy.value,
                    "clarification_requested": True,
                    "confidence": confidence,
                    "latency_ms": latency_ms,
                }
            )
            return {
                "answer": clarification_prompt,
                "tool_trace": [],
                "stream": stages,
                "plan": asdict(plan),
            }

        if plan.strategy == Strategy.CACHE_FIRST and cached_payload:
            stages.append("Checking cache...")
            payload = cached_payload
        else:
            stages.append("Executing aggregation query...")
            min_days = None
            for flt in intent.filters:
                if flt.field == "last_contact_days" and flt.operator in (">", ">="):
                    min_days = int(flt.value)
            payload = self.aggregator.query_clients(
                limit=int(intent.limit),
                sort_by=intent.sort.field,
                order=intent.sort.direction,
                min_last_contact_days=min_days,
            )
            self.cache.put(key, payload)

        stages.append("Ranking clients...")
        rows = payload.get("rows", payload if isinstance(payload, list) else [])
        freshness_ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        explain_rows = [
            {
                **row,
                "explainability": {
                    "matched_filters": [asdict(f) for f in intent.filters],
                    "ranking_basis": intent.sort.field,
                    "source_fields": ["client_id", "name", "free_liquidity_chf", "last_contact_days"],
                    "freshness_timestamp": freshness_ts,
                },
            }
            for row in rows
        ]

        latency_ms = int((time.perf_counter() - started) * 1000)
        reward = self.rl_hooks.score_reward(latency_ms, cache_hit)
        self.telemetry.record(
            {
                "event": "query_execution",
                "strategy": plan.strategy.value,
                "cache_hit": cache_hit,
                "latency_ms": latency_ms,
                "rows_returned": len(explain_rows),
                "clarification_requested": False,
                "reward": reward,
            }
        )

        return {
            "answer": f"Returned {len(explain_rows)} clients using {plan.strategy.value}.",
            "rows": explain_rows,
            "tool_trace": [
                {
                    "strategy": plan.strategy.value,
                    "cache_hit": cache_hit,
                    "intent": asdict(intent),
                    "estimated_latency_ms": plan.estimated_latency_ms,
                    "estimated_cost": plan.estimated_cost,
                }
            ],
            "stream": stages,
            "plan": asdict(plan),
            "telemetry": self.telemetry.events[-1],
        }
