import asyncio
from typing import Generic, List, TypeVar

from fastapi import Query
from pydantic.generics import GenericModel
from tortoise import QuerySet

default_offset = 0
max_offset = None

default_limit = 10
max_limit = 1000

DataT = TypeVar("DataT")


class PaginationResult(GenericModel, Generic[DataT]):
    count: int
    results: List[DataT]


class Pagination:
    def __init__(
        self,
        limit: int = Query(default=default_limit, ge=1, le=max_limit),
        offset: int = Query(default=default_offset, ge=0, le=max_offset),
    ):
        self.limit = limit
        self.offset = offset

    async def apply(self, qs: QuerySet):
        count, results = await asyncio.gather(qs.count(), qs.limit(self.limit).offset(self.offset))
        return PaginationResult(count=count, results=results)
