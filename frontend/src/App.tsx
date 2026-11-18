import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { getHealth, getLens, getMatch } from './api';
import { CatchUpPage } from './components/CatchUp';
import Copilot from './components/Copilot';
import Dock from './components/Dock';
import Palette, { type Cmd } from './components/Palette';
import { AIQuality, ControlRoom, Dashboard, Fantasy, Impact, Lab, Settings, StatsPage } from './components/Pages';
import Support from './components/Support';
import { Icon, Mark } from './components/ui';
import type { Ctx, Insight, Lang, Lens, MatchData, Side } from './types';

type Page = 'catchup' | 'dashboard' | 'impact' | 'lab' | 'stats' | 'fantasy' | 'support' | 'control' | 'quality' | 'settings';
const MAIN: [Page, string][] = [['catchup', 'Catch me up'], ['dashboard', 'Match'], ['impact', 'Impact'], ['lab', 'What-if'], ['stats', 'Stats'], ['fantasy', 'Fantasy']];
const MORE: [Page, string][] = [['support', 'Support copilot'], ['control', 'Operations'], ['quality', 'AI quality'], ['settings', 'Settings']];
const LENSES: [Lens, string][] = [['casual', 'Casual'], ['tactical', 'Tactical'], ['fantasy', 'Fantasy']];
const LANGS: [Lang, string][] = [['en', 'English'], ['hinglish', 'Hinglish'], ['hi', 'हिन्दी']];
const SIDES: [Side, string][] = [['neutral', 'Neutral'], ['batting', 'Mumbai Meteors'], ['bowling', 'Chennai Comets']];
const saved = <T,>(k: string, d: T): T => { try { return (JSON.parse(localStorage.getItem(k) ?? 'null') as T) ?? d; } catch { return d; } };
const keep = (k: string, v: unknown) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* storage unavailable */ } };

function LensCard({ note, onClose, toast }: { note: Insight; onClose: () => void; toast?: boolean }) {
  return (
    <aside className={`lens ${toast ? 'toast' : ''}`} role="status" aria-live="polite">
      <div className="lens-h"><span className="live"><Icon n="bolt" s={13} /> LIVE LENS</span><span className={`tag k-${note.kind}`}>{note.ball} · {note.kind}</span>
        <button onClick={onClose} aria-label="Dismiss insight">Close</button></div>
      <p>{note.text}</p><small>{note.source}</small>
    </aside>
  );
}

function Seg<T extends string>({ label, value, set, items }: { label: string; value: T; set: (v: T) => void; items: [T, string][] }) {
  return (<div className="seg" role="radiogroup" aria-label={label}><span>{label}</span>{items.map(([k, n]) => <button key={k} role="radio" aria-checked={value === k} className={value === k ? 'on' : ''} onClick={() => set(k)}>{n}</button>)}</div>);
}

export default function App() {
  const [match, setMatch] = useState<MatchData | null>(null), [err, setErr] = useState('');
  const [t, setT] = useState(0), [playing, setPlaying] = useState(false), [speed, setSpeed] = useState(2);
  const [page, setPage] = useState<Page>('catchup'), [lens, setLens] = useState<Lens>(() => saved('sg_lens', 'casual'));
  const [lang, setLang] = useState<Lang>(() => saved('sg_lang', 'en')), [side, setSide] = useState<Side>(() => saved('sg_side', 'neutral')), [voice, setVoice] = useState<boolean>(() => saved('sg_voice', false));
  const [theme, setTheme] = useState<'light' | 'dark'>(() => saved('sg_theme', window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  const [prefs, setPrefs] = useState(false), [more, setMore] = useState(false), [pal, setPal] = useState(false), [cop, setCop] = useState(false);
  const [videoUrl, setVideoUrl] = useState(''), [offset, setOffset] = useState(0), [ai, setAi] = useState('');
  const [note, setNote] = useState<Insight | null>(null), [dismissed, setDismissed] = useState(-1);
  const tRef = useRef(0), video = useRef<HTMLVideoElement>(null);
  tRef.current = t;
  useEffect(() => { document.documentElement.dataset.theme = theme; keep('sg_theme', theme); }, [theme]);
  useEffect(() => { keep('sg_lens', lens); keep('sg_lang', lang); keep('sg_side', side); keep('sg_voice', voice); }, [lens, lang, side, voice]);
  useEffect(() => { getMatch<MatchData>().then(m => { setMatch(m); setT(m.deliveries[21].video_ts + 1); }).catch(e => setErr(e.message)); getHealth<{ ai_provider: string }>().then(h => setAi(h.ai_provider)).catch(() => {}); }, []);
  const dur = match?.duration ?? 0;
  useEffect(() => {
    if (!playing || videoUrl || !match) return;
    const id = setInterval(() => setT(v => { const n = v + 0.1 * speed; if (n >= dur) { setPlaying(false); return dur; } return n; }), 100);
    return () => clearInterval(id);
  }, [playing, speed, videoUrl, match, dur]);
  const ball = match ? match.deliveries.filter(d => d.video_ts <= t).length : 0;
  useEffect(() => {
    if (!match || ball === 0) { setNote(null); return; }
    const ac = new AbortController();
    getLens<Insight>(tRef.current, lens, lang, side, ac.signal).then(r => setNote(r.triggerAlert ? r : null)).catch(() => {});
    return () => ac.abort();
  }, [ball, lens, lang, side, match]);
  useEffect(() => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();
    if (!voice || !note || note.idx === dismissed) return;
    const u = new SpeechSynthesisUtterance(note.text ?? ''); u.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'; u.rate = 1.05;
    window.speechSynthesis.speak(u);
    return () => window.speechSynthesis.cancel();
  }, [note?.idx, note?.text, voice, lang, dismissed]);
  useEffect(() => {
    const k = (e: KeyboardEvent) => { if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); setPal(p => !p); } };
    window.addEventListener('keydown', k); return () => window.removeEventListener('keydown', k);
  }, []);
  const seekTo = useCallback((v: number) => { setT(v); if (video.current) video.current.currentTime = v - offset; }, [offset]);
  const nextKey = match?.deliveries.find(x => x.key && x.video_ts > t + 0.5);
  const joinLate = () => { if (match) { seekTo(match.deliveries[21].video_ts + 1); setPage('catchup'); } };

  const cmds: Cmd[] = useMemo(() => [
    ...[...MAIN, ...MORE].map(([k, n]): Cmd => ({ id: 'go-' + k, label: `Go to ${n}`, hint: 'Navigate', run: () => setPage(k) })),
    { id: 'cop', label: 'Open copilot', hint: 'Ask the AI agent', run: () => setCop(true) },
    { id: 'late', label: 'Simulate joining late (over 17.4)', hint: 'Catch me up demo', run: joinLate },
    { id: 'play', label: playing ? 'Pause replay' : 'Play replay', hint: 'Transport', run: () => setPlaying(p => !p) },
    { id: 'next', label: 'Next key moment', hint: 'Transport', run: () => nextKey && seekTo(nextKey.video_ts + 0.5) },
    ...LANGS.map(([k, n]): Cmd => ({ id: 'lang-' + k, label: `Language: ${n}`, hint: 'Preferences', run: () => setLang(k) })),
    ...LENSES.map(([k, n]): Cmd => ({ id: 'lens-' + k, label: `Explain as: ${n}`, hint: 'Preferences', run: () => setLens(k) })),
    ...SIDES.map(([k, n]): Cmd => ({ id: 'side-' + k, label: `I support: ${n}`, hint: 'Preferences', run: () => setSide(k) })),
    { id: 'voice', label: voice ? 'Turn voice commentary off' : 'Turn voice commentary on', hint: 'Preferences', run: () => setVoice(v => !v) },
    { id: 'theme', label: theme === 'dark' ? 'Switch to daylight theme' : 'Switch to floodlight theme', hint: 'Appearance', run: () => setTheme(x => (x === 'dark' ? 'light' : 'dark')) },
  ], [playing, voice, theme, nextKey, match]);  // eslint-disable-line react-hooks/exhaustive-deps

  if (err) return <main className="boot"><p className="err">Could not load the match. {err}. Check that the API is running.</p></main>;
  if (!match) return <main className="boot"><div className="spin" /><p>Loading Sightscreen</p></main>;

  const d = ball > 0 ? match.deliveries[ball - 1] : null, ctx: Ctx = { match, ball, t, lens, lang, side, seek: ts => seekTo(ts + 0.5) };
  const showNote = note && note.idx !== dismissed, aiOn = !!ai && ai !== 'none';
  const stage = (
    <div className="stagecard"><div className="stage">
      {videoUrl ? <video ref={video} src={videoUrl} controls onTimeUpdate={e => setT(e.currentTarget.currentTime + offset)} /> : (
        <div className="sim">
          <div className="sim-top"><span className="live"><i /> REPLAY</span><span>Overs 14.0 to 20.0 · {match.venue.name}</span></div>
          {d ? (<><p className="sim-over">Over {d.label}</p><p className="sim-call">{d.bowler} to {d.batter}</p>
            <p className={`sim-result k-${d.kind}`}>{d.kind === 'WICKET' ? 'OUT' : d.runs === 0 ? 'DOT' : d.kind === 'FOUR' || d.kind === 'SIX' ? d.kind : `${d.runs} RUN${d.runs > 1 ? 'S' : ''}`}</p>
            <p className="sim-how">{d.wicket ? d.how : d.region ? (d.region === 's' ? 'Over the short square boundary' : 'Down the ground') : ''}</p>
            <div className="over-strip">{match.deliveries.filter(x => x.over === d.over && x.idx <= d.idx).map(x => <span key={x.idx} className={`dot k-${x.kind}`}>{x.wicket ? 'W' : x.runs}</span>)}</div></>)
            : (<><p className="sim-call big">Mumbai Meteors need 70 from 36</p><button className="cta" onClick={() => setPlaying(true)}><Icon n="play" s={18} /> Play replay</button></>)}
        </div>)}
      {showNote && <LensCard note={note!} onClose={() => setDismissed(note!.idx!)} />}
    </div></div>
  );
  const nav = (k: Page, n: string) => <button key={k} className={page === k ? 'on' : ''} aria-current={page === k ? 'page' : undefined} onClick={() => { setPage(k); setMore(false); }}>{n}</button>;

  return (
    <div className="shell">
      <header className="top">
        <div className="brand"><Mark /><b>Sightscreen</b></div>
        <nav aria-label="Sections">{MAIN.map(([k, n]) => nav(k, n))}
          <div className="menu"><button className={MORE.some(([k]) => k === page) ? 'on' : ''} aria-expanded={more} onClick={() => { setMore(m => !m); setPrefs(false); }}>More <Icon n="chevron" s={12} /></button>
            {more && <div className="pop" role="menu">{MORE.map(([k, n]) => nav(k, n))}</div>}</div></nav>
        <div className="tools">
          <button className="ghost" onClick={() => setPal(true)} aria-label="Open command palette"><Icon n="search" s={15} /><span className="kbd">Ctrl K</span></button>
          <div className="menu"><button className="ghost" aria-expanded={prefs} onClick={() => { setPrefs(p => !p); setMore(false); }} aria-label="Preferences"><Icon n="sliders" s={15} /><span className="hide-s">{LANGS.find(l => l[0] === lang)![1]}</span></button>
            {prefs && <div className="pop wide" role="dialog" aria-label="Preferences">
              <Seg label="Explain as" value={lens} set={setLens} items={LENSES} /><Seg label="Language" value={lang} set={setLang} items={LANGS} /><Seg label="I support" value={side} set={setSide} items={SIDES} />
              {'speechSynthesis' in window && <button className={`voice ${voice ? 'on' : ''}`} aria-pressed={voice} onClick={() => setVoice(v => !v)}><Icon n="speaker" s={14} /> Voice commentary {voice ? 'on' : 'off'}</button>}</div>}</div>
          <button className="ghost" onClick={() => setTheme(x => (x === 'dark' ? 'light' : 'dark'))} aria-label="Toggle theme"><Icon n={theme === 'dark' ? 'sun' : 'moon'} s={15} /></button>
          <button className={`ai-btn ${cop ? 'on' : ''}`} onClick={() => setCop(c => !c)} aria-pressed={cop}><Icon n="sparkle" s={15} /> Copilot<i className={aiOn ? 'dot-on' : ''} /></button>
        </div>
      </header>
      <main className="work">
        {page === 'catchup' && <CatchUpPage ball={ball} lang={lang} side={side} jumpLate={joinLate} onJump={i => seekTo(match.deliveries[i - 1].video_ts + 0.5)} goMatch={() => { setPage('dashboard'); setPlaying(true); }} />}
        {page === 'dashboard' && <Dashboard ctx={ctx} stage={stage} />}
        {page === 'impact' && <Impact ctx={ctx} />}
        {page === 'lab' && <Lab ctx={ctx} />}
        {page === 'stats' && <StatsPage ctx={ctx} />}
        {page === 'fantasy' && <Fantasy ctx={ctx} />}
        {page === 'support' && <Support lang={lang} />}
        {page === 'control' && <ControlRoom />}
        {page === 'quality' && <AIQuality ctx={ctx} />}
        {page === 'settings' && <Settings videoUrl={videoUrl} setVideoUrl={setVideoUrl} offset={offset} setOffset={setOffset} ai={ai} />}
        <p className="foot">Simulated match for demonstration. Not official scores, fantasy points or betting advice.</p>
      </main>
      {page !== 'dashboard' && page !== 'catchup' && page !== 'control' && page !== 'support' && page !== 'quality' && page !== 'settings' && showNote && !cop && <LensCard toast note={note!} onClose={() => setDismissed(note!.idx!)} />}
      {cop && <Copilot ball={ball} lens={lens} lang={lang} side={side} ai={aiOn} onClose={() => setCop(false)} />}
      <Dock match={match} t={t} setT={setT} ball={ball} playing={playing} setPlaying={setPlaying} speed={speed} setSpeed={setSpeed} hasNext={!!nextKey} videoUrl={videoUrl}
        onNextKey={() => nextKey && seekTo(nextKey.video_ts + 0.5)} seekTo={seekTo} />
      {pal && <Palette cmds={cmds} onClose={() => setPal(false)} />}
    </div>
  );
}
