import { useEffect, useRef, useState } from 'react';
import type { MatchData } from '../types';
import { Icon, Ring } from './ui';

type Props = { match: MatchData; t: number; setT: (v: number) => void; ball: number; playing: boolean; setPlaying: (f: (p: boolean) => boolean) => void;
  speed: number; setSpeed: (f: (s: number) => number) => void; onNextKey: () => void; hasNext: boolean; videoUrl: string; seekTo: (v: number) => void };

export default function Dock({ match, t, ball, playing, setPlaying, speed, setSpeed, onNextKey, hasNext, videoUrl, seekTo }: Props) {
  const ref = useRef<HTMLDivElement>(null), [w, setW] = useState(600), s = match.frames[ball], H = 66, dur = match.duration;
  useEffect(() => { const el = ref.current; if (!el) return; const ro = new ResizeObserver(() => setW(el.clientWidth)); ro.observe(el); setW(el.clientWidth); return () => ro.disconnect(); }, []);
  const x = (ts: number) => (Math.min(ts, dur) / dur) * w, y = (p: number) => 38 - (p / 100) * 28;
  const pts = match.frames.map((f, i) => `${x(i === 0 ? 0 : match.deliveries[i - 1].video_ts)},${y(f.pressure)}`);
  const upto = pts.slice(0, ball + 1);
  const at = (e: React.PointerEvent) => { const r = ref.current!.getBoundingClientRect(); seekTo(Math.max(0, Math.min(1, (e.clientX - r.left) / r.width)) * dur); };
  const key = (e: React.KeyboardEvent) => {
    const i = e.key === 'ArrowRight' ? Math.min(match.deliveries.length, ball + 1) : e.key === 'ArrowLeft' ? Math.max(0, ball - 1) : e.key === 'Home' ? 0 : e.key === 'End' ? match.deliveries.length : -1;
    if (i < 0) return; e.preventDefault(); seekTo(i === 0 ? 0 : match.deliveries[i - 1].video_ts + 0.5);
  };
  const overStarts = match.deliveries.filter(d => d.ball === 1);
  return (
    <footer className="dock">
      <div className="bug" aria-live="off">
        <span className="crest m">MM</span>
        <div><b className="mono">{s.runs}/{s.wickets}</b><small>{s.overs_display} ov</small></div>
        <div className="need"><b>{s.result ?? `Need ${s.runs_needed} off ${s.balls_remaining}`}</b><small>RRR {s.required_rate.toFixed(2)} · target {s.target}</small></div>
        <Ring value={s.pressure} size={44} />
      </div>
      <div className="tl" ref={ref} role="slider" tabIndex={0} aria-label="Match timeline" aria-valuemin={0} aria-valuemax={match.deliveries.length} aria-valuenow={ball}
        aria-valuetext={ball ? `ball ${match.deliveries[ball - 1].label}` : 'before the first ball'} onKeyDown={key}
        onPointerDown={e => { (e.currentTarget as HTMLElement).setPointerCapture(e.pointerId); at(e); }} onPointerMove={e => { if (e.buttons) at(e); }}>
        <svg width={w} height={H} aria-hidden="true">
          <polygon points={`0,38 ${pts.join(' ')} ${w},38`} className="p-area" />
          {ball > 0 && <polygon points={`0,38 ${upto.join(' ')} ${x(t)},38`} className="p-done" />}
          <polyline points={pts.join(' ')} className="p-line" />
          {overStarts.map(d => <g key={d.idx}><line x1={x(d.video_ts)} x2={x(d.video_ts)} y1="4" y2="44" className="ovl" /><text x={x(d.video_ts) + 3} y="62" className="ovt">{d.over + 1}</text></g>)}
          {match.deliveries.filter(d => d.key).map(d => d.wicket
            ? <path key={d.idx} d={`M${x(d.video_ts)},46 l5,5 l-5,5 l-5,-5z`} className="ev-w"><title>{d.label} wicket</title></path>
            : <circle key={d.idx} cx={x(d.video_ts)} cy="51" r={d.runs === 6 ? 5 : 3.2} className="ev-b"><title>{d.label} {d.kind.toLowerCase()}</title></circle>)}
          <line x1={x(t)} x2={x(t)} y1="2" y2="58" className="phd" /><circle cx={x(t)} cy="38" r="4" className="phc" />
        </svg>
      </div>
      <div className="xport">
        <button className="primary" onClick={() => setPlaying(p => !p)} disabled={!!videoUrl} aria-label={playing ? 'Pause' : 'Play replay'}><Icon n={playing ? 'pause' : 'play'} s={15} /><span className="hide-s">{playing ? 'Pause' : t > 0 ? 'Resume' : 'Play'}</span></button>
        <button onClick={() => setSpeed(v => (v === 1 ? 2 : v === 2 ? 4 : 1))} disabled={!!videoUrl} aria-label="Playback speed">{speed}x</button>
        <button onClick={onNextKey} disabled={!hasNext}><Icon n="next" s={13} /><span className="hide-s">Next key</span></button>
      </div>
    </footer>
  );
}
