"""Test the ref_resolver module."""


import os
import shutil
import sys
import tempfile

import pytest
from requests import Session

from schema_salad.exceptions import ValidationException
from schema_salad.ref_resolver import DefaultFetcher, Loader, file_uri
from schema_salad.tests.util import get_data

from _pytest.fixtures import FixtureRequest

def is_fs_case_sensitive(path: str) -> bool:  # https://stackoverflow.com/a/36612604/1585509
    with tempfile.NamedTemporaryFile(prefix="TmP", dir=path) as tmp_file:
        return not os.path.exists(tmp_file.name.lower())


@pytest.fixture
def tmp_dir_fixture(request: FixtureRequest) -> str:
    d = tempfile.mkdtemp()

    @request.addfinalizer
    def teardown() -> None:
        shutil.rmtree(d)

    return d


def test_Loader_initialisation_for_HOME_env_var(tmp_dir_fixture: str) -> None:
    # Ensure HOME is set.
    os.environ["HOME"] = tmp_dir_fixture

    loader = Loader(ctx={})
    assert isinstance(loader.session, Session)


def test_Loader_initialisation_for_TMP_env_var(tmp_dir_fixture: str) -> None:
    # Ensure HOME is missing.
    if "HOME" in os.environ:
        del os.environ["HOME"]
    # Ensure TMP is present.
    os.environ["TMP"] = tmp_dir_fixture

    loader = Loader(ctx={})
    assert isinstance(loader.session, Session)


def test_Loader_initialisation_with_neither_TMP_HOME_set(tmp_dir_fixture: str) -> None:
    # Ensure HOME is missing.
    if "HOME" in os.environ:
        del os.environ["HOME"]
    if "TMP" in os.environ:
        del os.environ["TMP"]

    loader = Loader(ctx={})
    assert isinstance(loader.session, Session)


def test_Loader_initialisation_disable_doc_cache(tmp_dir_fixture: str) -> None:
    loader = Loader(ctx={}, doc_cache=False)
    assert isinstance(loader.session, Session)


def test_DefaultFetcher_urljoin_win32(tmp_dir_fixture: str) -> None:
    # Ensure HOME is set.
    os.environ["HOME"] = tmp_dir_fixture


def test_DefaultFetcher_urljoin_linux(tmp_dir_fixture: str) -> None:
    # Ensure HOME is set.
    os.environ["HOME"] = tmp_dir_fixture

    actual_platform = sys.platform
    try:
        # Pretend it's Linux (e.g. not win32)
        sys.platform = "linux2"
        fetcher = DefaultFetcher({}, None)
        url = fetcher.urljoin("file:///home/fred/foo.cwl", "soup.cwl")
        assert url == "file:///home/fred/soup.cwl"

        url = fetcher.urljoin("file:///home/fred/foo.cwl", "../alice/soup.cwl")
        assert url == "file:///home/alice/soup.cwl"
        # relative from root
        url = fetcher.urljoin("file:///home/fred/foo.cwl", "/baz/soup.cwl")
        assert url == "file:///baz/soup.cwl"

        url = fetcher.urljoin(
            "file:///home/fred/foo.cwl", "http://example.com/bar/soup.cwl"
        )
        assert url == "http://example.com/bar/soup.cwl"

        url = fetcher.urljoin("http://example.com/fred/foo.cwl", "soup.cwl")
        assert url == "http://example.com/fred/soup.cwl"

        # Root-relative -- here relative to http host, not file:///
        url = fetcher.urljoin("http://example.com/fred/foo.cwl", "/bar/soup.cwl")
        assert url == "http://example.com/bar/soup.cwl"

        # Security concern - can't resolve file: from http:
        with pytest.raises(ValidationException):
            url = fetcher.urljoin(
                "http://example.com/fred/foo.cwl", "file:///bar/soup.cwl"
            )

        # But this one is not "dangerous" on Linux
        fetcher.urljoin("http://example.com/fred/foo.cwl", "c:/bar/soup.cwl")

    finally:
        sys.platform = actual_platform


def test_import_list() -> None:
    import schema_salad.ref_resolver
    from schema_salad.sourceline import cmap

    basedir = schema_salad.ref_resolver.file_uri(os.path.dirname(__file__) + "/")
    loader = schema_salad.ref_resolver.Loader({})
    ra, _ = loader.resolve_all(cmap({"foo": {"$import": "list.json"}}), basedir)

    assert {"foo": ["bar", "baz"]} == ra


def test_fetch_inject_id() -> None:
    lower = lambda s: s.lower()
    if is_fs_case_sensitive(
        os.path.dirname(get_data("schema_salad/tests/inject-id1.yml"))
    ):
        lower = lambda a: a
    l1 = Loader({"id": "@id"})
    furi1 = file_uri(get_data("schema_salad/tests/inject-id1.yml"))
    r1, _ = l1.resolve_ref(furi1)
    assert {"id": furi1 + "#foo", "bar": "baz"} == r1
    assert [lower(furi1), lower(furi1 + "#foo")] == sorted(
        list(lower(k) for k in l1.idx.keys())
    )

    l2 = Loader({"id": "@id"})
    furi2 = file_uri(get_data("schema_salad/tests/inject-id2.yml"))
    r2, _ = l2.resolve_ref(furi2)
    assert {"id": furi2, "bar": "baz"} == r2
    assert [lower(furi2)] == sorted(list(lower(k) for k in l2.idx.keys()))

    l3 = Loader({"id": "@id"})
    furi3 = file_uri(get_data("schema_salad/tests/inject-id3.yml"))
    r3, _ = l3.resolve_ref(furi3)
    assert {"id": "http://example.com", "bar": "baz"} == r3
    assert [lower(furi3), "http://example.com"] == sorted(
        list(lower(k) for k in l3.idx.keys())
    )


def test_attachments() -> None:
    furi = file_uri(get_data("schema_salad/tests/multidoc.yml"))

    l1 = Loader({})
    r1, _ = l1.resolve_ref(furi)
    with open(get_data("schema_salad/tests/multidoc.yml"), "rt") as f:
        content = f.read()
        assert {"foo": "bar", "baz": content, "quux": content} == r1

    l2 = Loader({}, allow_attachments=lambda x: x["foo"] == "bar")
    r2, _ = l2.resolve_ref(furi)
    assert {
        "foo": "bar",
        "baz": "This is the {first attachment}.\n",
        "quux": "This is the [second attachment].",
    } == r2

    l3 = Loader({}, allow_attachments=lambda x: x["foo"] == "baz")
    r3, _ = l3.resolve_ref(furi)
    with open(get_data("schema_salad/tests/multidoc.yml"), "rt") as f:
        content = f.read()
        assert {"foo": "bar", "baz": content, "quux": content} == r3
