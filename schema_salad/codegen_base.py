"""Base class for the generation of loaders from schema-salad definitions."""
import collections
from typing import Any, Dict, List, MutableSequence, Optional, Union, Set

from . import schema


class TypeDef(object):  # pylint: disable=too-few-public-methods
    """Schema Salad type description."""

    __slots__ = [
        "name",
        "init",
        "is_uri",
        "scoped_id",
        "ref_scope",
        "loader_type",
        "instance_type",
    ]

    # switch to class-style typing.NamedTuple once support for Python < 3.6
    # is dropped
    def __init__(
        self,  # pylint: disable=too-many-arguments
        name: str,
        init: str,
        is_uri: bool = False,
        scoped_id: bool = False,
        ref_scope: Optional[int] = 0,
        loader_type: Optional[str] = None,
        instance_type: Optional[str] = None,
    ) -> None:
        self.name = name
        self.init = init
        self.is_uri = is_uri
        self.scoped_id = scoped_id
        self.ref_scope = ref_scope
        # Follow attributes used by Java but not Python.
        self.loader_type = loader_type
        self.instance_type = instance_type


class CodeGenBase(object):
    """Abstract base class for schema salad code generators."""

    def __init__(self) -> None:
        self.collected_types = (
            collections.OrderedDict()
        )  # type: collections.OrderedDict[str, TypeDef]
        self.vocab = {}  # type: Dict[str, str]

    def declare_type(self, declared_type: TypeDef) -> TypeDef:
        """Add this type to our collection, if needed."""
        if declared_type not in self.collected_types.values():
            self.collected_types[declared_type.name] = declared_type
        return declared_type

    def add_vocab(self, name: str, uri: str) -> None:
        """Add the given name as an abbreviation for the given URI."""
        self.vocab[name] = uri

    def prologue(self) -> None:
        """Trigger to generate the prolouge code."""
        raise NotImplementedError()

    @staticmethod
    def safe_name(name: str) -> str:
        """Generate a safe version of the given name."""
        return schema.avro_name(name)

    def begin_class(
        self,  # pylint: disable=too-many-arguments
        classname: str,
        extends: MutableSequence[str],
        doc: str,
        abstract: bool,
        field_names: MutableSequence[str],
        idfield: str,
        optional_fields: Set[str],
    ) -> None:
        """Produce the header for the given class."""
        raise NotImplementedError()

    def end_class(self, classname: str, field_names: List[str]) -> None:
        """Signal that we are done with this class."""
        raise NotImplementedError()

    def type_loader(
        self, type_declaration: Union[List[Any], Dict[str, Any]]
    ) -> TypeDef:
        """Parse the given type declaration and declare its components."""
        raise NotImplementedError()

    def declare_field(
        self, name: str, fieldtype: TypeDef, doc: Optional[str], optional: bool
    ) -> None:
        """Output the code to load the given field."""
        raise NotImplementedError()

    def declare_id_field(
        self, name: str, fieldtype: TypeDef, doc: str, optional: bool
    ) -> None:
        """Output the code to handle the given ID field."""
        raise NotImplementedError()

    def uri_loader(
        self,
        inner: TypeDef,
        scoped_id: bool,
        vocab_term: bool,
        ref_scope: Optional[int],
    ) -> TypeDef:
        """Construct the TypeDef for the given URI loader."""
        raise NotImplementedError()

    def idmap_loader(
        self, field: str, inner: TypeDef, map_subject: str, map_predicate: Optional[str]
    ) -> TypeDef:
        """Construct the TypeDef for the given mapped ID loader."""
        raise NotImplementedError()

    def typedsl_loader(self, inner: TypeDef, ref_scope: Optional[int]) -> TypeDef:
        """Construct the TypeDef for the given DSL loader."""
        raise NotImplementedError()

    def epilogue(self, root_loader: TypeDef) -> None:
        """Trigger to generate the epilouge code."""
        raise NotImplementedError()
