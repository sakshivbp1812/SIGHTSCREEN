"""Optional LLM layer. The app works fully without a key; with one, answers are rewritten from verified facts
and rejected if they contain any number that is not in those facts (hallucination guard)."""
import os
import re
import unicodedata
import httpx
from . import db
from .i18n import LANG_NAME

STATS = {"calls": 0, "failures": 0, "cache_hits": 0, "accepted": 0, "rejected": 0}
NUM = re.compile(r"\d+(?:\.\d+)?")
SYSTEM = ("You are Sightscreen, a cricket explainer. Use ONLY the FACTS provided. Never add players, numbers, events, "
          "probabilities, fantasy picks or betting advice. Plain language; at most 80 words unless a word limit is given.")


OPENAI_LIKE = {  # provider: (url, key env, model env, default model)
    "groq": ("https://api.groq.com/openai/v1/chat/completions", "GROQ_API_KEY", "GROQ_MODEL", "llama-3.1-8b-instant"),
    "openai": ("https://api.openai.com/v1/chat/completions", "OPENAI_API_KEY", "OPENAI_MODEL", "gpt-4o-mini"),
}
KEYS = {"anthropic": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY", "groq": "GROQ_API_KEY", "openai": "OPENAI_API_KEY"}


def provider() -> str:
    """AI_PROVIDER can force one; otherwise the first provider with a key (groq and gemini have free tiers)."""
    forced = os.getenv("AI_PROVIDER", "")
    if forced in KEYS and os.getenv(KEYS[forced]):
        return forced
    return next((p for p, k in KEYS.items() if os.getenv(k)), "none")


def grounded(answer: str, facts: str) -> bool:
    """True only if every number in the answer also appears in the verified facts."""
    def nums(t):  # Devanagari digits are mapped to 0-9 so they are checked too
        return set(NUM.findall("".join(str(unicodedata.digit(c)) if c.isdigit() else c for c in t)))
    return nums(answer) <= nums(facts)


def _call(prompt: str, system: str = SYSTEM):
    p = provider()
    STATS["calls"] += 1
    try:
        if p == "anthropic":
            r = httpx.post("https://api.anthropic.com/v1/messages", timeout=12, headers={
                "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"},
                json={"model": os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5"), "max_tokens": 250,
                      "system": system, "messages": [{"role": "user", "content": prompt}]})
            r.raise_for_status()
            return r.json()["content"][0]["text"].strip()
        if p == "gemini":
            model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            r = httpx.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent", timeout=12,
                           headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]},
                           json={"systemInstruction": {"parts": [{"text": system}]},
                                 "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                                 "generationConfig": {"temperature": 0.2, "maxOutputTokens": 250}})
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
        if p in OPENAI_LIKE:
            url, key, model, default = OPENAI_LIKE[p]
            r = httpx.post(url, timeout=12, headers={"Authorization": f"Bearer {os.environ[key]}"},
                           json={"model": os.getenv(model, default), "temperature": 0.2, "max_tokens": 250,
                                 "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]})
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        STATS["failures"] += 1
        return None
    return None


def polish(cache_key: str, draft: str, facts: list, lens: str, question: str = "", lang: str = "en", extra: str = "", use_cache: bool = True):
    """Return (text, source). Falls back to the deterministic draft on any failure or ungrounded output."""
    if provider() == "none":
        return draft, "grounded rules engine"
    with db.conn() as c:
        row = c.execute("SELECT text FROM insight_cache WHERE k=?", (cache_key,)).fetchone() if use_cache else None
    if row:
        STATS["cache_hits"] += 1
        return row["text"], f"AI ({provider()}), cached"
    facts_txt = "\n".join(facts)
    out = _call(f"Write the answer in {LANG_NAME.get(lang, 'English')}. Keep player names exactly as in FACTS and write every number with digits 0-9. {extra}\nFan lens: {lens}\nFACTS:\n{facts_txt}\nDRAFT:\n{draft}\nQuestion: {question or 'Explain this moment.'}\n"
                "Rewrite the draft (or answer the question) using only the facts.")
    if not out or not grounded(out, facts_txt + " " + draft):
        STATS["rejected"] += 1
        return draft, "grounded rules engine (AI output rejected or unavailable)"
    STATS["accepted"] += 1
    with db.conn() as c:
        c.execute("INSERT OR REPLACE INTO insight_cache VALUES(?,?)", (cache_key, out))
    return out, f"AI ({provider()}), verified against facts"


JUDGE_SYS = ("You are a strict fact-checker. Given FACTS and an ANSWER, score faithfulness from 1 to 5 "
             "(5 = every claim is supported by the FACTS, 1 = it contains unsupported claims). Reply with JSON only: {\"score\": n, \"reason\": \"...\"}.")


def judge(answer: str, facts: str) -> dict:
    """LLM-as-judge faithfulness score; falls back to the deterministic number check when no model is available."""
    import json
    rules = {"score": 5 if grounded(answer, facts) else 1, "reason": "number check only (no LLM judge configured)", "by": "rules"}
    if provider() == "none":
        return rules
    out = _call(f"FACTS:\n{facts}\nANSWER:\n{answer}", system=JUDGE_SYS)
    try:
        d = json.loads(re.search(r"\{.*\}", out or "", re.S).group(0))
        return {"score": max(1, min(5, int(d["score"]))), "reason": str(d.get("reason", ""))[:200], "by": provider()}
    except Exception:
        return {**rules, "reason": "judge output unusable; number check used"}
