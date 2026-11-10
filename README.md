# TFT 뉴비 헬퍼

로컬·내부망 전용 TFT 덱 추천 웹 앱입니다. 왼쪽에서 보유 유닛과 아이템을 고르면 오른쪽에 추천 덱이 표시됩니다. 덱을 클릭하면 구성 유닛·핵심 아이템·출처 통계를 펼쳐 볼 수 있습니다. [PRD](./PRD.md)를 참고하세요.

현재 조합은 [LoLCHESS 추천메타](https://lolchess.gg/meta)에서 수집해 저장한 스냅샷입니다. 덱 전체 유닛과 유닛별 장착 아이템을 표시하고, 각 카드의 **공략 페이지 열기**는 해당 덱의 LoLCHESS 상세 페이지를 엽니다. 추천메타에는 등수·표본 통계를 제공하지 않아 해당 수치는 표시하지 않습니다. Riot API와 API 키를 사용하지 않으며, 자동·정기 수집도 하지 않습니다. 챔피언·아이템 이름과 이미지는 Community Dragon 데이터를 사용합니다.

## 로컬 실행

Python 3.12+와 Node.js 20+가 필요합니다. 저장소 루트에서 실행합니다.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
Copy-Item .env.example .env
python -m backend.cli init-db
python -m backend.cli load-cdragon
python -m backend.cli import-lolchess
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

별도 터미널에서 프론트를 실행합니다.

```powershell
cd frontend
npm install
npm run dev
```

브라우저에서 `http://127.0.0.1:5173`을 엽니다. 재시작할 때는 저장소 루트의 `restart-local.bat`을 실행하세요. 스크립트가 시작한 API와 프론트 프로세스의 PID를 기록하고, 다음 실행 때 PID와 이미지 이름을 함께 확인해 해당 프로세스만 종료합니다. 데이터 갱신은 원하는 때 Community Dragon을 불러오고, `data/lolchess_snapshot.tsv`와 `data/lolchess_unit_items.tsv` 스냅샷을 `python -m backend.cli import-lolchess`로 저장합니다. 추천 요청은 로컬 DB만 읽습니다. 패치 변경점 메뉴는 공식 TFT 패치 노트 1개를 불러옵니다.

## 확인

`http://127.0.0.1:8000/health`의 `reference_comp_n`으로 저장된 조합 수를 확인할 수 있습니다. 유닛 1개 이상을 클릭하면 해당 유닛이 포함된 덱을 추천하고, 완성 아이템 1개 또는 재료 3개 이상을 클릭하면 아이템 추천이 표시됩니다. `python -m pytest backend -q`로 백엔드 검증을 실행할 수 있습니다.

내부망의 다른 장치에서는 실행 PC의 사설 IP로 `http://<사설-IP>:5173`에 접속합니다. `restart-local.bat`은 프론트와 API를 내부망 인터페이스에 바인딩하며, 프론트가 API 요청을 프록시합니다. Windows 방화벽이 연결을 차단하면 실행 PC에서 TCP 5173 인바운드 허용 규칙을 추가하세요. 공개 호스팅, 클라이언트 오버레이, LCU·메모리 읽기, 자동 플레이 기능은 없습니다.

## Riot 고지

TFT 뉴비 헬퍼 isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
