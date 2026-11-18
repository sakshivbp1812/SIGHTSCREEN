import { useEffect, useState } from 'react';
import { getCatchUp, getPush } from '../api';
import type { Lang, Side } from '../types';
import { Card, Icon } from './ui';

type Brief = { ball: number; since: number; mode: string; text: string; source: string; words: number; read_seconds: number;
  moments: { idx: number; ball: string; kind: string; impact: number; text: string }[]; skipped_moments: number };
type Push = { send: boolean; priority?: string; title?: string; body?: string };
const MISSED: [string, number][] = [['1 over ago', 6], ['2 overs ago', 12], ['3 overs ago', 18], ['From the start', 999]];

export function CatchUpCard({ ball, lang, side, onJump, standalone }: { ball: number; lang: Lang; side: Side; onJump?: (idx: number) => void; standalone?: boolean }) {
  const [mode, setMode] = useState<'quick' | 'full'>('quick'), [missed, setMissed] = useState(12), [b, setB] = useState<Brief | null>(null);
  const [push, setPush] = useState<Push | null>(null), [err, setErr] = useState(''), [msg, setMsg] = useState('');
  const since = Math.max(0, ball - missed);
  useEffect(() => {
    setErr('');
    getCatchUp<Brief>(ball, since, mode, lang, side).then(r => { setB(r); const last = [...r.moments].pop(); if (last) getPush<Push>(last.idx, lang).then(setPush).catch(() => setPush(null)); else setPush(null); }).catch(e => setErr(e.message));
  }, [ball, since, mode, lang, side]);
  const link = `${location.origin}/?catchup=${ball}&lang=${lang}&side=${side}&mode=${mode}`;
  const share = async () => {
    const text = `${b?.text ?? ''}\n${link}`;
    try { if (navigator.share) await navigator.share({ title: 'Sightscreen catch-up', text: b?.text, url: link }); else { await navigator.clipboard.writeText(text); setMsg('Copied to clipboard'); } }
    catch { setMsg('Sharing was cancelled'); }
  };
  const speak = () => { if (!b || !('speechSynthesis' in window)) return; window.speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(b.text); u.lang = lang === 'hi' ? 'hi-IN' : 'en-IN'; window.speechSynthesis.speak(u); };
  return (
    <Card title="Catch me up" sub="You just opened the app mid-match. Here is what you need, in about 30 seconds." cls="catch"
      right={<div className="row"><button className={`chip ${mode === 'quick' ? 'on' : ''}`} onClick={() => setMode('quick')}>30 seconds</button><button className={`chip ${mode === 'full' ? 'on' : ''}`} onClick={() => setMode('full')}>2 minutes</button></div>}>
      <div className="chips" role="radiogroup" aria-label="When did you last look"><b className="lbl">I last looked</b>
        {MISSED.filter(([, n]) => n < 999 || ball > 18).map(([l, n]) => <button key={l} role="radio" aria-checked={missed === n} className={`chip ${missed === n ? 'on' : ''}`} onClick={() => setMissed(n)}>{l}</button>)}</div>
      {err && <p className="err" role="alert">{err}</p>}
      {b ? <>
        <p className="brief">{b.text}</p>
        <div className="meta"><span className="tag">~{b.read_seconds} s read · {b.words} words</span><span className={`src ${b.source.startsWith('AI') ? 'ai' : ''}`}>{b.source}</span>
          {b.skipped_moments > 0 && <span className="tag">{b.skipped_moments} smaller moment(s) skipped</span>}</div>
        {b.moments.length > 0 && <div className="mom">{b.moments.map(x => <button key={x.idx} className={`chip k-${x.kind}`} onClick={() => onJump?.(x.idx)} disabled={!onJump}>{x.ball} {x.kind === 'WICKET' ? 'Wicket' : x.kind === 'SIX' ? 'Six' : 'Four'} · impact {x.impact}</button>)}</div>}
        <div className="row act"><button className="primary" onClick={speak}><Icon n="speaker" s={15} /> Read aloud</button><button onClick={share}><Icon n="send" s={15} /> Share</button>
          {standalone && <a className="btnlink" href="/">Open the full match room</a>}{msg && <small>{msg}</small>}</div>
        {push?.send && <div className="phone" aria-label="Notification preview"><small>Notification this moment would send ({push.priority})</small>
          <div className="note"><b>Sightscreen</b><strong>{push.title}</strong><span>{push.body}</span></div></div>}
      </> : !err && <p className="empty">Preparing your briefing</p>}
    </Card>
  );
}

export function CatchUpPage({ ball, lang, side, jumpLate, onJump, goMatch }: { ball: number; lang: Lang; side: Side; jumpLate: () => void; onJump: (idx: number) => void; goMatch: () => void }) {
  return (
    <div className="page wide">
      <div className="hero"><div><h1>Joined late? Get caught up in 30 seconds.</h1>
        <p>Sightscreen ranks what changed since you last looked, explains it in your language and tells you what to watch next. Every number comes from the match engine, never from the AI.</p></div>
        <div className="row"><button className="primary" onClick={jumpLate}>Simulate joining late (over 17.4)</button><button onClick={goMatch}>Watch the replay</button></div></div>
      <CatchUpCard ball={ball} lang={lang} side={side} onJump={onJump} />
    </div>
  );
}

export function Standalone() {
  const q = new URLSearchParams(location.search), ball = Math.max(0, Math.min(36, Number(q.get('catchup')) || 0));
  const lang = (['en', 'hinglish', 'hi'].includes(q.get('lang') ?? '') ? q.get('lang') : 'en') as Lang, side = (['batting', 'bowling'].includes(q.get('side') ?? '') ? q.get('side') : 'neutral') as Side;
  return <div className="stand"><header><b>Sightscreen</b><small>Simulated match for demonstration</small></header><CatchUpCard ball={ball} lang={lang} side={side} standalone /></div>;
}
