import logging
from uuid import UUID
from celery import shared_task

from i3worker import db, constants
from i3worker.config import get_settings
from i3worker.schema import IndexEntity
from salinic import IndexRW, create_engine


logger = logging.getLogger(__name__)
settings = get_settings()

RETRY_KWARGS = {
    'max_retries': 7,  # number of times to retry the task
    'countdown': 5  # Time in seconds to delay the retry for.
}


def get_index():
    engine = create_engine(settings.SEARCH_URL)
    return IndexRW(engine, schema=IndexEntity)


@shared_task(
    name=constants.INDEX_ADD_NODE,
    autoretry_for=(Exception,),
    retry_kwargs=RETRY_KWARGS
)
def index_add_node(node_id: str):
    """Add node to the search index

    Add operation means either insert or update depending
    on if folder entity is already present in the index.
    In other words, if folder was already indexed (added before), its record
    in index will be updated otherwise its record will be inserted.
    """
    node = BaseTreeNode.objects.get(pk=node_id)

    logger.debug(f'ADD node title={node.title} ID={node.id} to INDEX')
    index = get_index()

    if node.is_document:
        models = from_document(node)
    else:
        models = [from_folder(node)]

    logger.debug(f"Adding to index {models}")
    for model in models:
        index.add(model)



@shared_task(
    name=constants.INDEX_ADD_DOCS,
    autoretry_for=(Exception,),
    retry_kwargs=RETRY_KWARGS
)
def index_add_docs(doc_ids: list[str]):
    """Add list of documents to index"""
    logger.debug(f"Add docs with {doc_ids} BEGIN")
    docs = Document.objects.filter(pk__in=doc_ids)
    index = get_index()

    for doc in docs:
        models = from_document(doc)
        for model in models:
            logger.debug(f"Adding {model} to index")
            index.add(model)

    logger.debug(f"Add docs with {doc_ids} END")


@shared_task(
    name=constants.INDEX_REMOVE_NODE,
    autoretry_for=(Exception,),
    retry_kwargs=RETRY_KWARGS
)
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


@shared_task(
    name=constants.INDEX_ADD_PAGES,
    autoretry_for=(Exception,),
    retry_kwargs=RETRY_KWARGS
)
def add_pages_to_index(page_ids: list[str]):
    index_entities = [from_page(page_id) for page_id in page_ids]
    logger.debug(
        f"Add pages to index: {index_entities}"
    )
    index = get_index()
    for model in index_entities:
        index.add(model)


@shared_task(
    name=constants.INDEX_UPDATE,
    autoretry_for=(Exception,),
    retry_kwargs=RETRY_KWARGS
)
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
    try:
        add_ver = DocumentVersion.objects.get(pk=add_ver_id)
    except DocumentVersion.DoesNotExist:
        logger.debug(
            f"Index add doc version {add_ver_id} not found."
        )
    try:
        remove_ver = DocumentVersion.objects.get(pk=remove_ver_id)
    except DocumentVersion.DoesNotExist:
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


def from_page(page_id: str) -> IndexEntity:
    """Given page_id returns index entity"""
    page = Page.objects.get(pk=page_id)
    last_doc_ver = page.document_version
    doc = last_doc_ver.document

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
        document_version_id=str(last_doc_ver.id),
        page_number=page.number,
        page_count=page.page_count,
        text=page.text,
        parent_id=str(doc.parent_id),
        entity_type=PAGE,
        tags=[
            ColoredTag(
                name=tag.name,
                fg_color=tag.fg_color,
                bg_color=tag.bg_color
            ) for tag in doc.tags.all()
        ],
        breadcrumb=[
            (str(item[0]), item[1]) for item in doc.breadcrumb
        ]
    )

    return index_entity


def from_folder(node: BaseTreeNode) -> IndexEntity:
    index_entity = IndexEntity(
        id=str(node.id),
        title=node.title,
        user_id=str(node.user_id),
        entity_type=FOLDER,
        parent_id=str(node.parent_id),
        tags=[
            ColoredTag(
                name=tag.name,
                fg_color=tag.fg_color,
                bg_color=tag.bg_color
            ) for tag in node.tags.all()
        ],
        breadcrumb=[
            (str(item[0]), item[1]) for item in node.breadcrumb
        ]
    )

    return index_entity


def from_document(node: BaseTreeNode | Document) -> List[Model]:
    result = []
    if isinstance(node, BaseTreeNode):
        doc = node.document
    else:
        doc = node  # i.e. node is instance of Document

    last_ver: DocumentVersion = doc.versions.last()

    for page in last_ver.pages.all():
        if len(page.text) == 0 and last_ver.number > 1:
            logger.warning(
                f"NO OCR TEXT FOUND! version={last_ver.number} "
                f" title={doc.title}"
                f" page.number={page.number}"
                f" doc.ID={doc.id}"
                f" node.ID={node.id}"
            )

        index_entity = IndexEntity(
            id=str(page.id),
            title=node.title,
            user_id=str(node.user_id),
            document_id=str(node.document.id),
            document_version_id=str(last_ver.id),
            page_number=page.number,
            page_count=page.page_count,
            text=page.text,
            parent_id=str(node.parent_id),
            entity_type=PAGE,
            tags=[
                ColoredTag(
                    name=tag.name,
                    fg_color=tag.fg_color,
                    bg_color=tag.bg_color
                ) for tag in node.tags.all()
            ],
            breadcrumb=[
                (str(item[0]), item[1]) for item in node.breadcrumb
            ]
        )
        result.append(index_entity)

    return result