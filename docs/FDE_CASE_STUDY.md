# Sightscreen 5.0 - forward-deployed case study

## 1. The problem (a hypothesis to validate, not a fact)
Around live matches, fans need two kinds of help: *understanding* what just happened, and, after the match, *trusting their fantasy points*. When official scorers correct a decision (a dismissal type, runs credited to bat or byes), a customer's points can change after the match, and "why did my points change?" is a natural support ticket. I have no Dream11 ticket data, so every volume in this repo is a placeholder. First week with the real team: confirm whether this is a top ticket category before building more.

## 2. Who it is for
Fans (understand moments in their language), support agents (fewer repetitive tickets, clean handoffs), operations engineers (feed integrity and AI health), product owners (measurable deflection and quality).

## 3. What was built (one product, three layers)
| Layer | What it does | Proof in the repo |
|---|---|---|
| Fan companion | Live Lens, Hinglish/Hindi, voice, fan side, what-if, stats, fantasy pulse | 32 tests, screenshots |
| Operations | Messy two-vendor feed repaired and reconciled; latency, errors, AI guard block rate | Control room, runbook, load test |
| Support copilot | Points ledger, scorer corrections, change notifications, resolve-or-escalate copilot, deflection eval, impact calculator | Support copilot page, evaluation |

## 4. Key design decisions (and why)
- **Rules decide, AI words.** Whether to resolve or escalate, and every number, come from deterministic code. The LLM only rewrites an already-verified answer, and a guard rejects output containing any number not in the facts. Reason: in a support setting a wrong confident answer is worse than a handoff.
- **Escalate by default.** Payments, KYC, rank, refunds and anything unrecognised go to a human queue with a summary. The evaluation tracks *false resolutions*, which must stay 0.
- **Event-sourced data.** Everything is rebuilt from ball-by-ball events, so corrections are a re-computation with a full audit ledger, never an overwrite.
- **Rules as data.** Scoring rules are a replaceable table (example values, not official Dream11 scoring).
- **Measure, do not assume.** Evaluation and red-team harnesses, plus a load test.

## 5. Measured results (simulated data, local run)
- Support evaluation: 14 simulated tickets, 57% auto-resolved, 100% routing correct, 0 false resolutions, 100% key facts present.
- Live Lens red-team: 11 of 11 checks pass on the rules engine; guard blocks all 5 hallucinated test answers.
- Feed pipeline: 37 messages with 1 duplicate, 1 late event, 2 bad events; rebuilt score reconciles to 183/7.
- Capacity: about 470 requests/s on one worker, p95 41-52 ms (sandbox). My first load test said 40 requests/s; the cause was the test client, not the server.
Not measured: real LLM quality (no key was used in testing), real user behaviour, real ticket data.

## 6. Impact model (placeholders)
Tickets deflected per month = points tickets x share about points x measured auto-resolve rate. With the default placeholders (10,000 tickets, 35% about points, 57%) that is about 2,000 tickets, 133 agent hours and 79,800 rupees a month. These defaults are not Dream11 numbers; the point is the transparent method, and that real volumes replace them.

## 7. Rollout plan
1. **Shadow (weeks 1-2):** run on historical tickets, compare with human answers, no customer exposure.
2. **Assist (weeks 3-4):** suggest answers to agents; measure edit rate.
3. **Pilot (weeks 5-8):** answer a small cohort for one ticket type behind a flag; keep instant human escalation.
4. **Scale:** add languages and ticket types only while false resolutions stay 0 and CSAT does not drop.

## 8. Risks and mitigations
Wrong points explanation (rules and ledger, guard, shadow first); AI inventing facts (guard, rejection metric); data-feed faults (validation, quarantine, backfill, reconciliation); privacy (no personal data stored in this demo; production needs consent, retention rules, access control on the Control room); regulation (no betting advice or guarantees; legal review of customer copy); cost (cache, rate limits, small model).

## 9. Questions I expect, with my answers
**Why not let the LLM answer tickets directly?** It can be fluent and wrong, and support answers touch money-adjacent trust. I let code decide and compute, and use the model only for tone, behind a number check.
**How do you know it works?** Deterministic tests, a ticket evaluation with a zero-false-resolution target, a red-team suite, and a shadow phase before any customer sees it.
**How would it scale to millions of fans?** Insights depend on (match, ball, lens, language, side), so generate once and cache; push updates over WebSocket/SSE through pub/sub; Postgres as source of truth with Redis for current state; queue for ingestion with idempotent writes by ball; per-user rate limits. See docs/ARCHITECTURE.md.
**What if the vendor feed breaks mid-match?** Validate, dedupe, re-order, quarantine bad events, backfill from a secondary source, and reconcile; the Control room shows it and the runbook says what to do.
**What did you get wrong along the way?** I miscounted overs in my own match script (tests caught it) and misread a load-test result (the client was the bottleneck). Both are why I insist on measuring.
**What would you do first at Dream11?** Sit with support and ops, pull the real ticket and feed data, validate the hypothesis, pick the smallest slice that saves agent time, and ship it in shadow mode.
**What are the limits?** Simulated data, example scoring rules, partial Hindi/Hinglish without an AI key, browser-dependent voice, no authentication on the Control room.
**30/60/90 days:** 30: discovery, data access, shadow evaluation. 60: agent-assist pilot with real tickets. 90: first customer-facing ticket type with dashboards and on-call runbook.

## 10. 200-word summary
Sightscreen 5.0 is an AI cricket companion built like a forward-deployed engagement. Fans get Live Lens explanations of wickets, fours and sixes in English, Hinglish or Hindi, with voice, a fan-side view, what-if scenarios and stats. Behind it sits what a customer team needs to run it: a Control room that rebuilds the match from a deliberately messy two-vendor data feed and proves it reconciles, live latency and AI-guard metrics, and a runbook. The newest layer is a support copilot for a problem I hypothesise to be common, fantasy-points questions after scorer corrections: a points engine with an audit ledger, corrections that change points, a copilot that resolves only what it can prove and escalates everything else, and an evaluation with zero false resolutions on 14 simulated tickets. Design rule: code decides and computes, the LLM (Groq) only words verified answers, and a guard rejects any number not in the facts. Built with React, TypeScript, FastAPI, SQLite, Docker, GitHub Actions and Render using Claude and ChatGPT. All data is simulated; impact figures are placeholders until validated with real ticket data.
