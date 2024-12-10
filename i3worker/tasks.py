import uuid
import logging
from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy import exc

from i3worker import constants, schema
from i3worker.db.engine import Session
from i3worker.db import api
from i3worker.config import get_settings
from i3worker.index import IndexEntity, PAGE, FOLDER
from salinic import IndexRW, create_engine


logger = logging.getLogger(__name__)
settings = get_settings()


def get_index():
    engine = create_engine(settings.papermerge__search__url)
    return IndexRW(engine, schema=IndexEntity)


@shared_task(name=constants.INDEX_ADD_NODE)
def index_add_node(node_id: str):
    """Add node to the search index

    Add operation means either insert or update depending
    on if folder entity is already present in the index.
    In other words, if folder was already indexed (added before), its record
    in index will be updated otherwise its record will be inserted.
    """
    logger.debug('Task started')
    with Session() as db_session:
        node = api.get_node(db_session, uuid.UUID(node_id))
        index = get_index()
        logger.debug(f'Node={node}')

        if node.ctype == schema.NodeType.document:
            items = from_document(db_session, node)
        else:
            items = [from_folder(db_session, node)]

    logger.debug(f"Adding to index {items}")
    for item in items:
        index.add(item)


@shared_task(name=constants.INDEX_ADD_DOCS)
def index_add_docs(doc_ids: list[str]):
    """Add list of documents to index"""
    logger.debug(f"Add docs with {doc_ids} BEGIN")
    index = get_index()
    with Session() as db_session:
        docs = api.get_docs(
            db_session,
            [uuid.UUID(doc_id) for doc_id in doc_ids]
        )

        for doc in docs:
            items = from_document(db_session, doc)
            for item in items:
                logger.debug(f"Adding {item} to index")
                index.add(item)


@shared_task(name=constants.INDEX_REMOVE_NODE)
def remove_folder_or_page_from_index(item_ids: list[str]):
    """Removes folder or page from search index
    """
    logger.debug(f'Removing folder or page {item_ids} from index')
    logger.debug(
        f"Remove pages or folder from index len(item_ids)= {len(item_ids)}"
    )
    index = get_index()
    for item_id in item_ids:
        try:
            logger.debug(f'index remove {item_id}')
            index.remove(id=item_id)
        except Exception as exc:
            logger.error(exc)
            raise

    logger.debug('End of remove_folder_or_page_from_index')


@shared_task(name=constants.INDEX_ADD_PAGES)
def add_pages_to_index(page_ids: list[str]):
    with Session() as db_session:
        index_entities = [
            from_page(db_session, uuid.UUID(page_id)) for page_id in page_ids
        ]
        logger.debug(
            f"Add pages to index: {index_entities}"
        )
        index = get_index()
        for model in index_entities:
            index.add(model)


@shared_task(name=constants.INDEX_UPDATE)
def update_index(add_ver_id: str, remove_ver_id: str):
    """Updates index

    Removes pages of `remove_ver_id` document version and adds
    pages of `add_ver_id` from/to index in one "transaction".
    """
    logger.debug(
        f"Index Update: add={add_ver_id}, remove={remove_ver_id}"
    )
    add_ver = None
    remove_ver = None
    with Session() as db_session:
        try:
            add_ver = api.get_doc_ver(db_session, uuid.UUID(add_ver_id))
        except exc.NoResultFound:
            logger.debug(
                f"Index add doc version {add_ver_id} not found."
            )
        try:
            remove_ver = api.get_doc_ver(db_session, uuid.UUID(remove_ver_id))
        except exc.NoResultFound:
            logger.warning(f"Index remove doc version {remove_ver_id} not found")

        if add_ver:  # doc ver is there, but does it have pages?
            add_page_ids = [str(page.id) for page in add_ver.pages.all()]
            if len(add_page_ids) > 0:
                # doc ver is there and it has pages
                add_pages_to_index(add_page_ids)
            else:
                logger.debug("Empty page ids. Nothing to add to index")

        if remove_ver:  # doc ver is there, but does it have pages?
            remove_page_ids = [str(page.id) for page in remove_ver.pages.all()]
            if len(remove_page_ids) > 0:
                # doc ver is there and it has pages
                remove_folder_or_page_from_index(remove_page_ids)
            else:
                logger.debug("Empty page ids. Nothing to remove from index")


def from_page(db_session: Session, page_id: uuid.UUID) -> IndexEntity:
    """Given page_id returns index entity"""
    with Session() as db_session:
        page = api.get_page(db_session, page_id)
        last_doc_ver = api.get_doc_ver(db_session, page.document_version_id)
        doc = api.get_doc(db_session, last_doc_ver.document_id)

        if len(page.text) == 0 and last_doc_ver.number > 1:
            logger.warning(
                f"NO OCR TEXT FOUND! version={last_doc_ver.number} "
                f" title={doc.title}"
                f" page.number={page.number}"
                f" doc.ID={doc.id}"
            )

    index_entity = IndexEntity(
        id=str(page.id),
        title=doc.title,
        user_id=str(doc.user_id),
        document_id=str(doc.id),
        page_number=page.number,
        text=page.text,
        entity_type=PAGE,
        tags=[tag.name for tag in doc.tags],
    )

    return index_entity


def from_folder(db_session: Session, node: schema.Node) -> IndexEntity:
    index_entity = IndexEntity(
        id=str(node.id),
        title=node.title,
        user_id=str(node.user_id),
        entity_type=FOLDER,
        tags=node.tags
    )

    return index_entity


def from_document(db_session: Session, node: schema.Document) -> list[IndexEntity]:
    result = []

    with Session() as db_session:
        last_ver: schema.DocumentVersion = api.get_last_version(db_session, node.id)
        for page in api.get_pages(db_session, last_ver.id):
            if len(page.text) == 0 and last_ver.number > 1:
                logger.warning(
                    f"NO OCR TEXT FOUND! version={last_ver.number} "
                    f" title={node.title}"
                    f" page.number={page.number}"
                    f" doc.ID={node.id}"
                )

            index_entity = IndexEntity(
                id=str(page.id),
                title=node.title,
                user_id=str(node.user_id),
                document_id=str(node.id),
                page_number=page.number,
                text=page.text,
                entity_type=PAGE,
                tags=node.tags,
            )
            result.append(index_entity)

    return result
