from typing import TypeAlias

from rdflib.graph import ConjunctiveGraph, Graph

Stats: TypeAlias = dict[str, int | str]

class IsomorphicGraph(ConjunctiveGraph):
    pass

def to_isomorphic(graph: Graph = ...) -> IsomorphicGraph: ...
