from typing import Sequence

def levenshtein(a: str, b: str) -> int:
    a = a or ""
    b = b or ""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if la == 0: return lb
    if lb == 0: return la
    prev = list(range(lb + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0]*lb
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur[j] = min(prev[j] + 1, cur[j-1] + 1, prev[j-1] + cost)
        prev = cur
    return prev[-1]

def fuzzy_match(full_name: str, login: str, query: str, max_dist: int = 2) -> bool:
    if not query:
        return True
    q = query.strip().lower()
    return min(levenshtein((full_name or '').lower(), q),
               levenshtein((login or '').lower(), q)) <= max_dist

def quality_component(user_skills: Sequence[float], req: Sequence[float]) -> float:
    if not user_skills or not req:
        return 0.0
    n = min(3, len(user_skills), len(req))
    dot = sum(float(user_skills[i]) * float(req[i]) for i in range(n))
    return dot / 3.0