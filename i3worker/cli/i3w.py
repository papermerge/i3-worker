import uuid
from typing import Optional

import typer
from rich import print_json, print
from salinic import IndexRW, create_engine
from typing_extensions import Annotated

from i3worker import db, config, models
from i3worker.schema import FOLDER, PAGE, IndexEntity


app = typer.Typer(help="Index documents")
settings = config.get_settings()
engine = create_engine(settings.papermerge__search__url)

index = IndexRW(engine, schema=IndexEntity)
Session = db.get_db()

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

    with Session() as db_session:
        nodes = db.get_nodes(db_session, node_ids)
        items = []  # to be added to the index
        for node in nodes:
            if isinstance(node, models.Document):
                last_ver = db.get_last_version(
                    db_session,
                    doc_id=node.id
                )
                pages = db.get_pages(db_session, last_ver.id)
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

        for item in items:
            index.add(item)
