import json, re, time, sys
import requests
from bs4 import BeautifulSoup

JSONL_PATH = "/workspaces/UGRP_2026/UG_2026_curriculum_courses.jsonl"
LOG_PATH = "/workspaces/UGRP_2026/scrape_progress.log"
ID_START = int(sys.argv[1]) if len(sys.argv) > 1 else 12000
ID_END = int(sys.argv[2]) if len(sys.argv) > 2 else 13000  # inclusive
DELAY = 0.35
YEAR_MIN = int(sys.argv[3]) if len(sys.argv) > 3 else 2015
YEAR_MAX = int(sys.argv[4]) if len(sys.argv) > 4 else 2026
YEAR_RE = re.compile(r"\((\d{4})-\d{3}")

FIELD_MAP = {
    "3. Course Objectives": "course_objectives",
    "4. Prerequisites & require": "prerequisites",
    "7. Course References": "course_references",
    "8. Course Plan": "course_plan",
}

def split_course_codes(course_code):
    if "/" in course_code:
        return [c.strip() for c in course_code.split("/") if c.strip()]
    if "," in course_code:
        parts = [c.strip() for c in course_code.split(",") if c.strip()]
        m = re.match(r"^([A-Za-z]+)", parts[0])
        prefix = m.group(1) if m else ""
        out = [parts[0]]
        for p in parts[1:]:
            out.append(p if re.match(r"^[A-Za-z]", p) else prefix + p)
        return out
    return [course_code]

def load_courses():
    records = []
    by_code = {}
    lookup = {}
    with open(JSONL_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            records.append(d)
            by_code[d["course_code"]] = d
            for alt in split_course_codes(d["course_code"]):
                lookup.setdefault(alt, d)
    return records, by_code, lookup

def save_courses(records):
    tmp_path = JSONL_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        for d in records:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    import os
    os.replace(tmp_path, JSONL_PATH)

def extract_year(html_text):
    m = YEAR_RE.search(html_text)
    return int(m.group(1)) if m else None

def extract_course_no(soup):
    th = soup.find("th", string=re.compile(r"^\s*Course No\.\s*$"))
    if not th:
        return None
    td = th.find_next_sibling("td")
    if not td:
        return None
    return td.get_text(strip=True)

def extract_fields(soup):
    result = {}
    for h4 in soup.find_all("h4", class_="sub-title"):
        title = h4.get_text(strip=True)
        for prefix, key in FIELD_MAP.items():
            if title.startswith(prefix):
                box = h4.find_parent("div", class_="box")
                if not box:
                    continue
                ta = box.find("div", class_="textarea")
                if ta is None:
                    text = ""
                else:
                    text = ta.get_text(separator="\n", strip=True)
                result[key] = text
    return result

def main():
    records, by_code, lookup = load_courses()
    done_count = sum(1 for d in records if "course_objectives" in d)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    added = 0
    checked = 0
    log = open(LOG_PATH, "a", encoding="utf-8")

    for sid in range(ID_START, ID_END + 1):
        if done_count >= len(records):
            log.write(f"[{sid}] all {len(records)} target courses filled, stopping early\n")
            break
        url = f"https://plms.postech.ac.kr/local/ubion/course/syllabusV.php?id={sid}&lang=en"
        try:
            resp = session.get(url, timeout=15)
        except Exception as e:
            log.write(f"[{sid}] ERROR fetch: {e}\n")
            time.sleep(DELAY)
            continue
        checked += 1
        if resp.status_code != 200:
            log.write(f"[{sid}] HTTP {resp.status_code}\n")
            time.sleep(DELAY)
            continue

        year = extract_year(resp.text)
        if year is None or year < YEAR_MIN or year > YEAR_MAX:
            time.sleep(DELAY)
            continue

        soup = BeautifulSoup(resp.text, "html.parser")
        course_no = extract_course_no(soup)
        if not course_no:
            log.write(f"[{sid}] no Course No. found\n")
            time.sleep(DELAY)
            continue

        record = lookup.get(course_no)
        if record is None:
            time.sleep(DELAY)
            continue

        if "course_objectives" in record:
            log.write(f"[{sid}] {course_no} (-> {record['course_code']}) already recorded, pass\n")
            time.sleep(DELAY)
            continue

        fields = extract_fields(soup)
        record.update(fields)
        record["syllabus_source_id"] = sid
        record["syllabus_matched_code"] = course_no
        done_count += 1
        added += 1
        log.write(f"[{sid}] ADDED {record['course_code']} (matched via {course_no}) -> {list(fields.keys())}\n")
        log.flush()

        save_courses(records)

        time.sleep(DELAY)

    log.write(f"DONE. checked={checked} added={added} total_done={done_count}/{len(records)}\n")
    log.close()
    print(f"checked={checked} added={added} total_done={done_count}/{len(records)}")

if __name__ == "__main__":
    main()
