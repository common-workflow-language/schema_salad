import os
import sys
import urllib
import re
from typing import List, Optional

import requests

from .exceptions import ValidationException
from .utils import CacheType

_re_drive = re.compile(r"/([a-zA-Z]):")


class Fetcher(object):
    def __init__(
        self, cache: CacheType, session: Optional[requests.sessions.Session],
    ) -> None:
        pass

    def fetch_text(self, url: str) -> str:
        raise NotImplementedError()

    def check_exists(self, url: str) -> bool:
        raise NotImplementedError()

    def urljoin(self, base_url: str, url: str) -> str:
        raise NotImplementedError()

    schemes = ["file", "http", "https", "mailto"]

    def supported_schemes(self) -> List[str]:
        return self.schemes


class DefaultFetcher(Fetcher):
    def __init__(
        self, cache: CacheType, session: Optional[requests.sessions.Session],
    ) -> None:
        self.cache = cache
        self.session = session

    def fetch_text(self, url: str) -> str:
        if url in self.cache and self.cache[url] is not True:
            # treat "True" as a placeholder that indicates something exists but
            # not necessarily what its contents is.
            result = self.cache[url]
            assert isinstance(result, str)
            return result

        split = urllib.parse.urlsplit(url)
        scheme, path = split.scheme, split.path

        if scheme in ["http", "https"] and self.session is not None:
            try:
                resp = self.session.get(url)
                resp.raise_for_status()
            except Exception as e:
                raise ValidationException("Error fetching {}: {}".format(url, e)) from e
            return resp.text
        if scheme == "file":
            try:
                # On Windows, url.path will be /drive:/path ; on Unix systems,
                # /path. As we want drive:/path instead of /drive:/path on Windows,
                # remove the leading /.
                if os.path.isabs(
                    path[1:]
                ):  # checking if pathis valid after removing front / or not
                    path = path[1:]
                with open(
                    urllib.request.url2pathname(str(path)), encoding="utf-8"
                ) as fp:
                    return str(fp.read())

            except OSError as err:
                if err.filename == path:
                    raise ValidationException(str(err)) from err
                else:
                    raise ValidationException(
                        "Error reading {}: {}".format(url, err)
                    ) from err
        raise ValidationException("Unsupported scheme in url: {}".format(url))

    def check_exists(self, url: str) -> bool:
        if url in self.cache:
            return True

        split = urllib.parse.urlsplit(url)
        scheme, path = split.scheme, split.path

        if scheme in ["http", "https"] and self.session is not None:
            try:
                resp = self.session.head(url)
                resp.raise_for_status()
            except Exception:
                return False
            self.cache[url] = True
            return True
        if scheme == "file":
            return os.path.exists(urllib.request.url2pathname(str(path)))
        if scheme == "mailto":
            return True
        raise ValidationException("Unsupported scheme in url: {}".format(url))

    def urljoin(self, base_url: str, url: str) -> str:
        if url.startswith("_:"):
            return url

        basesplit = urllib.parse.urlsplit(base_url)
        split = urllib.parse.urlsplit(url)
        if basesplit.scheme and basesplit.scheme != "file" and split.scheme == "file":
            raise ValidationException(
                "Not resolving potential remote exploit {} from base {}".format(
                    url, base_url
                )
            )

        if sys.platform == "win32":
            if base_url == url:
                return url
            basesplit = urllib.parse.urlsplit(base_url)
            # note that below might split
            # "C:" with "C" as URI scheme
            split = urllib.parse.urlsplit(url)

            has_drive = split.scheme and len(split.scheme) == 1

            if basesplit.scheme == "file":
                # Special handling of relative file references on Windows
                # as urllib seems to not be quite up to the job

                # netloc MIGHT appear in equivalents of UNC Strings
                # \\server1.example.com\path as
                # file:///server1.example.com/path
                # https://tools.ietf.org/html/rfc8089#appendix-E.3.2
                # (TODO: test this)
                netloc = split.netloc or basesplit.netloc

                # Check if url is a local path like "C:/Users/fred"
                # or actually an absolute URI like http://example.com/fred
                if has_drive:
                    # Assume split.scheme is actually a drive, e.g. "C:"
                    # so we'll recombine into a path
                    path_with_drive = urllib.parse.urlunsplit(
                        (split.scheme, "", split.path, "", "")
                    )
                    # Compose new file:/// URI with path_with_drive
                    # .. carrying over any #fragment (?query just in case..)
                    return urllib.parse.urlunsplit(
                        ("file", netloc, path_with_drive, split.query, split.fragment)
                    )
                if (
                    not split.scheme
                    and not netloc
                    and split.path
                    and split.path.startswith("/")
                ):
                    # Relative - but does it have a drive?
                    base_drive = _re_drive.match(basesplit.path)
                    drive = _re_drive.match(split.path)
                    if base_drive and not drive:
                        # Keep drive letter from base_url
                        # https://tools.ietf.org/html/rfc8089#appendix-E.2.1
                        # e.g. urljoin("file:///D:/bar/a.txt", "/foo/b.txt")
                        #          == file:///D:/foo/b.txt
                        path_with_drive = "/{}:{}".format(
                            base_drive.group(1), split.path
                        )
                        return urllib.parse.urlunsplit(
                            (
                                "file",
                                netloc,
                                path_with_drive,
                                split.query,
                                split.fragment,
                            )
                        )

                # else: fall-through to resolve as relative URI
            elif has_drive:
                # Base is http://something but url is C:/something - which urllib
                # would wrongly resolve as an absolute path that could later be used
                # to access local files
                raise ValidationException(
                    "Not resolving potential remote exploit {} from base {}".format(
                        url, base_url
                    )
                )

        return urllib.parse.urljoin(base_url, url)
