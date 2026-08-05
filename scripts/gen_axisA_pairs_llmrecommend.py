"""Generate axis-A LLM-recommend (distillation) pairs.

Each row: a broader career/research-goal query authored by Claude, paired with
1-3 POSTECH courses Claude judges as the best match — but every course is only
kept if a grounding keyword genuinely appears in that course's own
content/course_objectives text (grep-verified), to keep this from being pure
prior-knowledge bias. Confidence fixed at 0.15 (PROJECT_DESIGN.md §7.3,
decided 2026-08-04: user-specified 0.1~0.15 range, upper end chosen because
the rationale field makes each pick auditable).
"""
import json

CURRICULUM = "UG_2026_curriculum_courses.jsonl"
OUT = "UG_2026_axisA_pairs_llmrecommend.jsonl"
CONFIDENCE = 0.15

# (query, [(course_code, grounding_keyword, rationale), ...])
# grounding_keyword is checked case-insensitively against that course's
# content + course_objectives; if absent, the (course, pair) is dropped and
# reported, not silently kept.
QUERIES = [
    ("인공지능 대학원 진학을 준비하려면 학부에서 어떤 과목들을 들어야 하나요?", [
        ("CSED342", "인공지능", "AI 전공과목 자체"),
        ("CSED343", "기계학습", "AI에 필요한 수학적 기초"),
        ("MATH442", "인공지능", "AI 응용수학 전용 과목"),
    ]),
    ("반도체 소자 설계 커리어를 목표로 하는데 뭘 들어야 할까요?", [
        ("SEMI203", "반도체 소자", "반도체 소자 개론"),
        ("SEMI344", "집적회로", "집적회로 설계 실무"),
        ("DISU434", "반도체 설계", "시스템 반도체 설계"),
    ]),
    ("로봇공학 쪽으로 진로를 잡고 싶은데 기계공학과에서 뭘 들어야 하나요?", [
        ("MECH439", "로보틱스", "로보틱스 개론"),
        ("MECH211", "동역학", "로봇 운동학/동역학 기초"),
        ("MECH323", "제어", "로봇 제어 기초"),
    ]),
    ("신약 개발 연구를 하고 싶은 생명과학과 학생인데 어떤 과목이 도움될까요?", [
        ("CHEM261", "의약생명화학", "신약개발 직결 과목"),
        ("LIFE319", "생화학", "분자 수준 이해 기초"),
        ("LIFE420", "면역학", "약물-면역 상호작용 이해"),
    ]),
    ("배터리/이차전지 산업에 취업하고 싶은데 화학공학과에서 뭘 들어야 하나요?", [
        ("CHEB412", "이차전지", "이차전지 화학공정 직결 과목"),
        ("AMSE414", "에너지 소재", "에너지 소재 전공"),
        ("CHEB204", "화공열역학", "전지 열역학 기초"),
    ]),
    ("데이터 사이언티스트가 되고 싶은데 산업경영공학과에서 뭘 들으면 좋을까요?", [
        ("IMEN472", "데이터사이언스", "데이터사이언스 방법론 직결"),
        ("IMEN473", "비즈니스 애널리틱스", "비즈니스 데이터 분석"),
        ("IMEN272", "통계", "통계 기초"),
    ]),
    ("풍력/태양광 같은 신재생에너지 분야에서 일하고 싶어요", [
        ("MECH451", "에너지시스템", "에너지시스템 직결 과목"),
        ("CHEB214", "에너지환경공학", "에너지-환경 공정"),
        ("AMSE414", "에너지 소재", "에너지 소재 개발"),
    ]),
    ("디스플레이 산업(OLED 등)에 관심 있는 전자전기공학과 학생입니다", [
        ("EECE411", "디스플레이공학", "디스플레이공학 직결 과목"),
        ("DISU412", "DISPLAY", "디스플레이용 반도체"),
        ("AMSE452", "광 소자", "광소자 기초"),
    ]),
    ("컴퓨터 비전/이미지 인식 연구를 하고 싶어요", [
        ("CSED441", "컴퓨터비전", "컴퓨터비전 개론 직결"),
        ("CSED342", "인공지능", "AI 기초"),
        ("MATH442", "인공지능", "관련 수학 기초"),
    ]),
    ("암 연구(종양생물학)를 하고 싶은 생명과학도입니다", [
        ("LIFE424", "암생물학", "암생물학 직결 과목"),
        ("LIFE217", "세포생물학", "세포 수준 기초"),
        ("LIFE315", "유전학", "유전자 변이 이해 기초"),
    ]),
    ("자율주행차 관련 제어/센서 분야로 가고 싶어요", [
        ("MECH323", "제어", "시스템 제어 기초"),
        ("MECH280", "센서", "센서 및 측정"),
        ("EECE320", "자동제어", "자동제어공학"),
    ]),
    ("반도체 공정 엔지니어가 되고 싶은데 실습 위주 과목이 있나요?", [
        ("DISU301", "반도체공정실습", "공정 실습 직결"),
        ("SEMI207", "집적공정", "집적공정 캡스톤디자인"),
        ("SEMI204", "반도체 공학 실험", "실습 과목"),
    ]),
    ("금융공학/퀀트 쪽으로 진로를 생각 중인 수학과 학생입니다", [
        ("MATH472", "금융공학", "금융공학 직결 과목"),
        ("MATH431", "확률", "확률론 기초"),
        ("CMEF304", "금융경제학", "금융 도메인 지식"),
    ]),
    ("생체재료/조직공학 연구를 하고 싶은데 어느 과목이 맞을까요?", [
        ("CITE451", "생체재료", "생체재료 및 바이오패브리케이션 직결"),
        ("MECH423", "생체재료", "동일 과목 기계공학 버전"),
        ("AMSE416", "바이오의료 소재", "바이오의료 소재 기초"),
    ]),
    ("VLSI/칩 설계 엔지니어가 되고 싶어요", [
        ("EECE434", "VLSI", "VLSI 설계 입문 직결"),
        ("SEMI442", "집적회로", "풀커스텀 집적회로 설계"),
        ("SEMI344", "초집적회로", "초집적회로 설계"),
    ]),
    ("블록체인/암호화폐 관련 개발자가 되고 싶어요", [
        ("CSED403", "블록체인", "블록체인 및 암호화폐 직결"),
        ("CSED415", "보안", "컴퓨터 보안 기초"),
    ]),
    ("생태학/환경과학 분야로 진로를 잡고 싶은 생명과학도입니다", [
        ("LIFE323", "생태학", "생태학 및 야외실습 직결"),
        ("CHEB214", "환경공학", "환경공학적 관점"),
    ]),
    ("양자컴퓨팅 연구를 하고 싶은데 어느 과목이 관련 있나요?", [
        ("DISU421", "양자정보", "기초양자정보 직결"),
        ("SEMI422", "양자 소자", "양자 소자 및 컴퓨팅"),
        ("PHYS301", "양자물리", "양자역학 기초"),
    ]),
    ("경영 컨설턴트가 되고 싶은데 산업경영공학과에서 뭘 들으면 좋을까요?", [
        ("IMEN301", "기술경영", "기술경영 및 전략"),
        ("IMEN302", "경영학원론", "경영 기초"),
        ("IMEN303", "마케팅", "마케팅 지식"),
    ]),
    ("스타트업 창업을 준비 중인데 어떤 과목이 도움될까요?", [
        ("ENTP201", "기업가정신", "기업가정신 입문 직결"),
        ("ENTP301", "비즈니스플래닝", "사업계획 작성"),
        ("IMEN110", "기업가정신", "기술혁신과 기업가정신"),
    ]),
    ("전산 언어학/자연어처리 연구에 관심이 있어요", [
        ("CSED342", "인공지능", "AI 기초"),
        ("CSED343", "기계학습", "머신러닝 수학 기초"),
    ]),
    ("정밀의료(personalized medicine) 분야 연구를 하고 싶어요", [
        ("LIFE414", "시스템생물학", "시스템생물학적 접근"),
        ("LIFE326", "후성유전학", "후성유전학 기초"),
        ("CHEM261", "의약생명화학", "약물 설계 관점"),
    ]),
    ("촉매/화학반응공학 연구를 하고 싶은 화학공학도입니다", [
        ("CHEB306", "촉매공학", "촉매공학 직결"),
        ("CHEB305", "반응공학", "반응공학 기초"),
    ]),
    ("우주/항공 분야 유체역학·공기역학에 관심 있어요", [
        ("MECH471", "공기역학", "공기역학 직결"),
        ("MECH370", "유체역학", "유체역학 기초"),
        ("MECH470", "응용유체역학", "응용 유체역학"),
    ]),
    ("네트워크 엔지니어/통신 분야로 가고 싶은 전자전기공학도입니다", [
        ("EECE442", "통신 및 네트워크", "통신네트워크 개론 직결"),
        ("EECE308", "디지털통신", "디지털통신개론"),
        ("CSED353", "컴퓨터네트워크", "네트워크 기초"),
    ]),
    ("UX/UI 디자이너가 되고 싶은데 공대에서 관련 과목이 있나요?", [
        ("IMEN443", "UX디자인", "UX디자인개론 직결"),
        ("CITE203", "인터랙션 디자인", "인터랙션 디자인 스튜디오"),
        ("IMEN446", "감성공학", "사용자 감성 이해"),
    ]),
    ("복잡계/네트워크 과학 연구에 관심이 있어요", [
        ("IMEN474", "복잡계", "복잡계 직결 과목"),
        ("MATH464", "그래프론", "그래프 이론 기초"),
    ]),
    ("합성생물학 연구를 하고 싶은 화학생명공학도입니다", [
        ("CHEB409", "합성생물학", "합성생물학개론 직결"),
        ("CHEB308", "생물공학", "생물공학개론 기초"),
        ("LIFE325", "생물공학", "생명과학 관점 생물공학"),
    ]),
    ("임베디드 시스템 개발자가 되고 싶은 컴퓨터공학도입니다", [
        ("CSED425", "임베디드", "임베디드시스템 프로그래밍 직결"),
        ("EECE455", "임베디드", "임베디드 시스템-온-칩 설계"),
        ("EECE372", "마이크로프로세서", "마이크로프로세서 구조"),
    ]),
    ("행동경제학/실험경제학 연구를 하고 싶어요", [
        ("CMEF414", "행동", "행동·실험경제학 직결"),
        ("CMEF406", "게임이론", "전략적 의사결정 기초"),
    ]),
    ("컴퓨터 그래픽스/게임 개발 쪽으로 가고 싶어요", [
        ("CSED451", "컴퓨터 그래픽스", "컴퓨터 그래픽스 직결"),
        ("CITE304", "게임 설계", "놀이와 게임 설계 스튜디오"),
    ]),
    ("고체물리/응집물질물리학 연구를 하고 싶은 물리학도입니다", [
        ("PHYS401", "고체물리", "고체물리 직결"),
        ("PHYS304", "열물리", "통계물리 기초"),
    ]),
    ("금속 신소재/합금 설계 연구를 하고 싶어요", [
        ("AMSE321", "금속소재", "금속소재 개론 직결"),
        ("AMSE423", "금속공학", "금속공학 실험"),
        ("AMSE315", "상평형", "합금 설계 이론 기초"),
    ]),
    ("뇌과학/신경과학 연구를 하고 싶은 생명과학도입니다", [
        ("LIFE419", "뇌", "뇌와행동의 이해 직결"),
        ("LIFE216", "생리학", "신경생리학 기초"),
    ]),
    ("공급망 관리(SCM) 분야로 취업하고 싶어요", [
        ("IMEN422", "공급망관리", "공급망관리 직결"),
        ("IMEN376", "생산운영관리", "생산운영관리 기초"),
    ]),
    ("RF 회로 설계 엔지니어가 되고 싶은데 어떤 과목이 맞을까요?", [
        ("EECE414", "RF", "RF/아날로그 회로 설계 기초 직결"),
        ("SEMI445", "RF", "동일 주제 반도체공학 버전"),
        ("DISU361", "초고주파", "초고주파공학 이론"),
    ]),
    ("고분자 소재 연구(플라스틱, 고무 등)를 하고 싶어요", [
        ("AMSE361", "고분자소재", "고분자소재 개론 직결"),
        ("CHEB405", "고분자", "고분자개론"),
        ("CHEM451", "고분자화학", "고분자화학 기초"),
    ]),
    ("모바일 앱/유비쿼터스 컴퓨팅 개발자가 되고 싶어요", [
        ("CSED404", "유비쿼터스", "모바일 및 유비쿼터스 컴퓨팅 직결"),
    ]),
    ("컴퓨터 구조/하드웨어 설계 연구를 하고 싶은 반도체공학도입니다", [
        ("SEMI342", "컴퓨터 구조", "컴퓨터 구조 설계 직결"),
        ("EECE375", "컴퓨터설계", "컴퓨터설계 기초"),
    ]),
    ("서비스업/플랫폼 비즈니스 운영관리를 배우고 싶어요", [
        ("IMEN482", "서비스경영", "서비스경영 직결"),
        ("IMEN381", "경영정보시스템", "경영정보시스템 기초"),
    ]),
]


def load_courses():
    courses = {}
    for l in open(CURRICULUM, encoding="utf-8"):
        c = json.loads(l)
        courses[c["course_code"]] = c
        # composite codes like "CITE451/MECH423" or "EECE434/DISU434" — index
        # each component so a query written with a single component resolves
        # to the real (composite) course_code and its text.
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
        for qi, (query, picks) in enumerate(QUERIES):
            for course_code, keyword, rationale in picks:
                c = courses.get(course_code)
                if c is None:
                    dropped.append((course_code, keyword, "code_not_in_corpus"))
                    continue
                if not grounded(c, keyword):
                    dropped.append((course_code, keyword, "keyword_not_found_in_text"))
                    continue
                real_code = c["course_code"]
                row = {
                    "pair_id": f"recommend_{qi}_{course_code}",
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
    print(f"distinct queries: {len(QUERIES)}")


if __name__ == "__main__":
    main()
