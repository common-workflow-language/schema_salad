"""Base class for the generation of loaders from schema-salad definitions."""
import collections
from typing import (Any, Dict, List, MutableSequence, Optional, Union)

from typing_extensions import Text  # pylint: disable=unused-import
# move to a regular typing import when Python 3.3-3.6 is no longer supported

from . import schema

class TypeDef(object):  # pylint: disable=too-few-public-methods
    """Schema Salad type description."""
    # switch to class-style typing.NamedTuple once support for Python < 3.6
    # is dropped
    def __init__(self,  # pylint: disable=too-many-arguments
                 name,             # type: Text
                 init,             # type: Text
                 is_uri=False,     # type: bool
                 scoped_id=False,  # type: bool
                 ref_scope=0       # type: Optional[int]
                ):  # type: (...) -> None
        self.name = name
        self.init = init
        self.is_uri = is_uri
        self.scoped_id = scoped_id
        self.ref_scope = ref_scope

class CodeGenBase(object):
    """Abstract base class for schema salad code generators."""
    def __init__(self):  # type: () -> None
        self.collected_types = collections.OrderedDict()  # type: collections.OrderedDict[Text, TypeDef]
        self.vocab = {}  # type: Dict[Text, Text]

    def declare_type(self, declared_type):  # type: (TypeDef) -> TypeDef
        """Add this type to our collection, if needed."""
        if declared_type not in self.collected_types:
            self.collected_types[declared_type.name] = declared_type
        return declared_type

    def add_vocab(self, name, uri):  # type: (Text, Text) -> None
        """Add the given name as an abbreviation for the given URI."""
        self.vocab[name] = uri

    def prologue(self):  # type: () -> None
        """Trigger to generate the prolouge code."""
        raise NotImplementedError()

    @staticmethod
    def safe_name(name):  # type: (Text) -> Text
        """Generate a safe version of the given name."""
        return schema.avro_name(name)

    def begin_class(self,  # pylint: disable=too-many-arguments
                    classname,    # type: Text
                    extends,      # type: MutableSequence[Text]
                    doc,          # type: Text
                    abstract,     # type: bool
                    field_names,  # type: MutableSequence[Text]
                    idfield       # type: Text
                   ):  # type: (...) -> None
        """Produce the header for the given class."""
        raise NotImplementedError()

    def end_class(self, classname, field_names):
        # type: (Text, List[Text]) -> None
        """Signal that we are done with this class."""
        raise NotImplementedError()

    def type_loader(self, type_declaration):
        # type: (Union[List[Any], Dict[Text, Any]]) -> TypeDef
        """Parse the given type declaration and declare its components."""
        raise NotImplementedError()

    def declare_field(self, name, fieldtype, doc, optional):
        # type: (Text, TypeDef, Text, bool) -> None
        """Output the code to load the given field."""
        raise NotImplementedError()

    def declare_id_field(self, name, fieldtype, doc, optional):
        # type: (Text, TypeDef, Text, bool) -> None
        """Output the code to handle the given ID field."""
        raise NotImplementedError()

    def uri_loader(self, inner, scoped_id, vocab_term, ref_scope):
        # type: (TypeDef, bool, bool, Union[int, None]) -> TypeDef
        """Construct the TypeDef for the given URI loader."""
        raise NotImplementedError()

    def idmap_loader(self, field, inner, map_subject, map_predicate):
        # type: (Text, TypeDef, Text, Union[Text, None]) -> TypeDef
        """Construct the TypeDef for the given mapped ID loader."""
        raise NotImplementedError()

    def typedsl_loader(self, inner, ref_scope):
        # type: (TypeDef, Union[int, None]) -> TypeDef
        """Construct the TypeDef for the given DSL loader."""
        raise NotImplementedError()

    def epilogue(self, root_loader):  # type: (TypeDef) -> None
        """Trigger to generate the epilouge code."""
        raise NotImplementedError()
