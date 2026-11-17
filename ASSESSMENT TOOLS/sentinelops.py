"""SentinelOps SOC alert-triage module (debugged and optimised).

Functions
---------
sort_alerts          stable sort of alerts by severity, highest first
build_blocklist      one-time hash index of the blocklist
is_blocked           blocklist membership test (list scan or hash index)
find_signature       every start index of a pattern in a log line
closest_logins       closest pair of login locations

Run ``python sentinelops.py`` to execute the built-in test harness.
"""
import math


# --------------------------------------------------------------------------
# 1. Alert sorting
# --------------------------------------------------------------------------
def sort_alerts_insertion(alerts):
    """Corrected insertion sort (reference version, O(n^2) worst case).

    Sorts (alert_id, severity) tuples in place, highest severity first.
    Strict '<' means equal severities are never swapped -> stable.
    Fixes: loop bound j >= 0 (was j > 0) and key placed at j + 1 (was j).
    """
    for i in range(1, len(alerts)):
        key = alerts[i]
        j = i - 1
        while j >= 0 and alerts[j][1] < key[1]:   # FIX 1: j >= 0
            alerts[j + 1] = alerts[j]
            j -= 1
        alerts[j + 1] = key                       # FIX 2: j + 1
    return alerts


def sort_alerts(alerts):
    """Optimised stable sort, highest severity first (in place, returns list).

    Uses Timsort (Python's built-in): O(n) on nearly sorted input,
    O(n log n) worst case, and stable. reverse=True keeps the arrival
    order of equal severities.
    """
    alerts[:] = sorted(alerts, key=lambda a: a[1], reverse=True)
    return alerts


# --------------------------------------------------------------------------
# 2. Blocklist lookup
# --------------------------------------------------------------------------
def build_blocklist(blocklist):
    """Build the hash index once: O(b). Reuse it for every lookup."""
    return frozenset(blocklist)


def is_blocked(blocklist, ip):
    """Return True if ``ip`` is on the blocklist, else False.

    ``blocklist`` may be a list (linear scan, O(b)) or the set returned by
    build_blocklist (average O(1)). An empty blocklist blocks nothing.
    """
    if isinstance(blocklist, (set, frozenset)):
        return ip in blocklist
    for entry in blocklist:
        if entry == ip:
            return True            # FIX 3: match -> True
    return False                   # FIX 4: 'not found' only after full scan


# --------------------------------------------------------------------------
# 3. Signature search
# --------------------------------------------------------------------------
def find_signature(log, pattern):
    """Return every start index where ``pattern`` occurs in ``log``.

    Brute force with early exit on the first mismatch. Overlapping
    matches are reported. An empty or too-long pattern returns [].
    """
    n, m = len(log), len(pattern)
    if m == 0 or m > n:
        return []
    hits = []
    for i in range(n - m + 1):               # FIX 5: last window included
        for j in range(m):
            if log[i + j] != pattern[j]:
                break                        # mismatch: stop this window
        else:                                # FIX 6: for-else = all m matched
            hits.append(i)
    return hits


# --------------------------------------------------------------------------
# 4. Closest pair of logins
# --------------------------------------------------------------------------
def closest_logins_bruteforce(events):
    """Corrected brute force: all pairs i < j, O(n^2).

    Returns ((i, j), distance) or (None, None) for fewer than 2 events.
    """
    best = None                                       # FIX 7: start at +inf
    pair = None
    for i in range(len(events)):
        for j in range(i + 1, len(events)):           # FIX 9: no self/repeat
            d = math.sqrt((events[i][0] - events[j][0]) ** 2 +
                          (events[i][1] - events[j][1]) ** 2)
            if best is None or d < best:              # FIX 8: '<' not '>'
                best = d
                pair = (i, j)
    return pair, best


def closest_logins(events):
    """Optimised closest pair with identical output to the brute force.

    * only pairs i < j (no self / repeated pairs)
    * squared distances (no sqrt in the loop; one sqrt at the end)
    * events sorted by x; the inner loop stops as soon as the x-gap alone
      makes the pair too far (dx^2 > best), pruning most pairs.
    Ties are broken towards the lexicographically smallest (i, j), the same
    pair the brute force would report. Worst case is still O(n^2)
    (e.g. all x equal); typical case is close to O(n log n).
    """
    n = len(events)
    if n < 2:
        return None, None
    order = sorted(range(n), key=lambda k: (events[k][0], k))
    best_d2, best_pair = None, None
    for a in range(n):
        i = order[a]
        xi, yi = events[i]
        for b in range(a + 1, n):
            j = order[b]
            xj, yj = events[j]
            dx2 = (xi - xj) ** 2
            if best_d2 is not None and dx2 > best_d2:
                break                                 # prune: too far in x
            d2 = dx2 + (yi - yj) ** 2
            p = (i, j) if i < j else (j, i)
            if best_d2 is None or d2 < best_d2 or (d2 == best_d2 and p < best_pair):
                best_d2, best_pair = d2, p
    return best_pair, math.sqrt(best_d2)


# --------------------------------------------------------------------------
# Test harness
# --------------------------------------------------------------------------
def run_tests():
    """Check every function, including boundary cases. Raises on failure."""
    import random
    passed = 0

    def check(name, got, want):
        nonlocal passed
        ok = got == want
        print("[%s] %-46s got=%r" % ("PASS" if ok else "FAIL", name, got))
        assert ok, "%s: expected %r" % (name, want)
        passed += 1

    alerts = [("A1", 3), ("A2", 9), ("A3", 5), ("A4", 9), ("A5", 1)]
    want = [("A2", 9), ("A4", 9), ("A3", 5), ("A1", 3), ("A5", 1)]
    # --- sort_alerts
    check("sort_alerts_insertion (given data)", sort_alerts_insertion(list(alerts)), want)
    check("sort_alerts (given data)", sort_alerts(list(alerts)), want)
    check("sort_alerts empty", sort_alerts([]), [])
    check("sort_alerts single", sort_alerts([("X", 4)]), [("X", 4)])
    eq = [("B1", 5), ("B2", 5), ("B3", 5)]
    check("sort_alerts all equal (stable)", sort_alerts(list(eq)), eq)
    check("insertion all equal (stable)", sort_alerts_insertion(list(eq)), eq)
    rev = [("R%d" % i, i) for i in range(6)]
    check("sort_alerts ascending input", sort_alerts(list(rev)), rev[::-1])
    for _ in range(200):                      # optimised == corrected reference
        data = [("a%d" % k, random.randint(0, 5)) for k in range(random.randint(0, 30))]
        assert sort_alerts(list(data)) == sort_alerts_insertion(list(data))
    check("sort_alerts == insertion (200 random)", True, True)
    # --- is_blocked
    bl = ["10.0.0.5", "10.0.0.9", "172.16.4.2"]
    idx = build_blocklist(bl)
    for ip, w in [("10.0.0.9", True), ("10.0.0.5", True), ("172.16.4.2", True), ("8.8.8.8", False)]:
        check("is_blocked list %s" % ip, is_blocked(bl, ip), w)
        check("is_blocked index %s" % ip, is_blocked(idx, ip), w)
    check("is_blocked empty list", is_blocked([], "10.0.0.5"), False)
    check("is_blocked empty index", is_blocked(build_blocklist([]), "1.1.1.1"), False)
    # --- find_signature
    check("find_signature given data", find_signature("FAILFAIXFAIL", "FAIL"), [0, 8])
    check("find_signature at very end", find_signature("xxxxFAIL", "FAIL"), [4])
    check("find_signature pattern == log", find_signature("FAIL", "FAIL"), [0])
    check("find_signature pattern longer", find_signature("FA", "FAIL"), [])
    check("find_signature overlapping", find_signature("aaaa", "aa"), [0, 1, 2])
    check("find_signature no match", find_signature("abcdef", "xyz"), [])
    check("find_signature empty log", find_signature("", "ab"), [])
    check("find_signature empty pattern", find_signature("abc", ""), [])
    check("find_signature single char", find_signature("abaca", "a"), [0, 2, 4])
    # --- closest_logins
    ev = [(2, 3), (12, 30), (40, 50), (5, 1), (12, 10), (3, 4)]
    check("closest_logins given data", closest_logins(ev), ((0, 5), math.sqrt(2)))
    check("closest_logins brute given", closest_logins_bruteforce(ev), ((0, 5), math.sqrt(2)))
    check("closest_logins empty", closest_logins([]), (None, None))
    check("closest_logins one event", closest_logins([(1, 1)]), (None, None))
    check("closest_logins two events", closest_logins([(0, 0), (3, 4)]), ((0, 1), 5.0))
    check("closest_logins duplicate points", closest_logins([(1, 1), (9, 9), (1, 1)]), ((0, 2), 0.0))
    check("closest_logins ties -> first pair", closest_logins([(0, 0), (1, 0), (2, 0)]), ((0, 1), 1.0))
    check("closest_logins same x (no pruning)", closest_logins([(5, 0), (5, 9), (5, 3)]), ((0, 2), 3.0))
    for _ in range(300):                      # optimised == corrected brute force
        pts = [(random.randint(0, 15), random.randint(0, 15)) for _ in range(random.randint(0, 40))]
        assert closest_logins(pts) == closest_logins_bruteforce(pts), pts
    check("closest_logins == brute force (300 random)", True, True)
    print("\nAll %d checks passed." % passed)


if __name__ == "__main__":
    run_tests()
