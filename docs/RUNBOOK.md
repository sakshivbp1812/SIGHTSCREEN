# Sightscreen runbook (operator guide)

Where to look first: **Control room** page (service health, AI guard, feed integrity) and `/health`.

| Symptom | Likely cause | Check | Action |
|---|---|---|---|
| Sidebar says "AI off" | No LLM key, or provider mismatch | `/health` -> `ai_provider` | Set `GROQ_API_KEY` (or `GEMINI_API_KEY`) in Render Environment; redeploy |
| AI on but sources say "rejected or unavailable" | Model name changed, provider outage, or rate limit | Control room: LLM failures vs AI guard blocked | Set `GROQ_MODEL`/`GEMINI_MODEL` to a current model; the app keeps serving rules-engine text meanwhile |
| Guard block rate rises | Model is inventing numbers | Control room AI guard; run AI quality > red-team suite | Lower model temperature / change model; no user impact (blocked text is replaced) |
| p95 latency high | Cold start (free tier), CPU saturation | Control room latency; `python scripts/loadtest.py <url>` | Wake the service; scale instance size or add workers |
| Many 429 responses | Per-IP rate limit (60/min, eval 6/10 min) | Browser network tab | Expected under abuse; raise limits only after checking the LLM budget |
| Feed shows quarantined events | Vendor sent corrupt or incomplete payloads | Control room > Replay feed, incident table | Gap is backfilled from the secondary scorecard; raise with the vendor, attach the raw payload from the table |
| Reconciliation says MISMATCH | Rebuilt state differs from the reference | Incident summary | Treat as sev-1 for data: freeze the feed, compare messages in order, fix the adapter, add a regression test |
| Support evaluation shows false resolutions above 0 | Router resolved something it should have escalated | Support copilot > Run evaluation | Sev-1: disable auto-answers (escalate everything), fix the router, add the ticket to the evaluation set |
| Customer says points are wrong | Correction not applied or rules changed | Support copilot ledger for that player | Compare ledger with the scorer log; fix rules or data, then notify affected customers |
| Briefing text looks wrong or too long | Template or ranking regression | AI quality > Run Catch-me-up sweep (all checks must be 100%) | Fix the template or ranking, add the failing ball to tests; the AI wording layer is optional and can be turned off by removing the key |
| Copilot answers say 'rules router used' every time | LLM unreachable, wrong model name, or verification rejecting answers | Copilot answer note; Operations: LLM failures and guard block rate | Set GROQ_MODEL/GEMINI_MODEL to a current model; if rejections are high, inspect the rejected tool results and prompt; users still get correct rules-router answers |
| Operations or evaluation pages say 'Admin token required' | ADMIN_TOKEN is set on the server | Settings > Admin access | Enter the token (kept only for the browser tab). Rotate it in Render if it leaks |
| Agent answers fall back more often | Verification failing or provider issues | Operations > AI traces: outcome breakdown and recent runs | Open a failing run, read the step results and reason; fix prompt or tool; run AI quality > Agent safety regression before redeploying |
| Key leaked | Key committed or shared | GitHub secret scanning | Revoke the key at the provider, create a new one, update Render |

## Release checklist
1. `cd backend && python -m pytest -q` (57 tests) and `cd frontend && npm run build`.
2. Push to GitHub; CI runs both.
3. Render redeploys; check `/health`, Control room, replay one match, run AI quality.

## Measured capacity (one Uvicorn worker, local sandbox, 800 requests, concurrency 20)
About 470 requests/second, p50 29 ms, p95 41-52 ms, 0 server errors (rate-limited 429s are the limiter working). Note: the first load test showed 40 req/s because the test script created a new HTTP client per request, so it was measuring the client. The fix was in the test, not the server. Re-run on your own deployment: `python scripts/loadtest.py https://<your-url> 400 20`.
