import { useEffect, useRef, useState } from 'react';
import { streamAgent } from '../api';
import type { AgentResult, Lang, Lens, Side, Step } from '../types';
import { Icon } from './ui';

type Msg = { id: number; q: string; steps: Step[]; text: string; done: boolean; result?: AgentResult; err?: string };
const ASKS = ['Why did that moment matter?', 'What happens if the next ball is a six?', 'Explain Umpire\'s Call', 'How is the pressure index calculated?', 'How is the bowler doing?', 'Who is standing out for fantasy fans?'];
const SR: any = typeof window !== 'undefined' ? ((window as any).SpeechRecognition || (window as any).webkitSpeechRecognition) : undefined;
const short = (a: Record<string, unknown>) => { const s = JSON.stringify(a); return s === '{}' ? '' : s.length > 46 ? s.slice(0, 45) + '…' : s; };

export default function Copilot({ ball, lens, lang, side, ai, onClose }: { ball: number; lens: Lens; lang: Lang; side: Side; ai: boolean; onClose: () => void }) {
  const [msgs, setMsgs] = useState<Msg[]>([]), [q, setQ] = useState(''), [busy, setBusy] = useState(false), [listening, setListening] = useState(false);
  const end = useRef<HTMLDivElement>(null), ac = useRef<AbortController | null>(null), seq = useRef(0);
  useEffect(() => { end.current?.scrollIntoView({ block: 'nearest' }); }, [msgs]);
  useEffect(() => () => ac.current?.abort(), []);
  const patch = (id: number, f: (m: Msg) => Msg) => setMsgs(ms => ms.map(m => (m.id === id ? f(m) : m)));
  const send = (text: string) => {
    if (text.trim().length < 2 || busy) return;
    const id = ++seq.current;
    setQ(''); setBusy(true); setMsgs(ms => [...ms, { id, q: text, steps: [], text: '', done: false }]);
    ac.current?.abort(); ac.current = new AbortController();
    streamAgent(text, lens, ball, lang, side, e => {
      if (e.type === 'step') patch(id, m => ({ ...m, steps: [...m.steps, { tool: e.tool, args: e.args, observation: e.observation }] }));
      else if (e.type === 'token') patch(id, m => ({ ...m, text: m.text + e.text }));
      else if (e.type === 'final') patch(id, m => ({ ...m, done: true, result: e.result, text: e.result.answer }));
    }, ac.current.signal).catch(err => patch(id, m => ({ ...m, done: true, err: err.message }))).finally(() => setBusy(false));
  };
  const listen = () => { const r = new SR(); r.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'; r.onstart = () => setListening(true); r.onend = () => setListening(false); r.onerror = () => setListening(false); r.onresult = (e: any) => send(e.results[0][0].transcript); r.start(); };
  return (
    <aside className="drawer" role="complementary" aria-label="Copilot">
      <header><div><b><Icon n="sparkle" s={16} /> Copilot</b><small>Plans, calls tools, shows its work</small></div>
        <div className="row"><span className={`src ${ai ? 'ai' : ''}`}>{ai ? 'LLM agent' : 'Rules router'}</span><button className="icon" onClick={onClose} aria-label="Close copilot"><Icon n="x" s={16} /></button></div></header>
      <div className="msgs" aria-live="polite">
        {msgs.length === 0 && <div className="intro"><p>Ask about the match or the rules. With an LLM key the copilot chooses tools itself; every answer is checked against what the tools returned.</p>
          <div className="chips">{ASKS.map(a => <button key={a} className="chip" onClick={() => send(a)}>{a}</button>)}</div></div>}
        {msgs.map(m => (
          <div key={m.id} className="turn"><div className="mu">{m.q}</div>
            <div className="ma">
              {m.steps.length > 0 && <ol className="trace" aria-label="Steps taken">{m.steps.map((s, i) => <li key={i}><span className="ok"><Icon n="check" s={12} /></span><div><code>{s.tool}{short(s.args) && <i>{short(s.args)}</i>}</code><details><summary>result</summary><pre>{s.observation}</pre></details></div></li>)}</ol>}
              {!m.done && m.steps.length === 0 && !m.text && <p className="think">Planning</p>}
              {m.err ? <p className="err" role="alert">{m.err}</p> : <p className={`say ${m.done ? '' : 'typing'}`}>{m.text}</p>}
              {m.result && <>
                <div className="meta"><span className={`src ${m.result.mode === 'agent' ? 'ai' : ''}`}>{m.result.mode === 'agent' ? `Agent · ${m.result.steps} tool call(s)` : 'Rules router'}</span>
                  {m.result.mode === 'router' && m.result.tools.map(t => <span className="tag" key={t}>{t}</span>)}</div>
                {m.result.note && <small className="hint">{m.result.note}</small>}
                {m.result.citations.map(c => <details className="cite" key={c.id}><summary>[{c.id}] {c.title}</summary><p>{c.text}</p><small>{c.source}</small></details>)}
                <small className="hint">{m.result.source}</small></>}
            </div></div>))}
        <div ref={end} />
      </div>
      <form className="composer" onSubmit={e => { e.preventDefault(); send(q); }}>
        <input value={q} onChange={e => setQ(e.target.value)} placeholder="Ask about this moment or a rule" aria-label="Question" maxLength={300} />
        {SR && <button type="button" className={`icon ${listening ? 'on' : ''}`} onClick={listen} aria-label="Ask by voice"><Icon n="mic" s={16} /></button>}
        <button className="primary" disabled={busy}><Icon n="send" s={15} /></button>
      </form>
    </aside>
  );
}
