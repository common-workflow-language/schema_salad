from typing import Optional
from urllib.parse import urljoin, urlsplit

import requests

import schema_salad.ref_resolver


class testFetcher(schema_salad.ref_resolver.Fetcher):
    def __init__(
        self,
        cache: schema_salad.ref_resolver.CacheType,
        session: Optional[requests.sessions.Session],
    ) -> None:
        pass

    def fetch_text(self, url: str) -> str:
        if url == "keep:abc+123/foo.txt":
            return "hello: keepfoo"
        if url.endswith("foo.txt"):
            return "hello: foo"
        else:
            raise RuntimeError("Not foo.txt")

    def check_exists(self, url: str) -> bool:
        if url.endswith("foo.txt"):
            return True
        else:
            return False

    def urljoin(self, base: str, url: str) -> str:
        urlsp = urlsplit(url)
        if urlsp.scheme:
            return url
        basesp = urlsplit(base)

        if basesp.scheme == "keep":
            return base + "/" + url
        return urljoin(base, url)


class CWLTestFetcher(schema_salad.ref_resolver.Fetcher):
    def __init__(
        self,
        cache: schema_salad.ref_resolver.CacheType,
        session: Optional[requests.sessions.Session],
    ) -> None:
        pass

    def fetch_text(self, url):  # type: (str) -> str
        if url == "baz:bar/foo.cwl":
            return """
cwlVersion: v1.0
class: CommandLineTool
baseCommand: echo
inputs: []
outputs: []
"""
        raise RuntimeError("Not foo.cwl, was %s" % url)

    def check_exists(self, url):  # type: (str) -> bool
        return url == "baz:bar/foo.cwl"

    def urljoin(self, base: str, url: str) -> str:
        urlsp = urlsplit(url)
        if urlsp.scheme:
            return url
        basesp = urlsplit(base)

        if basesp.scheme == "keep":
            return base + "/" + url
        return urljoin(base, url)
