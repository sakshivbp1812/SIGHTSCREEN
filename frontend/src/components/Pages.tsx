import { useEffect, useRef, useState, type ReactNode } from 'react';
import { getAuth, getEvalAgent, getEvalBrief, getEvalLens, getEvalRag, getEvalRed, getFeed, getImpact, getOps, getStats, getTraceStats, getTraces, postAsk, postScenario, setAdminToken } from '../api';
import type { Ctx, Snap, Stats } from '../types';
import { Card, Delta, Ground, Icon, OverBars, Ring, Worm, heat } from './ui';

const rr = (n: number) => n.toFixed(2);
function useStats(ball: number) {
  const [s, setS] = useState<Stats | null>(null);
  useEffect(() => { getStats<Stats>(ball).then(setS).catch(() => setS(null)); }, [ball]);
  return s;
}
const Watch = ({ list }: { list: any[] }) => (
  <ol className="watch">{list.map((w, i) => (
    <li key={w.name + w.role}><span className="rank">{i + 1}</span><div><b>{w.name}</b><em>{w.role}</em><small>{w.why}</small></div>
      <strong>{w.impact}</strong></li>))}</ol>
);

export function Dashboard({ ctx, stage }: { ctx: Ctx; stage: ReactNode }) {
  const { match, ball, seek } = ctx, s = match.frames[ball], st = useStats(ball), feed = match.deliveries.slice(0, ball).reverse();
  const tiles: [string, string | number, string][] = [
    ['Runs needed', s.runs_needed, `target ${s.target}`], ['Balls left', s.balls_remaining, `${s.overs_display} overs bowled`],
    ['Required rate', rr(s.required_rate), `current ${rr(s.current_rate)}`], ['Wickets in hand', 10 - s.wickets, `${s.wickets} down`]];
  return (
    <div className="dash">
      <div className="stage-col">{stage}</div>
      <Card title="Match pulse" sub="Live numbers from the match engine" cls="pulse">
        <div className="tiles">{tiles.map(([a, b, c]) => <div key={a} className="tile"><span>{a}</span><b>{b}</b><small>{c}</small></div>)}</div>
        <div className="pressure"><Ring value={s.pressure} size={84} />
          <div><b style={{ color: heat(s.pressure) }}>{s.pressure >= 75 ? 'Intense' : s.pressure >= 45 ? 'Tense' : 'Comfortable'}</b>
            <small>Chase pressure index. A transparent heuristic from required rate and wickets in hand, not a win probability.</small></div></div>
        {s.result && <p className="result">{s.result}{s.result.startsWith(s.batting) ? ` with ${10 - s.wickets} wickets in hand` : ''}</p>}
      </Card>
      <Card title="Chase chart" sub="Runs still needed, ball by ball, against the even-rate path"><Worm match={match} ball={ball} /></Card>
      <Card title="Runs by over" sub="Red bars mark an over with a wicket">{st ? <OverBars data={st.runs_by_over} /> : <p className="empty">Loading</p>}</Card>
      <Card title="Ball by ball" sub="Click a ball to jump the replay to it" cls="feed">
        {feed.length === 0 ? <p className="empty">Press Play replay to start. Key moments trigger Live Lens.</p> :
          <ol className="tl">{feed.map(d => <li key={d.idx}><button onClick={() => seek(d.video_ts)} className={`k-${d.kind}`}>
            <b>{d.label}</b><span>{d.bowler} to {d.batter}</span><i>{d.wicket ? `OUT · ${d.how}` : d.runs === 0 ? '·' : d.runs}</i></button></li>)}</ol>}
      </Card>
      <Card title="Standout players" sub="Illustrative impact score">{st && st.watchlist.length ? <Watch list={st.watchlist.slice(0, 3)} /> : <p className="empty">Appears once the replay starts.</p>}</Card>
      <Card title="Venue analysis" right={<span className="pin"><Icon n="pin" s={14} /> {st?.venue.name}</span>}>
        {st ? <VenueBlock st={st} /> : <p className="empty">Loading</p>}
      </Card>
    </div>
  );
}

function VenueBlock({ st }: { st: Stats }) {
  const b = st.boundaries, sq = b.four_square + b.six_square, str = b.four_straight + b.six_straight;
  return (<>
    <Ground square={st.venue.square_m} straight={st.venue.straight_m} sq={sq} str={str} />
    <p className="hint">Sixes {b.six_square + b.six_straight}, fours {b.four_square + b.four_straight} so far. The ground is drawn to scale; boundaries are counted by zone, not by exact direction.</p>
  </>);
}

function Compare({ before, after, delta }: { before: Snap; after: Snap; delta: any }) {
  const rows: [string, string, string, ReactNode][] = [
    ['Score', `${before.runs}/${before.wickets}`, `${after.runs}/${after.wickets}`, null],
    ['Needed', `${before.runs_needed} from ${before.balls_remaining}`, `${after.runs_needed} from ${after.balls_remaining}`, <Delta a={before.runs_needed} b={after.runs_needed} lowerIsBetter />],
    ['Required rate', rr(before.required_rate), rr(after.required_rate), <Delta a={before.required_rate} b={after.required_rate} lowerIsBetter />],
    ['Pressure', String(before.pressure), String(after.pressure), <Delta a={before.pressure} b={after.pressure} lowerIsBetter />]];
  return (
    <div className="ba">{rows.map(r => (<div key={r[0]}><span>{r[0]}</span><b>{r[1]}</b><em>to</em><b>{r[2]}</b>{r[3]}</div>))}
      <small>{delta.runs_added} run(s), {delta.wickets_lost} wicket(s), {delta.balls_used} ball(s) used</small></div>
  );
}

export function Impact({ ctx }: { ctx: Ctx }) {
  const { match, ball, lens, lang, side } = ctx, [sel, setSel] = useState(0), [r, setR] = useState<any>(null);
  const idx = sel && sel <= ball ? sel : match.key_moments.filter(k => k <= ball).pop() ?? 0;
  useEffect(() => { if (idx > 0) getImpact(idx, lens, lang, side).then(setR).catch(() => setR(null)); else setR(null); }, [idx, lens, lang, side]);
  const keys = match.key_moments.filter(k => k <= ball);
  return (
    <div className="page">
      <Card title="Impact replay" sub="How one delivery changed the match. Pick a key moment.">
        <div className="chips">{keys.map(k => { const d = match.deliveries[k - 1]; return (
          <button key={k} className={`chip k-${d.kind} ${k === idx ? 'on' : ''}`} onClick={() => setSel(k)}>{d.label} · {d.kind === 'WICKET' ? 'W' : d.runs}</button>); })}</div>
        {!r ? <p className="empty">Play the replay past a wicket, four or six to unlock impact analysis.</p> : (<>
          <div className="insight"><span className="tag">{r.kind} · {r.ball}</span><p>{r.text}</p><small>{r.source}</small></div>
          <Compare before={r.before} after={r.after} delta={r.delta} /></>)}
      </Card>
    </div>
  );
}

const PRESETS: [string, string, [number, boolean][]][] = [
  ['Dot ball', 'Bowler wins the ball', [[0, false]]], ['Single', 'Rotate the strike', [[1, false]]], ['Four', 'Boundary', [[4, false]]],
  ['Six', 'Maximum', [[6, false]]], ['Wicket', 'Batting side loses one', [[0, true]]],
  ['Big over', '6, 6, 1, 1, 1, 1', [[6, false], [6, false], [1, false], [1, false], [1, false], [1, false]]],
  ['Quiet over + wicket', '0, 1, W, 0, 1, 0', [[0, false], [1, false], [0, true], [0, false], [1, false], [0, false]]]];
export function Lab({ ctx }: { ctx: Ctx }) {
  const { ball } = ctx, [r, setR] = useState<any>(null), [name, setName] = useState(''), [err, setErr] = useState('');
  useEffect(() => { setR(null); setName(''); }, [ball]);
  const run = (n: string, b: [number, boolean][]) => { setName(n); setErr(''); postScenario(ball, b).then(setR).catch(e => setErr(e.message)); };
  return (
    <div className="page">
      <Card title="What-if lab" sub="Starting from the current ball. The replay itself never changes.">
        <div className="presets">{PRESETS.map(([n, d, b]) => <button key={n} className={n === name ? 'on' : ''} onClick={() => run(n, b)}><b>{n}</b><small>{d}</small></button>)}</div>
        {err && <p className="err" role="alert">{err}</p>}
        {r ? <><p className="say">{name}: required rate {rr(r.before.required_rate)} to {rr(r.after.required_rate)}, pressure {r.before.pressure} to {r.after.pressure}.</p>
          <Compare before={r.before} after={r.after} delta={r.delta} /></> : <p className="empty">Choose a scenario to see how the chase would change.</p>}
      </Card>
    </div>
  );
}

export function StatsPage({ ctx }: { ctx: Ctx }) {
  const s = useStats(ctx.ball);
  if (!s) return <div className="page"><p className="empty">Loading</p></div>;
  return (
    <div className="page two">
      <Card title="Batters" sub="Totals include innings before the replay window">
        <table className="tbl"><thead><tr><th>Name</th><th>Runs</th><th>Balls</th><th>SR</th><th>4s</th><th>6s</th></tr></thead>
          <tbody>{s.batters.map(x => <tr key={x.name}><th>{x.name}{x.out ? <em> out</em> : <em className="live"> in</em>}</th><td>{x.runs}</td><td>{x.balls}</td><td>{x.sr}</td><td>{x.fours}</td><td>{x.sixes}</td></tr>)}</tbody></table>
      </Card>
      <Card title="Bowlers" sub="Figures within this replay (overs 14 to 20)">
        <table className="tbl"><thead><tr><th>Name</th><th>W/R</th><th>Balls</th><th>Econ</th><th>Dots</th></tr></thead>
          <tbody>{s.bowlers.map(x => <tr key={x.name}><th>{x.name}</th><td>{x.wickets}/{x.runs}</td><td>{x.balls}</td><td>{x.econ}</td><td>{x.dots}</td></tr>)}</tbody></table>
      </Card>
      <Card title="Runs by over"><OverBars data={s.runs_by_over} /></Card>
      <Card title="Venue analysis" right={<span className="pin"><Icon n="pin" s={14} /> {s.venue.name}</span>}><VenueBlock st={s} /></Card>
    </div>
  );
}

export function Fantasy({ ctx }: { ctx: Ctx }) {
  const { ball, lens, lang, side } = ctx, s = useStats(ball), [res, setRes] = useState<any>(null), [busy, setBusy] = useState(false), [err, setErr] = useState('');
  useEffect(() => { setRes(null); }, [ball]);
  const explain = () => { setBusy(true); setErr('');
    postAsk('Which players are standing out for fantasy-minded fans right now, and why?', lens, ball, lang, side).then(setRes).catch(e => setErr(e.message)).finally(() => setBusy(false)); };
  if (!s) return <div className="page"><p className="empty">Loading</p></div>;
  const top = Math.max(1, ...s.watchlist.map(w => w.impact));
  return (
    <div className="page">
      <Card title="Fantasy pulse" sub="Who is making the most impact in this match so far" right={<button className="primary" onClick={explain} disabled={busy || ball === 0}>{busy ? 'Thinking' : 'Explain with AI'}</button>}>
        {s.watchlist.length === 0 ? <p className="empty">Play the replay to see standout players.</p> : (
          <ol className="watch big">{s.watchlist.map((w, i) => (
            <li key={w.name + w.role}><span className="rank">{i + 1}</span><div><b>{w.name}</b><em>{w.role}</em><small>{w.why}</small>
              <div className="meter"><i style={{ width: `${(w.impact / top) * 100}%` }} /></div></div><strong>{w.impact}</strong></li>))}</ol>)}
        {err && <p className="err" role="alert">{err}</p>}
        {res && <div className="insight"><span className="tag">AI explanation</span><p>{res.answer}</p><small>{res.source}. Tools: {res.tools.join(', ')}</small></div>}
        <p className="disc">{s.disclaimer}</p>
      </Card>
    </div>
  );
}

export function Settings({ videoUrl, setVideoUrl, offset, setOffset, ai }: { videoUrl: string; setVideoUrl: (v: string) => void; offset: number; setOffset: (n: number) => void; ai: string }) {
  const on = ai && ai !== 'none';
  return (
    <div className="page two">
      <Card title="AI status"><p className="say"><span className={`src ${on ? 'ai' : ''}`}>{on ? `AI on: ${ai}` : 'AI off: rules engine'}</span></p>
        <p className="hint">{on ? 'Explanations and answers are written by the model from verified match facts. Output with an unverified number is rejected.' :
          'No LLM key is set on the server, so answers come from the deterministic engine. Add GROQ_API_KEY or GEMINI_API_KEY to the server environment to switch the LLM on.'}</p></Card>
      <Card title="Use your own video" sub="Optional. Only use video you have the rights to use.">
        <input className="txt" value={videoUrl} onChange={e => setVideoUrl(e.target.value.trim())} placeholder="https://example.com/replay.mp4" aria-label="Video URL" />
        <label className="hint">Sync offset in seconds <input className="txt sm" type="number" value={offset} onChange={e => setOffset(Number(e.target.value))} /></label>
      </Card>
      <AdminAccess />
      <Card title="About this demo"><p className="hint">Fictional teams, players and venue. The match is simulated ball by ball and stored in a database. No official live scores,
        fantasy points or betting advice. The impact score and pressure index are illustrative metrics.</p></Card>
    </div>
  );
}

type LensEval = { avg_faithfulness: number; judge_by: string; provider: string; n: number; ai_used_pct: number; guard_rejections: number; key_fact_coverage_pct: number; grounded_pct: number; avg_ms: number; max_words: number;
  rows: { ball: string; kind: string; source: string; covers_key_facts: boolean; ms: number; text: string }[] };
type Red = { provider: string; total: number; passed: number; cases: { case: string; question: string; passed: boolean; source: string; answer: string }[] };

export function AIQuality({ ctx }: { ctx: Ctx }) {
  const { lens, lang, side } = ctx, [le, setLe] = useState<LensEval | null>(null), [rt, setRt] = useState<Red | null>(null), [bs, setBs] = useState<any>(null), [rg, setRg] = useState<any>(null), [ag, setAg] = useState<any>(null), [busy, setBusy] = useState(''), [err, setErr] = useState('');
  const run = (which: 'lens' | 'red' | 'brief' | 'rag' | 'agent') => { setBusy(which); setErr('');
    (which === 'lens' ? getEvalLens<LensEval>(lens, lang, side, 6).then(setLe) : which === 'red' ? getEvalRed<Red>(lang, side).then(setRt) : which === 'brief' ? getEvalBrief<any>().then(setBs) : which === 'agent' ? getEvalAgent<any>().then(setAg) : getEvalRag<any>().then(setRg)).catch(e => setErr(e.message)).finally(() => setBusy('')); };
  const kpi = (a: string, b: string | number, c: string) => <div className="tile" key={a}><span>{a}</span><b>{b}</b><small>{c}</small></div>;
  return (
    <div className="page">
      <Card title="AI quality" sub="Sightscreen tests its own AI instead of trusting it. Uses the current Explain-as, language and fan-side settings.">
        <p className="hint">Runs call the live model when an AI key is set (about 15 seconds), otherwise they test the rules engine. Limited to a few runs per IP.</p>
        <div className="row"><button className="primary" onClick={() => run('lens')} disabled={!!busy}>{busy === 'lens' ? 'Running' : 'Run Live Lens evaluation'}</button>
          <button className="primary" onClick={() => run('red')} disabled={!!busy}>{busy === 'red' ? 'Running' : 'Run red-team suite'}</button>
          <button className="primary" onClick={() => run('brief')} disabled={!!busy}>{busy === 'brief' ? 'Running' : 'Run Catch-me-up sweep'}</button>
          <button className="primary" onClick={() => run('rag')} disabled={!!busy}>{busy === 'rag' ? 'Running' : 'Run retrieval evaluation'}</button>
          <button className="primary" onClick={() => run('agent')} disabled={!!busy}>{busy === 'agent' ? 'Running' : 'Run agent safety regression'}</button></div>
        {err && <p className="err" role="alert">{err}</p>}
      </Card>
      {ag && <Card title="Agent safety regression" sub={`${ag.passed} of ${ag.total} cases pass · ${ag.model} · prompt ${ag.prompt_version}. Replays recorded model outputs through the real agent loop and verifier; no LLM calls.`}>
        <table className="tbl"><thead><tr><th>Case</th><th>Expected outcome</th><th>Result</th></tr></thead><tbody>{ag.cases.map((c: any) => <tr key={c.case}><th>{c.case}</th><td className="sm">{c.expected}</td><td className={c.passed ? 'pass' : 'fail'}>{c.passed ? 'pass' : `fail (${c.got})`}</td></tr>)}</tbody></table></Card>}
      {rg && <Card title="Retrieval evaluation" sub={`${rg.n} labelled questions against the cited knowledge base (BM25 search).`}>
        <div className="tiles four">{[kpi('Recall at 1', `${rg.recall_at_1}%`, 'right passage ranked first'), kpi('Recall at 3', `${rg.recall_at_3}%`, 'right passage in the top three'), kpi('MRR', rg.mrr, 'mean reciprocal rank')]}</div>
        {rg.misses.length > 0 && <p className="hint">Not ranked first: {rg.misses.join('; ')}</p>}</Card>}
      {bs && <Card title="Catch-me-up sweep" sub={`${bs.n} briefings: every ball x 3 languages x 2 lengths. Average ${bs.avg_words} words, about ${bs.avg_read_seconds} s to read, longest ${bs.max_words} words.`}>
        <div className="tiles four">{Object.entries(bs.pass_pct).map(([k, v]) => kpi(k.replace(/_/g, ' '), `${v}%`, 'of briefings'))}</div></Card>}
      {le && <Card title="Live Lens evaluation" sub={`${le.n} key moments · ${lens} · ${lang} · provider ${le.provider}`}>
        <div className="tiles four">{[kpi('Key facts covered', `${le.key_fact_coverage_pct}%`, 'name and runs needed present'), kpi('Numbers verified', `${le.grounded_pct}%`, 'every number found in facts'), kpi('Faithfulness', `${le.avg_faithfulness} / 5`, `judge: ${le.judge_by}`),
          kpi('AI answers used', `${le.ai_used_pct}%`, 'rest fell back to rules'), kpi('Hallucinations blocked', le.guard_rejections, `avg ${le.avg_ms} ms`)]}</div>
        <table className="tbl"><thead><tr><th>Ball</th><th>Moment</th><th>Source</th><th>Facts</th><th>ms</th></tr></thead><tbody>
          {le.rows.map(r => <tr key={r.ball}><th>{r.ball}</th><td>{r.kind}</td><td className="sm">{r.source}</td><td className={r.covers_key_facts ? 'pass' : 'fail'}>{r.covers_key_facts ? 'pass' : 'fail'}</td><td>{r.ms}</td></tr>)}</tbody></table></Card>}
      {rt && <Card title="Red-team suite" sub={`${rt.passed} of ${rt.total} checks passed · provider ${rt.provider}`}>
        <table className="tbl"><thead><tr><th>Check</th><th>Question</th><th>Result</th></tr></thead><tbody>
          {rt.cases.map(c => <tr key={c.case}><th>{c.case}</th><td className="sm">{c.question}</td><td className={c.passed ? 'pass' : 'fail'}>{c.passed ? 'pass' : 'fail'}</td></tr>)}</tbody></table></Card>}
    </div>
  );
}

type Ops = { uptime_s: number; requests: number; error_rate_pct: number; p50_ms: number; p95_ms: number; ai_provider: string; guard_block_rate_pct: number;
  llm: { calls: number; failures: number; cache_hits: number; accepted: number; rejected: number } };
type Feed = { raw_count: number; accepted: number; duplicates: number; reordered: number; quarantined: number; backfilled: number; reconciled: boolean;
  final: { runs: number; wickets: number; overs: string }; reference: { runs: number; wickets: number; overs: string };
  cells: { pos: number; label: string; status: string }[]; incidents: { severity: string; type: string; reason: string; message: number; vendor: string }[];
  samples: { vendor: string; raw: object; canonical: object }[]; summary: { text: string; source: string } };

export function ControlRoom() {
  const [tstats, setTstats] = useState<any>(null), [tr, setTr] = useState<any[]>([]), [ops, setOps] = useState<Ops | null>(null), [feed, setFeed] = useState<Feed | null>(null), [busy, setBusy] = useState(false), [err, setErr] = useState('');
  const refresh = () => { getOps<Ops>().then(setOps).catch(e => setErr(e.message)); getTraceStats<any>().then(setTstats).catch(() => {}); getTraces<any[]>().then(setTr).catch(() => {}); };
  useEffect(() => { refresh(); const id = setInterval(refresh, 5000); return () => clearInterval(id); }, []);
  const run = (inject: boolean) => { setBusy(true); setErr(''); getFeed<Feed>(inject).then(f => { setFeed(f); refresh(); }).catch(e => setErr(e.message)).finally(() => setBusy(false)); };
  const t = (a: string, b: string | number, c: string) => <div className="tile" key={a}><span>{a}</span><b>{b}</b><small>{c}</small></div>;
  const mins = (s: number) => (s >= 3600 ? `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m` : `${Math.floor(s / 60)}m ${s % 60}s`);
  return (
    <div className="page wide">
      <Card title="Control room" sub="What an operator sees: service health, AI behaviour and data-feed integrity. Refreshes every 5 seconds."
        right={ops && <span className={`src ${ops.ai_provider !== 'none' ? 'ai' : ''}`}>{ops.ai_provider !== 'none' ? `AI on: ${ops.ai_provider}` : 'AI off'}</span>}>
        {ops ? <div className="tiles four">{[t('Uptime', mins(ops.uptime_s), 'since last deploy'), t('API requests', ops.requests, `${ops.error_rate_pct}% server errors`),
          t('Latency', `${ops.p95_ms} ms`, `p95 · p50 ${ops.p50_ms} ms`), t('AI guard', `${ops.guard_block_rate_pct}%`, `blocked · ${ops.llm.rejected} of ${ops.llm.accepted + ops.llm.rejected}`),
          t('LLM calls', ops.llm.calls, `${ops.llm.failures} failed`), t('Cache hits', ops.llm.cache_hits, 'insights served without a model call')]}</div> : <p className={err ? 'err' : 'empty'} role={err ? 'alert' : undefined}>{err || 'Loading'}</p>}
      </Card>
      <Card title="Vendor feed pipeline" sub="Two vendors, two schemas, real-world faults. The pipeline repairs the feed and proves the result matches the scorecard.">
        <div className="row"><button className="primary" disabled={busy} onClick={() => run(true)}>{busy ? 'Running' : 'Replay messy vendor feed'}</button>
          <button disabled={busy} onClick={() => run(false)}>Replay clean feed</button></div>
        {err && <p className="err" role="alert">{err}</p>}
        {feed && <>
          <div className="tiles four">{[t('Raw messages', feed.raw_count, '2 vendors'), t('Duplicates dropped', feed.duplicates, 'idempotent by ball'), t('Re-ordered', feed.reordered, 'late arrivals fixed'),
            t('Quarantined', feed.quarantined, `${feed.backfilled} backfilled`)]}</div>
          <div className={`recon ${feed.reconciled ? 'ok' : 'bad'}`}><b>{feed.reconciled ? 'Reconciled' : 'MISMATCH'}</b>
            <span>Rebuilt {feed.final.runs}/{feed.final.wickets} ({feed.final.overs} ov) vs reference {feed.reference.runs}/{feed.reference.wickets} ({feed.reference.overs} ov)</span></div>
          <div className="cells" aria-label="Pipeline status per ball">{feed.cells.map(c => <i key={c.pos} className={`c-${c.status}`} title={`${c.label}: ${c.status}`} />)}</div>
          <div className="legend"><span><u className="g" />ok</span><span><u className="a" />re-ordered</span><span><u className="b" />duplicate seen</span><span><u className="r" />quarantined, backfilled</span></div>
          <div className="insight"><span className="tag">Incident summary</span><p>{feed.summary.text}</p><small>{feed.summary.source}</small></div>
          <table className="tbl"><thead><tr><th>Severity</th><th>Type</th><th>Detail</th><th>Msg</th><th>Vendor</th></tr></thead><tbody>
            {feed.incidents.map((i, k) => <tr key={k}><th className={`sev ${i.severity}`}>{i.severity}</th><td className="sm">{i.type}</td><td className="sm">{i.reason}</td><td>{i.message}</td><td>{i.vendor}</td></tr>)}</tbody></table>
          <h3 className="h3">Same ball, two vendor schemas, one canonical event</h3>
          <div className="samples">{feed.samples.map(s => <div key={s.vendor}><b>Vendor {s.vendor} raw</b><pre>{JSON.stringify(s.raw, null, 1)}</pre><b>Canonical</b><pre>{JSON.stringify(s.canonical, null, 1)}</pre></div>)}</div></>}
      </Card>
      <Card title="AI traces" sub="Every Copilot run is stored with per-step latency and a machine-readable outcome, so failures can be diagnosed and trends watched.">
        {tstats && tstats.runs > 0 ? <>
          <div className="tiles four">{[t('AI runs', tstats.runs, `${tstats.llm_calls} model calls`), t('Agent answered', `${tstats.agent_pct}%`, `${tstats.fallbacks} fell back to rules`), t('Latency', `${tstats.p95_ms} ms`, `p95 · p50 ${tstats.p50_ms} ms`), t('Avg tool steps', tstats.avg_steps, 'per run')]}</div>
          <h3 className="h3">Outcomes</h3>
          <div className="reasons">{Object.entries(tstats.reasons as Record<string, number>).map(([k, v]) => <div key={k}><span className="sm">{k}</span><i style={{ width: `${(v / tstats.runs) * 100}%` }} className={k === 'ok' ? 'good' : k.startsWith('verification') ? 'bad' : ''} /><b>{v}</b></div>)}</div>
          <h3 className="h3">Recent runs</h3>
          {tr.map(x => <details className="trc" key={x.id}><summary><span className={`badge2 ${x.status === 'accepted' ? 'ok' : 'esc'}`}>{x.status}</span> {x.question} <small>{x.total_ms} ms · {x.reason}</small></summary>
            <div className="wf">{x.steps.length === 0 ? <small>No tool steps (rules router).</small> : x.steps.map((st: any, k: number) => <div key={k}><code>{st.tool}</code><span><i className="l" style={{ width: `${Math.min(100, ((st.llm_ms ?? 0) / Math.max(1, x.total_ms)) * 100)}%` }} title={`model ${st.llm_ms} ms`} /><i className="t" style={{ width: `${Math.min(100, ((st.tool_ms ?? 0) / Math.max(1, x.total_ms)) * 100)}%` }} title={`tool ${st.tool_ms} ms`} /></span><small>model {st.llm_ms} ms · tool {st.tool_ms} ms</small></div>)}
              <small>prompt {x.prompt_version} · provider {x.provider}</small></div></details>)}</>
          : <p className="empty">No AI runs yet. Ask the Copilot a question and refresh.</p>}
      </Card>
    </div>
  );
}

function AdminAccess() {
  const [st, setSt] = useState<{ protected: boolean; ok: boolean } | null>(null), [v, setV] = useState('');
  const check = () => getAuth<{ protected: boolean; ok: boolean }>().then(setSt).catch(() => setSt(null));
  useEffect(() => { check(); }, []);
  return (
    <Card title="Admin access" sub="Operations, AI traces and evaluation pages can be protected with an ADMIN_TOKEN set on the server.">
      <p className="say"><span className={`src ${st?.protected ? 'ai' : ''}`}>{st ? (st.protected ? (st.ok ? 'Protected: unlocked' : 'Protected: locked') : 'Not protected (public demo)') : 'Checking'}</span></p>
      <form className="composer" onSubmit={e => { e.preventDefault(); setAdminToken(v); setV(''); check(); }}>
        <input className="txt" type="password" autoComplete="off" value={v} onChange={e => setV(e.target.value)} placeholder="Admin token (kept for this browser tab only)" aria-label="Admin token" />
        <button className="primary">Save</button><button type="button" onClick={() => { setAdminToken(''); check(); }}>Clear</button>
      </form>
      <p className="hint">Fan-facing pages never need the token. Without ADMIN_TOKEN on the server, these pages are open, which is fine for a demo but not for production.</p>
    </Card>
  );
}
