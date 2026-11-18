# Lead idea: "Catch me up" - joined the match late? Get caught up in 30 seconds

## 1. The real problem
Almost nobody watches a whole match. Fans open the app from a commute, a meeting, a dinner table or while switching between matches. They arrive mid-chase and face the same three questions: *Where are we? What did I miss? What should I watch for?* Scores answer the first one only. Commentary feeds are long, English-heavy and written for people already following. The cost is a fan who feels lost, closes the app and comes back later, or never.
(Assumption to validate: late joiners are a large share of sessions. I have no Dream11 data, so the first week of any engagement measures this before building more.)

## 2. The idea in one line
A briefing that ranks what changed since you last looked, explains it in your language in about 30 seconds, and says what to watch next, with every number computed by code and never invented by AI.

## 3. User stories
- As a late joiner, I want one short briefing so I understand the match without scrolling a feed.
- As a Hindi or Hinglish reader, I want it in my language, with the same numbers as everyone else.
- As a supporter of one team, I want to know whether the last few overs were good or bad news for my side.
- As a fan who is busy, I want a lock-screen notification that already says the important thing, and a link I can forward to a friend.

## 4. How it works
1. **Playhead and last-seen marker.** The app knows the current ball and when the fan last looked (the demo lets the fan choose: 1, 2 or 3 overs ago, or from the start).
2. **Rank, do not list.** Every key moment since then gets an *impact score*: the swing in the chase-pressure index plus a bonus for a wicket. The top 2 (30-second mode) or top 4 (2-minute mode) are kept, shown in time order, and the rest are counted as skipped.
3. **Three blocks.** Where we are (score, runs needed, required rate, pressure), what you missed (the ranked moments), what to watch (who is on strike, who is bowling, and what a six or a wicket would change, from the what-if engine). A trend line says whether pressure eased or rose, framed for the team you support.
4. **Word budget.** 90 words for 30 seconds, 170 for two minutes. If the text is too long it drops the what-to-watch block, then the weakest moment. Reading time is shown.
5. **Language.** English, Hinglish and Hindi from deterministic templates; names and digits stay unchanged so numbers remain checkable.
6. **Optional AI wording.** If an LLM key is set, the model rewrites the briefing in a friendlier voice from verified facts. A guard rejects any output containing a number that is not in those facts and shows the rules-engine text instead.

## 5. Where it would live in the real world
| Surface | How | In this repo |
|---|---|---|
| In-app on open | Show the briefing when the last-seen marker is old | Catch me up page |
| Push notification | A payload for each key moment, with priority, collapse key per over and a deep link | `GET /api/matches/{id}/catchup/push` |
| Shareable link / WhatsApp | A full-screen mobile card that needs no login | `/?catchup=22&lang=hinglish` and the Share button |
| Voice | Read aloud for hands-busy moments | Read aloud button (browser speech) |
| Lock screen / widget | Same payload as push | Payload only |

Notification contract (example): `{ "send": true, "priority": "high", "title": "Wicket! 4 down, need 64 off 31", "body": "14.5: Dev Malhotra out (caught at long-on), 64 needed from 31.", "deep_link": "/?catchup=5&lang=en", "collapse_key": "demo-t20-chase:0" }`. Non-key balls return `{ "send": false }`, which keeps volume low. The collapse key lets a notification service replace older alerts from the same over.

## 6. What "good" looks like (metrics)
- **North star:** among late joiners, the share who stay or return within the same match after seeing the briefing.
- **Supporting:** time to first interaction, briefing read-through, share rate, push open rate and opt-outs, 30-second vs 2-minute usage, language mix.
- **Guardrails:** AI guard block rate, complaint rate, latency, and any briefing that fails the quality sweep.
- **Experiment:** randomise late joiners into briefing vs no briefing; compare return rate and session length; keep a holdout during rollout.

## 7. What I measured here (simulated match, rules engine)
- A quality sweep of **222 briefings** (every ball, 3 languages, 2 lengths): 100% inside the word budget, 100% contain the key number, 100% pick only valid moments, 100% rank correctly, 100% use the right script for Hindi. Average 88 words, about 27 seconds to read, longest 114 words.
- 40 automated tests, including an independent re-ranking check, edge cases (start, end of match, nothing new) and the AI guard rejecting an invented probability.
Not measured: real fans, real latency in production, real LLM quality, any effect on engagement.

## 8. Cost and scale
The rules-engine briefing has no marginal cost. AI wording is optional and cached by (match, ball, since, length, language, side). Briefings are small, so they are cheap to precompute at each key moment and serve from a cache or CDN to every fan with the same key. Production would add a ball-by-ball feed with idempotent ingestion, Redis for the current state and WebSocket or server-sent updates; see ARCHITECTURE.md.

## 9. Risks and honest limits
Simulated data only; no licensed feed. The pressure index is a transparent heuristic, not a win probability. Briefings that sound certain about the future would mislead, so "what to watch" shows only engine what-ifs. Hindi and Hinglish templates are mine and need native-speaker review. Voice depends on the browser. No authentication or personalisation store yet; "last looked" is chosen by the user in this demo.

## 10. Questions I expect, with answers
**Why this idea?** It is the smallest thing that solves a daily, universal fan problem, can be shown in 30 seconds, and is useful on every surface.
**Why not just summarise with an LLM?** Fluent summaries can invent numbers. Code selects moments and computes every figure; the model only words it, behind a number check.
**How do you rank moments?** Pressure swing plus a wicket bonus. It is simple, explainable and testable; a real system could tune the weights from engagement data.
**What if the fan has no time even for 30 seconds?** The push notification carries the headline, and the two-line version sits at the top of the card.
**How would you evaluate usefulness, not just correctness?** An A/B test on late joiners, plus short thumbs up/down on each briefing, reviewed against the sweep.
**What would you build next?** A real last-seen marker per user, a per-match briefing cache, native-speaker review of Hindi and Hinglish, and a licensed live feed.

## 11. 200-word summary
Sightscreen solves one problem: the fan who joins a live match late and has no idea what happened. Most people check a match between other things, and a score alone does not tell them why it matters. Catch me up builds a briefing in about 30 seconds: where the chase stands, the few moments they missed ranked by how much they changed the match, and what to watch next. It speaks English, Hinglish or Hindi, frames events for the team the fan supports, can be read aloud, and ships as a shareable mobile card and a push-notification payload. Design rule: code selects the moments and computes every number; an optional LLM (Groq) only words verified facts, and a guard rejects any number that is not in them. A quality sweep of 222 briefings passes every check. Around it sit a Live Lens, a what-if lab, stats, a control room for a messy data feed and a support copilot. Built with React, TypeScript, FastAPI, SQLite and Docker using Claude and ChatGPT. All data is simulated; engagement impact is untested and would be measured with an A/B test.

## 12. Three-minute talk track
**0:00** "Most fans join a match late. A score doesn't tell them what they missed or why it matters."
**0:20** Open Catch me up. "I just joined at over 17.4. In about 25 seconds I know: 26 needed off 14, a wicket and a four are why, and a six would drop the rate to 9.23."
**1:00** Switch to Hinglish, then Hindi, then set "I support Mumbai Meteors". "Same numbers, different language and framing."
**1:30** Point to the notification preview and Share. "The same payload can be a push notification or a WhatsApp link, no login."
**2:00** Open AI quality, run the sweep. "222 briefings, every check passes. The AI never decides a number; a guard blocks any it invents."
**2:30** "Everything else - Live Lens, what-if, control room, support copilot - supports this. What I'd do next: measure late joiners with real data."
