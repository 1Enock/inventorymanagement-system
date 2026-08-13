import pytest

from app import create_app
from models import db


@pytest.fixture()
def app():
    """A Flask app configured with a fresh in-memory SQLite DB per test."""
    app = create_app({
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "TESTING": True,
    })
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()
