import logging
import uuid
from typing import Optional
import typer
from rich import print_json, print
from salinic import SchemaManager, create_engine, IndexRW, Search
from typing_extensions import Annotated

from i3worker.db.engine import Session
from i3worker import schema, config
from i3worker.db import api
from i3worker.index import FOLDER, PAGE, IndexEntity


app = typer.Typer(help="i3 command line interface")
settings = config.get_settings()
engine = create_engine(settings.papermerge__search__url)
schema_manager = SchemaManager(engine, model=IndexEntity)

logger = logging.getLogger(__name__)
index = IndexRW(engine, schema=IndexEntity)

NodeIDsType = Annotated[
    Optional[list[uuid.UUID]],
    typer.Argument()
]


@app.command(name="index")
def index_cmd(
    node_ids: NodeIDsType = None,
    dry_run: bool = False,
    rebuild: bool = False
):
    """Indexes given nodes. If no nodes are given will index all
    nodes in the database

    `--rebuild` - will drop all documents from the index first, and then
     start indexing the rest of the documents
     `--dry-run`
    """
    logger.debug("index cmd")
    with Session() as db_session:
        logger.debug("getting nodes")
        nodes = api.get_nodes(db_session, node_ids)
        items = []  # to be added to the index
        for node in nodes:
            if isinstance(node, schema.Document):
                last_ver = api.get_last_version(
                    db_session,
                    doc_id=node.id
                )
                pages = api.get_pages(db_session, last_ver.id)
                for page in pages:
                    item = IndexEntity(
                        id=str(page.id),
                        title=node.title,
                        user_id=str(node.user_id),
                        document_id=str(node.id),
                        document_version_id=str(last_ver.id),
                        page_number=page.number,
                        text=page.text,
                        entity_type=PAGE,
                        tags=[tag.name for tag in node.tags],
                    )
                    items.append(item)
            else:
                item = IndexEntity(
                    id=str(node.id),
                    title=node.title,
                    user_id=str(node.user_id),
                    entity_type=FOLDER,
                    tags=[tag.name for tag in node.tags],
                )
                items.append(item)

    if dry_run:
        for item in items:
            print_json(data=item.model_dump())
    else:
        if rebuild:
            # drop all documents from the index
            index.remove(query="*:*")
        logger.debug("adding items")
        for item in items:
            logger.debug(f"adding item {item}")
            index.add(item)


@app.command(name="config")
def print_config_cmd():
    """Print config settings"""
    print_json(settings.json())


@app.command(name="apply")
def apply_cmd(dry_run: bool = False):
    """Apply schema fields"""

    if dry_run:
        print_json(data=schema_manager.apply_dict_dump())
    else:
        schema_manager.apply()


@app.command(name="delete")
def delete_cmd(dry_run: bool = False):
    """Delete schema fields"""
    if dry_run:
        print_json(data=schema_manager.delete_dict_dump())
    else:
        schema_manager.delete()


@app.command(name="create")
def create_cmd(dry_run: bool = False):
    """Create schema fields"""
    if dry_run:
        print_json(data=schema_manager.create_dict_dump())
    else:
        schema_manager.create()


@app.command(name="search")
def search_command(q: str, user_id: uuid.UUID, page_number: int = 1, page_size: int = 10):
    """Search documents"""
    sq = Search(IndexEntity).query(q, page_number=page_number, page_size=page_size)
    results = index.search(sq, user_id=str(user_id))
    print(results)