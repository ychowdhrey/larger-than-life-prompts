"""Seeded, dependency-free statistics.

Resampling is used in preference to normal approximations because the samples here are
small and clustered by task. Every resampling routine takes an explicit seed so a reported
interval can be recomputed exactly.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Optional, Sequence, Tuple

BOOTSTRAP_DRAWS = 10000
PERMUTATION_DRAWS = 20000


def mean(xs: Sequence[float]) -> Optional[float]:
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def stdev(xs: Sequence[float]) -> Optional[float]:
    xs = [x for x in xs if x is not None]
    if len(xs) < 2:
        return None
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def cluster_bootstrap_ci(clusters: List[List[float]], *, seed: int,
                         draws: int = BOOTSTRAP_DRAWS,
                         alpha: float = 0.05) -> Optional[Tuple[float, float]]:
    """Percentile CI for a mean, resampling whole tasks rather than single observations.

    Observations from the same task are not independent, so the task is the resampling
    unit. Ignoring that would report intervals that are too narrow.
    """
    clusters = [[v for v in c if v is not None] for c in clusters]
    clusters = [c for c in clusters if c]
    if len(clusters) < 2:
        return None
    rng = random.Random(seed)
    n = len(clusters)
    means = []
    for _ in range(draws):
        picked = [clusters[rng.randrange(n)] for _ in range(n)]
        flat = [v for c in picked for v in c]
        if flat:
            means.append(sum(flat) / len(flat))
    if not means:
        return None
    means.sort()
    lo = means[int((alpha / 2) * len(means))]
    hi = means[min(len(means) - 1, int((1 - alpha / 2) * len(means)))]
    return (lo, hi)


def paired_permutation_test(diffs: Sequence[float], *, seed: int,
                            draws: int = PERMUTATION_DRAWS) -> Optional[float]:
    """Two-sided sign-flip test on paired differences.

    Under the null that the appended text does nothing, the sign of each paired difference
    is exchangeable. Exact enumeration is used when there are few enough pairs.
    """
    d = [x for x in diffs if x is not None]
    if not d:
        return None
    observed = abs(sum(d) / len(d))
    n = len(d)
    if n <= 20:  # exact: 2^20 is a million, still fast enough
        count, total = 0, 0
        for mask in range(1 << n):
            s = sum(-v if (mask >> i) & 1 else v for i, v in enumerate(d))
            total += 1
            if abs(s / n) >= observed - 1e-12:
                count += 1
        return count / total
    rng = random.Random(seed)
    count = 0
    for _ in range(draws):
        s = sum(-v if rng.random() < 0.5 else v for v in d)
        if abs(s / n) >= observed - 1e-12:
            count += 1
    return (count + 1) / (draws + 1)


def cohens_dz(diffs: Sequence[float]) -> Optional[float]:
    d = [x for x in diffs if x is not None]
    if len(d) < 2:
        return None
    sd = stdev(d)
    if not sd:
        return None
    return (sum(d) / len(d)) / sd


def binom_test_two_sided(successes: int, trials: int, p: float = 0.5) -> Optional[float]:
    """Exact two-sided binomial test."""
    if trials <= 0:
        return None
    def pmf(k):
        return math.comb(trials, k) * (p ** k) * ((1 - p) ** (trials - k))
    observed = pmf(successes)
    return min(1.0, sum(pmf(k) for k in range(trials + 1) if pmf(k) <= observed + 1e-15))


def wilson_ci(successes: int, trials: int, z: float = 1.959963985) -> Optional[Tuple[float, float]]:
    if trials <= 0:
        return None
    phat = successes / trials
    denom = 1 + z * z / trials
    centre = (phat + z * z / (2 * trials)) / denom
    half = (z * math.sqrt(phat * (1 - phat) / trials + z * z / (4 * trials * trials))) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def benjamini_hochberg(pvalues: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    """Benjamini-Hochberg adjusted p values (q values) across a family of tests.

    Holm controls the probability of ANY false positive, which is the right instrument when
    a single experiment asks three questions. A battery that screens dozens of phrases is a
    different job: there, controlling the expected PROPORTION of false discoveries keeps the
    screen usable while still correcting for having looked many times. Both are reported;
    which one is the decision rule is fixed in the preregistration, not chosen afterwards.
    """
    items = [(k, v) for k, v in pvalues.items() if v is not None]
    if not items:
        return {k: None for k in pvalues}
    items.sort(key=lambda kv: kv[1])
    m = len(items)
    adjusted: Dict[str, Optional[float]] = {}
    running = 1.0
    # Step up from the largest p value, enforcing monotonicity.
    for i in range(m - 1, -1, -1):
        k, p = items[i]
        running = min(running, m * p / (i + 1))
        adjusted[k] = min(1.0, running)
    for k in pvalues:
        adjusted.setdefault(k, None)
    return adjusted


def holm(pvalues: Dict[str, Optional[float]]) -> Dict[str, Optional[float]]:
    """Holm-Bonferroni adjustment across a family of tests."""
    items = [(k, v) for k, v in pvalues.items() if v is not None]
    if not items:
        return {k: None for k in pvalues}
    items.sort(key=lambda kv: kv[1])
    m = len(items)
    adjusted: Dict[str, Optional[float]] = {}
    running = 0.0
    for i, (k, p) in enumerate(items):
        val = min(1.0, (m - i) * p)
        running = max(running, val)  # enforce monotonicity
        adjusted[k] = running
    for k in pvalues:
        adjusted.setdefault(k, None)
    return adjusted
