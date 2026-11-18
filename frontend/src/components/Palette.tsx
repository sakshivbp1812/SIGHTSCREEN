import { useEffect, useMemo, useRef, useState } from 'react';
import { Icon } from './ui';

export type Cmd = { id: string; label: string; hint: string; run: () => void };

export default function Palette({ cmds, onClose }: { cmds: Cmd[]; onClose: () => void }) {
  const [q, setQ] = useState(''), [i, setI] = useState(0), inp = useRef<HTMLInputElement>(null);
  const list = useMemo(() => { const t = q.trim().toLowerCase(); return t ? cmds.filter(c => (c.label + ' ' + c.hint).toLowerCase().includes(t)) : cmds; }, [q, cmds]);
  useEffect(() => { inp.current?.focus(); }, []);
  useEffect(() => { setI(0); }, [q]);
  const go = (c?: Cmd) => { if (!c) return; onClose(); c.run(); };
  return (
    <div className="scrim" onMouseDown={onClose}>
      <div className="palette" role="dialog" aria-modal="true" aria-label="Command palette" onMouseDown={e => e.stopPropagation()}
        onKeyDown={e => { if (e.key === 'Escape') onClose(); if (e.key === 'ArrowDown') { e.preventDefault(); setI(v => Math.min(list.length - 1, v + 1)); } if (e.key === 'ArrowUp') { e.preventDefault(); setI(v => Math.max(0, v - 1)); } if (e.key === 'Enter') go(list[i]); }}>
        <div className="p-in"><Icon n="search" s={16} /><input ref={inp} value={q} onChange={e => setQ(e.target.value)} placeholder="Type a command: hindi, catch me up, theme, quality" aria-label="Command" aria-controls="cmdlist" /></div>
        <ul id="cmdlist" role="listbox">
          {list.length === 0 && <li className="none">No matching command</li>}
          {list.map((c, k) => <li key={c.id} role="option" aria-selected={k === i} className={k === i ? 'sel' : ''} onMouseEnter={() => setI(k)} onClick={() => go(c)}><span>{c.label}</span><small>{c.hint}</small></li>)}
        </ul>
        <div className="p-f"><span>Up and down to move</span><span>Enter to run</span><span>Esc to close</span></div>
      </div>
    </div>
  );
}
