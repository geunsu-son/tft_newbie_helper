from __future__ import annotations

import argparse

from .cdragon import load_units
from .db import init_db
from .ingest import collect


def main() -> None:
    parser = argparse.ArgumentParser(description="TFT 뉴비 헬퍼 데이터 도구")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db")
    cdragon = sub.add_parser("load-cdragon")
    cdragon.add_argument("--url", default=None)
    collect_parser = sub.add_parser("collect")
    collect_parser.add_argument("--page-limit", type=int, default=20)
    collect_parser.add_argument("--matches-per-player", type=int, default=None)
    args = parser.parse_args()
    if args.command == "init-db":
        init_db()
    elif args.command == "load-cdragon":
        print(f"유닛 {load_units(args.url)}개를 로드했습니다.")
    else:
        players, matches = collect(
            page_limit=args.page_limit, matches_per_player=args.matches_per_player
        )
        print(f"플레이어 {players}명, 매치 {matches}개를 저장했습니다.")


if __name__ == "__main__":
    main()
