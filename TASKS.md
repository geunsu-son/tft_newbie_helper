# TFT 뉴비 헬퍼 — MVP 구현 태스크

PRD(`PRD.md`)의 **MVP 범위**만 구현한다: 유닛≥2 추천(Jaccard) + 패치 변경점 뷰 + 로컬 배치.  
아이템 추천·증강 가중·상징 점수(`S_emblem`)는 **M4(이후)** — MVP에 넣지 않는다.

## Proposed tech stack (제안 — PRD 미고정)

로컬·내부망 전용에 맞춘 단순 스택 제안이다. 구현 중 동등한 대안으로 교체 가능하되, PRD 제약(로컬 서버·로컬 DB·배치·반응형 웹)을 지킬 것.

| 층 | 제안 |
| --- | --- |
| Backend | Python 3.12+ · **FastAPI** |
| DB | **SQLite** (로컬 파일) |
| Batch / scheduler | 앱 기동 시 잡 + **APScheduler**(또는 동등)로 매일 15:00 Asia/Seoul · catch-up |
| Frontend | **React + Vite** · 한국어 UI · 반응형 |
| Config | `.env`에 `RIOT_API_KEY` (Personal). 키를 레포에 커밋하지 말 것 |
| Static data | Community Dragon TFT JSON (+ 필요 시 Data Dragon 아이콘) |

디렉터리 제안(강제 아님):

```text
tft_newbie_helper/
  PRD.md
  TASKS.md
  backend/          # FastAPI, ETL, recommend
  frontend/         # Vite React
  data/             # sqlite + cache (gitignore)
  .env.example
  README.md
```

---

## M0 — PRD·키·등록

- [ ] **T0.1** Personal Riot API 키 발급·로컬 `.env`만 사용 (레포 미포함)
- [ ] **T0.2** Developer Portal에 개인/토이 제품 등록(권장/요구)
- [ ] **T0.3** README에 미공식 고지문·로컬 실행·내부망 전용·에메랄드+·유닛≥2 게이트 명시

**완료 기준(Acceptance)**

- [ ] 키가 환경변수로만 주입됨을 문서화
- [ ] README에 Riot 미공식 문구 + 비목표(오버레이/자동화 금지) 명시
- [ ] `PRD.md` / `TASKS.md`가 레포에 있음

---

## M1 — KR 시드 + 매치 PoC + CDragon

- [ ] **T1.1** `tft-league-v1`(KR): challenger / grandmaster / master + `entries/EMERALD|DIAMOND/I–IV` 페이지 수집
- [ ] **T1.2** `tft-match-v1`(ASIA): 시드 puuid → match id → match detail (Personal 한도 준수·백오프)
- [ ] **T1.3** 랭크 큐·현재 세트 필터, Participant 필드 저장(placement, units, traits, augments, items)
- [ ] **T1.4** CDragon TFT 정적 데이터 로드(챔피언 id↔이름 등). UI 하드코딩 챔프명 금지
- [ ] **T1.5** SQLite 스키마: players/matches/participants/units(+items) · batch_runs

**완료 기준**

- [ ] KR 에메랄드+ 시드 → 매치 상세가 DB에 적재되는 스크립트/커맨드가 동작
- [ ] Personal rate limit에 걸리기 전 429 처리·재시도
- [ ] CDragon에서 유닛 목록을 API/스크립트로 조회 가능

---

## M2 — 클러스터·점수·배치·n_min

- [ ] **T2.1** 최종 보드 유닛 집합 Jaccard 클러스터링 (코사인 미사용)
- [ ] **T2.2** 클러스터 통계: 평균 등수, Top4율, 승률(=placement 1), 핵심 유닛, 표본 n
- [ ] **T2.3** 매 배치 `N`으로 \(n_{\min}=\max(30,\lceil 0.005\cdot N\rceil)\) 재계산·적용, n < n_min 숨김
- [ ] **T2.4** \(S_{\mathrm{unit}}\), \(S_{\mathrm{final}}\) (초안 \(w_m=0.65\), \(w_p=0.35\)) · Top-N(3~5)
- [ ] **T2.5** 유닛→후보 덱 사전계산/역인덱스 테이블
- [ ] **T2.6** 스케줄: **프로세스 시작 시** 배치 + **매일 15:00 Asia/Seoul** · 놓친 15:00은 **다음 시작 catch-up** · 실패 시 직전 스냅샷 유지

**완료 기준**

- [ ] 배치 1회 후 클러스터·n_min·사전계산 테이블이 DB에 존재
- [ ] 유닛 집합(≥2) 입력 시 Top-N이 매치 API 재호출 없이 DB 조회로만 나옴
- [ ] 시작/15:00/catch-up 동작을 로그 또는 테스트로 확인

---

## M3 — 로컬 MVP UI (유닛 추천 + 패치)

- [ ] **T3.1** FastAPI: `POST /recommend/units` (유닛≥2 게이트, 미만 시 안내 메시지)
- [ ] **T3.2** React/Vite: 유닛 검색·다중선택·성급, 판 중 재입력(직전 입력 유지)
- [ ] **T3.3** 결과 카드: 덱명, 평균 등수, Top4율, 승률(정의 표기), 유사도, 다음 유닛, 표본 n
- [ ] **T3.4** 데이터 기준 시각·패치·KR·에메랄드+ 고정 고지, 콜드스타트 배너, 티어 필터 UI **없음**
- [ ] **T3.5** 패치 변경점 뷰(간단): 공식 TFT 패치 노트 기반 챔피언/아이템/증강 상향·하향 리스트(+출처 링크)
- [ ] **T3.6** 로컬 바인딩(예: `127.0.0.1` 또는 내부망 인터페이스). 공인 배포 설정 없음
- [ ] **T3.7** 추천 조회 p95 < 300ms 목표 측정(로컬 DB 기준, 네트워크 제외)

**완료 기준**

- [ ] 유닛 1개만 넣면 추천 대신 안내 문구
- [ ] 유닛 2개+면 Top-N 카드 표시, 요청 시 Riot 매치 미호출
- [ ] 패치 변경점 페이지/섹션이 공식 노트 출처와 함께 보임
- [ ] README만으로 로컬 기동(백엔드+프론트+배치) 가능

---

## M4 — 이후 (MVP 제외, 참고만)

PRD상 이후 단계. Codex MVP 작업 범위 **밖**.

- [ ] 아이템 게이트(부품≥3 | 완제≥1 | 완제≥1∧부품≥1) + 별도 추천 섹션 · \(S_{\mathrm{item\_fit}}\)
- [ ] 증강 가중
- [ ] 상징 점수 \(S_{\mathrm{emblem}}\) + 관련 덱 (Legend 승률 표시 금지)

---

## 명시적 금지 (모든 마일스톤)

- 게임 클라이언트 오버레이 / LCU·메모리 읽기 / 자동 선택·롤링
- lolchess.gg·tft.op.gg HTML 스크래핑을 1차 데이터 소스로 사용
- Legend / Legend 기반 증강 승률 표시
- Personal 키로 공개 서비스·오픈 알파 운영
- 공인 호스팅·외부 공개 배포(현 단계)

## 구현 시 PRD 수식 요약

```text
(0) n_min = max(30, ceil(0.005 * N))   # 매 배치 재계산
(1) S_unit = |U ∩ C_core| / |C_core|
(2) S_final = 0.65 * S_unit + 0.35 * S_perf(C)
```
