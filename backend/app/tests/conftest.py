import pytest
from app import create_app, db as _db
from app.models import Client, RateLimitConfig


@pytest.fixture(scope="session")
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="function")
def db(app):
    with app.app_context():
        yield _db
        _db.session.remove()
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def client_obj(db):
    """A standard test client with a known rate config."""
    c = Client(name="test-client", api_key="test-key-abc123", tier="standard")
    db.session.add(c)
    db.session.flush()
    config = RateLimitConfig(client_id=c.id, requests_per_window=5, window_seconds=60)
    db.session.add(config)
    db.session.commit()
    return c


@pytest.fixture
def http_client(app):
    return app.test_client()
