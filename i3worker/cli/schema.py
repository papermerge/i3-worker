import os

import typer
from rich import print_json
from salinic import SchemaManager, create_engine

from i3worker import config, models
from i3worker.schema import IndexEntity

app = typer.Typer(help="Index Schema Management")

settings = config.get_settings()
engine = create_engine(settings.papermerge__search__url)
schema_manager = SchemaManager(engine, model=IndexEntity)


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
