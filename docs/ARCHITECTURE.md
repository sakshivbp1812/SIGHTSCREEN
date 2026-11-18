# Architecture and scaling (v3: insights are also keyed by language and fan side)

```
 Browser (React + TS)                         FastAPI                       SQLite (demo) / Postgres (prod)
 Player clock / <video> -- ball changes -->  /lens  -> lens.py -> llm.polish   matches, venues, deliveries
 Match room, Impact, Lab, Ask  ------------>  /impact /scenario /ask (agent.py)  insight_cache, ask_log
                                               engine.py = all arithmetic
```
**Flow of a Live Lens insight:** playhead enters ball N -> `GET /lens?t=` -> ball found by timestamp -> only key moments inside a 12 s window trigger -> facts assembled from stored deliveries and replayed state -> deterministic draft -> optional LLM rewrite -> number-grounding check -> cache -> overlay.

## From demo to millions of fans (system-design answer)
- **Ingest:** licensed ball-by-ball feed -> queue (Kafka/Kinesis) -> idempotent writer -> Postgres (source of truth) + Redis (current state per match).
- **Fan-out:** a state change is pushed once through a pub/sub layer to WebSocket/SSE gateways; clients never poll the database. Browsers receive deltas (one delivery) not full state.
- **AI cost control:** an insight depends only on (match, ball, lens), so generate once per key moment and per lens, store it, and serve the same text to every fan from a CDN or Redis. At 5M viewers this is 3 LLM calls per key moment, not 15M.
- **Ask traffic:** per-user rate limits, response cache keyed by normalized question + ball, smaller model first, timeout with deterministic fallback.
- **Safety:** numbers are verified against facts; guardrails refuse picks and bets; every answer exposes its tools and sources; `ask_log` supports review.
- **Observability:** latency and error rate per endpoint, LLM rejection rate (grounding failures), cache hit ratio, cost per match.
- **Reliability:** AI is optional by design; if the model is down the rules engine answers. Multi-AZ, health checks, graceful degradation.
