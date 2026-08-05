"""Third coverage pass for axis-A LLM-recommend pairs — remaining uncovered
courses after batches 1 and 2. Same discipline: query hand-written from real
course text, grounding keyword verified against that text before being kept.
"""
import json

CURRICULUM = "UG_2026_curriculum_courses.jsonl"
OUT = "UG_2026_axisA_pairs_llmrecommend3.jsonl"
CONFIDENCE = 0.15

ROWS = [
    ("소재/공정 캡스톤디자인을 4학기까지 이어서 완성해보고 싶어요", "AMSE406", "재료와 공정", "소재/공정 디자인 종합설계Ⅳ 직결"),
    ("논문연구를 두 학기째 이어서 진행하고 싶은 화공생입니다", "CHEB426", "research projects", "논문연구Ⅱ 직결"),
    ("나노스케일 소재과학의 기초 물성물리를 배우고 싶은 화공생입니다", "CHEB463", "solid state physics", "나노공학개론(화공) 직결"),
    ("원자구조와 화학결합 등 화학의 기초를 종합적으로 배우고 싶어요", "CHEM101", "화학결합", "일반화학 I 직결"),
    ("일반화학 기본개념을 실험으로 직접 확인해보고 싶어요", "CHEM102", "화학적 현상", "일반화학실험 I 직결"),
    ("일반화학II 내용을 실험으로 심화해서 익히고 싶어요", "CHEM104", "화학적 현상", "일반화학실험 II 직결"),
    ("유기화학 원리를 응용문제까지 심화해서 배우고 싶어요", "CHEM222", "organic chemical principles", "유기화학 Ⅱ 직결"),
    ("유기화학 합성/분리/정제 실험 기술을 화학과에서 배우고 싶어요", "CHEM292", "분리, 정제", "유기반응실험 직결"),
    ("기업시민이라는 최근 경영 트렌드를 특강으로 배우고 싶어요", "CMEF499", "기업시민", "경제학특강 직결"),
    ("데이터 분석 기초 방법과 도구를 특강 형태로 배우고 싶어요", "CSED490A", "data analysis methods", "컴퓨터공학 특강A 직결"),
    ("신호와 시스템 이론을 전자전기공학과에서 배우고 싶어요", "EECE233", "신호", "신호 및 시스템 직결"),
    ("전공 미정 학부생인데 MATLAB으로 전자공학을 재미있게 맛보고 싶어요", "EECE236", "전공학과를 아직 정하지 않은", "MATLAB으로 배우는 전자공학 직결"),
    ("가제어성/가관측성 등 현대제어이론을 전자전기공학과에서 배우고 싶어요", "EECE309", "가제어성", "현대제어이론(EECE309) 직결"),
    ("의료기기의 기능과 설계를 전자전기공학과 관점에서 배우고 싶어요", "EECE415", "medical instruments", "생체전자기기(EECE415) 직결"),
    ("나노스케일 소재 연구를 전자전기공학과에서 배우고 싶어요", "EECE417", "nanoscale science", "나노공학개론(EECE417) 직결"),
    ("EECE423으로도 개설되는 현대제어이론을 전자전기공학과에서 듣고 싶어요", "EECE423", "상태공간 방정식", "현대제어이론(EECE423) 직결"),
    ("전력전자공학을 전자전기공학과 학수번호로 듣고 싶어요", "EECE425", "power electronic", "전력전자공학(EECE425) 직결"),
    ("전력망 운영 기초를 전자전기공학과 학수번호로 듣고 싶어요", "EECE429", "power grid", "전력시스템 제어 및 운영의 기초(EECE429) 직결"),
    ("생명과학과 공학이 만나는 의공학을 전자전기공학과에서 배우고 싶어요", "EECE480", "biological and physical sciences", "의공학(EECE480) 직결"),
    ("종합설계 I에 이어 시연 가능한 하드웨어/소프트웨어 과제를 완성하고 싶어요", "EECE492", "시연가능한 과제물", "종합설계과제Ⅱ 직결"),
    ("떠오르는 산업분야 창업 사례를 실무자에게 배우고 싶어요(B반)", "ENTP451B", "현업 종사자", "실전창업특강B 직결"),
    ("피터 드러커가 강조한 기업가정신을 산업경영공학과에서 배우고 싶어요", "IMEN411", "피터 드러커", "기업가정신 입문(IMEN411) 직결"),
    ("증거기반 기업가정신으로 사업계획서 작성법을 산업경영공학과에서 배우고 싶어요", "IMEN412", "Evidence-based Entrepreneurship", "비즈니스플래닝(IMEN412) 직결"),
    ("심화 실험 전에 생명과학 기초 실험법과 연구 자세를 배우고 싶어요", "LIFE209", "기초 실험법", "생명과학실험원리론 및 실습 직결"),
    ("미적분학 II로 계속 이어서 심화 미적분을 배우고 싶어요", "MATH102", "calculus", "미적분학 II 직결"),
    ("공대 신입생용 미적분학 통합과정을 배우고 싶어요", "MATH103", "calculus", "미적분학(통합) 직결"),
    ("머신러닝/데이터사이언스에 응용되는 선형대수 특강을 듣고 싶어요", "MATH409", "machine learning, data", "489 특강 직결"),
    ("나노스케일 소재과학을 기계공학과 학수번호로 배우고 싶어요", "MECH403", "solid state physics", "나노공학개론(MECH403) 직결"),
    ("우수학생 대상 고급 물리실험(Honor)을 해보고 싶어요", "PHYS353", "basic physical measurements", "물리실험III(Honor) 직결"),
    ("강사에 따라 달라지는 현대물리 최신이론 특강을 듣고 싶어요", "PHYS422", "현대 물리학의 최신 이론들", "현대물리특강 직결"),
    ("반도체 생산 현장을 국내에서 견학하며 진로를 설정하고 싶어요", "SEMI412", "생산 현장", "국내 현장 연수 직결"),
]


def load_courses():
    courses = {}
    for l in open(CURRICULUM, encoding="utf-8"):
        c = json.loads(l)
        courses[c["course_code"]] = c
        for part in c["course_code"].replace(",", "/").split("/"):
            part = part.strip()
            if part and part not in courses:
                courses[part] = c
    return courses


def grounded(course, keyword):
    text = (course.get("content") or "") + " " + (course.get("course_objectives") or "") + " " + (course.get("course_name_kr") or "")
    return keyword.lower() in text.lower()


def main():
    courses = load_courses()
    written = 0
    dropped = []
    with open(OUT, "w", encoding="utf-8") as f:
        for i, (query, course_code, keyword, rationale) in enumerate(ROWS):
            c = courses.get(course_code)
            if c is None:
                dropped.append((course_code, keyword, "code_not_in_corpus"))
                continue
            if not grounded(c, keyword):
                dropped.append((course_code, keyword, "keyword_not_found_in_text"))
                continue
            real_code = c["course_code"]
            row = {
                "pair_id": f"recommend3_{i}_{real_code}",
                "source": "llm_recommend",
                "confidence": CONFIDENCE,
                "anchor_text": query,
                "positive_course": real_code,
                "rationale": rationale,
            }
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
            written += 1
    print(f"written: {written}")
    print(f"dropped: {len(dropped)}")
    for d in dropped:
        print("  ", d)


if __name__ == "__main__":
    main()
