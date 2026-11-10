import json

import pytest

from .batch import Board, cluster_boards, jaccard
from .db import init_db, transaction
from .recommend import recommend_items, recommend_units


def test_jaccard_and_components():
    assert jaccard({"a", "b"}, {"a", "b", "c"}) == 2 / 3
    groups = cluster_boards([Board({"a", "b"}, 1), Board({"a", "b"}, 2), Board({"x", "y"}, 3)])
    assert sorted(map(len, groups)) == [1, 2]


def test_recommend_reads_precomputed_rows(tmp_path):
    path = tmp_path / "test.sqlite3"
    init_db(path)
    with transaction(path) as db:
        db.execute(
            """INSERT INTO clusters VALUES
            (1,'A · B','["a","b","c"]',2.0,.5,.1,30,30,.4,'now')"""
        )
        db.execute("INSERT INTO unit_cluster_index VALUES('a',1)")
        db.execute("INSERT INTO unit_cluster_index VALUES('b',1)")
    result = recommend_units(["a", "b"], path=path)
    assert result[0]["similarity"] == pytest.approx(2 / 3, abs=0.0001)
    assert result[0]["next_units"] == ["c"]


def test_item_recommendation_gate_and_recipe(tmp_path):
    path = tmp_path / "items.sqlite3"
    init_db(path)
    with transaction(path) as db:
        db.execute("INSERT INTO items VALUES('a','A',NULL,'[]')")
        db.execute("INSERT INTO items VALUES('b','B',NULL,'[]')")
        db.execute("INSERT INTO items VALUES('ab','AB',NULL,'[\"a\",\"b\"]')")
        db.execute("INSERT INTO clusters VALUES(1,'deck','[\"u\"]',2,.5,.1,30,30,.4,'now')")
        db.execute("INSERT INTO cluster_items VALUES(1,'ab',0.6)")
    assert recommend_items(["a", "b"], path=path) == []
    assert recommend_items(["a", "b", "a"], path=path)[0]["matched_items"] == ["ab"]
    assert recommend_items(["ab"], path=path)[0]["score"] == 0.6
