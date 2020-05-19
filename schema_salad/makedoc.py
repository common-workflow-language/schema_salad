import argparse
import copy
import logging
import os
import re
import sys
from codecs import StreamWriter
from io import StringIO, TextIOWrapper, open
from typing import (
    IO,
    Any,
    Dict,
    List,
    MutableMapping,
    MutableSequence,
    Optional,
    Set,
    Tuple,
    Union,
    cast,
)
from urllib.parse import urldefrag

import mistune

from . import schema
from .exceptions import SchemaSaladException, ValidationException
from .utils import add_dictlist, aslist

_logger = logging.getLogger("salad")


def has_types(items: Any) -> List[str]:
    r = []  # type: List[str]
    if isinstance(items, MutableMapping):
        if items["type"] == "https://w3id.org/cwl/salad#record":
            return [items["name"]]
        for n in ("type", "items", "values"):
            if n in items:
                r.extend(has_types(items[n]))
        return r
    if isinstance(items, MutableSequence):
        for i in items:
            r.extend(has_types(i))
        return r
    if isinstance(items, str):
        return [items]
    return []


def linkto(item: str) -> str:
    frg = urldefrag(item)[1]
    return "[{}](#{})".format(frg, to_id(frg))


class MyRenderer(mistune.Renderer):
    def __init__(self) -> None:
        super(MyRenderer, self).__init__()
        self.options = {}

    def header(self, text: str, level: int, raw: Optional[Any] = None) -> str:
        return """<h{} id="{}" class="section">{} <a href="#{}">&sect;</a></h{}>""".format(
            level, to_id(text), text, to_id(text), level
        )

    def table(self, header: str, body: str) -> str:
        return (
            '<table class="table table-striped">\n<thead>{}</thead>\n'
            "<tbody>\n{}</tbody>\n</table>\n"
        ).format(header, body)


def to_id(text: str) -> str:
    textid = text
    if text[0] in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"):
        try:
            textid = text[text.index(" ") + 1 :]
        except ValueError:
            pass
    return textid.replace(" ", "_")


class ToC(object):
    def __init__(self) -> None:
        self.first_toc_entry = True
        self.numbering = [0]
        self.toc = ""
        self.start_numbering = True

    def add_entry(self, thisdepth, title):  # type: (int, str) -> str
        depth = len(self.numbering)
        if thisdepth < depth:
            self.toc += "</ol>"
            for _ in range(0, depth - thisdepth):
                self.numbering.pop()
                self.toc += "</li></ol>"
            self.numbering[-1] += 1
        elif thisdepth == depth:
            if not self.first_toc_entry:
                self.toc += "</ol>"
            else:
                self.first_toc_entry = False
            self.numbering[-1] += 1
        elif thisdepth > depth:
            self.numbering.append(1)

        num = (
            "{}.{}".format(
                self.numbering[0], ".".join([str(n) for n in self.numbering[1:]])
            )
            if self.start_numbering
            else ""
        )
        self.toc += """<li><a href="#{}">{} {}</a><ol>\n""".format(
            to_id(title), num, title
        )
        return num

    def contents(self, idn: str) -> str:
        toc = """<h1 id="{}">Table of contents</h1>
               <nav class="tocnav"><ol>{}""".format(
            idn, self.toc
        )
        toc += "</ol>"
        for _ in range(0, len(self.numbering)):
            toc += "</li></ol>"
        toc += """</nav>"""
        return toc


basicTypes = (
    "https://w3id.org/cwl/salad#null",
    "http://www.w3.org/2001/XMLSchema#boolean",
    "http://www.w3.org/2001/XMLSchema#int",
    "http://www.w3.org/2001/XMLSchema#long",
    "http://www.w3.org/2001/XMLSchema#float",
    "http://www.w3.org/2001/XMLSchema#double",
    "http://www.w3.org/2001/XMLSchema#string",
    "https://w3id.org/cwl/salad#record",
    "https://w3id.org/cwl/salad#enum",
    "https://w3id.org/cwl/salad#array",
)


def number_headings(toc: ToC, maindoc: str) -> str:
    mdlines = []
    skip = False
    for line in maindoc.splitlines():
        if line.strip() == "# Introduction":
            toc.start_numbering = True
            toc.numbering.clear()
            toc.numbering.append(0)

        if "```" in line:
            skip = not skip

        if not skip:
            m = re.match(r"^(#+) (.*)", line)
            if m is not None:
                group1 = m.group(1)
                assert group1 is not None
                group2 = m.group(2)
                assert group2 is not None
                num = toc.add_entry(len(group1), group2)
                line = "{} {} {}".format(group1, num, group2)
            line = re.sub(r"^(https?://\S+)", r"[\1](\1)", line)
        mdlines.append(line)

    maindoc = "\n".join(mdlines)
    return maindoc


def fix_doc(doc: Union[List[str], str]) -> str:
    docstr = "".join(doc) if isinstance(doc, MutableSequence) else doc
    return "\n".join(
        [
            re.sub(r"<([^>@]+@[^>]+)>", r"[\1](mailto:\1)", d)
            for d in docstr.splitlines()
        ]
    )


class RenderType(object):
    def __init__(
        self,
        toc: ToC,
        j: List[Dict[str, str]],
        renderlist: str,
        redirects: Dict[str, str],
        primitiveType: str,
    ) -> None:
        self.typedoc = StringIO()
        self.toc = toc
        self.subs = {}  # type: Dict[str, str]
        self.docParent = {}  # type: Dict[str, List[str]]
        self.docAfter = {}  # type: Dict[str, List[str]]
        self.rendered = set()  # type: Set[str]
        self.redirects = redirects
        self.title = None  # type: Optional[str]
        self.primitiveType = primitiveType

        for t in j:
            if "extends" in t:
                for e in aslist(t["extends"]):
                    add_dictlist(self.subs, e, t["name"])
                    # if "docParent" not in t and "docAfter" not in t:
                    #    add_dictlist(self.docParent, e, t["name"])

            if t.get("docParent"):
                add_dictlist(self.docParent, t["docParent"], t["name"])

            if t.get("docChild"):
                for c in aslist(t["docChild"]):
                    add_dictlist(self.docParent, t["name"], c)

            if t.get("docAfter"):
                add_dictlist(self.docAfter, t["docAfter"], t["name"])

        metaschema_loader = schema.get_metaschema()[2]
        alltypes = schema.extend_and_specialize(j, metaschema_loader)

        self.typemap = {}  # type: Dict[str, Dict[str, str]]
        self.uses = {}  # type: Dict[str, List[Tuple[str, str]]]
        self.record_refs = {}  # type: Dict[str, List[str]]
        for entry in alltypes:
            self.typemap[entry["name"]] = entry
            try:
                if entry["type"] == "record":
                    self.record_refs[entry["name"]] = []
                    fields = entry.get(
                        "fields", []
                    )  # type: Union[str, List[Dict[str, str]]]
                    if isinstance(fields, str):
                        raise KeyError("record fields must be a list of mappings")
                    for f in fields:  # type: Dict[str, str]
                        p = has_types(f)
                        for tp in p:
                            if tp not in self.uses:
                                self.uses[tp] = []
                            if (entry["name"], f["name"]) not in self.uses[tp]:
                                _, frg1 = urldefrag(t["name"])
                                _, frg2 = urldefrag(f["name"])
                                self.uses[tp].append((frg1, frg2))
                            if (
                                tp not in basicTypes
                                and tp not in self.record_refs[entry["name"]]
                            ):
                                self.record_refs[entry["name"]].append(tp)
            except KeyError:
                _logger.error("Did not find 'type' in %s", t)
                _logger.error("record refs is %s", self.record_refs)
                raise

        for entry in alltypes:
            if entry["name"] in renderlist or (
                (not renderlist)
                and ("extends" not in entry)
                and ("docParent" not in entry)
                and ("docAfter" not in entry)
            ):
                self.render_type(entry, 1)

    def typefmt(
        self,
        tp: Any,
        redirects: Dict[str, str],
        nbsp: bool = False,
        jsonldPredicate: Optional[Dict[str, str]] = None,
    ) -> str:
        if isinstance(tp, MutableSequence):
            if nbsp and len(tp) <= 3:
                return "&nbsp;|&nbsp;".join(
                    [
                        self.typefmt(n, redirects, jsonldPredicate=jsonldPredicate)
                        for n in tp
                    ]
                )
            return " | ".join(
                [
                    self.typefmt(n, redirects, jsonldPredicate=jsonldPredicate)
                    for n in tp
                ]
            )
        if isinstance(tp, MutableMapping):
            if tp["type"] == "https://w3id.org/cwl/salad#array":
                ar = "array&lt;{}&gt;".format(
                    self.typefmt(tp["items"], redirects, nbsp=True)
                )
                if jsonldPredicate is not None and "mapSubject" in jsonldPredicate:
                    if "mapPredicate" in jsonldPredicate:
                        ar += " | "
                        if len(ar) > 40:
                            ar += "<br>"

                        ar += (
                            "<a href='#map'>map</a>&lt;<code>{}</code>"
                            ",&nbsp;<code>{}</code> | {}&gt".format(
                                jsonldPredicate["mapSubject"],
                                jsonldPredicate["mapPredicate"],
                                self.typefmt(tp["items"], redirects),
                            )
                        )
                    else:
                        ar += " | "
                        if len(ar) > 40:
                            ar += "<br>"
                        ar += "<a href='#map'>map</a>&lt;<code>{}</code>,&nbsp;{}&gt".format(
                            jsonldPredicate["mapSubject"],
                            self.typefmt(tp["items"], redirects),
                        )
                return ar
            if tp["type"] in (
                "https://w3id.org/cwl/salad#record",
                "https://w3id.org/cwl/salad#enum",
            ):
                frg = schema.avro_name(tp["name"])
                if tp["name"] in redirects:
                    return """<a href="{}">{}</a>""".format(redirects[tp["name"]], frg)
                if tp["name"] in self.typemap:
                    return """<a href="#{}">{}</a>""".format(to_id(frg), frg)
                if (
                    tp["type"] == "https://w3id.org/cwl/salad#enum"
                    and len(tp["symbols"]) == 1
                ):
                    return "constant value <code>{}</code>".format(
                        schema.avro_name(tp["symbols"][0])
                    )
                return frg
            if isinstance(tp["type"], MutableMapping):
                return self.typefmt(tp["type"], redirects)
        else:
            if str(tp) in redirects:
                return """<a href="{}">{}</a>""".format(redirects[tp], redirects[tp])
            if str(tp) in basicTypes:
                return """<a href="{}">{}</a>""".format(
                    self.primitiveType, schema.avro_name(str(tp))
                )
            frg2 = urldefrag(tp)[1]
            if frg2 != "":
                tp = frg2
            return """<a href="#{}">{}</a>""".format(to_id(tp), tp)
        raise SchemaSaladException("We should not be here!")

    def render_type(self, f: Dict[str, Any], depth: int) -> None:
        if f["name"] in self.rendered or f["name"] in self.redirects:
            return
        self.rendered.add(f["name"])

        if f.get("abstract"):
            return

        if "doc" not in f:
            f["doc"] = ""

        f["type"] = copy.deepcopy(f)
        f["doc"] = ""
        f = f["type"]

        if "doc" not in f:
            f["doc"] = ""

        def extendsfrom(item: Dict[str, Any], ex: List[Dict[str, Any]]) -> None:
            if "extends" in item:
                for e in aslist(item["extends"]):
                    ex.insert(0, self.typemap[e])
                    extendsfrom(self.typemap[e], ex)

        ex = [f]
        extendsfrom(f, ex)

        enumDesc = {}
        if f["type"] == "enum" and isinstance(f["doc"], MutableSequence):
            for e in ex:
                for i in e["doc"]:
                    idx = i.find(":")
                    if idx > -1:
                        enumDesc[i[:idx]] = i[idx + 1 :]
                e["doc"] = [
                    i
                    for i in e["doc"]
                    if i.find(":") == -1 or i.find(" ") < i.find(":")
                ]

        f["doc"] = fix_doc(f["doc"])

        if f["type"] == "record":
            for field in f.get("fields", []):
                if "doc" not in field:
                    field["doc"] = ""

        if f["type"] != "documentation":
            lines = []
            for line in f["doc"].splitlines():
                if len(line) > 0 and line[0] == "#":
                    line = ("#" * depth) + line
                lines.append(line)
            f["doc"] = "\n".join(lines)

            frg = urldefrag(f["name"])[1]
            num = self.toc.add_entry(depth, frg)
            doc = "{} {} {}\n".format(("#" * depth), num, frg)
        else:
            doc = ""

        if self.title is None and f["doc"]:
            title = f["doc"][0 : f["doc"].index("\n")]
            if title.startswith("# "):
                self.title = title[2:]
            else:
                self.title = title

        if f["type"] == "documentation":
            f["doc"] = number_headings(self.toc, f["doc"])

        doc = doc + "\n\n" + f["doc"]

        doc = mistune.markdown(doc, renderer=MyRenderer())

        if f["type"] == "record":
            doc += "<h3>Fields</h3>"
            doc += """
<div class="responsive-table">
<div class="row responsive-table-header">
<div class="col-xs-3 col-lg-2">field</div>
<div class="col-xs-2 col-lg-1">required</div>
<div class="col-xs-7 col-lg-3">type</div>
<div class="col-xs-12 col-lg-6 description-header">description</div>
</div>"""
            required = []
            optional = []
            for i in f.get("fields", []):
                tp = i["type"]
                if (
                    isinstance(tp, MutableSequence)
                    and tp[0] == "https://w3id.org/cwl/salad#null"
                ):
                    opt = False
                    tp = tp[1:]
                else:
                    opt = True

                desc = i["doc"]

                rfrg = schema.avro_name(i["name"])
                tr = """
<div class="row responsive-table-row">
<div class="col-xs-3 col-lg-2"><code>{}</code></div>
<div class="col-xs-2 col-lg-1">{}</div>
<div class="col-xs-7 col-lg-3">{}</div>
<div class="col-xs-12 col-lg-6 description-col">{}</div>
</div>""".format(
                    rfrg,
                    "required" if opt else "optional",
                    self.typefmt(
                        tp, self.redirects, jsonldPredicate=i.get("jsonldPredicate")
                    ),
                    mistune.markdown(desc),
                )
                if opt:
                    required.append(tr)
                else:
                    optional.append(tr)
            for i in required + optional:
                doc += i
            doc += """</div>"""
        elif f["type"] == "enum":
            doc += "<h3>Symbols</h3>"
            doc += """<table class="table table-striped">"""
            doc += "<tr><th>symbol</th><th>description</th></tr>"
            for e in ex:
                for i in e.get("symbols", []):
                    doc += "<tr>"
                    efrg = schema.avro_name(i)
                    doc += "<td><code>{}</code></td><td>{}</td>".format(
                        efrg, enumDesc.get(efrg, "")
                    )
                    doc += "</tr>"
            doc += """</table>"""
        f["doc"] = doc

        self.typedoc.write(f["doc"])

        subs = self.docParent.get(f["name"], []) + self.record_refs.get(f["name"], [])
        if len(subs) == 1:
            self.render_type(self.typemap[subs[0]], depth)
        else:
            for s in subs:
                self.render_type(self.typemap[s], depth + 1)

        for s in self.docAfter.get(f["name"], []):
            self.render_type(self.typemap[s], depth)


def avrold_doc(
    j: List[Dict[str, Any]],
    outdoc: Union[IO[Any], StreamWriter],
    renderlist: str,
    redirects: Dict[str, str],
    brand: str,
    brandlink: str,
    primtype: str,
    brandstyle: Optional[str] = None,
    brandinverse: Optional[bool] = False,
) -> None:
    toc = ToC()
    toc.start_numbering = False

    rt = RenderType(toc, j, renderlist, redirects, primtype)
    content = rt.typedoc.getvalue()

    if brandstyle is None:
        bootstrap_url = (
            "https://maxcdn.bootstrapcdn.com/bootstrap/3.3.4/css/bootstrap.min.css"
        )
        bootstrap_integrity = (
            "sha384-604wwakM23pEysLJAhja8Lm42IIwYrJ0dEAqzFsj9pJ/P5buiujjywArgPCi8eoz"
        )
        brandstyle_template = (
            '<link rel="stylesheet" href={} integrity={} crossorigin="anonymous">'
        )
        brandstyle = brandstyle_template.format(bootstrap_url, bootstrap_integrity)

    picturefill_url = (
        "https://cdn.rawgit.com/scottjehl/picturefill/3.0.2/dist/picturefill.min.js"
    )
    picturefill_integrity = (
        "sha384-ZJsVW8YHHxQHJ+SJDncpN90d0EfAhPP+yA94n+EhSRzhcxfo84yMnNk+v37RGlWR"
    )
    outdoc.write(
        """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {}
    <script>
    // Picture element HTML5 shiv
    document.createElement( "picture" );
    </script>
    <script src="{}"
        integrity="{}"
        crossorigin="anonymous" async></script>
    """.format(
            brandstyle, picturefill_url, picturefill_integrity
        )
    )

    outdoc.write("<title>{}</title>".format(rt.title))

    outdoc.write(
        """
    <style>
    :target {
      padding-top: 61px;
      margin-top: -61px;
    }
    body {
      padding-top: 61px;
    }
    .tocnav ol {
      list-style: none
    }
    pre {
      margin-left: 2em;
      margin-right: 2em;
    }
    .section a {
      visibility: hidden;
    }
    .section:hover a {
      visibility: visible;
      color: rgb(201, 201, 201);
    }
    .responsive-table-header {
      text-align: left;
      padding: 8px;
      vertical-align: top;
      font-weight: bold;
      border-top-color: rgb(221, 221, 221);
      border-top-style: solid;
      border-top-width: 1px;
      background-color: #f9f9f9
    }
    .responsive-table > .responsive-table-row {
      text-align: left;
      padding: 8px;
      vertical-align: top;
      border-top-color: rgb(221, 221, 221);
      border-top-style: solid;
      border-top-width: 1px;
    }
    @media (min-width: 0px), print {
      .description-header {
        display: none;
      }
      .description-col {
        margin-top: 1em;
        margin-left: 1.5em;
      }
    }
    @media (min-width: 1170px) {
      .description-header {
        display: inline;
      }
      .description-col {
        margin-top: 0px;
        margin-left: 0px;
      }
    }
    .responsive-table-row:nth-of-type(odd) {
       background-color: #f9f9f9
    }
    </style>
    </head>
    <body>
    """
    )

    navbar_extraclass = "navbar-inverse" if brandinverse else ""
    outdoc.write(
        """
      <nav class="navbar navbar-default navbar-fixed-top {}">
        <div class="container">
          <div class="navbar-header">
            <a class="navbar-brand" href="{}">{}</a>
    """.format(
            navbar_extraclass, brandlink, brand
        )
    )

    if "<!--ToC-->" in content:
        content = content.replace("<!--ToC-->", toc.contents("toc"))
        outdoc.write(
            """
                <ul class="nav navbar-nav">
                  <li><a href="#toc">Table of contents</a></li>
                </ul>
        """
        )

    outdoc.write(
        """
          </div>
        </div>
      </nav>
    """
    )

    outdoc.write(
        """
    <div class="container">
    """
    )

    outdoc.write(
        """
    <div class="row">
    """
    )

    outdoc.write(
        """
    <div class="col-md-12" role="main" id="main">"""
    )

    outdoc.write(content)

    outdoc.write("""</div>""")

    outdoc.write(
        """
    </div>
    </div>
    </body>
    </html>"""
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("schema")
    parser.add_argument("--only", action="append")
    parser.add_argument("--redirect", action="append")
    parser.add_argument("--brand")
    parser.add_argument("--brandlink")
    parser.add_argument("--brandstyle")
    parser.add_argument("--brandinverse", default=False, action="store_true")
    parser.add_argument("--primtype", default="#PrimitiveType")

    args = parser.parse_args()

    makedoc(args)


def makedoc(args: argparse.Namespace) -> None:

    s = []  # type: List[Dict[str, Any]]
    a = args.schema
    with open(a, encoding="utf-8") as f:
        if a.endswith("md"):
            s.append(
                {
                    "name": os.path.splitext(os.path.basename(a))[0],
                    "type": "documentation",
                    "doc": f.read(),
                }
            )
        else:
            uri = "file://" + os.path.abspath(a)
            metaschema_loader = schema.get_metaschema()[2]
            j = metaschema_loader.resolve_ref(uri, "")[0]
            if isinstance(j, MutableSequence):
                s.extend(j)
            elif isinstance(j, MutableMapping):
                s.append(j)
            else:
                raise ValidationException("Schema must resolve to a list or a dict")
    redirect = {}
    for r in args.redirect or []:
        redirect[r.split("=")[0]] = r.split("=")[1]
    renderlist = args.only if args.only else []
    stdout = (
        TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        if sys.stdout.encoding != "UTF-8"
        else cast(TextIOWrapper, sys.stdout)
    )  # type: Union[TextIOWrapper, StreamWriter]
    avrold_doc(
        s,
        stdout,
        renderlist,
        redirect,
        args.brand,
        args.brandlink,
        args.primtype,
        brandstyle=args.brandstyle,
        brandinverse=args.brandinverse,
    )


if __name__ == "__main__":
    main()
