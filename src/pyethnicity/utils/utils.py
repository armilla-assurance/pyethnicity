import functools
import math
from collections.abc import Iterable, Sequence
from typing import SupportsFloat, SupportsIndex, Union

import polars as pl
import requests
from polars._utils.parse.expr import parse_into_list_of_expressions
from polars._utils.wrap import wrap_expr
from polars.type_aliases import IntoExpr

from .paths import DAT_PATH
from .types import ArrayLike

RACES = ("asian", "black", "hispanic", "white")
RACES_6 = ("asian", "black", "hispanic", "multiple", "native", "white")


def _assert_equal_lengths(*inputs: Union[object, ArrayLike]):
    lengths = []

    for input in inputs:
        if not hasattr(input, "__len__") or isinstance(input, str):
            input = [input]

        lengths.append(len(input))

    mean_length = sum(lengths) / len(lengths)

    if any(length != mean_length for length in lengths):
        raise ValueError("All inputs need to be of equal length.")


@functools.lru_cache()
def _remove_single_chars(name: str) -> str:
    return " ".join(part for part in name.split(" ") if len(part) > 1)


def _std_norm(values: Sequence[float]) -> list[float]:
    total = sum(values)

    return [v / total for v in values]


def _is_null(x: Union[SupportsFloat, SupportsIndex]):
    return math.isnan(x) or x is None


def _set_name(x, name: str):
    try:
        name = x.name
    except AttributeError:
        pass

    return name


def _download(path: str):
    r = requests.get(
        f"https://raw.githubusercontent.com/CangyuanLi/pyethnicity/master/src/pyethnicity/data/{path}"
    )
    if r.status_code != 200:
        raise requests.exceptions.HTTPError(f"{r.status_code}: DOWNLOAD FAILED")

    parent_folder = path.split("/")[0]
    (DAT_PATH / parent_folder).mkdir(exist_ok=True)

    with open(DAT_PATH / path, "wb") as f:
        f.write(r.content)


def _sum_horizontal(*exprs: Union[IntoExpr, Iterable[IntoExpr]]) -> pl.Expr:
    exprs = [wrap_expr(e) for e in parse_into_list_of_expressions(*exprs)]

    return (
        pl.when(pl.all_horizontal(e.is_null() for e in exprs))
        .then(None)
        .otherwise(pl.sum_horizontal(exprs))
    )
