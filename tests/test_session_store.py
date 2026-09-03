from backend.session_store import SessionStore


def test_session_store_create_get_and_delete() -> None:
    store = SessionStore(ttl_seconds=60)
    session = store.create(filename="guide.pdf", graph=object(), chunk_count=4)

    assert store.get(session.session_id) == session
    assert store.delete(session.session_id) is True
    assert store.get(session.session_id) is None
    assert store.delete(session.session_id) is False
