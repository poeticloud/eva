# pylint: disable=R0902,E1101,W0201,too-few-public-methods,W0613

import datetime
import uuid

from sqlalchemy_utils import UUIDType
from haomo.conf import settings
from sqlalchemy import (
    event,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Sequence,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship

from . import Base


_USER_ROLES = Table(
    "eva_identity__role",
    Base.metadata,
    Column("identity_id", Integer, ForeignKey("eva_identity.id", ondelete="CASCADE")),
    Column("role_id", Integer, ForeignKey("eva_role.id", ondelete="CASCADE")),
)


_ROLE_PERMISSIONS = Table(
    "eva_role__permission",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("eva_role.id", ondelete="CASCADE")),
    Column(
        "permission_id", Integer, ForeignKey("eva_permission.id", ondelete="CASCADE")
    ),
)


class SimilarBase:
    def update(self, **kwargs):
        length = len(kwargs)
        if "summary" in kwargs:
            self.summary = kwargs.pop("summary")
        if "description" in kwargs:
            self.description = kwargs.pop("description")
        if len(kwargs) != length:
            self.updated = datetime.datetime.utcnow()

    @property
    def isimple(self):
        return {"id": str(self.uuid), "name": self.name, "summary": self.summary}

    @property
    def ifull(self):
        return {
            "id": str(self.uuid),
            "name": self.name,
            "summary": self.summary,
            "description": self.description,
        }


class Role(Base, SimilarBase):
    """
    角色与一组权限绑定，用户可以属于多个角色。
    """

    __tablename__ = "eva_role"

    id = Column(Integer, Sequence("eva_role_id_seq"), primary_key=True)
    code = Column(String(128), unique=True)
    name = Column(String(128), unique=True)
    summary = Column(String(1024))
    description = Column(Text)
    updated = Column(DateTime(), default=datetime.datetime.utcnow)
    created = Column(DateTime(), default=datetime.datetime.utcnow)

    permissions = relationship(
        "Permission", secondary=_ROLE_PERMISSIONS, backref="roles"
    )

    users = relationship("Identity", secondary=_USER_ROLES, backref="roles")


class Permission(Base, SimilarBase):
    """
    提供“标识“，判断用户是否拥有某个“权限”
    """

    __tablename__ = "eva_permission"

    id = Column(Integer, Sequence("eva_permission_id_seq"), primary_key=True)
    code = Column(String(128), unique=True)
    name = Column(String(128), unique=True)
    summary = Column(String(1024))
    description = Column(Text)
    updated = Column(DateTime(), default=datetime.datetime.utcnow)
    created = Column(DateTime(), default=datetime.datetime.utcnow)


def has_permission(identity, permission):
    for role in identity.roles:
        # 如果拥有超级管理员角色名称，拥有权限
        if role.name == settings.ADMIN_ROLE_NAME:
            return True
        for perm in role.permissions:
            if perm.id == permission.id:
                return True
    return False
