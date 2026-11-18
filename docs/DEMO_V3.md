# Sightscreen - demo script. LEAD WITH CATCH ME UP (see docs/LEAD_FEATURE_CATCHUP.md for the 3-minute talk track); the steps below are optional depth.

1. **Problem (20 s).** Fans see a wicket or a six but not why it matters, and most explanations are English-only. Note the Simulated demo badge.
2. **Live Lens (60 s).** Press Play, then Next key moment. Show a wicket. Switch Explain as: Casual, Tactical, Fantasy.
3. **Language and voice (45 s).** Switch to Hinglish, then Hindi. Turn Voice on and replay a key moment. Open Ask, tap the mic and ask "Agar agla ball chhakka ho toh kya hoga?".
4. **Fan perspective (30 s).** Choose I support: Mumbai Meteors. The same wicket reads as a tough moment for you; choose Chennai Comets and it flips.
5. **AI quality (60 s).** Open AI quality. Run the Live Lens evaluation and the red-team suite. Explain: the engine computes every number, the guard rejects any model output with a number not in the facts, and the suite proves refusals and tool use.
6. **Control room (60 s).** Open Control room. Replay the messy vendor feed: 37 messages, 1 duplicate, 1 late event, 2 corrupt or incomplete, 2 backfilled, and the rebuilt score reconciles to 183/7. Show the two vendor schemas becoming one event, then the live latency and AI guard tiles. Say: this is the integration and operations work an FDE does after the demo.
7. **Support copilot (75 s).** Open Support copilot, choose the Ball 14.5 correction: the team total drops 149.5 to 124.5 and a customer notification explains exactly why. Ask 'Why did my points drop?' (resolved with the ledger) and 'Where is my withdrawal?' (escalated to Payments with a summary). Run the evaluation: 57% auto-resolved, 0 false resolutions. Say: volumes are placeholders until validated with real ticket data.
8. **Engineering (25 s).** Event-sourced SQLite, tool-based agent, caching, rate limits, 51 tests, CI, one-container deploy.

## Honest limits to mention
- Match data is simulated; no licensed live feed.
- Voice uses browser speech APIs: best in Chrome; Hindi voices depend on the device.
- Without an AI key, Hinglish/Hindi Ask answers are partial (localised summary plus English facts); with a key the model writes the full answer, still number-checked.
- The pressure index and impact score are illustrative, not win probability or official points.

## Likely questions
- *How do you stop hallucinations?* Numbers are computed by the engine; model text is rejected if any number is not in the verified facts; tests include hallucinated candidates.
- *How would it scale?* Insights depend only on (match, ball, lens, language, side), so generate once and cache; fan-out with WebSockets/Redis. See ARCHITECTURE.md.
- *Why evals?* To measure quality and regressions instead of trusting a prompt.

## New in this version (add 60 seconds if asked about AI depth)
- Press Ctrl or Cmd + K, type "hindi" and press Enter: the whole product switches language.
- Open Copilot and ask "Explain Umpire's Call": a cited passage appears. With an LLM key, ask "What happens if the next ball is a six?" and show the tool steps stream in, then the verified answer.
- Say: the model plans and words; code computes and verifies; every failure falls back to a safe answer and tells the user why.
- Open AI quality: run the retrieval evaluation (recall@1 94%, recall@3 100%) and the Live Lens evaluation (faithfulness score).
