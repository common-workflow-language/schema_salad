from typing import Dict, Union

from rdflib.graph import ConjunctiveGraph, Graph

Stats = Dict[str, Union[int, str]]

class IsomorphicGraph(ConjunctiveGraph):
    pass

def to_isomorphic(graph: Graph = ...) -> IsomorphicGraph: ...
