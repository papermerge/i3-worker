from sqlalchemy import select
from i3worker import db
from i3worker.db.models import Node
from i3worker.tasks import from_folder, from_document
from i3worker.schema import PAGE, FOLDER


def test_from_folder(session, seed_two_folders):
    """`from_folder` should return index_entity"""
    some_node = session.scalars(
        select(Node).where(Node.title=="My Documents")
    ).one()
    index_entity = from_folder(session, some_node)

    assert index_entity.title == "My Documents"
    assert index_entity.entity_type == FOLDER


def test_from_document(session, seed_receipt_doc):
    """`from_document` should return list of index_entities"""
    some_node = session.scalars(
        select(Node).where(Node.title=="receipt_001.pdf")
    ).one()
    index_entities = from_document(session, some_node)

    assert index_entities[0].title == "receipt_001.pdf"
    assert index_entities[0].entity_type == PAGE
    assert index_entities[1].title == "receipt_001.pdf"
    assert index_entities[1].entity_type == PAGE


def test_get_node_with_tags(session, node_with_tags):
    """`get_node` should return correctly node/folder with tags"""
    node = db.get_node(session, node_with_tags.id)

    assert set(node.tags) == {'one', 'two'}
