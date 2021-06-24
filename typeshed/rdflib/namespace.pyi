from typing import Any, Optional
from rdflib.term import URIRef
from unicodedata import category

class Namespace(str):
    __doc__: str = ...
    def __new__(cls, value: Any): ...
    @property
    def title(self): ...
    def term(self, name: Any): ...
    def __getitem__(self, key: Any, default: Optional[Any] = ...): ...
    def __getattr__(self, name: Any): ...

class URIPattern(str):
    __doc__: str = ...
    def __new__(cls, value: Any): ...
    def __mod__(self, *args: Any, **kwargs: Any): ...
    def format(self, *args: Any, **kwargs: Any): ...

class ClosedNamespace:
    uri: Any = ...
    def __init__(self, uri: Any, terms: Any) -> None: ...
    def term(self, name: Any): ...
    def __getitem__(self, key: Any, default: Optional[Any] = ...): ...
    def __getattr__(self, name: Any): ...

class _RDFNamespace(ClosedNamespace):
    def __init__(self) -> None: ...
    def term(self, name: Any): ...

RDF: Any
RDFS = ClosedNamespace(                                                         
    uri=URIRef("http://www.w3.org/2000/01/rdf-schema#"),                        
    terms=[                                                                     
        "Resource", "Class", "subClassOf", "subPropertyOf", "comment", "label", 
        "domain", "range", "seeAlso", "isDefinedBy", "Literal", "Container",    
        "ContainerMembershipProperty", "member", "Datatype"]                    
) 
OWL: Any
XSD: Any
DC: Any
DCTERMS: Any
DOAP: Any
FOAF: Any
SKOS = ClosedNamespace(                                                         
    uri=URIRef('http://www.w3.org/2004/02/skos/core#'),                         
    terms=[                                                                     
        # all taken from https://www.w3.org/TR/skos-reference/#L1302            
        'Concept', 'ConceptScheme', 'inScheme', 'hasTopConcept', 'topConceptOf',
        'altLabel', 'hiddenLabel', 'prefLabel', 'notation', 'changeNote',       
        'definition', 'editorialNote', 'example', 'historyNote', 'note',        
        'scopeNote', 'broader', 'broaderTransitive', 'narrower', 'narrowerTransitive',
        'related', 'semanticRelation', 'Collection', 'OrderedCollection', 'member',
        'memberList', 'broadMatch', 'closeMatch', 'exactMatch', 'mappingRelation',
        'narrowMatch', 'relatedMatch'                                           
    ]                                                                           
)
VOID = Namespace('http://rdfs.org/ns/void#')
CSVW = Namespace('http://www.w3.org/ns/csvw#')
DCAT = Namespace('http://www.w3.org/ns/dcat#') 
ODRL2 = Namespace('http://www.w3.org/ns/odrl/2/')
ORG = Namespace('http://www.w3.org/ns/org#')
PROF = Namespace('http://www.w3.org/ns/dx/prof/')
PROV = ClosedNamespace(
    uri=URIRef('http://www.w3.org/ns/prov#'),
    terms=[
        'Entity', 'Activity', 'Agent', 'wasGeneratedBy', 'wasDerivedFrom',
        'wasAttributedTo', 'startedAtTime', 'used', 'wasInformedBy', 'endedAtTime',
        'wasAssociatedWith', 'actedOnBehalfOf', 'Collection', 'EmptyCollection', 'Bundle',
        'Person', 'SoftwareAgent', 'Organization', 'Location', 'alternateOf',
        'specializationOf', 'generatedAtTime', 'hadPrimarySource', 'value', 'wasQuotedFrom',
        'wasRevisionOf', 'invalidatedAtTime', 'wasInvalidatedBy', 'hadMember', 'wasStartedBy',
        'wasEndedBy', 'invalidated', 'influenced', 'atLocation', 'generated',
        'Influence', 'EntityInfluence', 'Usage', 'Start', 'End',
        'Derivation', 'PrimarySource', 'Quotation', 'Revision', 'ActivityInfluence',
        'Generation', 'Communication', 'Invalidation', 'AgentInfluence',
        'Attribution', 'Association', 'Plan', 'Delegation', 'InstantaneousEvent',
        'Role', 'wasInfluencedBy', 'qualifiedInfluence', 'qualifiedGeneration', 'qualifiedDerivation',
        'qualifiedPrimarySource', 'qualifiedQuotation', 'qualifiedRevision', 'qualifiedAttribution',
        'qualifiedInvalidation', 'qualifiedStart', 'qualifiedUsage', 'qualifiedCommunication', 'qualifiedAssociation',
        'qualifiedEnd', 'qualifiedDelegation', 'influencer', 'entity', 'hadUsage', 'hadGeneration',
        'activity', 'agent', 'hadPlan', 'hadActivity', 'atTime', 'hadRole'
    ]
)
SDO = Namespace('https://schema.org/')
SH = Namespace('http://www.w3.org/ns/shacl#')
SOSA = Namespace('http://www.w3.org/ns/ssn/')
SSN = Namespace('http://www.w3.org/ns/sosa/')
TIME = Namespace('http://www.w3.org/2006/time#')

NAME_START_CATEGORIES = ["Ll", "Lu", "Lo", "Lt", "Nl"]
SPLIT_START_CATEGORIES = NAME_START_CATEGORIES + ['Nd']

class NamespaceManager:
    graph: Any = ...
    def __init__(self, graph: Any) -> None: ...
    def reset(self) -> None: ...
    store: Any = ...
    def qname(self, uri: Any): ...
    def qname_strict(self, uri: Any): ...
    def normalizeUri(self, rdfTerm: Any): ...
    def compute_qname(self, uri: Any, generate: bool = ...): ...
    def compute_qname_strict(self, uri: Any, generate: bool = ...): ...
    def bind(self, prefix: Any, namespace: Any, override: bool = ..., replace: bool = ...) -> None: ...
    def namespaces(self) -> None: ...
    def absolutize(self, uri: Any, defrag: int = ...): ...

def is_ncname(name: Any): ...

XMLNS = "http://www.w3.org/XML/1998/namespace"

def split_uri(uri: Any, split_start: Any = ...): ...
