# TFT 뉴비 헬퍼

로컬·내부망 전용 Teamfight Tactics 뉴비용 덱 추천 웹 헬퍼 (개인 토이프로젝트).

- **PRD:** [PRD.md](./PRD.md)
- **구현 태스크(MVP):** [TASKS.md](./TASKS.md)

## 한 줄

KR 에메랄드+ 매치를 로컬에 모아 둔 뒤, 판 중 **유닛 ≥2**를 수동 입력하면 사전 계산된 메타 덱 Top-N을 추천합니다. 클라이언트 연동·오버레이·자동 선택은 없습니다.

## 범위 (MVP)

| 포함 | 제외(이후) |
| --- | --- |
| 유닛 기반 추천 (Jaccard) | 아이템 조합 추천 |
| 패치 변경점 뷰 | 증강 가중·상징 점수 |
| 로컬 배치 (시작 + 15:00 KST) | 공인 호스팅 |

## 제안 스택

Python FastAPI + SQLite + APScheduler · React/Vite — 상세는 `TASKS.md`의 Proposed tech stack.

## Riot 고지

TFT 뉴비 헬퍼 isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc.

## 라이선스

개인 토이프로젝트. 별도 라이선스 명시 전까지 비공식·비상업용으로만 사용.
