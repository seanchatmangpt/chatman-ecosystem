from dataclasses import dataclass

@dataclass(frozen=True, order=True)
class Regression:
    obligation_id: str
    before_state: str
    after_state: str
    severity: str

def regressions(before_census, after_census):
    before = {row[0]: row[3] for row in before_census}
    after = {row[0]: row[3] for row in after_census}
    rows = []
    for oid in sorted(set(before) | set(after)):
        a = before.get(oid, "UNKNOWN")
        b = after.get(oid, "UNKNOWN")
        if a == "PASS" and b != "PASS":
            severity = "HARD" if b in {"FAIL","REFUSED"} else "SOFT"
            rows.append(Regression(oid, a, b, severity))
    return tuple(rows)
