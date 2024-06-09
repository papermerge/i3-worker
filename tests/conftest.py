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
def folder_factory(session, socrates):
    def _create_folder(
        title: str,
    ):
        folder = Folder(
            id=uuid.uuid4(),
            ctype="folder",
            title=title,
            lang="en",
            user_id=socrates.id
        )

        session.add(folder)
        session.commit()

        return folder

    return _create_folder


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
def doc_factory(session, socrates):

    def _create_doc(
        title: str,
        file_name: str = "receipt_001.pdf",
        page_count: int = 2
    ):
        doc_id = uuid.uuid4()
        doc_ver_id = uuid.uuid4()
        doc = Document(
            id=doc_id,
            ctype="document",
            title=title,
            lang="en",
            user_id=socrates.id
        )
        doc_ver = DocumentVersion(
            id=doc_ver_id,
            number=1,
            file_name=file_name,
            document_id=doc_id
        )

        session.add_all([doc, doc_ver])
        for page_number in range(1, page_count + 1):
            page = Page(
                id=uuid.uuid4(),
                number=page_number,
                document_version_id=doc_ver_id
            )
            session.add(page)

        session.commit()

        return doc

    return _create_doc

