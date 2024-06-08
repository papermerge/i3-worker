from uuid import UUID
from typing import Literal
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


CType = Literal["document", "folder"]


class Node(Base):
    __tablename__ = "core_basetreenode"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    ctype: Mapped[CType]
    tags: list[str] = []
    user_id: Mapped[UUID] = mapped_column(ForeignKey("core_user.id"))

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
    )

    __mapper_args__ = {
        "polymorphic_identity": "folder",
    }


class Document(Node):
    __tablename__ = "core_document"

    id: Mapped[UUID] = mapped_column(
        'basetreenode_ptr_id',
        ForeignKey("core_basetreenode.id"), primary_key=True
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
    id: Mapped[UUID] = mapped_column(primary_key=True)
    name: Mapped[str]
    bg_color: Mapped[str]
    fg_color: Mapped[str]
    description: Mapped[str]
    pinned: Mapped[bool]


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
