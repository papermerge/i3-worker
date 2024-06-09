import uuid

import pytest
from i3worker.db.models import (
    Folder,
    Document,
    DocumentVersion,
    Page,
    Tag,
    ColoredTag,
    User
)
from i3worker import db
from i3worker.db import Base, engine


@pytest.fixture(scope="function")
def session():
    Base.metadata.create_all(engine)
    db_session = db.get_db()
    try:
        with db_session() as se:
            yield se
    finally:
        Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def socrates(session):
    user = User(
        username='socrates',
        password='truth',
        email='socrates@gmail.com'
    )
    session.add(user)
    session.commit()

    return user


@pytest.fixture(scope="function")
def seed_two_folders(session, socrates):
    session.add_all(
        [
            Folder(
                id=uuid.uuid4(),
                ctype="folder",
                title="My Documents",
                lang="en",
                user_id=socrates.id
            ),
            Folder(
                id=uuid.uuid4(),
                ctype="folder",
                title="Inbox",
                lang="en",
                user_id=socrates.id
            ),
        ]
    )
    session.commit()


@pytest.fixture(scope="function")
def node_with_tags(session, socrates):
    tag_one = Tag(name="one", id=uuid.uuid4())
    tag_two = Tag(name="two", id=uuid.uuid4())
    session.add(tag_one)
    session.add(tag_two)
    session.commit()

    folder_id = uuid.uuid4()

    folder = Folder(
        id=folder_id,
        ctype="folder",
        title="Scrolls",
        lang="en",
        user_id=socrates.id
    )
    session.add(folder)
    session.commit()

    session.add_all([
        ColoredTag(id=1, object_id=folder_id, tag_id=tag_one.id),
        ColoredTag(id=2, object_id=folder_id, tag_id=tag_two.id)
    ])
    session.commit()

    return folder


@pytest.fixture(scope="function")
def seed_receipt_doc(session, socrates):
    doc = Document(
        id=uuid.uuid4(),
        ctype="document",
        title="receipt_001.pdf",
        lang="en",
        user_id=socrates.id
    )
    session.add(doc)
    session.commit()
