from sqlalchemy import select
from i3worker import db
from i3worker.db.models import Node
from i3worker.tasks import from_folder, from_document, from_page
from i3worker.schema import PAGE, FOLDER


def test_from_folder(session, folder_factory):
    """`from_folder` should return index_entity"""
    folder_factory(title="My Documents")

    some_node = session.scalars(
        select(Node).where(Node.title=="My Documents")
    ).one()
    index_entity = from_folder(session, some_node)

    assert index_entity.title == "My Documents"
    assert index_entity.entity_type == FOLDER


def test_from_document(session, doc_factory):
    """`from_document` should return list of index_entities"""
    doc_factory(title="receipt_001.pdf", page_count=2)

    some_node = session.scalars(
        select(Node).where(Node.title=="receipt_001.pdf")
    ).one()

    index_entities = from_document(session, some_node)

    assert index_entities[0].title == "receipt_001.pdf"
    assert index_entities[0].entity_type == PAGE
    assert index_entities[1].title == "receipt_001.pdf"
    assert index_entities[1].entity_type == PAGE


def test_from_page(session, page_factory):
    page = page_factory(title="My Receipt", page_number=1, text="hello")

    index_entity = from_page(session, page.id)

    assert index_entity.title == "My Receipt"
    assert index_entity.entity_type == PAGE


def test_get_node_with_tags(session, folder_factory):
    """`get_node` should return correctly node/folder with tags"""

    folder = folder_factory(title="My Folder", tags=["one", "two"])
    node = db.get_node(session, folder.id)

    assert set(node.tags) == {'one', 'two'}
