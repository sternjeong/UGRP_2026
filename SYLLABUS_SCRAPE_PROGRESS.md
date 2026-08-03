# PLMS 강의계획서 스크레이핑 진행 상황 (재개용 메모)

## 작업 목표
POSTECH PLMS(`https://plms.postech.ac.kr/local/ubion/course/syllabusV.php?id=<ID>`)의
강의계획서 페이지를 id **12000~13000** 범위로 순회하며, 각 페이지에서 아래 4개 항목을 파싱한다:

- `3. Course Objectives` → `course_objectives`
- `4. Prerequisites & require` → `prerequisites`
- `7. Course References` → `course_references`
- `8. Course Plan` → `course_plan`

페이지의 `Course No.`(학수번호)가 `UG_2026_curriculum_courses.jsonl`에 이미 있는 `course_code`와
일치하는 경우에만 해당 레코드에 위 4개 필드를 **merge**한다 (덮어쓰기 아님, 새 필드 추가).
일치하지 않으면 스킵.

**중요 — 페이지 언어**: URL에 `&lang=en`을 반드시 붙여야 영문 라벨("Course No.", "Course Objectives" 등)로
렌더링된다. 이게 없으면 한국어 라벨(`학수번호` 등)로 나와서 파싱이 실패한다.

## Dedup 규칙 (사용자 확정)
- 기준: **course_code 단위**. 같은 과목이 여러 학기/섹션으로 다른 id에 걸쳐 나와도 **최초 1회만** 채택.
- 이미 `course_objectives` 필드가 채워진 course_code는 재확인 없이 곧바로 `pass` (로그에 `already recorded, pass` 기록).
- 즉, 이 스크립트는 **몇 번을 다시 돌려도 안전(idempotent)** 하다 — 이미 채워진 과목은 건드리지 않고,
  아직 안 채워진 과목만 마저 채운다. **중단됐다가 이어서 할 때도 그냥 스크립트를 처음부터(12000) 다시 돌리면 됨.**

## 스크립트 위치 (프로젝트 루트, git 추적 대상)
`/workspaces/UGRP_2026/scrape_syllabus.py`

실행 방법:
```bash
python3 /workspaces/UGRP_2026/scrape_syllabus.py
```
- 요청 간 딜레이 0.35초 (사용자 요청: 서버 부하 고려)
- 매 매칭(ADDED)마다 **즉시** `UG_2026_curriculum_courses.jsonl`을 통째로 다시 써서 저장 (원자적 교체, `.tmp` → `os.replace`)
  → 따라서 스크립트가 중간에 죽어도 **그 시점까지 찾은 과목 정보는 이미 파일에 반영되어 있음**. 데이터 유실 없음.
- 로그: 현재는 스크래치패드 경로에 append (`scrape_progress.log`) — **이 로그는 세션이 끝나면 사라짐**.
  진행 여부 확인은 로그 대신 아래 "진행 상황 확인 방법"을 사용할 것.
- 전체 범위(1001개 id)를 다 돌면 자연 종료. 만약 654개 과목이 스크래핑 대상 id 범위 안에서 전부 채워지면
  중간에 조기 종료(`all N target courses filled, stopping early`).

## 진행 상황 확인 방법 (새 세션에서 실행)
```bash
python3 -c "
import json
n=0; tot=0
with open('/workspaces/UGRP_2026/UG_2026_curriculum_courses.jsonl') as f:
    for line in f:
        d=json.loads(line); tot+=1
        if 'course_objectives' in d: n+=1
print(f'{n} / {tot} 과목에 syllabus 필드 채워짐')
"
```
이 값이 654/654가 아니면 아직 안 끝난 것 → `python3 scrape_syllabus.py` 다시 실행하면 이어서 채워짐.

## 현재 상태 — id 12000~13000 범위 스크레이핑 **완료**
- 완료 시각: 2026-07-24
- 결과: id 1001개 전부 확인 (`checked=1001`), 이 범위에서 **172개 과목 신규 추가**, 최종 **175 / 654** 과목에
  4개 필드(course_objectives/prerequisites/course_references/course_plan)가 채워짐.
  (참고: 12000~13000대는 2025-Spring 학기 강좌들이 몰려 있는 id 구간으로 보임 — 예: id=12677이 2025-Spring)
- 나머지 **479개 과목은 이 id 범위 안에 강의계획서가 없었음** → 정상 종료(`stopping early` 조건은 미도달,
  1001개를 끝까지 다 돌고 자연 종료됨).

## 남은 479개 과목을 마저 채우려는 시도 (2차 라운드, 2023~2025년만)

사용자 요청: 2023~2025년도 강의계획서만 1차 필터링해서 스크레이핑. id 표본 조사 결과:
| id | 학기 |
|---|---|
| 6000 | 2022-091 |
| 7000 | 2023-090 |
| 9000 | 2023-092 |
| 10000 | 2024-090 |
| 11000 | 2024-092 |
| 12000 | 2025-090 |
| 13000 | 2025-090 |
| 14000 | 2025-092 |
| 15000 | 2026-090 |

→ 2023~2025년은 대략 id **7000~14999** 구간에 분포. 정확한 경계를 이진탐색으로 찾으려다,
`scrape_syllabus.py`에 이미 연도 필터(`YEAR_MIN=2023, YEAR_MAX=2025`, 페이지 title의 `(YYYY-SSS` 패턴으로 판정)를
넣어뒀으므로 굳이 정밀 경계가 필요 없다고 판단 → **여유 있게 넓은 범위를 돌리고 필터가 알아서 걸러내는 방식**으로 변경.

### 스크립트 변경 사항 (이번 라운드에 추가됨)
- `ID_START`/`ID_END`를 커맨드라인 인자로 받도록 변경: `python3 scrape_syllabus.py <START> <END>`
  (인자 없이 실행하면 기본값 12000~13000)
- 연도 필터 추가: 페이지에서 연도를 뽑아 2023~2025가 아니면 즉시 skip (course_no 파싱 이전에 필터링, 빠름)
- 로그 경로를 스크래치패드 → **프로젝트 루트 `scrape_progress.log`** 로 변경 (세션 간 영속되도록)

### 이번에 실행한 명령 (백그라운드, harness-tracked)
```bash
python3 scrape_syllabus.py 5800 11999 && python3 scrape_syllabus.py 13001 15100
```
- 12000~13000은 1차 라운드에서 이미 전부 확인했으므로 제외하고, 앞뒤로 여유(5800, 15100)를 두고 두 구간을 이어서 실행.
- 총 대상 id 수 약 8300개 × 0.35초 딜레이 ≈ **예상 48분 소요**.
- 이 역시 idempotent — 중단되면 그냥 같은 명령 다시 실행하면 됨 (이미 채워진 course_code는 자동 스킵).
- 백그라운드 bash task ID: `bpl0v4vqt` (이번 세션에서만 유효, 새 세션에서는 무의미 — 아래 진행률 확인 명령으로 대체)

### 2차 라운드 완료 결과 (2026-07-24)
- id 5800~11999: checked=6193, added=243
- id 13001~15100: checked=2100, added=12
- **최종: 430 / 654** 과목에 syllabus 필드 채워짐 (1차 175개 + 2차 255개)
- 654줄 전부 유효 JSON 확인 완료, 데이터 손상 없음
- 나머지 **224개 과목은 2023~2025년 id 범위(5800~15100) 안에 강의계획서를 못 찾음** — 해당 기간에
  개설되지 않았거나(캡스톤/졸업연구 등 비정기 개설 과목 다수 포함), PLMS 학수번호 표기가 미묘하게 달랐을 가능성.
  미채워진 224개 목록은 위 "완료 후 해야 할 일" 명령으로 재확인 가능.

## 3차 라운드 — 범위 확대 (사용자 요청: "범위를 넓혀서 찾아줘")

id 상한 재조사: id=16400 → 2026-092(존재), id=16600 → 404. 즉 PLMS syllabus id 유효 범위는 대략 **1 ~ 16599** 정도로 추정.
남은 224개 과목을 찾기 위해 연도 필터를 사실상 해제(2015~2026)하고, 아직 안 돈 두 구간을 마저 스캔:
- id 1~5799 (2022년 이하)
- id 15101~16599 (2026년)

`scrape_syllabus.py`에 `YEAR_MIN`/`YEAR_MAX`도 3번째/4번째 커맨드라인 인자로 받도록 변경함
(기본값 2015~2026, 사실상 필터 없음).

### 실행 명령 (백그라운드, harness-tracked, task id: `bm90i8qty`)
```bash
python3 scrape_syllabus.py 1 5799 && python3 scrape_syllabus.py 15101 16599
```
예상 소요 약 7300개 id × 0.35초 ≈ **43분**.

### 3차 라운드 완료 결과 (2026-07-24)
- id 1~5799: checked=5799, added=42
- id 15101~16599: checked=1499, added=20
- **최종: 492 / 654** 과목에 syllabus 필드 채워짐
- 654줄 전부 유효 JSON 확인 완료

## PLMS id 공간 전체 커버리지 — 이제 확장 여지 없음
지금까지 스크레이핑한 id 구간을 합치면 **1 ~ 16599 전체**를 이미 다 돈 것 (12000~13000 + 5800~11999 +
13001~15100 + 1~5799 + 15101~16599 = 1~16599 전 구간). id=16600부터는 404 확인됨(PLMS syllabus id 상한).
**즉, id 범위를 더 넓혀도 추가로 찾을 수 있는 과목이 없음.**

### 남은 162개가 안 채워지는 이유 (id 범위 문제가 아님)
`UG_2026_curriculum_courses.jsonl`의 `course_code` 필드 자체가 PLMS의 단일 학수번호 형식과 안 맞는 경우가 다수:
- 콤마로 묶인 복수 학수번호: 예) `"MATH301, 302"`, `"PHYS101, 102"`, `"MSUS102, 103"`
- 슬래시로 묶인 cross-listing: 예) `"CITE241/MECH361"`, `"EECE442/NGCN301"`
- PLMS의 `Course No.` 필드는 항상 단일 코드(예: `"MATH301"`)라서 위 형식과 정확히 일치할 수 없어 자동으로 스킵됨.
- 나머지는 캡스톤/졸업연구/세미나류 등 정규 학기에 강의계획서가 등록되지 않는 과목으로 추정.

이 162개를 마저 채우려면 id 범위 확장이 아니라 **매칭 로직 변경**이 필요함 (예: `course_code`를 `,` `/` 기준으로
분리해서 각 개별 코드로도 매칭 시도). 사용자가 원하면 다음 세션에서 이 매칭 로직 개선부터 시작하면 됨.

## 4차 라운드 — 복합 학수번호(콤마/슬래시) 분리 매칭 (사용자 요청)

사용자 요청: `"CITE241/MECH361"` 같은 복합 코드는 `CITE241`로 먼저 찾아보고 없으면 `MECH361`로 찾는 식으로
각각 접근. 먼저 매칭되면 그걸로 채우고 더 이상 건드리지 않음.

### 스크립트 변경 사항
- `split_course_codes(course_code)` 함수 추가:
  - `/` 포함 시: 그냥 `/`로 split (예: `"CITE241/MECH361"` → `["CITE241","MECH361"]`)
  - `,` 포함 시: 첫 코드에서 접두어(알파벳)를 뽑아 숫자만 있는 뒷부분에 붙여줌
    (예: `"MATH301, 302"` → `["MATH301","MATH302"]`, `"PHYS101H, 102H"` → `["PHYS101H","PHYS102H"]`)
  - 둘 다 없으면 원본 그대로 `[course_code]`
- `load_courses()`가 이제 `records, by_code, lookup` 3개를 반환. `lookup`은 **분리된 개별 코드 → 원본 레코드**
  매핑 (`setdefault`라서 먼저 등록된 레코드가 우선, 충돌 시 덮어쓰지 않음).
- 매칭 판정을 `course_code` 문자열 동일성이 아니라 **레코드 객체에 `course_objectives` 필드가 있는지**로 변경.
  → 복합 코드의 어느 alt(예: MECH361)로 먼저 채워지면, 나머지 alt(CITE241)로 다시 찾아도 이미 채워진 걸로
  인식해서 자동 skip (사용자가 요청한 "먼저 채워지면 가만히 내버려두고" 정확히 구현됨).
- 채워질 때 실제 매칭에 쓰인 alt 코드를 `syllabus_matched_code` 필드로 같이 저장해둠 (추적용).

### 실행 명령 (백그라운드, harness-tracked task id: `bmjst9epj`, Monitor task id: `bg0dc9hlc`)
```bash
python3 scrape_syllabus.py 1 16599
```
전체 id 공간(1~16599)을 다시 순회 — 이미 채워진 492개 레코드는 즉시 skip되므로 빠르게 지나가고,
아직 안 채워진 162개(및 그 alt 코드들)만 실질적으로 매칭 시도함. 예상 소요 약 16599개 id × 0.35초 ≈ **97분**.
(Monitor의 timeout은 60분 한도라 완료 전에 만료될 수 있음 — 이 경우 Bash 백그라운드 task 자체의 완료 알림을
기다리면 됨. 새 세션에서는 진행률 확인 명령으로 상태 체크.)

### 새 세션에서 이어가기
```bash
# 진행률 확인
python3 -c "
import json
n=0; tot=0
with open('/workspaces/UGRP_2026/UG_2026_curriculum_courses.jsonl') as f:
    for line in f:
        d=json.loads(line); tot+=1
        if 'course_objectives' in d: n+=1
print(f'{n} / {tot}')
"
# 프로세스가 이미 죽어있는지 확인
pgrep -af scrape_syllabus.py || echo "실행 중인 스크레이핑 프로세스 없음 -> 아래로 재실행"
# 재실행 (필요시)
python3 scrape_syllabus.py 5800 11999 && python3 scrape_syllabus.py 13001 15100
```

## 완료 후 해야 할 일
- 없음(추가 검증 필요시: 4개 필드가 비어있는(`""`) 케이스가 있는지, 즉 id 범위 안에 해당 과목의
  강의계획서가 아예 없었는지 확인하고 싶다면 아래로 카운트):
```bash
python3 -c "
import json
missing=[]
with open('/workspaces/UGRP_2026/UG_2026_curriculum_courses.jsonl') as f:
    for line in f:
        d=json.loads(line)
        if 'course_objectives' not in d: missing.append(d['course_code'])
print(len(missing), 'courses still missing syllabus fields')
print(missing[:30])
"
```
  (12000~13000 범위 밖의 학기에만 개설된 과목이면 이 범위 스크레이핑으로는 못 채움 — 정상적인 경우임)
