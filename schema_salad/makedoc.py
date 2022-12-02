import argparse
import copy
import html
import logging
import os
import re
import sys
from io import StringIO, TextIOWrapper
from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    MutableMapping,
    MutableSequence,
    Optional,
    Set,
    Tuple,
    Union,
)
from urllib.parse import urldefrag

from mistune import create_markdown
from mistune.renderers import HTMLRenderer
from mistune.util import escape_html

from .exceptions import SchemaSaladException, ValidationException
from .schema import avro_field_name, extend_and_specialize, get_metaschema
from .utils import add_dictlist, aslist
from .validate import avro_type_name

if TYPE_CHECKING:
    # avoid import error since typing stubs do not exist in actual package
    from mistune import State
    from mistune.markdown import Markdown
    from mistune.plugins import PluginName

_logger = logging.getLogger("salad")


def vocab_type_name(url: str) -> str:
    """Remove the avro namespace, if any."""
    return avro_type_name(url).split(".")[-1]


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
    return f"[{frg}](#{to_id(frg)})"


class MyRenderer(HTMLRenderer):
    """Custom renderer with different representations of selected HTML tags."""

    def heading(self, text: str, level: int) -> str:
        """Override HTML heading creation with text IDs."""
        return (
            """<h{} id="{}" class="section">{} <a href="#{}">&sect;</a></h{}>""".format(
                level, to_id(text), text, to_id(text), level
            )
        )

    def text(self, text: str) -> str:
        """Don't escape quotation marks."""
        # avoid convert of & if already escaped
        text = html.unescape(text)
        # html.escape does both single/double quotes ('/")
        # mistune.util.escape does only double quotes
        return html.escape(text, quote=self._escape)

    def inline_html(self, html: str) -> str:
        """Don't escape characters in predefined HTML within paragraph tags."""
        return html + "\n"

    def block_html(self, html: str) -> str:
        """Don't escape characters nor wrap predefined HTML within paragraph tags."""
        return html + "\n"

    def block_code(self, code: str, info: Optional[str] = None) -> str:
        """Don't escape quotation marks."""
        text = "<pre><code"
        if info is not None:
            info = info.strip()
        if info:
            lang = info.split(None, 1)[0]
            lang = escape_html(lang)
            text += ' class="language-' + lang + '"'
        return text + ">" + html.escape(code, quote=self._escape) + "</code></pre>\n"


def markdown_list_hook(markdown, text, state):
    # type: (Markdown[str, Any], str, State) -> Tuple[str, State]
    """Patches problematic Markdown lists for later HTML generation.

    When a Markdown list with paragraphs not indented with the list
    markers (no spaces before following lines), ``mistune`` v2 does
    not handle them correctly. This is however permitted as per
    https://daringfireball.net/projects/markdown/syntax#list

    For example:

    ```markdown
    * some list
    * item with
    paragraph
    * other item
    ```

    Similarly, lists that are completely indented or that contains nested lists
    produce incorrect HTML ``<p>``/``<li>`` tag combinations.

    Because list parsing is deeply nested within ``mistune.block_parser.BlockParser``
    and that there is no easy way to override utility functions it employs to adjust
    patterns of list items without reimplementing it or a lot of monkey patching,
    instead catch the problem cases before rendering and adjust them with a hook.

    See https://github.com/lepture/mistune/issues/296
    and https://github.com/common-workflow-language/schema_salad/pull/619
    """
    pattern = re.compile(
        r"^"
        r"(?P<before>\n*)"  # detect newline to start capture on bullet line
        r"(?P<indent>\s*)"
        r"(?P<bullet>[0-9]+[.)]?|[*-])"
        r"(?P<spacing>\s+)"
        r"(?P<first_line>.*)"
        # if more than one empty line is found, end search (paragraph after list)
        r"(?!\n\s*\n\s*)"
        # otherwise, find all lines part of the same bullet item
        # if this bullet item is indented (nested list), match indents to collect
        # use negative lookahead to avoid over capturing following bullets
        r"(?P<other_lines>(?:\n\s*(?![0-9]+[.)]+|[*-])(?P=indent).*"
        r"(?!\n\s*\n\s*)"  # avoid match past list on last indented line
        r")+)*"  # end 'other_lines'
        # because of negative lookahead logic, there is sometimes a remaining
        # trailing character to capture on the last list item line
        r"(?P<remain>.*)",
        re.MULTILINE,
    )
    matches = list(re.finditer(pattern, text))
    if not matches:
        return text, state
    result = ""
    begin = 0
    for match in matches:
        start, end = match.start(), match.end()
        start += len(match.group("before"))
        result += text[begin:start]  # add text in between matched lists

        # process and indented list (de-indent, apply fixes, and re-indent)
        indent_prefix = match.group("indent")
        if indent_prefix:
            intend_list = text[start:end]
            intend_list = "\n".join(
                [
                    line.strip()
                    for line in intend_list.split("\n")
                    # mistune is having trouble understanding list items
                    # if they are separated by an additional line in between
                    # ignore empty lines to group items together,
                    # avoiding split into distinct list after injecting <p> tags
                    if line.strip()
                ]
            )
            intend_list, _ = markdown_list_hook(markdown, intend_list, state)
            # remove final newline from other if/else branch
            intend_list = intend_list.rstrip()
            intend_list = "\n".join(
                [indent_prefix + line for line in intend_list.split("\n")]
            )
            result += intend_list + "\n"
        # process a plain list
        # pad extra spaces to multi-lines items contents after bullet
        else:
            item = (
                match.group("indent") + match.group("bullet") + match.group("spacing")
            )
            result += item + match.group("first_line")
            indent = (
                "\n"
                + match.group("indent").split("\n")[-1]
                + (" " * len(match.group("bullet")))
                + match.group("spacing")
            )
            other = match.group("other_lines")
            if other:
                other = indent.join(
                    [
                        line.strip()
                        for line in other.split("\n")
                        # mistune is having trouble understanding list items
                        # if they are separated by an additional line in between
                        # ignore empty lines to group items together,
                        # avoiding split into distinct list after injecting <p> tags
                        if line.strip()
                    ]
                )
                # Add a single space to ensure words remain separated.
                # If we use newline/indent like in other lines above, mistune
                # splits the items into 2 lists. Although technically the Markdown
                # will have an extra space, spacing will be patched when generating
                # the HTML whether newline or space was used.
                if (
                    # only apply the extra space if items are actually
                    # 2 words to avoid incorrect split of compound words
                    # (e.g.: "key-value", not "key- value").
                    re.match(r".*[^-]$", result[-2:], re.I)
                    and re.match(r"^[^-].*", other[:2], re.I)
                ):
                    result += " "
                result += other
            result += match.group("remain") + "\n"

        begin = end + 1
    result += text[begin:]
    # Because lists regexes are designed to detect line-by-line bullets/paragraphs,
    # we cannot directly (or easily / with certainty) detect "list-like" encase in
    # fenced code definitions that could be much above/below the "list-like" items.
    # Instead, simply revert them after the fact with document-level matches of fenced codes.
    _logger.debug("Original Markdown:\n\n%s\n\n", text)
    _logger.debug("Modified Markdown:\n\n%s\n\n", result)
    result = patch_fenced_code(text, result)
    _logger.debug("Patched Markdown:\n\n%s\n\n", result)
    return result, state


def patch_fenced_code(original_markdown_text: str, modified_markdown_text: str) -> str:
    """
    Reverts fenced code fragments found in the modified contents back to their original definition.
    """
    # Pattern inspired from 'mistune.block_parser.BlockParser.FENCED_CODE'.
    # However, instead of the initial ' {0,3}' part to match any indented fenced-code,
    # use any quantity of spaces, as long as they match at the end as well (using '\1').
    # Because of nested fenced-code in lists, it can be more indented than "normal".
    fenced_code_pattern = re.compile(
        r"( *)(`{3,}|~{3,})([^`\n]*)\n(?:|([\s\S]*?)\n)(?:\1\2[~`]* *\n+|$)"
    )
    matches_original = list(re.finditer(fenced_code_pattern, original_markdown_text))
    matches_modified = list(re.finditer(fenced_code_pattern, modified_markdown_text))
    if len(matches_original) != len(matches_modified):
        raise ValueError(
            "Cannot patch fenced code definitions with inconsistent matches."
        )
    result = ""
    begin = 0
    for original, modified in zip(matches_original, matches_modified):
        ori_s, ori_e = original.start(), original.end()
        mod_s, mod_e = modified.start(), modified.end()
        result += modified_markdown_text[begin:mod_s]  # add text in between matches
        result += original_markdown_text[ori_s:ori_e]  # revert the fenced code
        begin = mod_e  # skip over the modified fenced code for next match
    result += modified_markdown_text[begin:]  # left over text after last match
    return result


def to_id(text: str) -> str:
    textid = text
    if text[0] in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"):
        try:
            textid = text[text.index(" ") + 1 :]
        except ValueError:
            pass
    return textid.replace(" ", "_")


class ToC:
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
                assert group1 is not None  # nosec
                group2 = m.group(2)
                assert group2 is not None  # nosec
                num = toc.add_entry(len(group1), group2)
                line = f"{group1} {num} {group2}"
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


class RenderType:
    def __init__(
        self,
        toc: ToC,
        j: List[Dict[str, Any]],
        renderlist: List[str],
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

        metaschema_loader = get_metaschema()[2]
        alltypes = extend_and_specialize(j, metaschema_loader)

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
        jsonldPredicate: Optional[Union[Dict[str, str], str]] = None,
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
                if (
                    isinstance(jsonldPredicate, dict)
                    and "mapSubject" in jsonldPredicate
                ):
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
                frg = vocab_type_name(tp["name"])
                if tp["name"] in redirects:
                    return """<a href="{}">{}</a>""".format(redirects[tp["name"]], frg)
                if tp["name"] in self.typemap:
                    return f"""<a href="#{to_id(frg)}">{frg}</a>"""
                if (
                    tp["type"] == "https://w3id.org/cwl/salad#enum"
                    and len(tp["symbols"]) == 1
                ):
                    return "constant value <code>{}</code>".format(
                        avro_field_name(tp["symbols"][0])
                    )
                return frg
            if isinstance(tp["type"], MutableMapping):
                return self.typefmt(tp["type"], redirects)
        else:
            if str(tp) in redirects:
                return f"""<a href="{redirects[tp]}">{redirects[tp]}</a>"""
            if str(tp) in basicTypes:
                return """<a href="{}">{}</a>""".format(
                    self.primitiveType, vocab_type_name(str(tp))
                )
            frg2 = urldefrag(tp)[1]
            if frg2 != "":
                tp = frg2
            return f"""<a href="#{to_id(tp)}">{tp}</a>"""
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

        # Save the first line of the first type definition for the
        # HTML <title> tag
        if self.title is None and f["doc"]:
            self.title = f["doc"].partition("\n")[0]
            if self.title.startswith("# "):
                self.title = self.title[2:]

        if f["type"] == "documentation":
            f["doc"] = number_headings(self.toc, f["doc"])

        doc = doc + "\n\n" + f["doc"]
        plugins = [
            "strikethrough",
            "footnotes",
            "table",
            "url",
        ]  # type: List[PluginName]  # fix error Generic str != explicit Literals
        # if escape active, wraps literal HTML into '<p> {HTML} </p>'
        # we must pass it to both since 'MyRenderer' is predefined
        escape = False
        markdown2html = create_markdown(
            renderer=MyRenderer(escape=escape),
            plugins=plugins,
            escape=escape,
        )  # type: Markdown[str, Any]
        markdown2html.before_parse_hooks.append(markdown_list_hook)
        doc = markdown2html(doc)

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

                rfrg = avro_field_name(i["name"])
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
                    markdown2html(desc),
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
                    efrg = avro_field_name(i)
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
    outdoc: IO[Any],
    renderlist: List[str],
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
            "https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css"
        )
        bootstrap_integrity = (
            "sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC"
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

    outdoc.write(f"<title>{rt.title}</title>")

    outdoc.write(
        """
    <style>
    :target {
      padding-top: 61px;
      margin-top: -61px;
    }
    .tocnav ol {
      list-style: none
    }
    pre {
      margin: 0 2em 10px 2em;
      padding: 9.5px;
      line-height: 1.42857143;
      color: #333;
      word-break: break-all;
      word-wrap: break-word;
      background-color: #f5f5f5;
      border: 1px solid #ccc;
      border-radius: 4px;
    }
    pre code {
      padding: 0;
      font-size: inherit;
      color: inherit;
      white-space: pre-wrap;
      background-color: transparent;
      border-radius: 0;
    }
    code {
      background-color: #f9f2f4;
      border-radius: 4px;
      padding: 2px 4px;
      color: #c7254e;
    }
    blockquote {
      padding: 10px 20px 1px 20px;
      border-left: 5px solid #eee;
    }
    a {
      text-decoration: none;
    }
    a code {
      color: #c7254e;
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
      <nav class="navbar sticky-top navbar-expand-lg navbar-light bg-light {}">
        <div class="container">
          <a class="navbar-brand" href="{}">{}</a>
    """.format(
            navbar_extraclass, brandlink, brand
        )
    )

    if "<!--ToC-->" in content:
        content = content.replace("<!--ToC-->", toc.contents("toc"))
        outdoc.write(
            """
              <ul class="navbar-nav me-auto">
                <li class="nav-item"><a class="nav-link" href="#toc">Table of contents</a></li>
              </ul>
        """
        )

    outdoc.write(
        """
        </div>
      </nav>
    """
    )

    outdoc.write(
        """
    <div class="container mt-4">
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


def arg_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument("schema")
    parser.add_argument("--only", action="append")
    parser.add_argument("--redirect", action="append")
    parser.add_argument("--brand")
    parser.add_argument("--brandlink")
    parser.add_argument("--brandstyle")
    parser.add_argument("--brandinverse", default=False, action="store_true")
    parser.add_argument("--primtype", default="#PrimitiveType")
    parser.add_argument("--debug", action="store_true")
    return parser


def main() -> None:
    """Shortcut entrypoint."""
    args = arg_parser().parse_args()
    if args.debug:
        _logger.setLevel(logging.DEBUG)
    makedoc(
        sys.stdout,
        args.schema,
        args.redirect,
        args.only,
        args.brand,
        args.brandlink,
        args.primtype,
        args.brandstyle,
        args.brandinverse,
    )


def makedoc(
    stdout: IO[Any],
    schema: str,
    redirects: Optional[List[str]] = None,
    only: Optional[List[str]] = None,
    brand: Optional[str] = None,
    brandlink: Optional[str] = None,
    primtype: Optional[str] = None,
    brandstyle: Optional[str] = None,
    brandinverse: Optional[bool] = False,
) -> None:
    """Emit HTML representation of a given schema."""
    s: List[Dict[str, Any]] = []
    with open(schema, encoding="utf-8") as f:
        if schema.endswith("md"):
            s.append(
                {
                    "name": os.path.splitext(os.path.basename(schema))[0],
                    "type": "documentation",
                    "doc": f.read(),
                }
            )
        else:
            uri = "file://" + os.path.abspath(schema)
            metaschema_loader = get_metaschema()[2]
            j = metaschema_loader.resolve_ref(uri, "")[0]
            if isinstance(j, MutableSequence):
                s.extend(j)
            elif isinstance(j, MutableMapping):
                s.append(j)
            else:
                raise ValidationException("Schema must resolve to a list or a dict")
    redirect = {}
    for r in redirects or []:
        redirect[r.split("=")[0]] = r.split("=")[1]
    renderlist = only or []
    if hasattr(stdout, "buffer") and getattr(stdout, "encoding", None) != "UTF-8":
        wrapped_stdout: IO[Any] = TextIOWrapper(stdout.buffer, encoding="utf-8")
    else:
        wrapped_stdout = stdout
    avrold_doc(
        s,
        wrapped_stdout,
        renderlist,
        redirect,
        brand or "",
        brandlink or "",
        primtype or "",
        brandstyle=brandstyle,
        brandinverse=brandinverse,
    )


if __name__ == "__main__":
    main()
