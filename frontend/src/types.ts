export type Snap = {
  runs: number; wickets: number; overs: number; balls: number; target: number; batting: string; bowling: string;
  overs_display: string; balls_remaining: number; runs_needed: number; current_rate: number; required_rate: number;
  pressure: number; result: string | null;
};
export type Delivery = {
  idx: number; label: string; over: number; ball: number; bowler: string; batter: string; runs: number; wicket: boolean;
  how: string | null; kind: string; region: string | null; video_ts: number; key: boolean;
};
export type MatchData = {
  meta: { id: string; title: string; batting: string; bowling: string; target: number; data_mode: string };
  venue: { name: string; straight_m: number; square_m: number };
  deliveries: Delivery[]; frames: Snap[]; key_moments: number[]; duration: number;
};
export type Lens = 'casual' | 'tactical' | 'fantasy';
export type Lang = 'en' | 'hinglish' | 'hi';
export type Side = 'neutral' | 'batting' | 'bowling';
export type Insight = { triggerAlert: boolean; ball?: string; idx?: number; text?: string; source?: string; kind?: string };
export type Delta = { runs_added: number; wickets_lost: number; balls_used: number; pressure_before: number; pressure_after: number; required_rate_before: number; required_rate_after: number };
export type Ctx = { match: MatchData; ball: number; t: number; lens: Lens; lang: Lang; side: Side; seek: (ts: number) => void };
export type Stats = { batters: any[]; bowlers: any[]; runs_by_over: { over: number; runs: number; wickets: number }[]; boundaries: Record<string, number>;
  venue: { name: string; straight_m: number; square_m: number }; watchlist: any[]; disclaimer: string };
export type Step = { tool: string; args: Record<string, unknown>; observation: string };
export type Citation = { id: string; title: string; source: string; text: string };
export type AgentResult = { answer: string; source: string; mode: 'agent' | 'router'; steps: number; trace: Step[]; citations: Citation[]; note?: string; tools: string[] };
export type AgentEvent = { type: 'step' } & Step | { type: 'token'; text: string } | { type: 'final'; result: AgentResult };
