# Stubs for pkg_resources (Python 2)
#
# NOTE: This dynamically typed stub was automatically generated by stubgen.

from typing import Any
from os import open as os_open
from collections import namedtuple

require = ... # type: Any
working_set = ... # type: Any

class PEP440Warning(RuntimeWarning): ...

class _SetuptoolsVersionMixin:
    def __hash__(self): ...
    def __lt__(self, other): ...
    def __le__(self, other): ...
    def __eq__(self, other): ...
    def __ge__(self, other): ...
    def __gt__(self, other): ...
    def __ne__(self, other): ...
    def __getitem__(self, key): ...
    def __iter__(self): ...

def parse_version(v): ...

class ResolutionError(Exception): ...

class VersionConflict(ResolutionError):
    @property
    def dist(self): ...
    @property
    def req(self): ...
    def report(self): ...
    def with_context(self, required_by): ...

class ContextualVersionConflict(VersionConflict):
    @property
    def required_by(self): ...

class DistributionNotFound(ResolutionError):
    @property
    def req(self): ...
    @property
    def requirers(self): ...
    @property
    def requirers_str(self): ...
    def report(self): ...

class UnknownExtra(ResolutionError): ...

EGG_DIST = ... # type: Any
BINARY_DIST = ... # type: Any
SOURCE_DIST = ... # type: Any
CHECKOUT_DIST = ... # type: Any
DEVELOP_DIST = ... # type: Any

def register_loader_type(loader_type, provider_factory): ...
def get_provider(moduleOrReq): ...

get_platform = ... # type: Any

def compatible_platforms(provided, required): ...
def run_script(dist_spec, script_name): ...

run_main = ... # type: Any

def get_distribution(dist): ...
def load_entry_point(dist, group, name): ...
def get_entry_map(dist, group=None): ...
def get_entry_info(dist, group, name): ...

class IMetadataProvider:
    def has_metadata(name): ...
    def get_metadata(name): ...
    def get_metadata_lines(name): ...
    def metadata_isdir(name): ...
    def metadata_listdir(name): ...
    def run_script(script_name, namespace): ...

class IResourceProvider(IMetadataProvider):
    def get_resource_filename(manager, resource_name): ...
    def get_resource_stream(manager, resource_name): ...
    def get_resource_string(manager, resource_name): ...
    def has_resource(resource_name): ...
    def resource_isdir(resource_name): ...
    def resource_listdir(resource_name): ...

class WorkingSet:
    entries = ... # type: Any
    entry_keys = ... # type: Any
    by_key = ... # type: Any
    callbacks = ... # type: Any
    def __init__(self, entries=None): ...
    def add_entry(self, entry): ...
    def __contains__(self, dist): ...
    def find(self, req): ...
    def iter_entry_points(self, group, name=None): ...
    def run_script(self, requires, script_name): ...
    def __iter__(self): ...
    def add(self, dist, entry=None, insert=True, replace=False): ...
    def resolve(self, requirements, env=None, installer=None, replace_conflicting=False): ...
    def find_plugins(self, plugin_env, full_env=None, installer=None, fallback=True): ...
    def require(self, *requirements): ...
    def subscribe(self, callback): ...

class _ReqExtras(dict):
    def markers_pass(self, req): ...

class Environment:
    platform = ... # type: Any
    python = ... # type: Any
    def __init__(self, search_path=None, platform=..., python=...): ...
    def can_add(self, dist): ...
    def remove(self, dist): ...
    def scan(self, search_path=None): ...
    def __getitem__(self, project_name): ...
    def add(self, dist): ...
    def best_match(self, req, working_set, installer=None): ...
    def obtain(self, requirement, installer=None): ...
    def __iter__(self): ...
    def __iadd__(self, other): ...
    def __add__(self, other): ...

AvailableDistributions = ... # type: Any

class ExtractionError(RuntimeError): ...

class ResourceManager:
    extraction_path = ... # type: Any
    cached_files = ... # type: Any
    def __init__(self): ...
    def resource_exists(self, package_or_requirement, resource_name): ...
    def resource_isdir(self, package_or_requirement, resource_name): ...
    def resource_filename(self, package_or_requirement, resource_name): ...
    def resource_stream(self, package_or_requirement, resource_name): ...
    def resource_string(self, package_or_requirement, resource_name): ...
    def resource_listdir(self, package_or_requirement, resource_name): ...
    def extraction_error(self): ...
    def get_cache_path(self, archive_name, names=...): ...
    def postprocess(self, tempname, filename): ...
    def set_extraction_path(self, path): ...
    def cleanup_resources(self, force=False): ...

def get_default_cache(): ...
def safe_name(name): ...
def safe_version(version): ...
def safe_extra(extra): ...
def to_filename(name): ...
def invalid_marker(text): ...
def evaluate_marker(text, extra=None): ...

class NullProvider:
    egg_name = ... # type: Any
    egg_info = ... # type: Any
    loader = ... # type: Any
    module_path = ... # type: Any
    def __init__(self, module): ...
    def get_resource_filename(self, manager, resource_name): ...
    def get_resource_stream(self, manager, resource_name): ...
    def get_resource_string(self, manager, resource_name): ...
    def has_resource(self, resource_name): ...
    def has_metadata(self, name): ...
    def get_metadata(self, name): ...
    def get_metadata_lines(self, name): ...
    def resource_isdir(self, resource_name): ...
    def metadata_isdir(self, name): ...
    def resource_listdir(self, resource_name): ...
    def metadata_listdir(self, name): ...
    def run_script(self, script_name, namespace): ...

class EggProvider(NullProvider):
    def __init__(self, module): ...

class DefaultProvider(EggProvider):
    def get_resource_stream(self, manager, resource_name): ...

class EmptyProvider(NullProvider):
    module_path = ... # type: Any
    def __init__(self): ...

empty_provider = ... # type: Any

class ZipManifests(dict):
    @classmethod
    def build(cls, path): ...
    load = ... # type: Any

class ZipProvider(EggProvider):
    eagers = ... # type: Any
    zip_pre = ... # type: Any
    def __init__(self, module): ...
    @property
    def zipinfo(self): ...
    def get_resource_filename(self, manager, resource_name): ...

class FileMetadata(EmptyProvider):
    path = ... # type: Any
    def __init__(self, path): ...
    def has_metadata(self, name): ...
    def get_metadata(self, name): ...
    def get_metadata_lines(self, name): ...

class PathMetadata(DefaultProvider):
    module_path = ... # type: Any
    egg_info = ... # type: Any
    def __init__(self, path, egg_info): ...

class EggMetadata(ZipProvider):
    zip_pre = ... # type: Any
    loader = ... # type: Any
    module_path = ... # type: Any
    def __init__(self, importer): ...

def register_finder(importer_type, distribution_finder): ...
def find_distributions(path_item, only=False): ...
def register_namespace_handler(importer_type, namespace_handler): ...
def declare_namespace(packageName): ...
def fixup_namespace_packages(path_item, parent=None): ...
def normalize_path(filename): ...
def yield_lines(strs): ...

class EntryPoint:
    name = ... # type: Any
    module_name = ... # type: Any
    attrs = ... # type: Any
    extras = ... # type: Any
    dist = ... # type: Any
    def __init__(self, name, module_name, attrs=..., extras=..., dist=None): ...
    def load(self, require=True, *args, **kwargs): ...
    def resolve(self): ...
    def require(self, env=None, installer=None): ...
    pattern = ... # type: Any
    @classmethod
    def parse(cls, src, dist=None): ...
    @classmethod
    def parse_group(cls, group, lines, dist=None): ...
    @classmethod
    def parse_map(cls, data, dist=None): ...

class Distribution:
    PKG_INFO = ... # type: Any
    project_name = ... # type: Any
    py_version = ... # type: Any
    platform = ... # type: Any
    location = ... # type: Any
    precedence = ... # type: Any
    def __init__(self, location=None, metadata=None, project_name=None, version=None, py_version=..., platform=None, precedence=...): ...
    @classmethod
    def from_location(cls, location, basename, metadata=None, **kw): ...
    @property
    def hashcmp(self): ...
    def __hash__(self): ...
    def __lt__(self, other): ...
    def __le__(self, other): ...
    def __gt__(self, other): ...
    def __ge__(self, other): ...
    def __eq__(self, other): ...
    def __ne__(self, other): ...
    @property
    def key(self): ...
    @property
    def parsed_version(self): ...
    @property
    def version(self): ...
    def requires(self, extras=...): ...
    def activate(self, path=None): ...
    def egg_name(self): ...
    def __getattr__(self, attr): ...
    @classmethod
    def from_filename(cls, filename, metadata=None, **kw): ...
    def as_requirement(self): ...
    def load_entry_point(self, group, name): ...
    def get_entry_map(self, group=None): ...
    def get_entry_info(self, group, name): ...
    def insert_on(self, path, loc=None, replace=False): ...
    def check_version_conflict(self): ...
    def has_version(self): ...
    def clone(self, **kw): ...
    @property
    def extras(self): ...

class EggInfoDistribution(Distribution): ...

class DistInfoDistribution(Distribution):
    PKG_INFO = ... # type: Any
    EQEQ = ... # type: Any

class RequirementParseError(ValueError): ...

def parse_requirements(strs): ...

def ensure_directory(path): ...
def split_sections(s): ...

def resource_stream(package_or_requirement: str, resource_name: str): ...

# Modified manually by the unwise @jmchilton
def resource_listdir(package_or_request: str, resource_name: str): ...
def resource_string(package_or_request: str, resource_name: str): ...

# Names in __all__ with no definition:
#   add_activation_listener
#   cleanup_resources
#   iter_entry_points
#   resource_exists
#   resource_filename
#   resource_isdir
#   resource_listdir
#   resource_stream
#   resource_string
#   set_extraction_path
