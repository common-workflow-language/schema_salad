import os

import pytest  # type: ignore

import schema_salad.main
import schema_salad.ref_resolver
import schema_salad.schema

from .other_fetchers import testFetcher


def test_fetcher() -> None:

    loader = schema_salad.ref_resolver.Loader({}, fetcher_constructor=testFetcher)
    assert {"hello": "foo"} == loader.resolve_ref("foo.txt")[0]
    assert {"hello": "keepfoo"} == loader.resolve_ref(
        "foo.txt", base_url="keep:abc+123"
    )[0]
    assert loader.check_exists("foo.txt")

    with pytest.raises(RuntimeError):
        loader.resolve_ref("bar.txt")
    assert not loader.check_exists("bar.txt")


def test_cache() -> None:
    loader = schema_salad.ref_resolver.Loader({})
    foo = os.path.join(os.getcwd(), "foo.txt")
    foo = schema_salad.ref_resolver.file_uri(foo)
    loader.cache.update({foo: "hello: foo"})
    print(loader.cache)
    assert {"hello": "foo"} == loader.resolve_ref("foo.txt")[0]
    assert loader.check_exists(foo)
