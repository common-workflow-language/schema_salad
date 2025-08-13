"""Rust code generator for schema salad definitions."""

__all__ = ["RustCodeGen"]

import functools
import itertools
import json
import re
import shutil
import sys
from abc import ABC, abstractmethod
from collections.abc import Iterator, MutableMapping, MutableSequence, Sequence
from importlib.resources import files as resource_files
from io import StringIO
from pathlib import Path
from time import sleep
from typing import IO, Any, ClassVar, Optional, Pattern, Union, cast

from . import _logger
from .avro.schema import ArraySchema, EnumSchema
from .avro.schema import Field as SaladField
from .avro.schema import JsonDataType, NamedSchema, NamedUnionSchema
from .avro.schema import Names as SaladNames
from .avro.schema import (
    PrimitiveSchema,
    RecordSchema,
    Schema,
    UnionSchema,
    make_avsc_object,
)
from .codegen_base import CodeGenBase
from .schema import make_valid_avro
from .validate import avro_shortname

#
# Util Functions
#

__RUST_RESERVED_WORDS = [
    "type", "self", "let", "fn", "struct", "impl", "trait", "enum", "pub",
    "mut", "true", "false", "return", "match", "if", "else", "for", "in",
    "where", "ref", "use", "mod", "const", "static", "as", "move", "async",
    "await", "dyn", "loop", "break", "continue", "super", "crate", "unsafe",
    "extern", "box", "virtual", "override", "macro", "while", "yield",
    "typeof", "sizeof", "final", "pure", "abstract", "become", "do",
    "alignof", "offsetof", "priv", "proc", "unsized",
]  # fmt: skip

# __FIELD_NAME_REX_DICT = [
#     (re.compile(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])"), "_"),
#     (re.compile(r"([\W_]$)|\W"), lambda m: "" if m.group(1) else "_"),
#     (re.compile(r"^([0-9])"), lambda m: f"_{m.group(1)}"),
# ]
__TYPE_NAME_REX_DICT = [
    (re.compile(r"(?:^|[^a-zA-Z0-9.])(\w)"), lambda m: m.group(1).upper()),
    (re.compile(r"\.([a-zA-Z])"), lambda m: m.group(1).upper()),
    (re.compile(r"(?:^|\.)([0-9])"), lambda m: f"_{m.group(1)}"),
]
__MD_NON_HYPERLINK_REX = re.compile(
    r"(?<![\[(<\"])(\b[a-zA-Z]+://[a-zA-Z0-9\-.]+\.[a-zA-Z]{2,}(?::[0-9]+)?(?:/\S*)?)(?!\S*[])>\"])"
)


# TODO Check strings for Unicode standard for `XID_Start` and `XID_Continue`
# @functools.cache
def rust_sanitize_field_ident(value: str) -> str:
    """Check whether the field name is a Rust reserved world, or escape it."""
    if value in __RUST_RESERVED_WORDS:
        return f"r#{value}"
    return value


# TODO Check strings for Unicode standard for `XID_Start` and `XID_Continue`
@functools.cache
def rust_sanitize_type_ident(value: str) -> str:
    """Convert an input string into a valid Rust type name (PascalCase).

    Results are cached for performance optimization.
    """
    return functools.reduce(lambda s, r: re.sub(r[0], r[1], s), __TYPE_NAME_REX_DICT, value)


def rust_sanitize_doc_iter(value: Union[Sequence[str], str]) -> Iterator[str]:
    """Sanitize Markdown doc-strings by splitting lines and wrapping non-hyperlinked URLs in angle brackets."""
    return map(
        lambda v: re.sub(__MD_NON_HYPERLINK_REX, lambda m: f"<{str(m.group())}>", v),
        itertools.chain.from_iterable(map(  # flat_map
            lambda v: v.rstrip().split("\n"),
            [value] if isinstance(value, str) else value,
        )),
    )  # fmt: skip


@functools.cache
def to_rust_literal(value: Any) -> str:
    """Convert Python values to their equivalent Rust literal representation.

    Results are cached for performance optimization.
    """
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        if value.startswith('"') and value.endswith('"'):
            value = value[1:-1]
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (list, tuple)):
        list_entries = ", ".join(map(to_rust_literal, value))
        return f"[{list_entries}]"
    if value is None:
        return "Option::None"
    raise TypeError(f"Unsupported type for Rust literal conversion: {type(value).__name__}")


def make_avro(items: MutableSequence[JsonDataType]) -> MutableSequence[NamedSchema]:
    """Process a list of dictionaries to generate a list of Avro schemas."""
    # Same as `from .utils import convert_to_dict`, which, however, is not public
    def convert_to_dict(j4: Any) -> Any:
        """Convert generic Mapping objects to dicts recursively."""
        if isinstance(j4, MutableMapping):
            return {k: convert_to_dict(v) for k, v in j4.items()}
        if isinstance(j4, MutableSequence):
            return list(map(convert_to_dict, j4))
        return j4

    name_dict = {entry["name"]: entry for entry in items}
    avro = make_valid_avro(items, name_dict, set())
    avro = [
        t
        for t in avro
        if isinstance(t, MutableMapping)
        and not t.get("abstract")
        and t.get("type") != "org.w3id.cwl.salad.documentation"
    ]

    names = SaladNames()
    make_avsc_object(convert_to_dict(avro), names)
    return list(names.names.values())


#
# Rust AST Nodes
#


# ASSERT: The string is a valid Rust identifier.
RustIdent = str  # alias


class RustLifetime:
    """Represents a Rust lifetime parameter (e.g., `'a`)."""

    __slots__ = ("ident",)

    def __init__(self, ident: RustIdent):
        self.ident = ident

    def __hash__(self) -> int:
        return hash(self.ident)

    def __str__(self) -> str:
        return f"'{str(self.ident)}"


class RustType(ABC):
    """Abstract class for Rust types."""

    pass


class RustMeta(ABC):
    """Abstract class for Rust attribute metas."""

    pass


class RustAttribute:
    """Represents a Rust attribute (e.g., `#[derive(Debug)]`)."""

    __slots__ = ("meta",)

    def __init__(self, meta: RustMeta):
        self.meta = meta

    def __hash__(self) -> int:
        return hash(self.meta)

    def __str__(self) -> str:
        return f"#[{str(self.meta)}]"


RustAttributes = Sequence[RustAttribute]  # alias
RustAttributesMut = MutableSequence[RustAttribute]  # alias


RustGenerics = Sequence[Union[RustLifetime, "RustPath"]]  # alias
RustGenericsMut = MutableSequence[Union[RustLifetime, "RustPath"]]  # alias


class RustPathSegment:
    """Represents a segment in a Rust path with optional generics."""

    __slots__ = ("ident", "generics")

    REX: ClassVar[Pattern[str]] = re.compile(
        r"^([a-zA-Z_]\w*)(?:<([ \w\t,'<>]+)>)?$"
    )  # Using `re.Pattern[str]` raise CI build errors

    def __init__(self, ident: RustIdent, generics: Optional[RustGenerics] = None):
        self.ident = ident
        self.generics = () if generics is None else generics

    def __hash__(self) -> int:
        return hash((self.ident, self.generics))

    def __str__(self) -> str:
        if not self.generics:
            return self.ident
        generics = sorted(self.generics, key=lambda r: 0 if isinstance(r, RustLifetime) else 1)
        generics_str = ", ".join(map(str, generics))
        return f"{self.ident}<{generics_str}>"

    @classmethod
    @functools.cache
    def from_str(cls, value: str) -> "RustPathSegment":
        """Parse a string into RustPathSegment class.

        Results are cached for performance optimization.
        """

        def parse_generics_string(value_generics: str) -> RustGenerics:
            generics_sequence: Union[MutableSequence[str], RustGenerics] = []
            current: list[str] = []
            deep = 0
            for char in value_generics:
                deep += (char == "<") - (char == ">")
                if deep == 0 and char == ",":
                    assert isinstance(generics_sequence, list)
                    generics_sequence.append("".join(current).strip())
                    current = []
                elif deep < 0:
                    raise ValueError(f"Poorly formatted Rust path generics: '{value}'.")
                else:
                    current.append(char)
            if deep > 0:
                raise ValueError(f"Poorly formatted Rust path generics: '{value}'.")
            assert isinstance(generics_sequence, list)
            generics_sequence.append("".join(current).strip())
            return tuple([
                RustLifetime(ident=g[1:]) if g.startswith("'") else RustPath.from_str(g)
                for g in generics_sequence
            ])  # fmt: skip

        #
        # `from_str(...)` method
        if match := re.match(RustPathSegment.REX, value):
            ident, generics = match.groups()
            return cls(
                ident=ident, generics=parse_generics_string(generics) if generics else tuple()
            )
        raise ValueError(f"Poorly formatted Rust path segment: '{value}'.")


RustPathSegments = Sequence[RustPathSegment]  # alias
RustPathSegmentsMut = MutableSequence[RustPathSegment]  # alias


class RustPath(RustMeta):
    """Represents a complete Rust path (e.g., `::std::vec::Vec<T>`)."""

    __slots__ = ("segments", "leading_colon")

    # ASSERT: Never initialized with an empty sequence
    def __init__(self, segments: RustPathSegments, leading_colon: bool = False):
        self.segments = segments
        self.leading_colon = leading_colon

    def __hash__(self) -> int:
        return hash((self.segments, self.leading_colon))

    def __truediv__(self, other: Union["RustPath", RustPathSegment]) -> "RustPath":
        if self.segments[-1].generics:
            raise ValueError("Cannot chain to a RustPath with generics.")

        if isinstance(other, RustPath):
            if other.leading_colon:
                raise ValueError("Cannot chain a RustPath with leading colon.")
            return RustPath(
                segments=tuple([*self.segments, *other.segments]),
                leading_colon=self.leading_colon,
            )
        if isinstance(other, RustPathSegment):
            return RustPath(
                segments=tuple([*self.segments, other]),
                leading_colon=self.leading_colon,
            )

    def __str__(self) -> str:
        leading_colon = "::" if self.leading_colon else ""
        path_str = "::".join(map(str, self.segments))
        return leading_colon + path_str

    @classmethod
    @functools.cache
    def from_str(cls, value: str) -> "RustPath":
        """Parse a string into RustPath class.

        Results are cached for performance optimization.
        """
        norm_value, leading_colon = (value[2:], True) if value.startswith("::") else (value, False)
        segments, segment_with_generics = [], 0
        for segment in map(RustPathSegment.from_str, norm_value.split("::")):
            if len(segment.generics):
                segment_with_generics += 1
            segments.append(segment)
        if segment_with_generics > 1:
            raise ValueError(f"Poorly formatted Rust path: '{value}'")
        return cls(segments=tuple(segments), leading_colon=leading_colon)


class RustTypeTuple(RustType):
    """Represents a Rust tuple type (e.g., `(T, U)`)."""

    __slots__ = ("types",)

    # ASSERT: Never initialized with an empty sequence
    def __init__(self, types: Sequence[RustPath]):
        self.types = types

    def __hash__(self) -> int:
        return hash(self.types)

    def __str__(self) -> str:
        types_str = ", ".join(str(ty) for ty in self.types)
        return f"({types_str})"


class RustMetaList(RustMeta):
    """Represents attribute meta list information (e.g., `derive(Debug, Clone)`).."""

    __slots__ = ("path", "metas")

    def __init__(self, path: RustPath, metas: Optional[Sequence[RustMeta]] = None):
        self.path = path
        self.metas = () if metas is None else metas

    def __hash__(self) -> int:
        return hash(self.path)

    def __str__(self) -> str:
        meta_str = ", ".join(str(meta) for meta in self.metas)
        return f"{str(self.path)}(" + meta_str + ")"


class RustMetaNameValue(RustMeta):
    """Represents attribute meta name-value information (e.g., `key = value`)."""

    __slots__ = ("path", "value")

    def __init__(self, path: RustPath, value: Any = True):
        self.path = path
        self.value = value

    def __hash__(self) -> int:
        return hash(self.path)

    def __str__(self) -> str:
        return f"{str(self.path)} = {to_rust_literal(self.value)}"


#
# Rust Type Representations
#


class RustNamedType(ABC):  # ABC class
    """Abstract class for Rust struct and enum types."""

    __slots__ = ("ident", "attrs", "visibility")

    def __init__(
        self, ident: RustIdent, attrs: Optional[RustAttributes] = None, visibility: str = "pub"
    ):
        self.ident = ident
        self.attrs = () if attrs is None else attrs
        self.visibility = visibility

    def __hash__(self) -> int:
        return hash(self.ident)

    @abstractmethod
    def write_to(self, writer: IO[str], depth: int = 0) -> None:
        pass

    def __str__(self) -> str:
        output = StringIO()
        self.write_to(output, 0)
        return output.getvalue()


class RustField:
    """Represents a field in a Rust struct."""

    __slots__ = ("ident", "type", "attrs")

    def __init__(self, ident: RustIdent, type: RustPath, attrs: Optional[RustAttributes] = None):
        self.ident = ident
        self.type = type
        self.attrs = () if attrs is None else attrs

    def __hash__(self) -> int:
        return hash(self.ident)

    def write_to(self, writer: IO[str], depth: int = 0) -> None:
        indent = "    " * depth

        if self.attrs:
            writer.write("\n".join(f"{indent}{str(attr)}" for attr in self.attrs) + "\n")
        writer.write(f"{indent}{self.ident}: {str(self.type)}")


RustFields = Union[Sequence[RustField], RustTypeTuple]  # alias
RustFieldsMut = Union[MutableSequence[RustField], RustTypeTuple]  # alias


class RustStruct(RustNamedType):
    """Represents a Rust struct definition."""

    __slots__ = ("fields",)

    def __init__(
        self,
        ident: RustIdent,
        fields: Optional[RustFields] = None,
        attrs: Optional[RustAttributes] = None,
        visibility: str = "pub",
    ):
        _attrs = () if attrs is None else attrs
        super().__init__(ident, _attrs, visibility)
        self.fields = fields

    def write_to(self, writer: IO[str], depth: int = 0) -> None:
        indent = "    " * depth

        if self.attrs:
            writer.write("\n".join(f"{indent}{str(attr)}" for attr in self.attrs) + "\n")

        writer.write(f"{indent}{self.visibility} struct {self.ident}")
        if self.fields is None:
            writer.write(";\n")
        elif isinstance(self.fields, RustTypeTuple):
            writer.write(f"{str(self.fields)};\n")
        else:
            writer.write(" {\n")
            for field_ in self.fields:
                field_.write_to(writer, depth + 1)
                writer.write(",\n")
            writer.write(f"{indent}}}\n")


class RustVariant:
    """Represents a variant in a Rust enum."""

    __slots__ = ("ident", "tuple", "attrs")

    def __init__(
        self,
        ident: RustIdent,
        tuple: Optional[RustTypeTuple] = None,
        attrs: Optional[RustAttributes] = None,
    ):
        self.ident = ident
        self.tuple = tuple
        self.attrs = () if attrs is None else attrs

    def __hash__(self) -> int:
        return hash(self.ident)

    def write_to(self, writer: IO[str], depth: int = 0) -> None:
        indent = "    " * depth

        if self.attrs:
            writer.write("\n".join(f"{indent}{str(attr)}" for attr in self.attrs) + "\n")
        writer.write(f"{indent}{self.ident}")
        if self.tuple:
            writer.write(str(self.tuple))

    @classmethod
    def from_path(cls, path: RustPath) -> "RustVariant":
        # Collect segments from the path and any RustPath objects in generics
        paths = [path]
        for g in path.segments[-1].generics:
            if isinstance(g, RustPath):
                paths.append(g)

        # Extract the identifiers from the last segment of each path
        idents = []
        for p in paths:
            idents.append(p.segments[-1].ident)

        ident = "".join(idents)
        ident = ident.replace("StrValue", "String", 1)  # HACK
        return cls(ident=ident, tuple=RustTypeTuple([path]))


RustVariants = Sequence[RustVariant]  # alias
RustVariantsMut = MutableSequence[RustVariant]  # alias


class RustEnum(RustNamedType):
    """Represents a Rust enum definition."""

    __slots__ = ("variants",)

    def __init__(
        self,
        ident: RustIdent,
        variants: Optional[RustVariants] = None,
        attrs: Optional[RustAttributes] = None,
        visibility: str = "pub",
    ):
        _attrs = () if attrs is None else attrs
        super().__init__(ident, _attrs, visibility)
        self.variants = () if variants is None else variants

    def write_to(self, writer: IO[str], depth: int = 0) -> None:
        indent = "    " * depth

        if self.attrs:
            writer.write("\n".join(f"{indent}{str(attr)}" for attr in self.attrs) + "\n")

        writer.write(f"{indent}{self.visibility} enum {self.ident} {{\n")
        for variant in self.variants:
            variant.write_to(writer, depth + 1)
            writer.write(",\n")
        writer.write(f"{indent}}}\n")


# Wrapper for the RustNamedType `write_to()` method call
def salad_macro_write_to(ty: RustNamedType, writer: IO[str], depth: int = 0) -> None:
    """Write a RustNamedType wrapping it in the Schema Salad macro."""
    indent = "    " * depth
    writer.write(indent + "salad_core::define_type! {\n")
    ty.write_to(writer, 1)
    writer.write(indent + "}\n\n")


#
# Rust Module Tree
#


class RustModuleTree:
    """Represents a Rust module with submodules and named types."""

    __slots__ = ("ident", "parent", "named_types", "submodules")

    def __init__(
        self,
        ident: RustIdent,  # ASSERT: Immutable field
        parent: Optional["RustModuleTree"] = None,  # ASSERT: Immutable field
        named_types: Optional[MutableMapping[RustIdent, RustNamedType]] = None,
        submodules: Optional[MutableMapping[RustIdent, "RustModuleTree"]] = None,
    ):
        self.ident = ident
        self.parent = parent
        self.named_types = {} if named_types is None else named_types
        self.submodules = {} if submodules is None else submodules

    def __hash__(self) -> int:
        return hash((self.ident, self.parent))

    def get_rust_path(self) -> RustPath:
        """Return the complete Rust path from root to this module."""
        segments: list[RustPathSegment] = []
        current: Optional["RustModuleTree"] = self

        while current:
            segments.append(RustPathSegment(ident=current.ident))
            current = current.parent
        return RustPath(segments=tuple(reversed(segments)))

    def add_submodule(self, path: Union[RustPath, str]) -> "RustModuleTree":
        """Create a new submodule or returns an existing one with the given path."""
        if isinstance(path, str):
            path = RustPath.from_str(path)
        segments = iter(path.segments)

        # First segment, corner case
        if (first := next(segments, None)) is None:
            return self

        if first.ident == self.ident:
            current = self
        else:
            current = self.submodules.setdefault(
                first.ident,
                RustModuleTree(ident=first.ident, parent=self),
            )

        # Subsequent segments
        for segment in segments:
            current = current.submodules.setdefault(
                segment.ident,
                RustModuleTree(ident=segment.ident, parent=current),
            )
        return current

    def add_named_type(self, ty: RustNamedType) -> RustPath:
        """Add a named type to this module tree and returns its complete Rust path.

        Raises `ValueError` if type with same name already exists.
        """
        module_rust_path = self.get_rust_path()
        if ty.ident in self.named_types:
            raise ValueError(f"Duplicate Rust type '{ty.ident}' in '{module_rust_path}'.")
        self.named_types[ty.ident] = ty
        return module_rust_path / RustPathSegment(ident=ty.ident)

    # def get_named_type(self, path: RustPath) -> Optional[RustNamedType]:
    #     if module := self.get_submodule(path.parent()):
    #         return module.named_types.get(path.segments[-1].ident)
    #     return None

    def write_to_fs(self, base_path: Path) -> None:
        """Write the module tree to the filesystem under the given base path."""

        def write_module_file(module: "RustModuleTree", path: Path, mode: str = "wt") -> None:
            with open(path, mode=mode) as module_rs:
                if module.submodules:
                    module_rs.write(
                        "\n".join([f"mod {mod.ident};" for mod in module.submodules.values()])
                        + "\n\n"
                    )
                if module.named_types:
                    for ty in module.named_types.values():
                        salad_macro_write_to(ty, module_rs, 0)

        #
        # `write_to_fs(...)` method
        path = base_path.resolve()
        traversing_stack: MutableSequence[tuple[Path, RustModuleTree]] = []

        # Write `lib.rs` module (corner case)
        if not self.parent:
            path.mkdir(mode=0o755, parents=True, exist_ok=True)
            write_module_file(module=self, path=path / "lib.rs", mode="at")
            traversing_stack.extend((path, sub_mod) for sub_mod in self.submodules.values())
        else:
            traversing_stack.append((path, self))

        # Generate module files
        while traversing_stack:
            path_parent, module = traversing_stack.pop()

            if not module.submodules:
                path_parent.mkdir(mode=0o755, parents=True, exist_ok=True)
                write_module_file(module=module, path=path_parent / f"{module.ident}.rs")
                continue

            path_module = path_parent / module.ident
            path_module.mkdir(mode=0o755, parents=True, exist_ok=True)
            write_module_file(module=module, path=path_module / "mod.rs")
            traversing_stack.extend(
                (path_module, sub_mod) for sub_mod in module.submodules.values()
            )


#
# Salad Core Types
#


def rust_type_option(rust_ty: RustPath) -> RustPath:
    return RustPath([RustPathSegment(ident="Option", generics=[rust_ty])])


def rust_type_list(rust_ty: RustPath) -> RustPath:
    return RustPath([
        RustPathSegment(ident="crate"),
        RustPathSegment(ident="core"),
        RustPathSegment(ident="List", generics=[rust_ty]),
    ])  # fmt: skip


_AVRO_TO_RUST_PRESET = {
    # Salad Types
    "boolean": RustPath.from_str("crate::core::Bool"),
    "int": RustPath.from_str("crate::core::Int"),
    "long": RustPath.from_str("crate::core::Long"),
    "float": RustPath.from_str("crate::core::Float"),
    "double": RustPath.from_str("crate::core::Double"),
    "string": RustPath.from_str("crate::core::StrValue"),
    "org.w3id.cwl.salad.Any": RustPath.from_str("crate::core::Any"),
    "org.w3id.cwl.salad.ArraySchema.type.Array_name": RustPath.from_str("crate::TypeArray"),
    "org.w3id.cwl.salad.EnumSchema.type.Enum_name": RustPath.from_str("crate::TypeEnum"),
    "org.w3id.cwl.salad.RecordSchema.type.Record_name": RustPath.from_str("crate::TypeRecord"),
    # CWL Types
    "org.w3id.cwl.cwl.Expression": RustPath.from_str("crate::core::StrValue"),
}


#
# Code generator
#


class RustCodeGen(CodeGenBase):
    """Rust code generator for schema salad definitions."""

    # Static
    CRATE_VERSION: ClassVar[str] = "0.1.0"  # Version of the generated crate
    __TEMPLATE_DIR: ClassVar[Path] = Path(
        str(resource_files("schema_salad").joinpath("rust"))
    ).resolve()

    # Parsing related
    __avro_to_rust: MutableMapping[str, RustPath]
    __document_root_paths: MutableSequence[RustPath]
    __module_tree: RustModuleTree
    __schema_stack: MutableSequence[NamedSchema]

    def __init__(
        self,
        base_uri: str,
        package: str,
        salad_version: str,
        target: Optional[str] = None,
    ) -> None:
        """Initialize the RustCodeGen class."""
        self.package = package
        self.package_version = self.__generate_crate_version(salad_version)
        self.output_dir = Path(target or ".").resolve()
        self.document_root_attr = RustAttribute(
            meta=RustMetaList(
                path=RustPath.from_str("salad"),
                metas=[
                    RustPath.from_str("root"),
                    RustMetaNameValue(
                        path=RustPath.from_str("base_uri"),
                        value=base_uri,
                    ),
                ],
            )
        )

    def parse(self, items: MutableSequence[JsonDataType]) -> None:
        """Parse the provided item list to generate the corresponding Rust types."""
        # Create output directory
        self.__init_output_directory()

        # Generate Rust named types
        self.__avro_to_rust = _AVRO_TO_RUST_PRESET.copy()
        self.__document_root_paths = []
        self.__module_tree = RustModuleTree(ident="crate", parent=None)
        self.__schema_stack = list(reversed(make_avro(items)))

        while self.__schema_stack:
            schema = self.__schema_stack.pop()

            if not schema.name.startswith(self.package):
                continue
            if schema.name in self.__avro_to_rust:
                _logger.warning(f"Skip parse step for schema: {schema.name}")
                continue

            rust_path = self.__parse_named_schema(schema)
            self.__avro_to_rust[schema.name] = rust_path

        # Generate `DocumentRoot` enum
        self.__module_tree.add_named_type(
            RustEnum(
                ident="DocumentRoot",
                attrs=[self.document_root_attr],
                variants=list(map(RustVariant.from_path, self.__document_root_paths)),
            )
        )

        # Write named types to the "src" folder
        self.__module_tree.write_to_fs(self.output_dir / "src")

    def __parse_named_schema(self, named: NamedSchema) -> RustPath:
        if isinstance(named, RecordSchema):
            return self.__parse_record_schema(named)
        if isinstance(named, EnumSchema):
            return self.__parse_enum_schema(named)
        if isinstance(named, NamedUnionSchema):
            return self.__parse_union_schema(named)
        raise ValueError(f"Cannot parse schema of type {type(named).__name__}.")

    def __parse_record_schema(self, record: RecordSchema) -> RustPath:
        ident = rust_sanitize_type_ident(avro_shortname(record.name))
        attrs, _ = self.__parse_named_schema_attrs(record)
        fields = list(set(self.__parse_record_field(f, record) for f in record.fields))
        is_doc_root = record.get_prop("documentRoot") or False

        if is_doc_root:
            attrs = [*attrs, self.document_root_attr]

        rust_path = self.__module_tree \
            .add_submodule(self.__get_submodule_path(record)) \
            .add_named_type(RustStruct(ident=ident, attrs=attrs, fields=fields))  # fmt: skip

        if is_doc_root:
            self.__document_root_paths.append(rust_path)
        return rust_path

    def __parse_record_field(self, field: SaladField, parent: RecordSchema) -> RustField:
        def parse_field_type(schema: Schema) -> RustPath:
            if isinstance(schema, UnionSchema):
                filtered_schemas = [s for s in schema.schemas if s.type != "null"]
                filtered_schemas_len = len(filtered_schemas)

                if filtered_schemas_len == 1:
                    rust_path: RustPath = parse_field_type(filtered_schemas[0])
                    if filtered_schemas_len < len(schema.schemas):
                        return rust_type_option(rust_path)
                    return rust_path

                union_name = f"{parent.name}.{field.name}"
                rust_path_opt: Optional[RustPath] = self.__avro_to_rust.get(union_name)
                if rust_path_opt is not None:
                    if filtered_schemas_len < len(schema.schemas):
                        return rust_type_option(rust_path_opt)
                    return rust_path_opt

                # else ...
                named_union_schema = NamedUnionSchema.__new__(NamedUnionSchema)
                named_union_schema._props = schema._props
                named_union_schema._schemas = filtered_schemas
                named_union_schema.set_prop("name", union_name)
                named_union_schema.set_prop("namespace", parent.name)
                named_union_schema.set_prop("doc", field.get_prop("doc"))

                self.__schema_stack.append(named_union_schema)
                type_path = self.__get_submodule_path(named_union_schema) / RustPathSegment(
                    rust_sanitize_type_ident(avro_shortname(union_name))
                )
                if filtered_schemas_len < len(schema.schemas):
                    return rust_type_option(type_path)
                return type_path

            if isinstance(schema, (RecordSchema, EnumSchema)):
                return self.__avro_to_rust.get(
                    schema.name,
                    self.__get_submodule_path(schema)
                    / RustPathSegment(ident=rust_sanitize_type_ident(avro_shortname(schema.name))),
                )

            if isinstance(schema, ArraySchema):
                return rust_type_list(parse_field_type(schema.items))

            if isinstance(schema, PrimitiveSchema):
                path = self.__avro_to_rust.get(schema.type)
                if path is None:
                    _logger.error(f"Unknown primitive schema type: {schema.type}")
                    sys.exit(1)
                return path

            raise ValueError(f"Cannot parse schema with type: '{type(schema).__name__}'.")

        #
        # `__parse_record_field(...)` method
        ident = rust_sanitize_field_ident(field.name)
        attrs, _ = self.__parse_field_schema_attrs(field)
        ty = parse_field_type(field.type)
        return RustField(ident=ident, attrs=attrs, type=ty)

    def __parse_union_schema(self, union: NamedUnionSchema) -> RustPath:
        def parse_variant_array_subtype(schema: Schema) -> RustPath:
            if isinstance(schema, UnionSchema):
                filtered_schemas = [s for s in schema.schemas if s.type != "null"]

                item_name = f"{union.name}_item"
                named_union_schema = NamedUnionSchema.__new__(NamedUnionSchema)
                named_union_schema._props = schema._props
                named_union_schema._schemas = filtered_schemas
                named_union_schema.set_prop("name", item_name)
                named_union_schema.set_prop("namespace", union.name)

                self.__schema_stack.append(named_union_schema)
                return self.__get_submodule_path(named_union_schema) / RustPathSegment(
                    rust_sanitize_type_ident(avro_shortname(item_name))
                )

            if isinstance(schema, (RecordSchema, EnumSchema)):
                return self.__avro_to_rust.get(
                    schema.name,
                    self.__get_submodule_path(schema)
                    / RustPathSegment(ident=rust_sanitize_type_ident(avro_shortname(schema.name))),
                )

            if isinstance(schema, PrimitiveSchema):
                path = self.__avro_to_rust.get(schema.type)
                if path is None:
                    raise ValueError(f"Unknown primitive schema type: {schema.type}")
                return path

            # Default case for any other schema type
            raise ValueError(
                f"Unhandled schema type in parse_variant_array_subtype: {type(schema).__name__}"
            )

        def parse_variant_type(schema: Schema) -> RustVariant:
            if isinstance(schema, (RecordSchema, EnumSchema)):
                return RustVariant.from_path(
                    self.__avro_to_rust.get(
                        schema.name,
                        self.__get_submodule_path(schema)
                        / RustPathSegment(
                            ident=rust_sanitize_type_ident(avro_shortname(schema.name))
                        ),
                    )
                )

            if isinstance(schema, PrimitiveSchema):
                path = self.__avro_to_rust.get(schema.type)
                if path is None:
                    raise ValueError(f"Unknown primitive schema type: {schema.type}")
                return RustVariant.from_path(path)

            if isinstance(schema, ArraySchema):
                return RustVariant.from_path(
                    rust_type_list(parse_variant_array_subtype(schema.items))
                )

            raise ValueError(f"Cannot parse schema with type: '{type(schema).__name__}'.")

        #
        # `__parse_union_schema(...)` method
        ident = rust_sanitize_type_ident(avro_shortname(union.name))
        attrs, _ = self.__parse_named_schema_attrs(union)
        variants = list(set(map(parse_variant_type, union.schemas)))

        return self.__module_tree \
            .add_submodule(self.__get_submodule_path(union)) \
            .add_named_type(RustEnum(ident=ident, attrs=attrs, variants=variants))  # fmt: skip

    def __parse_enum_schema(self, enum: EnumSchema) -> RustPath:
        ident = rust_sanitize_type_ident(avro_shortname(enum.name))
        attrs, docs_count = self.__parse_named_schema_attrs(enum)
        attrs = [
            *attrs,
            RustAttribute(
                RustMetaList(
                    path=RustPath.from_str("derive"),
                    metas=[RustPath.from_str("Copy")],
                )
            ),
        ]

        if len(enum.symbols) == 1:
            return self.__module_tree \
                .add_submodule(self.__get_submodule_path(enum)) \
                .add_named_type(
                    RustStruct(
                        ident=ident,
                        attrs=[
                            *attrs[:docs_count],
                            RustAttribute(
                                RustMetaNameValue(
                                    path=RustPath.from_str("doc"),
                                    value=f"Matches constant value `{enum.symbols[0]}`.",
                                )
                            ),
                            *attrs[docs_count:],
                            RustAttribute(
                                RustMetaList(
                                    path=RustPath.from_str("salad"),
                                    metas=[RustMetaNameValue(
                                        path=RustPath.from_str("as_str"),
                                        value=enum.symbols[0],
                                    )],
                                )
                            ),
                        ],
                    )
                )  # fmt: skip
        else:
            return self.__module_tree \
                .add_submodule(self.__get_submodule_path(enum)) \
                .add_named_type(
                    RustEnum(
                        ident=ident,
                        attrs=attrs,
                        variants=[
                            RustVariant(
                                ident=rust_sanitize_type_ident(symbol),
                                attrs=[
                                    RustAttribute(
                                        RustMetaNameValue(
                                            path=RustPath.from_str("doc"),
                                            value=f"Matches constant value `{symbol}`.",
                                        )
                                    ),
                                    RustAttribute(
                                        RustMetaList(
                                            path=RustPath.from_str("salad"),
                                            metas=[RustMetaNameValue(
                                                path=RustPath.from_str("as_str"),
                                                value=symbol,
                                            )],
                                        )
                                    ),
                                ],
                            )
                            for symbol in enum.symbols
                        ],
                    )
                )  # fmt: skip

    # End of named schemas parse block
    #
    @staticmethod
    def __parse_named_schema_attrs(schema: NamedSchema) -> tuple[RustAttributes, int]:
        attrs: list[RustAttribute] = []
        docs_count = 0

        if docs := schema.get_prop("doc"):
            if isinstance(docs, str):
                assert isinstance(docs, str)
            elif isinstance(docs, list) and all(isinstance(d, str) for d in docs):
                docs = cast(list[str], docs)
            else:
                _logger.error(
                    f"Invalid documentation for schema '{schema.name}': "
                    f"expected string or list of strings, got {type(docs).__name__}"
                )
                docs = []

            rust_path_doc = RustPath.from_str("doc")
            attrs.extend(
                RustAttribute(RustMetaNameValue(path=rust_path_doc, value=doc))
                for doc in rust_sanitize_doc_iter(docs)
            )
            docs_count = len(attrs)

        attrs.append(
            RustAttribute(
                RustMetaList(
                    path=RustPath.from_str("derive"),
                    metas=[
                        RustPath.from_str("Debug"),
                        RustPath.from_str("Clone"),
                    ],
                )
            )
        )

        return attrs, docs_count

    @staticmethod
    def __parse_field_schema_attrs(schema: SaladField) -> tuple[RustAttributes, int]:
        attrs: list[RustAttribute] = []
        docs_count = 0

        if docs := schema.get_prop("doc"):
            if isinstance(docs, str):
                assert isinstance(docs, str)
            elif isinstance(docs, list) and all(isinstance(d, str) for d in docs):
                docs = cast(list[str], docs)
            else:
                _logger.error(
                    f"Invalid documentation for schema '{schema.name}': "
                    f"expected string or list of strings, got {type(docs).__name__}"
                )
                docs = []

            rust_path_doc = RustPath.from_str("doc")
            attrs.extend(
                RustAttribute(RustMetaNameValue(path=rust_path_doc, value=doc))
                for doc in rust_sanitize_doc_iter(docs)
            )
            docs_count = len(attrs)

        metas: list[RustMeta] = []
        if default := schema.get_prop("default"):
            metas.append(RustMetaNameValue(path=RustPath.from_str("default"), value=default))
        if jsonld_predicate := schema.get_prop("jsonldPredicate"):
            if isinstance(jsonld_predicate, str) and jsonld_predicate == "@id":
                metas.append(RustPath.from_str("identifier"))
            elif isinstance(jsonld_predicate, MutableMapping):
                metas.extend(
                    RustMetaNameValue(path=RustPath.from_str(rust_path), value=value)
                    for key, rust_path in [
                        ("mapSubject", "map_key"),
                        ("mapPredicate", "map_predicate"),
                        ("subscope", "subscope"),
                    ]
                    if (value := jsonld_predicate.get(key))
                )
        if metas:
            attrs.append(RustAttribute(RustMetaList(path=RustPath.from_str("salad"), metas=metas)))

        return attrs, docs_count

    # End of attributes parse block
    #
    def __get_submodule_path(self, schema: NamedSchema) -> RustPath:
        segments = [RustPathSegment(ident="crate")]
        if namespace_prop := schema.get_prop("namespace"):
            if not isinstance(namespace_prop, str):
                _logger.error(
                    f"Invalid namespace for schema '{schema.name}': "
                    f"expected string, got {type(namespace_prop).__name__}"
                )
            elif (namespace := namespace_prop.removeprefix(self.package)) not in ("", "."):
                namespace_segment = namespace.split(".")[1].lower()
                module_ident = rust_sanitize_field_ident(namespace_segment)
                segments.append(RustPathSegment(ident=module_ident))
        return RustPath(segments=segments)

    def __init_output_directory(self) -> None:
        """Initialize the output directory structure."""
        if self.output_dir.is_file():
            raise ValueError(f"Output directory cannot be a file: {self.output_dir}")
        if not self.output_dir.exists():
            _logger.info(f"Creating output directory: {self.output_dir}")
            self.output_dir.mkdir(mode=0o755, parents=True)
        elif any(self.output_dir.iterdir()):
            _logger.warning(
                f"Output directory is not empty: {self.output_dir}.\n"
                "Wait for 3 seconds before proceeding..."
            )
            sleep(3)

        def copy2_wrapper(src: str, dst: str) -> Optional[object]:
            if not src.endswith("rust/Cargo.toml"):
                return shutil.copy2(src, dst)

            replace_dict = [
                ("{package_name}", self.output_dir.name),
                ("{package_version}", self.package_version),
            ]

            with open(src, "r") as src_f, open(dst, "w") as dst_f:
                content = src_f.read()
                for placeholder, value in replace_dict:
                    content = content.replace(placeholder, value)
                dst_f.write(content)
            return None

        shutil.copytree(
            RustCodeGen.__TEMPLATE_DIR,
            self.output_dir,
            dirs_exist_ok=True,
            copy_function=copy2_wrapper,
        )

    @classmethod
    def __generate_crate_version(cls, salad_version: str) -> str:
        salad_version = salad_version.removeprefix("v")
        return f"{cls.CRATE_VERSION}+salad{salad_version}"
