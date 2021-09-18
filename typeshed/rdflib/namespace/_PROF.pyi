from rdflib.namespace import DefinedNamespace as DefinedNamespace, Namespace as Namespace
from rdflib.term import URIRef as URIRef

class PROF(DefinedNamespace):
    Profile: URIRef
    ResourceDescriptor: URIRef
    ResourceRole: URIRef
    hasToken: URIRef
    hasArtifact: URIRef
    hasResource: URIRef
    hasRole: URIRef
    isInheritedFrom: URIRef
    isProfileOf: URIRef
    isTransitiveProfileOf: URIRef
