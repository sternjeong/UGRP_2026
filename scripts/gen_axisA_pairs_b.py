"""Generate axis-A (b) level-signal pairs.

Rule (PROJECT_DESIGN.md §7.3, confirmed 2026-08-04):
- year = first digit after the department code prefix (1/2 = low, 3/4 = high)
- "related" = same department (code prefix) only
- no 이수구분(필수) flag available in the corpus, so it's dropped from the rule
- confidence downgraded from the original 0.5~0.7 to 0.4 (weaker signal without the flag)
- pair = every (low-year, high-year) course combination within a department
- output schema matches the shared axis-A pair convention: course_code refs only, no text
"""
import json
import re

CURRICULUM = "UG_2026_curriculum_courses.jsonl"
OUT = "UG_2026_axisA_pairs_b.jsonl"
CONFIDENCE = 0.4

CODE_RE = re.compile(r"^([A-Z]{2,4})(\d)")


def dept_year(course_code):
    m = CODE_RE.match(course_code)
    if not m:
        return None, None
    return m.group(1), int(m.group(2))


def main():
    courses = [json.loads(l) for l in open(CURRICULUM, encoding="utf-8")]

    by_dept = {}
    for c in courses:
        dept, yr = dept_year(c["course_code"])
        if dept is None:
            continue
        by_dept.setdefault(dept, []).append((c["course_code"], yr))

    pairs = []
    for dept, lst in by_dept.items():
        low = [code for code, yr in lst if yr in (1, 2)]
        high = [code for code, yr in lst if yr in (3, 4)]
        for anchor in low:
            for positive in high:
                pairs.append((anchor, positive))

    with open(OUT, "w", encoding="utf-8") as f:
        for anchor, positive in pairs:
            row = {
                "pair_id": f"b_{anchor}_{positive}",
                "source": "b",
                "confidence": CONFIDENCE,
                "anchor_course": anchor,
                "positive_course": positive,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    depts_used = sorted(by_dept.keys())
    print(f"depts: {len(depts_used)}")
    print(f"pairs written: {len(pairs)}")
    per_dept = {}
    for anchor, positive in pairs:
        d, _ = dept_year(anchor)
        per_dept[d] = per_dept.get(d, 0) + 1
    for d in depts_used:
        print(f"  {d}: {per_dept.get(d, 0)}")


if __name__ == "__main__":
    main()
