"use client";
import { useState } from "react";
import { motion } from "framer-motion";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Ev = {
  stage: string; agent: string; detail: string;
  nudge?: { action_label: string }; executed?: boolean;
};

export default function Home() {
  const [events, setEvents] = useState<Ev[]>([]);
  const [running, setRunning] = useState(false);

  const run = () => {
    setEvents([]);
    setRunning(true);
    const es = new EventSource(`${API_URL}/api/stream`);
    es.onmessage = (e) => {
      const ev: Ev = JSON.parse(e.data);
      setEvents((prev) => [...prev, ev]);
      if (ev.stage === "done") { es.close(); setRunning(false); }
    };
    es.onerror = () => { es.close(); setRunning(false); };
  };

  return (
    <main className="min-h-screen bg-zinc-950 text-zinc-100 p-8">
      <h1 className="text-2xl font-bold">AriAgent</h1>
      <p className="text-zinc-400 mb-4">Proactive financial companion — live agent reasoning</p>
      <button onClick={run} disabled={running}
        className="px-4 py-2 rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50">
        {running ? "Running..." : "Run agent loop"}
      </button>
      <div className="mt-6 space-y-3 max-w-2xl">
        {events.map((ev, i) => (
          <motion.div key={i} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
            className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
            <div className="text-xs uppercase tracking-wide text-emerald-400">
              {ev.stage} · {ev.agent}
            </div>
            <div className="mt-1">{ev.detail}</div>
            {ev.nudge && (
              <button className="mt-3 px-3 py-1.5 rounded bg-sky-600 text-sm">
                {ev.nudge.action_label}
              </button>
            )}
          </motion.div>
        ))}
      </div>
    </main>
  );
}
