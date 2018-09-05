from __future__ import absolute_import, print_function

import json
import os
import unittest
from typing import Text

import rdflib
import ruamel.yaml as yaml
from six.moves import urllib

import schema_salad.main
import schema_salad.ref_resolver
import schema_salad.schema
from schema_salad.jsonld_context import makerdf


class TestFetcher(unittest.TestCase):
    def test_fetcher(self):
        class TestFetcher(schema_salad.ref_resolver.Fetcher):
            def __init__(self, a, b):
                pass

            def fetch_text(self, url):    # type: (Text) -> Text
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
                urlsp = urllib.parse.urlsplit(url)
                if urlsp.scheme:
                    return url
                basesp = urllib.parse.urlsplit(base)

                if basesp.scheme == "keep":
                    return base + "/" + url
                return urllib.parse.urljoin(base, url)

        loader = schema_salad.ref_resolver.Loader({}, fetcher_constructor=TestFetcher)
        self.assertEqual({"hello": "foo"}, loader.resolve_ref("foo.txt")[0])
        self.assertEqual({"hello": "keepfoo"}, loader.resolve_ref("foo.txt", base_url="keep:abc+123")[0])
        self.assertTrue(loader.check_exists("foo.txt"))

        with self.assertRaises(RuntimeError):
            loader.resolve_ref("bar.txt")
        self.assertFalse(loader.check_exists("bar.txt"))

    def test_cache(self):
        loader = schema_salad.ref_resolver.Loader({})
        foo = os.path.join(os.getcwd(), "foo.txt")
        foo = schema_salad.ref_resolver.file_uri(foo)
        loader.cache.update({foo: "hello: foo"})
        print(loader.cache)
        self.assertEqual({"hello": "foo"}, loader.resolve_ref("foo.txt")[0])
        self.assertTrue(loader.check_exists(foo))
