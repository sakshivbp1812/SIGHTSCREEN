const BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? '';
export const MATCH_ID = 'demo-t20-chase';

const adminToken = () => { try { return sessionStorage.getItem('sg_admin') ?? ''; } catch { return ''; } };
export const setAdminToken = (v: string) => { try { v ? sessionStorage.setItem('sg_admin', v) : sessionStorage.removeItem('sg_admin'); } catch { /* storage unavailable */ } };
async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const h: Record<string, string> = { 'Content-Type': 'application/json' }, tok = adminToken();
  if (tok) h['X-Admin-Token'] = tok;
  const r = await fetch(`${BASE}${path}`, { ...init, headers: { ...h, ...((init?.headers as Record<string, string>) ?? {}) } });
  if (!r.ok) throw new Error(r.status === 429 ? 'Too many requests. Wait a minute and try again.' : r.status === 401 ? 'Admin token required. Add it in Settings, under Admin access.' : `Request failed (${r.status})`);
  return r.json() as Promise<T>;
}
export const getMatch = <T,>() => call<T>(`/api/matches/${MATCH_ID}`);
export const getLens = <T,>(t: number, lens: string, lang: string, side: string, signal?: AbortSignal) =>
  call<T>(`/api/matches/${MATCH_ID}/lens?t=${t.toFixed(1)}&lens=${lens}&lang=${lang}&side=${side}`, { signal });
export const getImpact = <T,>(ball: number, lens: string, lang: string, side: string) =>
  call<T>(`/api/matches/${MATCH_ID}/impact?ball=${ball}&lens=${lens}&lang=${lang}&side=${side}`);
export const getEvalLens = <T,>(lens: string, lang: string, side: string, sample: number) =>
  call<T>(`/api/matches/${MATCH_ID}/eval/lens?lens=${lens}&lang=${lang}&side=${side}&sample=${sample}`);
export const getEvalRed = <T,>(lang: string, side: string) => call<T>(`/api/matches/${MATCH_ID}/eval/redteam?lang=${lang}&side=${side}`);
export const postScenario = <T,>(ball: number, balls: [number, boolean][]) =>
  call<T>(`/api/matches/${MATCH_ID}/scenario`, { method: 'POST', body: JSON.stringify({ ball, balls }) });
export const postAsk = <T,>(question: string, lens: string, ball: number, lang: string, side: string) =>
  call<T>(`/api/matches/${MATCH_ID}/ask`, { method: 'POST', body: JSON.stringify({ question, lens, ball, lang, side }) });
export const getStats = <T,>(ball: number) => call<T>(`/api/matches/${MATCH_ID}/stats?ball=${ball}`);
export const getHealth = <T,>() => call<T>('/health');
export const getOps = <T,>() => call<T>('/api/ops/summary');
export const getFeed = <T,>(inject: boolean) => call<T>(`/api/ops/feed/run?inject=${inject}`);
export const getTeam = <T,>(correction: string) => call<T>(`/api/matches/${MATCH_ID}/support/team?correction=${correction}`);
export const postSupport = <T,>(question: string, correction: string, lang: string) =>
  call<T>(`/api/matches/${MATCH_ID}/support/ask`, { method: 'POST', body: JSON.stringify({ question, correction, lang }) });
export const getSupportEval = <T,>() => call<T>(`/api/matches/${MATCH_ID}/support/eval`);
export const getCatchUp = <T,>(ball: number, since: number, mode: string, lang: string, side: string) =>
  call<T>(`/api/matches/${MATCH_ID}/catchup?ball=${ball}&since=${since}&mode=${mode}&lang=${lang}&side=${side}`);
export const getPush = <T,>(ball: number, lang: string) => call<T>(`/api/matches/${MATCH_ID}/catchup/push?ball=${ball}&lang=${lang}`);
export const getEvalBrief = <T,>() => call<T>(`/api/matches/${MATCH_ID}/eval/briefing`);

export async function streamAgent(q: string, lens: string, ball: number, lang: string, side: string, onEvent: (e: any) => void, signal?: AbortSignal) {
  const p = new URLSearchParams({ q, lens, ball: String(ball), lang, side });
  const r = await fetch(`${BASE}/api/matches/${MATCH_ID}/agent/stream?${p}`, { signal });
  if (!r.ok || !r.body) throw new Error(r.status === 429 ? 'Too many requests. Wait a minute and try again.' : `Request failed (${r.status})`);
  const reader = r.body.getReader(), dec = new TextDecoder();
  let buf = '';
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    let i: number;
    while ((i = buf.indexOf('\n\n')) >= 0) { const c = buf.slice(0, i); buf = buf.slice(i + 2); if (c.startsWith('data: ')) onEvent(JSON.parse(c.slice(6))); }
  }
}
export const getEvalRag = <T,>() => call<T>('/api/eval/rag');
export const getAuth = <T,>() => call<T>('/api/ops/auth');
export const getTraces = <T,>() => call<T>('/api/ops/traces?limit=12');
export const getTraceStats = <T,>() => call<T>('/api/ops/trace-stats');
export const getEvalAgent = <T,>() => call<T>(`/api/matches/${MATCH_ID}/eval/agent`);
