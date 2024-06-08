import uuid
from uuid import UUID
from datetime import datetime
from typing import Literal
from sqlalchemy import ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from i3worker.db.base import Base

CType = Literal["document", "folder"]


class Node(Base):
    __tablename__ = "core_basetreenode"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        insert_default=uuid.uuid4()
    )
    title: Mapped[str] = mapped_column(String(200))
    ctype: Mapped[CType]
    # actually `lang` attribute should be part of the document
    lang: Mapped[str] = mapped_column(String(8))
    tags: list[str] = []
    user_id: Mapped[UUID] = mapped_column(ForeignKey("core_user.id"))
    created_at: Mapped[datetime] = mapped_column(
        insert_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        insert_default=func.now(),
        onupdate=func.now()
    )

    __mapper_args__ = {
        "polymorphic_identity": "node",
        "polymorphic_on": "ctype",
    }


class Folder(Node):
    __tablename__ = "core_folder"

    id: Mapped[UUID] = mapped_column(
        'basetreenode_ptr_id',
        ForeignKey("core_basetreenode.id"),
        primary_key=True,
        insert_default=uuid.uuid4()
    )

    __mapper_args__ = {
        "polymorphic_identity": "folder",
    }


class Document(Node):
    __tablename__ = "core_document"

    id: Mapped[UUID] = mapped_column(
        'basetreenode_ptr_id',
        ForeignKey("core_basetreenode.id"),
        primary_key=True,
        insert_default=uuid.uuid4()
    )

    __mapper_args__ = {
        "polymorphic_identity": "document",
    }


class DocumentVersion(Base):
    __tablename__ = "core_documentversion"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    number: Mapped[int]
    file_name: Mapped[str]
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_document.basetreenode_ptr_id")
    )


class Page(Base):
    __tablename__ = "core_page"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    number: Mapped[int]
    document_version_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_documentversion.id")
    )


class Tag(Base):
    __tablename__ = "core_tag"
    id: Mapped[UUID] = mapped_column(
        primary_key=True
    )
    name: Mapped[str]
    bg_color: Mapped[str] = "#ff0000"
    fg_color: Mapped[str] = "#ffff00"
    description: Mapped[str] = ""
    pinned: Mapped[bool] = False


class ColoredTag(Base):
    __tablename__ = "core_coloredtag"
    id: Mapped[int] = mapped_column(primary_key=True)
    object_id: Mapped[UUID]
    tag_id: Mapped[UUID] = mapped_column(
        ForeignKey("core_tag.id")
    )
    tag: Mapped["Tag"] = relationship(
        primaryjoin="Tag.id == ColoredTag.tag_id"
    )


class User(Base):
    __tablename__ = "core_user"

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        insert_default=uuid.uuid4()
    )
    username: Mapped[str]
    email: Mapped[str]
    password: Mapped[str]
    is_superuser: Mapped[bool] = mapped_column(default=False)
    is_staff: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=False)
    first_name: Mapped[str] = mapped_column(default=' ')
    last_name: Mapped[str] = mapped_column(default=' ')
    created_at: Mapped[datetime] = mapped_column(
        insert_default=func.now()
    )
    date_joined: Mapped[datetime] = mapped_column(
        insert_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        insert_default=func.now(),
        onupdate=func.now()
    )


