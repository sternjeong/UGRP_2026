# GR 2026 커리큘럼 → JSONL 추출 작업 — ✅ 완료

`3. (KOR) GR 2026 curriculum_v.1.0_20260406.pdf` (전체 340페이지, 실제 인쇄 페이지는 338페이지까지)를
처음부터 끝까지 다 읽고 추출 완료.

## 결과
- 출력 파일: `/workspaces/UGRP_2026/gr_2026_courses.jsonl`
- **총 1047개 레코드**, 28개 학과/전공/프로그램
- 각 레코드 키: `course_code`, `course_name_en`, `course_name_kr`, `department`, `department_kr`, `description`
- 모든 라인 JSON 파싱 검증 완료, 누락 필드 없음.

## 포함된 학과/전공/프로그램 (28개, PDF 순서)
Mathematics, Physics, Chemistry, Life Sciences, Materials Science and Engineering,
Mechanical Engineering, Industrial and Management Engineering, Electrical Engineering,
Computer Science and Engineering, Chemical Engineering, IT Convergence Engineering,
Environmental Engineering, Graduate School of Artificial Intelligence, Advanced Nuclear Engineering,
Advanced Materials Science(ADMS), Interdisciplinary Bioscience and Bioengineering(IBIO),
Social Data Science(PSDS), Medical Science and Engineering(PMSE), Defense Science and Technology(SDST),
Management Science(MSIP), Convergence Food Technology(PCFT), Quantum Information Science(QIST),
Industrial Data Science(IDSC), Synthetic Biology(SYNB), Semiconductor Graduate School(GSST),
Sports AIX Convergence Graduate Program(SAIX), POSTECH-Samsung Semiconductor Education Program(PSEP),
University Common(공통 교양/연구윤리 등)

## 처리 원칙 요약 (참고용 — 유사 작업 재현 시 참고)
- 크로스리스팅 과목("XXXnnn/YYYmmm" 형태)은 대상 코드가 이미 등록돼 있고 과목명이 사실상 동일하면 스킵.
- bare code 검색만으로 부족한 경우가 많아 **course_name_kr로도 재검색**해서 이미 다른 챕터의 다른 코드로
  등록된 동일 과목인지 반드시 확인 (특히 CITE5xx, LIFE622Y 등 여러 대학원에서 반복 인용되는 "공통 특강"류).
- 같은 크로스리스팅 코드라도 챕터마다 이름/설명이 전혀 다르면 (PDF 자체의 표기 오류/불일치) 별도 신규 등록.
- SAIX(스포츠 AIX)처럼 챕터 자체에 교과목 개요(설명문)가 없고 단순 타학과 참조 리스트만 있는 항목은
  등록하지 않음 (필수과목처럼 실제 설명문이 있는 것만 등록).
- UNIV699/UNIV899(석박사논문연구)는 독립 학위과정 학과/전공마다 매번 새로 등록; SAIX/PSEP처럼 소속 학과
  규정을 따르는 순수 부가 프로그램은 별도 등록 안 함.

## 남은 후속 작업 (필요 시)
- 이 파일(GR2026_JSONL_PROGRESS.md)은 재개용 메모였으므로 더 이상 필요 없으면 삭제해도 됨.
- UG_2026_curriculum_courses.jsonl(654개, 학부 커리큘럼)과의 통합/대조 작업이 필요하면 별도로 진행.
