from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class QueryObjective(str, Enum):
    RANK_CLIENTS = "rank_clients"
    LIST_CLIENTS = "list_clients"


class Strategy(str, Enum):
    CACHE_FIRST = "CACHE_FIRST"
    DIRECT_SQL = "DIRECT_SQL"
    REFRESH_AND_QUERY = "REFRESH_AND_QUERY"
    HYBRID = "HYBRID"
    ASK_CLARIFICATION = "ASK_CLARIFICATION"


@dataclass
class QueryFilter:
    field: str
    operator: str
    value: Any


@dataclass
class SortSpec:
    field: str
    direction: str = "desc"


@dataclass
class ParsedIntent:
    objective: QueryObjective
    metrics: List[str] = field(default_factory=list)
    filters: List[QueryFilter] = field(default_factory=list)
    sort: SortSpec = field(default_factory=lambda: SortSpec(field="free_liquidity_chf", direction="desc"))
    limit: int = 20
    requires_fresh_data: bool = False


@dataclass
class CacheEntry:
    payload: Dict[str, Any]
    created_at: float
    ttl_seconds: int

    def is_valid(self) -> bool:
        return time.time() <= self.created_at + self.ttl_seconds


@dataclass
class ExecutionPlan:
    strategy: Strategy
    requires_clarification: bool
    stream_progress: bool
    estimated_cost: float
    estimated_latency_ms: int
    clarification_question: Optional[str] = None


class QueryIntentParser:
    def parse(self, query: str) -> ParsedIntent:
        text = query.lower().strip()
        metrics = ["free_liquidity_chf"] if "liquidity" in text else []
        sort = SortSpec(field="free_liquidity_chf", direction="desc")
        filters: List[QueryFilter] = []
        limit = 20

        if "top" in text:
            for token in text.split():
                if token.isdigit():
                    limit = max(1, min(100, int(token)))
                    break

        if "no contact" in text or "last contact" in text:
            days = 90
            for token in text.split():
                if token.isdigit():
                    days = int(token)
            filters.append(QueryFilter(field="last_contact_days", operator=">", value=days))

        fresh = any(keyword in text for keyword in ["fresh", "latest", "up to date", "real-time"])
        return ParsedIntent(
            objective=QueryObjective.RANK_CLIENTS if metrics else QueryObjective.LIST_CLIENTS,
            metrics=metrics,
            filters=filters,
            sort=sort,
            limit=limit,
            requires_fresh_data=fresh,
        )


class ClarificationEngine:
    AMBIGUOUS = {
        "risky clients": "Do you want risk ranked by risk_class, by no-contact duration, or by AUM exposure?",
        "need attention": "Should attention be based on inactivity, low liquidity, or risk class?",
    }

    def evaluate(self, query: str) -> Tuple[bool, float, Optional[str]]:
        text = query.lower()
        for phrase, prompt in self.AMBIGUOUS.items():
            if phrase in text:
                return True, 0.35, prompt
        return False, 0.92, None


class QueryCache:
    def __init__(self, default_ttl_seconds: int = 30) -> None:
        self.default_ttl_seconds = default_ttl_seconds
        self._store: Dict[str, CacheEntry] = {}

    def fingerprint(self, intent: ParsedIntent) -> str:
        raw = json.dumps(asdict(intent), sort_keys=True, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        entry = self._store.get(key)
        if not entry:
            return None
        if not entry.is_valid():
            self._store.pop(key, None)
            return None
        return entry.payload

    def put(self, key: str, payload: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        self._store[key] = CacheEntry(payload=payload, created_at=time.time(), ttl_seconds=ttl_seconds or self.default_ttl_seconds)


class AdaptiveQueryPlanner:
    def plan(self, intent: ParsedIntent, cache_hit: bool, estimated_rows: int, clarification_needed: bool, clarification_prompt: Optional[str]) -> ExecutionPlan:
        if clarification_needed:
            return ExecutionPlan(Strategy.ASK_CLARIFICATION, True, True, 0.0, 50, clarification_prompt)
        if intent.requires_fresh_data:
            return ExecutionPlan(Strategy.REFRESH_AND_QUERY, False, True, 0.06, 350)
        if cache_hit:
            return ExecutionPlan(Strategy.CACHE_FIRST, False, True, 0.0, 20)
        if estimated_rows > 500:
            return ExecutionPlan(Strategy.HYBRID, False, True, 0.03, 220)
        return ExecutionPlan(Strategy.DIRECT_SQL, False, True, 0.02, 120)


class TelemetrySink:
    def __init__(self) -> None:
        self.events: List[Dict[str, Any]] = []

    def record(self, event: Dict[str, Any]) -> None:
        self.events.append(event)


class RLHooks:
    def score_reward(self, latency_ms: int, cache_hit: bool) -> float:
        return (1.0 if cache_hit else 0.0) + max(0.0, 1.0 - latency_ms / 1000.0)
