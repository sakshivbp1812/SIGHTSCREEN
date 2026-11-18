"""Retrieval over the knowledge base: BM25 implemented in plain Python (no model download, fully testable)."""
import math
import re
from collections import Counter
from .kb import docs

STOP = set("a an the of to is are was be in on at for and or what how why does do did my me i it this that with by as from can you your".split())
TOK = re.compile(r"[a-z0-9]+")


def toks(t: str) -> list:
    return [w for w in TOK.findall(t.lower().replace("\u2019", "'").replace("'", "")) if w not in STOP]


class Index:
    def __init__(self, items: list, k1: float = 1.5, b: float = 0.75):
        self.items, self.k1, self.b = items, k1, b
        self.tf = [Counter(toks((d["title"] + " ") * 2 + d["text"] + " " + d["tags"])) for d in items]
        self.len = [sum(c.values()) for c in self.tf]
        self.avg = sum(self.len) / len(self.len)
        df = Counter(w for c in self.tf for w in c)
        n = len(items)
        self.idf = {w: math.log(1 + (n - f + 0.5) / (f + 0.5)) for w, f in df.items()}

    def scores(self, q: str) -> list:
        qt = toks(q)
        out = []
        for c, ln in zip(self.tf, self.len):
            out.append(sum(self.idf.get(w, 0) * c[w] * (self.k1 + 1) / (c[w] + self.k1 * (1 - self.b + self.b * ln / self.avg)) for w in qt if w in c))
        return out

    def search(self, q: str, k: int = 3, min_score: float = 0.0) -> list:
        sc = self.scores(q)
        order = sorted(range(len(sc)), key=lambda i: -sc[i])[:k]
        return [{**self.items[i], "score": round(sc[i], 2)} for i in order if sc[i] > min_score]


INDEX = Index(docs())

GOLD = [  # (query, expected id) - labelled retrieval set
    ("what is umpire's call", "R-umpires-call"), ("explain the free hit rule", "R-free-hit"), ("how many fielders outside the circle in the powerplay", "R-powerplay"),
    ("net run rate formula", "R-nrr"), ("what happens if the match is tied", "R-super-over"), ("rain interruption and revised target", "R-dls"),
    ("how is the chase pressure index calculated", "A-pressure"), ("how are impact points scored for standout players", "A-impact"),
    ("what is a wide ball", "R-wide"), ("bowler economy and batter strike rate formula", "R-economy"), ("three wickets in three balls", "R-hat-trick"),
    ("how does catch me up choose which moments to show", "A-catchup"), ("when is a batter out lbw", "R-lbw"), ("who gets credit for a run out", "R-run-out"),
    ("what is a maiden over", "R-maiden"), ("how are captain points multiplied", "A-points"),
]


def retrieval_eval() -> dict:
    ranks = []
    for q, want in GOLD:
        ids = [h["id"] for h in INDEX.search(q, k=len(INDEX.items))]
        ranks.append(ids.index(want) + 1 if want in ids else 0)
    n = len(GOLD)
    return {"n": n, "recall_at_1": round(100 * sum(r == 1 for r in ranks) / n), "recall_at_3": round(100 * sum(1 <= r <= 3 for r in ranks) / n),
            "mrr": round(sum(1 / r for r in ranks if r) / n, 3), "misses": [GOLD[i][0] for i, r in enumerate(ranks) if r != 1]}
