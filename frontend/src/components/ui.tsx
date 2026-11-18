import type { ReactNode } from 'react';
import type { MatchData } from '../types';

const P: Record<string, string> = {
  grid: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z', pulse: 'M3 12h4l3-8 4 16 3-8h4',
  flask: 'M9 3h6M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3', chat: 'M4 5h16v11H9l-5 4z',
  bars: 'M5 20V10M12 20V4M19 20v-7', star: 'M12 3l2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z',
  gear: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2',
  shield: 'M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6zM9 12l2 2 4-4', mic: 'M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3zM5 11a7 7 0 0 0 14 0M12 18v3', speaker: 'M4 9v6h4l5 4V5L8 9zM16 8a5 5 0 0 1 0 8',
  server: 'M4 5h16v5H4zM4 14h16v5H4zM8 7.5h.01M8 16.5h.01',
  life: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18zM12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM5.6 5.6l3.5 3.5M14.9 14.9l3.5 3.5M18.4 5.6l-3.5 3.5M9.1 14.9l-3.5 3.5',
  search: 'M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14zM21 21l-4.3-4.3', moon: 'M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z',
  sun: 'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8zM12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.5 1.5M17.5 17.5L19 19M19 5l-1.5 1.5M6.5 17.5L5 19',
  sparkle: 'M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8zM19 16l.8 2.2L22 19l-2.2.8L19 22l-.8-2.2L16 19l2.2-.8z', x: 'M6 6l12 12M18 6L6 18',
  sliders: 'M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M14 4v4M8 10v4M16 16v4', chevron: 'M6 9l6 6 6-6', check: 'M5 12l4 4 10-10',
  play: 'M7 4l13 8-13 8z', pause: 'M6 4h4v16H6zM14 4h4v16h-4z', next: 'M5 4l10 8-10 8zM18 4v16', send: 'M3 12l18-9-6 18-3-7z',
  bolt: 'M13 2L4 14h7l-1 8 9-12h-7z', pin: 'M12 22s7-6.5 7-12a7 7 0 0 0-14 0c0 5.5 7 12 7 12zM12 12a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z',
};
export const Icon = ({ n, s = 18 }: { n: string; s?: number }) => (
  <svg width={s} height={s} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={P[n]} /></svg>
);
export const Card = ({ title, sub, right, children, cls = '' }: { title?: string; sub?: string; right?: ReactNode; children: ReactNode; cls?: string }) => (
  <section className={`card ${cls}`}>
    {(title || right) && <header><div><h2>{title}</h2>{sub && <p>{sub}</p>}</div>{right}</header>}
    {children}
  </section>
);
export const heat = (p: number) => (p >= 75 ? 'var(--red)' : p >= 45 ? 'var(--gold)' : 'var(--green)');

export function Ring({ value, size = 64 }: { value: number; size?: number }) {
  const r = size / 2 - 6, c = 2 * Math.PI * r;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={`Pressure ${value} out of 100`}>
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--line)" strokeWidth="6" />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={heat(value)} strokeWidth="6" strokeLinecap="round"
        strokeDasharray={`${(value / 100) * c} ${c}`} transform={`rotate(-90 ${size / 2} ${size / 2})`} style={{ transition: 'stroke-dasharray .4s' }} />
      <text x="50%" y="54%" textAnchor="middle" className="ring-n">{value}</text>
    </svg>
  );
}

export function Worm({ match, ball }: { match: MatchData; ball: number }) {
  const f = match.frames, n = f.length - 1, W = 600, H = 190, pad = 30, max = f[0].runs_needed;
  const x = (i: number) => pad + (i / n) * (W - pad * 2), y = (v: number) => 14 + (1 - v / max) * (H - 44);
  const pts = f.slice(0, ball + 1).map((s, i) => `${x(i)},${y(s.runs_needed)}`).join(' ');
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart" role="img" aria-label="Runs still needed ball by ball versus even-rate path">
      {[0.25, 0.5, 0.75].map(g => <line key={g} x1={pad} x2={W - pad} y1={y(max * g)} y2={y(max * g)} className="grid" />)}
      <line x1={x(0)} y1={y(max)} x2={x(n)} y2={y(0)} className="par" />
      {ball > 0 && <polygon points={`${x(0)},${y(0)} ${pts} ${x(ball)},${y(0)}`} className="area" />}
      <polyline points={pts} className="act" />
      {match.deliveries.filter(d => d.wicket && d.idx <= ball).map(d => <circle key={d.idx} cx={x(d.idx)} cy={y(f[d.idx].runs_needed)} r="5" className="wk" />)}
      <line x1={x(ball)} x2={x(ball)} y1="8" y2={H - 26} className="head" />
      <text x={pad} y={H - 8}>14.0</text><text x={W / 2} y={H - 8} textAnchor="middle">17.0</text><text x={W - pad} y={H - 8} textAnchor="end">20.0</text>
      <text x={pad} y="10">{max} to win</text>
    </svg>
  );
}

export function OverBars({ data }: { data: { over: number; runs: number; wickets: number }[] }) {
  const max = Math.max(12, ...data.map(o => o.runs));
  return (
    <div className="bars" role="img" aria-label="Runs scored in each over">
      {[14, 15, 16, 17, 18, 19].map((ov, i) => {
        const o = data.find(d => d.over === ov + 1);
        return (<div key={ov} className="bar"><b>{o ? `${o.runs}${o.wickets ? ` · ${o.wickets}W` : ''}` : ''}</b>
          <i style={{ height: `${o ? Math.max(4, (o.runs / max) * 100) : 2}%`, background: o && o.wickets ? 'var(--red)' : 'var(--green)' }} /><span>Over {ov + 1}</span></div>);
      })}
    </div>
  );
}

export const Delta = ({ a, b, lowerIsBetter = false, fmt = (v: number) => String(v) }: { a: number; b: number; lowerIsBetter?: boolean; fmt?: (v: number) => string }) => {
  const d = b - a, good = lowerIsBetter ? d < 0 : d > 0;
  return <span className={d === 0 ? 'dl' : good ? 'dl up' : 'dl down'}>{d === 0 ? 'no change' : `${d > 0 ? '+' : ''}${fmt(Math.round(d * 100) / 100)}`}</span>;
};

export const Mark = ({ s = 28 }: { s?: number }) => (
  <svg width={s} height={s} viewBox="0 0 32 32" aria-hidden="true"><rect width="32" height="32" rx="8" fill="var(--text)" /><rect x="7" y="7" width="18" height="14" rx="2" fill="var(--card)" />
    <circle cx="16" cy="14" r="3.2" fill="var(--red)" /><rect x="15" y="21" width="2" height="5" fill="var(--card)" /></svg>
);

/** Ground drawn to scale from the venue's boundary sizes. Boundaries are counted by zone (square vs straight), not by direction. */
export function Ground({ square, straight, sq, str }: { square: number; straight: number; sq: number; str: number }) {
  const k = 1.5, rx = square * k, ry = straight * k, cx = 170, cy = ry + 22, W = 340, H = ry * 2 + 44;
  const pt = (deg: number) => [cx + rx * Math.cos((deg * Math.PI) / 180), cy + ry * Math.sin((deg * Math.PI) / 180)];
  const arc = (a: number, b: number) => { const [x1, y1] = pt(a), [x2, y2] = pt(b); return `M${x1},${y1} A${rx},${ry} 0 0 1 ${x2},${y2}`; };
  return (
    <figure className="ground">
      <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`Ground to scale: square boundary ${square} metres, straight boundary ${straight} metres`}>
        <ellipse cx={cx} cy={cy} rx={rx} ry={ry} className="turf" />
        <circle cx={cx} cy={cy} r={27.4 * k} className="ring30" />
        <rect x={cx - 3.5} y={cy - 15} width="7" height="30" rx="1.5" className="strip" />
        <path d={arc(-30, 30)} className="rope sqz" /><path d={arc(150, 210)} className="rope sqz" /><path d={arc(60, 120)} className="rope stz" /><path d={arc(240, 300)} className="rope stz" />
        <text x={cx + rx + 8} y={cy + 4} className="dim">{square} m</text><text x={cx - rx - 8} y={cy + 4} textAnchor="end" className="dim">{square} m</text>
        <text x={cx} y={14} textAnchor="middle" className="dim">{straight} m</text><text x={cx} y={H - 4} textAnchor="middle" className="dim">{straight} m</text>
      </svg>
      <figcaption><span><u className="g" />Square zone <b>{sq}</b></span><span><u className="s" />Straight zone <b>{str}</b></span></figcaption>
    </figure>
  );
}
