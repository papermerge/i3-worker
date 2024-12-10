from uuid import UUID
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.orm import selectinload


from i3worker import schema
from i3worker.db.engine import Session
from i3worker.db.orm import (Node, Tag, Document, DocumentVersion, Page)


def get_doc(db_session: Session, doc_id: UUID) -> schema.Document:
    stmt = select(Document).where(
        Document.id==doc_id
    )
    db_doc = db_session.scalars(stmt).one()
    model_doc = schema.Document.model_validate(db_doc)

    return model_doc


def get_docs(db_session: Session, doc_ids: list[UUID]) -> list[schema.Document]:
    stmt = select(Document).where(
        Document.id.in_(doc_ids)
    )
    db_docs = db_session.scalars(stmt).all()
    model_docs = [
        schema.Document.model_validate(db_doc) for db_doc in db_docs
    ]

    return model_docs


def get_last_version(
    db_session: Session,
    doc_id: UUID
) -> schema.DocumentVersion:
    """
    Returns last version of the document
    identified by doc_id
    """
    stmt = select(DocumentVersion).join(Document).where(
        DocumentVersion.document_id == doc_id,
    ).order_by(
        DocumentVersion.number.desc()
    ).limit(1)
    db_doc_ver = db_session.scalars(stmt).one()
    model_doc_ver = schema.DocumentVersion.model_validate(db_doc_ver)

    return model_doc_ver


def get_doc_ver(
    db_session: Session,
    id: UUID  # noqa
) -> schema.DocumentVersion:
    """
    Returns last version of the document
    identified by doc_id
    """
    stmt = select(DocumentVersion).where(DocumentVersion.id == id)
    db_doc_ver = db_session.scalars(stmt).one()
    model_doc_ver = schema.DocumentVersion.model_validate(db_doc_ver)

    return model_doc_ver


def get_pages(
    db_session: Session,
    doc_ver_id: UUID
) -> list[schema.Page]:
    """
    Returns first page of the document version
    identified by doc_ver_id
    """
    stmt = select(Page).where(
        Page.document_version_id == doc_ver_id,
    ).order_by(
        Page.number.asc()
    )

    db_pages = db_session.scalars(stmt).all()
    result = [
        schema.Page.model_validate(db_page)
        for db_page in db_pages
    ]

    return list(result)


def get_page(
    db_session: Session,
    id: UUID,
) -> schema.Page:
    stmt = select(Page).join(DocumentVersion).join(Document).where(
        Page.id == id,
    )
    db_page = db_session.scalars(stmt).one()
    result = schema.Page.model_validate(db_page)

    return result


def get_node(
    db_session: Session,
    node_id: UUID
) -> [schema.Document | schema.Folder]:
    stmt = select(Node).where(
        Node.id==node_id
    )
    db_node = db_session.scalars(stmt).one()
    colored_tags_stmt = select(Tag).where(
        Tag.object_id==node_id
    )
    colored_tags = db_session.scalars(colored_tags_stmt).all()
    db_node.tags = [
        tag.name for tag in _get_tags_for(colored_tags, db_node.id)
    ]

    model_node = schema.Node.model_validate(db_node)

    return model_node


def get_nodes(
    db_session: Session,
    node_ids: list[UUID] | None = None
) -> list[schema.Document | schema.Folder]:
    items = []
    if node_ids is None:
        node_ids = []

    if len(node_ids) > 0:
        stmt = select(Node).options(selectinload(Node.tags)).filter(
            Node.id.in_(node_ids)
        )
    else:
        stmt = select(Node).options(selectinload(Node.tags))

    nodes = db_session.scalars(stmt).all()

    for node in nodes:
        if node.ctype == 'folder':
            items.append(
                schema.Folder.model_validate(node)
            )
        else:
            items.append(
                schema.Document.model_validate(node)
            )

    return items


def _get_tags_for(
    colored_tags: Sequence[Tag],
    node_id: UUID
) -> list[schema.Tag]:
    node_tags = []

    for color_tag in colored_tags:
        if color_tag.object_id == node_id:
            node_tags.append(
                schema.Tag.model_validate(color_tag.tag)
            )

    return node_tags
