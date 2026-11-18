# Submission kit

## 200-word note (paste into the form)
Sightscreen 2.0 is an AI-native cricket companion. Most apps show a score; Sightscreen explains why a moment mattered. It has three connected experiences on one event-sourced match timeline: a Match Room (required rate, a transparent chase-pressure index, ball-by-ball timeline), a Live Lens replay where a floating overlay explains each wicket, four or six in casual, tactical or fantasy-minded language, and an Ask agent for questions, what-if scenarios and rule explainers like Umpire's Call.

The key design decision: the backend owns every number, and AI only explains verified facts. Any model output containing a number that is not in the facts is rejected and replaced by a deterministic explanation. The app works fully without an API key, declines picks and betting, and says plainly that its pressure index is not a win probability.

Built with React and TypeScript, FastAPI, SQLite, and AI coding assistants for speed; 12 automated tests, CI, rate limiting and a single-container deployment. The data is a clearly labelled simulated match because I do not have licensed live data. Next steps would be a licensed feed, WebSocket fan-out and cached per-moment insights for scale.

## Short answers (adapt to the form's questions)
- **What did you build?** A cricket replay companion that explains key moments with grounded AI, plus match intelligence and a question-answering agent.
- **Who is it for and why?** Casual fans who miss context, and fantasy-minded fans who want role and situation awareness without picks or odds.
- **How did you use AI?** Product feature: explanations, rewritten from verified facts with a number-grounding check. Process: AI coding assistants for scaffolding, tests and iteration; I reviewed and corrected the output (for example, fixing an over-count in my own match script through tests).
- **Hardest problem?** Keeping AI helpful without letting it invent cricket facts. Solved with tool-style fact retrieval, grounding validation and deterministic fallback.
- **What would you do with more time?** Licensed ball-by-ball feed, WebSocket/SSE fan-out, Postgres and Redis, per-moment insight caching, user feedback on insights, evaluation set for answer quality.
- **How did you test it?** 12 backend tests (cricket maths, last-ball finish, Live Lens triggering, guardrails, grounding check, API errors), a TypeScript production build, and a full-stack smoke test.

## Demo script (about 3 minutes)
1. (15 s) Problem: scores tell you what happened, not why it matters. Note the "Simulated demo" badge.
2. (60 s) Press Play at 4x. A wicket triggers Live Lens. Switch the lens to Tactical and Fantasy-minded to show the same facts told differently. Use "Next key moment".
3. (30 s) Impact replay and the chase chart: before and after the wicket.
4. (30 s) What-if lab: "Big over" then "Quiet over with a wicket".
5. (30 s) Ask: "Why did that moment matter?", "Explain Umpire's Call", then "Who should I captain?" to show the guardrail. Open "Facts behind this answer".
6. (15 s) Engineering: engine owns numbers, grounding check, tests, one-container deploy, scaling plan in docs.

## Be ready to explain
- Why SQLite, and what Postgres + Redis + WebSockets would add (see ARCHITECTURE.md).
- Why the pressure index is a heuristic: `60 * required_rate / (3.5 + 0.8 * wickets_in_hand)`, capped 0-100.
- Where AI can fail and how it is contained (grounding check, fallback, rate limit, cache).
- Complexity: ball lookup is O(n) over 36 balls; at scale use a sorted array with binary search on timestamps.
