import os
import uuid

import pytest
from i3worker.db.models import Folder, Node, CType, User


@pytest.fixture(scope="function")
def session():
    from i3worker import db
    from i3worker.db import Base, engine

    Base.metadata.create_all(engine)
    db_session = db.get_db()
    try:
        with db_session() as se:
            yield se
    finally:
        Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def seed(session):
    user = User(
        username='socrates',
        password='truth',
        email='socrates@gmail.com'
    )
    node_id1 = uuid.uuid4()
    node_id2 = uuid.uuid4()
    session.add(user)
    session.commit()
    session.add_all(
        [
            Node(
                id=node_id1,
                ctype="folder",
                title="My Documents",
                lang="en",
                user_id=user.id
            ),
            Node(
                id=node_id2,
                ctype="folder",
                title="Inbox",
                lang="en",
                user_id=user.id
            )
        ]
    )
    session.commit()
