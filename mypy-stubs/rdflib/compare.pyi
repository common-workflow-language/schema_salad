from typing import Dict, Union

from rdflib.graph import Graph, ReadOnlyGraphAggregate

Stats = Dict[str, Union[int, str]]

def to_canonical_graph(
    g1: Graph, stats: Stats | None = ...
) -> ReadOnlyGraphAggregate: ...
