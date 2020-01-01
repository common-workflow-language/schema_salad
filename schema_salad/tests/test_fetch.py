import os
from typing import Text
from urllib.parse import urljoin, urlsplit

import pytest

import schema_salad.main
import schema_salad.ref_resolver
import schema_salad.schema


def test_fetcher():
    class TestFetcher(schema_salad.ref_resolver.Fetcher):
        def __init__(self, a, b):
            pass

        def fetch_text(self, url):  # type: (Text) -> Text
            if url == "keep:abc+123/foo.txt":
                return "hello: keepfoo"
            if url.endswith("foo.txt"):
                return "hello: foo"
            else:
                raise RuntimeError("Not foo.txt")

        def check_exists(self, url):  # type: (Text) -> bool
            if url.endswith("foo.txt"):
                return True
            else:
                return False

        def urljoin(self, base, url):
            urlsp = urlsplit(url)
            if urlsp.scheme:
                return url
            basesp = urlsplit(base)

            if basesp.scheme == "keep":
                return base + "/" + url
            return urljoin(base, url)

    loader = schema_salad.ref_resolver.Loader({}, fetcher_constructor=TestFetcher)
    assert {"hello": "foo"} == loader.resolve_ref("foo.txt")[0]
    assert {"hello": "keepfoo"} == loader.resolve_ref(
        "foo.txt", base_url="keep:abc+123"
    )[0]
    assert loader.check_exists("foo.txt")

    with pytest.raises(RuntimeError):
        loader.resolve_ref("bar.txt")
    assert not loader.check_exists("bar.txt")


def test_cache():
    loader = schema_salad.ref_resolver.Loader({})
    foo = os.path.join(os.getcwd(), "foo.txt")
    foo = schema_salad.ref_resolver.file_uri(foo)
    loader.cache.update({foo: "hello: foo"})
    print(loader.cache)
    assert {"hello": "foo"} == loader.resolve_ref("foo.txt")[0]
    assert loader.check_exists(foo)
