import uuid

import pytest
from i3worker.db.models import Folder, Tag, ColoredTag, User


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
    session.add(user)
    session.commit()
    session.add_all(
        [
            Folder(
                id=uuid.uuid4(),
                ctype="folder",
                title="My Documents",
                lang="en",
                user_id=user.id
            ),
            Folder(
                id=uuid.uuid4(),
                ctype="folder",
                title="Inbox",
                lang="en",
                user_id=user.id
            ),
        ]
    )
    session.commit()


@pytest.fixture(scope="function")
def node_with_tags(session):
    user = User(
        username='plato',
        password='truth',
        email='plato@gmail.com'
    )
    tag_one = Tag(name="one", id=uuid.uuid4())
    tag_two = Tag(name="two", id=uuid.uuid4())
    session.add(user)
    session.add(tag_one)
    session.add(tag_two)
    session.commit()

    folder_id = uuid.uuid4()

    folder = Folder(
        id=folder_id,
        ctype="folder",
        title="Scrolls",
        lang="en",
        user_id=user.id
    )
    session.add(folder)
    session.commit()

    session.add(
        ColoredTag(id=1, object_id=folder_id, tag_id=tag_one.id),
        ColoredTag(id=2, object_id=folder_id, tag_id=tag_two.id)
    )
    session.commit()

    return folder
