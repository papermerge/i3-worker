from uuid import UUID
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import Session

from i3worker import models
from i3worker.db.models import Node, ColoredTag


def get_node(
    db_session: Session,
    node_id: UUID
) -> [models.Document | models.Folder]:
    with db_session as session:
        stmt = select(Node).where(
            Node.id==node_id
        )
        db_node = session.scalars(stmt).one()
        colored_tags_stmt = select(ColoredTag).where(
            ColoredTag.object_id==node_id
        )
        colored_tags = session.scalars(colored_tags_stmt).all()
        db_node.tags = [
            tag.name for tag in _get_tags_for(colored_tags, db_node.id)
        ]

        model_node = models.Node.model_validate(db_node)

    return model_node


def _get_tags_for(
    colored_tags: Sequence[ColoredTag],
    node_id: UUID
) -> list[models.Tag]:
    node_tags = []

    for color_tag in colored_tags:
        if color_tag.object_id == node_id:
            node_tags.append(
                models.Tag.model_validate(color_tag.tag)
            )

    return node_tags
