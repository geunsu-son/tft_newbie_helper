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

## 로컬 실행

1. Python 3.12+와 Node.js 20+를 설치합니다.
2. 백엔드 가상환경과 의존성을 설치합니다.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item .env.example .env
```

`.env`의 `RIOT_API_KEY`에 개인 Riot API 키를 직접 입력합니다. 키는 환경변수로만
주입하며 저장소에 커밋하지 않습니다. 이 프로젝트는 로컬·내부망 전용이므로 공개
서비스에 Personal 키를 사용하지 않습니다.

3. DB를 만들고 CDragon 유닛 데이터를 로드합니다.

```powershell
python -m backend.cli init-db
python -m backend.cli load-cdragon
```

4. API를 실행합니다. 시작 시 배치를 한 번 실행하고, 매일 15:00 Asia/Seoul에
자동 실행합니다. 15:00에 컴퓨터가 꺼져 있으면 다음 시작 때 catch-up을 시도하며,
실패 시 기존 스냅샷을 유지합니다.

```powershell
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

실제 수집을 검증하려면 API 키가 설정된 상태에서 `python -m backend.cli collect`를
실행하고, `data/tft.sqlite3`의 players/matches/participants 행을 확인합니다.
샘플 데이터로 로직만 검증하려면 `python -m pytest backend -q`를 실행합니다.

5. 별도 터미널에서 프론트를 실행합니다.

```powershell
cd frontend
npm install
npm run dev
```

브라우저에서 `http://127.0.0.1:5173`을 엽니다. 서버를 다른 내부망 장치에
노출할 때만 명시적으로 `--host 0.0.0.0`을 사용하십시오.

## Riot 고지

TFT 뉴비 헬퍼 isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc.

## 라이선스

개인 토이프로젝트. 별도 라이선스 명시 전까지 비공식·비상업용으로만 사용.
