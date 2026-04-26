import { FormEvent, useEffect, useState } from 'react';
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
      setAnswer(data.answer ?? data.error ?? 'No answer generated.');
      setToolTrace(data.tool_trace ?? []);
    } catch (error) {
      setAnswer(String(error));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="container">
      <header>
        <h1>Apollo Query Prototype</h1>
        <p>React + TypeScript frontend for Flask + Ollama tools backend.</p>
      </header>

      <form className="chat-form" onSubmit={onSubmit}>
        <textarea
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          rows={4}
          placeholder="Ask a multi-client CRM question..."
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Running...' : 'Ask'}
        </button>
      </form>

      {answer && (
        <section className="panel">
          <h2>Assistant response</h2>
          <p>{answer}</p>
        </section>
      )}

      {toolTrace.length > 0 && (
        <section className="panel">
          <h2>Tool trace</h2>
          <pre>{JSON.stringify(toolTrace, null, 2)}</pre>
        </section>
      )}

      <section className="panel">
        <h2>Top liquidity snapshot</h2>
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
      </section>
    </main>
  );
}

export default App;
