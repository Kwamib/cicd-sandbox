import os
def clean_name(name):
    """Trim spaces and lowercase a page name, so 'Home ' and 'home' count as one page."""
    cleaned = name.strip().lower()
    if not cleaned:
        raise ValueError("page name can't be empty")
    return cleaned


def record_visit(db, cache, name):
    """Count a visit in Redis and record it in Postgres. Returns the new count."""
    page = clean_name(name)
    count = cache.incr(f"visits:{page}")
    with db.cursor() as cur:
        cur.execute("INSERT INTO visits (page) VALUES (%s)", (page,))
    db.commit()
    return count
