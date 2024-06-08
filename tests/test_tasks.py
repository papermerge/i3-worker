from sqlalchemy import select
from i3worker import db
from i3worker.db.models import Node
from i3worker.tasks import from_folder


def test_basic_from_folder(session, seed):
    some_node = session.scalars(
        select(Node).where(Node.title=="My Documents")
    ).one()
    index_entity = from_folder(session, some_node)

    assert index_entity.title == "My Documents"
    assert index_entity.entity_type == "folder"


def test_get_node_with_tags(session, node_with_tags):
    """`get_node` should return correctly node/folder with tags"""
    node = db.get_node(session, node_with_tags.id)

    assert set(node.tags) == {'one', 'two'}
