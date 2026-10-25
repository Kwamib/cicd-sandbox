import os

import psycopg2
import pytest
import redis

from app.visits import clean_name, record_visit

DB_URL = os.environ.get("TEST_DATABASE_URL")
REDIS_URL = os.environ.get("REDIS_TEST_URL")


def test_clean_name_trims_and_lowercases():
    assert clean_name("  Home ") == "home"


def test_clean_name_rejects_empty():
    with pytest.raises(ValueError):
        clean_name("   ")


@pytest.mark.skipif(not (DB_URL and REDIS_URL), reason="TEST_DATABASE_URL and REDIS_TEST_URL not set")
def test_record_visit_counts_and_stores():
    db = psycopg2.connect(DB_URL)
    cache = redis.Redis.from_url(REDIS_URL)
    with db.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS visits")
        cur.execute("CREATE TABLE visits (id serial PRIMARY KEY, page text NOT NULL)")
    db.commit()
    cache.delete("visits:home")

    assert record_visit(db, cache, "Home") == 1
    assert record_visit(db, cache, "home ") == 2

    with db.cursor() as cur:
        cur.execute("SELECT count(*) FROM visits WHERE page = 'home'")
        assert cur.fetchone()[0] == 2
    db.close()
