import { FormEvent, useEffect, useMemo, useState } from 'react';
import './App.css';

type LiquidityRow = {
  client_id: string;
  name: string;
  free_liquidity_chf: number;
  last_contact_days: number;
};

type ChatResponse = {
  answer?: string;
  error?: string;
  tool_trace?: Array<Record<string, unknown>>;
};

function formatAssistantText(text: string): string {
  return text
    .replace(/\*\*/g, '')
    .replace(/`/g, '')
    .replace(/\|/g, ' ')
    .replace(/\s{2,}/g, ' ')
    .trim();
}

function App() {
  const [message, setMessage] = useState(
    'Which clients have the highest free liquidity and no contact in the last 90 days?'
  );
  const [answer, setAnswer] = useState('');
  const [toolTrace, setToolTrace] = useState<Array<Record<string, unknown>>>([]);
  const [rows, setRows] = useState<LiquidityRow[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch('/api/aggregation/liquidity?limit=5')
      .then((response) => response.json())
      .then((data) => setRows(data.rows ?? []))
      .catch(() => setRows([]));
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setAnswer('');
    setToolTrace([]);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      });
      const data: ChatResponse = await response.json();
      setAnswer(formatAssistantText(data.answer ?? data.error ?? 'No answer generated.'));
      setToolTrace(data.tool_trace ?? []);
    } catch (error) {
      setAnswer(String(error));
    } finally {
      setLoading(false);
    }
  }

  const prettyTrace = useMemo(() => JSON.stringify(toolTrace, null, 2), [toolTrace]);

  return (
    <main className="container">
      <header className="hero">
        <h1>Apollo Query Assistant</h1>
        <p>Ask cross-client questions in plain language. Results are computed by deterministic backend tools.</p>
      </header>

      <form className="chat-form" onSubmit={onSubmit}>
        <label htmlFor="prompt">Your question</label>
        <textarea
          id="prompt"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          rows={4}
          placeholder="Example: Give me top 5 clients by last_contact_days, sorted descending by first_name"
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Working…' : 'Ask'}
        </button>
      </form>

      {answer && (
        <section className="panel">
          <h2>Assistant response</h2>
          <p className="answer">{answer}</p>
        </section>
      )}

      {toolTrace.length > 0 && (
        <section className="panel muted">
          <h2>Tool trace</h2>
          <pre>{prettyTrace}</pre>
        </section>
      )}

      <section className="panel">
        <h2>Top liquidity snapshot</h2>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Client</th>
                <th>Liquidity (CHF)</th>
                <th>Last contact (days)</th>
                <th>Reference</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.client_id}>
                  <td>{row.name}</td>
                  <td>{row.free_liquidity_chf.toLocaleString()}</td>
                  <td>{row.last_contact_days}</td>
                  <td>{row.client_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  );
}

export default App;
