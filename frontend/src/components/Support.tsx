import { useEffect, useState } from 'react';
import { getSupportEval, getTeam, postSupport } from '../api';
import { Card } from './ui';

type Player = { name: string; role: string; tag: string; mult: number; base: number; points: number; events: { ball: string; points: number; reason: string }[] };
type Team = { current: { players: Player[]; total: number }; base: { total: number }; corrections: Record<string, { ball: string; title: string }>; note: string;
  diff?: { before: number; after: number; deltas: { name: string; delta: number }[] }; notice?: { text: string; source: string } };
type Reply = { resolved: boolean; answer: string; tools: string[]; source: string; handoff: { queue: string; summary: string } | null };
type Eval = { n: number; auto_resolved_pct: number; routing_correct_pct: number; false_resolutions: number; key_facts_pct: number;
  rows: { question: string; expected: string; got: string; routing_ok: boolean; queue: string | null }[] };
const SAMPLES = ['Why did my points drop after the match ended?', 'Why is my captain score doubled?', 'Mere points kam kyun hue?', 'How many points did Imran Qadri get?', 'Where is my withdrawal?', 'What is my rank in the contest?'];

export default function Support({ lang }: { lang: string }) {
  const [corr, setCorr] = useState('none'), [team, setTeam] = useState<Team | null>(null), [open, setOpen] = useState(''), [err, setErr] = useState('');
  const [q, setQ] = useState(''), [thread, setThread] = useState<{ q: string; r: Reply }[]>([]), [ev, setEv] = useState<Eval | null>(null), [busy, setBusy] = useState('');
  const [tickets, setTickets] = useState(10000), [mins, setMins] = useState(4), [cost, setCost] = useState(40), [share, setShare] = useState(35);
  useEffect(() => { getTeam<Team>(corr).then(setTeam).catch(e => setErr(e.message)); }, [corr]);
  const ask = (text: string) => { if (text.trim().length < 2) return; setBusy('ask'); setQ('');
    postSupport<Reply>(text, corr, lang).then(r => setThread(t => [{ q: text, r }, ...t])).catch(e => setErr(e.message)).finally(() => setBusy('')); };
  const runEval = () => { setBusy('eval'); getSupportEval<Eval>().then(setEv).catch(e => setErr(e.message)).finally(() => setBusy('')); };
  if (!team) return <div className="page"><p className="empty">{err || 'Loading'}</p></div>;
  const deflect = ev ? ev.auto_resolved_pct / 100 : 0, monthly = tickets * (share / 100) * deflect;
  return (
    <div className="page wide">
      <Card title="Support copilot" sub="Hypothesis to validate with the customer: after matches, many tickets ask why fantasy points changed. This module explains points, handles scorer corrections and escalates what it should not answer.">
        <p className="hint">{team.note} Simulated tickets and sample team only.</p>
        <div className="chips" role="radiogroup" aria-label="Scorer correction"><b className="lbl">Scorer correction</b>
          <button role="radio" aria-checked={corr === 'none'} className={`chip ${corr === 'none' ? 'on' : ''}`} onClick={() => setCorr('none')}>None</button>
          {Object.entries(team.corrections).map(([k, c]) => <button key={k} role="radio" aria-checked={corr === k} className={`chip ${corr === k ? 'on' : ''}`} onClick={() => setCorr(k)}>Ball {c.ball}: {k === 'c1' ? 'caught to run out' : 'four to leg byes'}</button>)}</div>
        <table className="tbl"><thead><tr><th>Your team</th><th>Role</th><th>Base</th><th>x</th><th>Points</th></tr></thead><tbody>
          {team.current.players.map(p => <><tr key={p.name} onClick={() => setOpen(open === p.name ? '' : p.name)} className="click"><th>{p.name}{p.tag && <em className="live"> {p.tag}</em>}</th><td className="sm">{p.role}</td><td>{p.base}</td><td>{p.mult}</td><td>{p.points}</td></tr>
            {open === p.name && <tr key={p.name + 'l'}><td colSpan={5} className="sm">{p.events.map(e => `${e.ball} ${e.reason} +${e.points}`).join(' · ') || 'No points events'}</td></tr>}</>)}
          <tr><th>Total</th><td /><td /><td /><td className="tot">{team.current.total}{team.diff && <small> (was {team.diff.before})</small>}</td></tr></tbody></table>
        <p className="hint">Tap a player to see the ledger behind their points.</p>
        {team.notice && <div className="insight"><span className="tag">Notification to customer</span><p>{team.notice.text}</p><small>{team.notice.source}</small></div>}
      </Card>
      <Card title="Ask the copilot" sub="Routing is decided by rules. The AI only polishes answers that were already verified. Anything out of scope is handed to a person.">
        <div className="chips">{SAMPLES.map(s => <button key={s} className="chip" onClick={() => ask(s)}>{s}</button>)}</div>
        <form className="composer" onSubmit={e => { e.preventDefault(); ask(q); }}><input value={q} onChange={e => setQ(e.target.value)} placeholder="Type a customer question" aria-label="Customer question" maxLength={300} />
          <button className="primary" disabled={busy === 'ask'}>Ask</button></form>
        {err && <p className="err" role="alert">{err}</p>}
        {thread.map((t, i) => <div key={i} className="ticket"><p className="tq">{t.q}</p>
          <span className={`badge2 ${t.r.resolved ? 'ok' : 'esc'}`}>{t.r.resolved ? 'Resolved by copilot' : 'Escalated to a person'}</span>
          <p className="say">{t.r.answer}</p>
          {t.r.handoff && <p className="hint"><b>Handoff:</b> {t.r.handoff.queue}. {t.r.handoff.summary}</p>}
          <small>{t.r.source} · tools: {t.r.tools.join(', ')}</small></div>)}
      </Card>
      <Card title="Deflection evaluation" sub="14 simulated tickets with known right answers. Safety metric: false resolutions must be 0."
        right={<button className="primary" onClick={runEval} disabled={busy === 'eval'}>{busy === 'eval' ? 'Running' : 'Run evaluation'}</button>}>
        {ev ? <><div className="tiles four">{[['Auto-resolved', `${ev.auto_resolved_pct}%`, 'of simulated tickets'], ['Routing correct', `${ev.routing_correct_pct}%`, 'resolve vs escalate'],
          ['False resolutions', ev.false_resolutions, 'must stay 0'], ['Key facts present', `${ev.key_facts_pct}%`, 'in resolved answers']].map(([a, b, c]) => <div className="tile" key={String(a)}><span>{a}</span><b>{b}</b><small>{c}</small></div>)}</div>
          <table className="tbl"><thead><tr><th>Ticket</th><th>Expected</th><th>Got</th><th>Queue</th></tr></thead><tbody>
            {ev.rows.map((r, i) => <tr key={i}><th>{r.question}</th><td className="sm">{r.expected}</td><td className={r.routing_ok ? 'pass' : 'fail'}>{r.got}</td><td className="sm">{r.queue ?? ''}</td></tr>)}</tbody></table></> : <p className="empty">Run the evaluation to measure how many tickets the copilot can safely resolve.</p>}
      </Card>
      <Card title="Impact calculator" sub="Placeholders, not Dream11 data. Replace with real volumes during discovery. Uses the measured deflection rate above.">
        <div className="calc">{([['Points tickets per month', tickets, setTickets], ['Minutes per ticket', mins, setMins], ['Cost per ticket (rupees)', cost, setCost], ['Share about points (%)', share, setShare]] as [string, number, (n: number) => void][])
          .map(([l, v, f]) => <label key={l}>{l}<input className="txt" type="number" min={0} value={v} onChange={e => f(Number(e.target.value))} /></label>)}</div>
        <div className="tiles four"><div className="tile"><span>Tickets deflected</span><b>{Math.round(monthly).toLocaleString('en-IN')}</b><small>per month</small></div>
          <div className="tile"><span>Agent hours freed</span><b>{Math.round(monthly * mins / 60).toLocaleString('en-IN')}</b><small>per month</small></div>
          <div className="tile"><span>Cost avoided</span><b>{Math.round(monthly * cost).toLocaleString('en-IN')}</b><small>rupees per month</small></div>
          <div className="tile"><span>Deflection used</span><b>{ev ? `${ev.auto_resolved_pct}%` : 'run eval'}</b><small>from simulated tickets</small></div></div>
      </Card>
    </div>
  );
}
