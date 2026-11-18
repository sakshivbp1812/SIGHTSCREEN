# Forward-deployed engineering: how Sightscreen would land with a real team

## Discovery questions (first week)
- Which fan moments matter most (wicket, six, last over)? What do fans ask support or social teams today?
- Which data feeds exist, who owns them, and what do their schemas, latencies and failure modes look like?
- What can never be said (betting, odds, official fantasy points)? Who signs off on AI copy?
- Which languages and surfaces (app, WhatsApp, web) are in scope? What are the latency and cost budgets?

## Rollout plan
1. **Shadow:** run beside the live feed, show nothing to fans, compare insights with human commentators.
2. **Pilot:** one match type and one language to a small cohort behind a flag; measure engagement and complaints.
3. **General availability:** expand languages and surfaces once guard block rate, latency and reconciliation are inside targets.

## Success metrics
Insight view-through rate, repeat sessions per match, questions answered without escalation, guard block rate (AI quality), feed reconciliation rate, p95 latency, cost per match.

## What this repo already demonstrates
Messy-feed integration with reconciliation, operator console, runbook, evaluation and red-team harness, grounding guard, measured load test, CI and one-container deploy. Next for production: licensed ball-by-ball feed, Postgres and Redis, WebSocket fan-out, authentication for the Control room, per-market compliance review.
