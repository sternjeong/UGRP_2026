"""axis-D hasSynergyWith 1차 소스: roadmap_raw.jsonl의 구조화된 학과별 로드맵
(courses_by_slot / tracks)을 파싱해, 같은 학과 로드맵 내 더 이른 슬롯 → 더
늦은 슬롯 과목쌍을 hasSynergyWith 후보로 생성한다 (§7.2 1차 방법).

대상: MECH, IMEN, semiconductor_track_unspecified_dept, CITE — 이 4개만
구조화(courses_by_slot/tracks) 상태이고, PHYS/CHEM은 자유서술 텍스트뿐이라
§7.3에서 이미 "다이어그램 수집은 여기서 마무리, 전학과 커버 목표 아님"으로
결정됨(2026-08-03). 그 결정을 그대로 따름 — 이 두 학과는 스킵.

로드맵 원문의 학수번호가 현재 UG_2026_curriculum_courses.jsonl과 버전이 달라
(예: MATH110 vs 현재 MATH101/102, 아예 코드 없이 과목명만 있는 경우도 많음)
코드 직접매칭 실패분은 과목명 fuzzy 매칭으로 보강한다. 매칭 실패는 버리지
않고 skipped 목록에 사유와 함께 남긴다(그룹B 소프트지만 재현성을 위해).

hasPrerequisite로 이미 확정된 쌍은 제외한다(§7.2: 중복 표현 방지).
confidence는 슬롯 거리에 따라 감쇠(§7.2).
"""
import json
import re

CURRICULUM = "UG_2026_curriculum_courses.jsonl"
ROADMAP = "roadmap_raw.jsonl"
PREREQ_PAIRS = "UG_2026_axisA_pairs_a.jsonl"
OUT = "UG_2026_axisD_hasSynergyWith.jsonl"
SKIPPED_OUT = "UG_2026_axisD_hasSynergyWith_skipped.jsonl"

CODE_RE = re.compile(r"\b([A-Z]{2,4}\d{3}[A-Za-z]?)\b")


def load_curriculum():
    courses = [json.loads(l) for l in open(CURRICULUM, encoding="utf-8")]
    by_code = {}
    by_name = {}
    for c in courses:
        for part in c["course_code"].replace(",", "/").split("/"):
            part = part.strip()
            if part:
                by_code[part] = c["course_code"]
        name = normalize_name(c["course_name_kr"])
        by_name.setdefault(name, []).append(c["course_code"])
    return by_code, by_name


def normalize_name(name):
    name = name or ""
    name = re.sub(r"[ⅠⅡⅢⅣⅤ]", "", name)
    name = re.sub(r"[IVX]+$", "", name)
    name = re.sub(r"\(.*?\)", "", name)
    name = re.sub(r"\d+$", "", name)
    name = re.sub(r"\s+", "", name)
    return name.strip()


def match_course(raw_str, by_code, by_name):
    """Return a real course_code for a roadmap entry string, or None."""
    m = CODE_RE.search(raw_str)
    if m and m.group(1) in by_code:
        return by_code[m.group(1)], "code_match"

    # strip leading code-like tokens / trailing credit "(3)" and try name match
    text = re.sub(r"^[A-Z]{2,4}\d{3}[A-Za-z]?\s*", "", raw_str)
    text = re.sub(r"\(\d+\)$", "", text)
    text = re.sub(r"\s*or\s*.*$", "", text, flags=re.I)  # "X or Y" -> just X
    key = normalize_name(text)
    if key in by_name and len(by_name[key]) == 1:
        return by_name[key][0], "name_match"
    return None, "no_match"


def extract_slots_courses_by_slot(structured):
    """MECH / semiconductor shape: {"courses_by_slot": {"1-1": [...], ...}}"""
    slots = structured.get("courses_by_slot") or {}
    out = []
    for slot_key, course_list in slots.items():
        m = re.match(r"(\d)-(\d)", slot_key)
        if not m:
            continue
        order = int(m.group(1)) * 2 + int(m.group(2))
        for entry in course_list:
            out.append((order, entry))
    return out


def extract_slots_tracks_semester(structured):
    """IMEN shape: {"tracks": {trackname: {"2-봄": [...], "3-가을": [...]}}}"""
    season_order = {"봄": 0, "가을": 1}
    results = {}
    for track, slots in (structured.get("tracks") or {}).items():
        out = []
        for slot_key, course_list in slots.items():
            m = re.match(r"(\d)-(봄|가을)", slot_key)
            if not m:
                continue
            order = int(m.group(1)) * 2 + season_order[m.group(2)]
            for entry in course_list:
                out.append((order, entry))
        results[track] = out
    return results


def extract_slots_tracks_level(structured):
    """CITE shape: {"tracks": {trackname: {"전공기초": [...], "전공심화": [...]}}}"""
    level_order = {"전공기초": 0, "전공심화": 1}
    results = {}
    for track, slots in (structured.get("tracks") or {}).items():
        out = []
        for slot_key, course_list in slots.items():
            order = level_order.get(slot_key)
            if order is None:
                continue
            for entry in course_list:
                out.append((order, entry))
        results[track] = out
    return results


def gen_edges_for_group(slot_course_pairs, by_code, by_name, group_label, skipped):
    """slot_course_pairs: list of (order:int, raw_course_string)."""
    resolved = []  # (order, course_code)
    for order, raw in slot_course_pairs:
        # an entry can be "A or B" (택일) — treat each candidate separately
        candidates = [raw]
        if " or " in raw:
            candidates = raw.split(" or ")
        for cand in candidates:
            code, reason = match_course(cand.strip(), by_code, by_name)
            if code:
                resolved.append((order, code))
            else:
                skipped.append({"group": group_label, "raw": cand.strip(), "reason": reason})

    edges = []
    for i, (order_a, code_a) in enumerate(resolved):
        for order_b, code_b in resolved:
            if order_b > order_a and code_a != code_b:
                distance = order_b - order_a
                edges.append((code_a, code_b, distance))
    return edges


def confidence_for_distance(distance):
    return max(0.2, round(0.7 - 0.1 * (distance - 1), 2))


def main():
    by_code, by_name = load_curriculum()

    existing_prereq = set()
    for line in open(PREREQ_PAIRS, encoding="utf-8"):
        row = json.loads(line)
        # hasPrerequisite(positive, anchor) — exclude this ordered pair and
        # its reverse from synergy candidates (§7.2: no duplicate expression)
        existing_prereq.add((row["anchor_course"], row["positive_course"]))
        existing_prereq.add((row["positive_course"], row["anchor_course"]))

    skipped = []
    all_edges = {}  # (a,b) -> min distance seen

    for line in open(ROADMAP, encoding="utf-8"):
        entry = json.loads(line)
        dept = entry.get("department")
        structured = entry.get("structured")
        if not structured or dept in (None, "_meta"):
            continue

        if "courses_by_slot" in structured:
            pairs = extract_slots_courses_by_slot(structured)
            edges = gen_edges_for_group(pairs, by_code, by_name, dept, skipped)
            for a, b, d in edges:
                key = (a, b)
                all_edges[key] = min(all_edges.get(key, 999), d)
        elif "tracks" in structured:
            # distinguish IMEN (semester-slot) vs CITE (level-slot) by key shape
            sample_track = next(iter(structured["tracks"].values()), {})
            if any(re.match(r"\d-(봄|가을)", k) for k in sample_track):
                grouped = extract_slots_tracks_semester(structured)
            else:
                grouped = extract_slots_tracks_level(structured)
            for track, pairs in grouped.items():
                edges = gen_edges_for_group(pairs, by_code, by_name, f"{dept}:{track}", skipped)
                for a, b, d in edges:
                    key = (a, b)
                    all_edges[key] = min(all_edges.get(key, 999), d)

    written = 0
    dropped_as_prereq = 0
    with open(OUT, "w", encoding="utf-8") as f:
        for (a, b), dist in all_edges.items():
            if (a, b) in existing_prereq:
                dropped_as_prereq += 1
                continue
            row = {
                "pair_id": f"synergy_{a}_{b}",
                "relation": "hasSynergyWith",
                "confidence": confidence_for_distance(dist),
                "anchor_course": a,
                "positive_course": b,
                "slot_distance": dist,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            written += 1

    with open(SKIPPED_OUT, "w", encoding="utf-8") as f:
        for s in skipped:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"hasSynergyWith edges written: {written}")
    print(f"dropped (already hasPrerequisite): {dropped_as_prereq}")
    print(f"unmatched roadmap entries (skipped): {len(skipped)}")
    reasons = {}
    for s in skipped:
        reasons[s["reason"]] = reasons.get(s["reason"], 0) + 1
    for r, n in reasons.items():
        print(f"  {r}: {n}")


if __name__ == "__main__":
    main()
