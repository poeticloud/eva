# pylint: disable=invalid-name

from eva.conf import settings
from sqlalchemy import asc, desc, func, inspect


def get_list(hdr, q, default_sort_by="id", allow_sort_by=None, model=None):
    # TODO: 单独测试该函数

    ins = inspect(model)
    pk = ins.primary_key[0]
    total = q.with_entities(func.count(pk)).scalar()

    sb = hdr.get_argument("sort_by", default_sort_by).lower()
    if sb not in allow_sort_by and sb != "id":
        return f"unknown-sort-by:{sb}", None, None
    # TODO: check sort_by exist!
    is_asc = hdr.get_argument("asc", "false") not in ["false", "0"]
    q = q.order_by(asc(sb) if is_asc else desc(sb))

    # pagination
    page_size = int(hdr.get_argument("page_size", int(settings.PAGE_SIZE)))
    current_page = int(hdr.get_argument("page", 1))
    start = (current_page - 1) * page_size
    stop = current_page * page_size

    if current_page < 1 or start > total:
        return f"no-such-page:{current_page}", None, None

    return (
        "",
        q.slice(start, stop),
        {
            "page_size": page_size,
            "page": current_page,
            "total": total,
            "sort_by": sb,
            "asc": is_asc,
        },
    )
