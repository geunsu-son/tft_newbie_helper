from __future__ import annotations

import argparse
from dotenv import load_dotenv

from .cdragon import load_units
from .db import init_db
from .lolchess import import_snapshot
from .reference_comps import import_comps


def main() -> None:
    load_dotenv()
    parser = argparse.ArgumentParser(description="TFT 뉴비 헬퍼 데이터 도구")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("init-db")
    cdragon = sub.add_parser("load-cdragon")
    cdragon.add_argument("--url", default=None)
    sub.add_parser("import-comps")
    lolchess = sub.add_parser("import-lolchess")
    lolchess.add_argument("--path", default="data/lolchess_snapshot.tsv")
    args = parser.parse_args()
    if args.command == "init-db":
        init_db()
    elif args.command == "load-cdragon":
        print(f"유닛 {load_units(args.url)}개를 로드했습니다.")
    elif args.command == "import-comps":
        print("저장한 조합 / 확인한 카드:", import_comps())
    elif args.command == "import-lolchess":
        print("저장한 LoLCHESS 덱:", import_snapshot(args.path))


if __name__ == "__main__":
    main()
