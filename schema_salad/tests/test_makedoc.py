"""
Test schema-salad-doc.

(also known as schema-salad-tool --print-doc)

For convenience, tests are checking exact strings. In the event of changes in
the "mistune" package, makedoc.py, or other changes, feel free to modify the test
strings as long as the new HTML renders the same way in typical browsers.

Likewise, if the schema-salad metaschema changes and it is missing one or more
of the features tested below, then please copy those old features to a new file
and update the affected tests to use those new file(s).
"""

import hashlib
from io import StringIO

import pytest

from schema_salad.makedoc import makedoc

from .util import get_data


def test_schema_salad_inherit_docs() -> None:
    """Test schema-salad-doc when types inherit and override values from parent types."""
    schema_path = get_data("tests/inherited-attributes.yml")
    assert schema_path
    stdout = StringIO()
    makedoc(stdout, schema_path)

    # The parent ID documentation (i.e. Parent ID) must appear exactly once.
    assert 1 == stdout.getvalue().count("Parent ID")


@pytest.fixture
def metaschema_doc() -> str:
    """Pytest Fixture of the rendered HTML for the metaschema schema."""
    schema_path = get_data("schema_salad/metaschema/metaschema.yml")
    assert schema_path
    stdout = StringIO()
    makedoc(stdout, schema_path)
    return stdout.getvalue()


def test_doc_headings_target_anchor(metaschema_doc) -> None:
    """Doc headers must have an id and section link."""
    assert (
        '<h1 id="Abstract" class="section">Abstract '
        '<a href="#Abstract">&sect;</a></h1>' in metaschema_doc
    )


def test_doc_render_table_of_contents(metaschema_doc) -> None:
    """The special Table of Contents token must be replaced with a rendered table."""
    assert "!--ToC--" not in metaschema_doc


def test_plain_links_autolinked(metaschema_doc) -> None:
    """Plan links should be treated as if they were wrapped in angle brackets."""
    assert (
        "This document is the product of the "
        '<a href="https://groups.google.com/forum/#!forum/common-workflow-language">'
        "Common Workflow Language working\ngroup</a>" in metaschema_doc
    )


def test_embedded_html_unescaped() -> None:
    """Raw HTML shouldn't get escaped."""
    schema_path = get_data("tests/inherited-attributes.yml")
    assert schema_path
    stdout = StringIO()
    makedoc(stdout, schema_path)
    html = stdout.getvalue()

    assert '<table class="table">' in html
    assert "&lt;table class=&quot;table&quot;&gt;" not in html


def test_multiline_list_entries_word_spacing(metaschema_doc) -> None:
    """Hanging indents in Markdown lists don't lead to wordsmushing."""
    assert "as itis poorly documented" not in metaschema_doc
    assert "base URI for the document used toresolve relative" not in metaschema_doc
    assert "The keys ofthe object are namespace prefixes" not in metaschema_doc
    assert (
        "This field may list URIreferences to documents in RDF-XML"
        not in metaschema_doc
    )
    assert "defines valid fields thatmake up a record type" not in metaschema_doc
    assert "set of symbols that arevalid value" not in metaschema_doc


def test_multiline_list_entries_without_indention(metaschema_doc) -> None:
    """Hanging indents are not required in Markdown lists."""
    # See https://daringfireball.net/projects/markdown/syntax#list
    # and https://spec.commonmark.org/0.30/#example-290
    assert (
        "<li><p>At least one record definition object which defines valid fields that\n"
        "make up a record type.  Record field definitions include the valid types\n"
        "that may be assigned to each field and annotations to indicate fields\n"
        'that represent identifiers and links, described below in "Semantic\n'
        'Annotations".</p>\n'
        "</li>\n"
        "<li><p>Any number of enumerated type objects which define a set of finite "
        "set of symbols that are\n"
        "valid value of the type.</p>\n"
        "</li>\n"
        "<li><p>Any number of documentation objects which allow in-line "
        "documentation of the schema.</p>\n"
        "</li>" in metaschema_doc
    )
    assert (
        "<li>At least one record definition object which defines valid fields that</li>"
        not in metaschema_doc
    )


def test_detect_changes_in_html(metaschema_doc) -> None:
    """Catch all for changes in HTML output, please adjust if the changes are innocent."""
    # If the hash changed because the metaschema itself changed (without changes
    # to makedoc.py or the version of mistune) then you can directly update the
    # hash value below.
    #
    # Otherwise, follow this procedure verify that the changed HTML rendering
    # is acceptable:
    # 1. Render the metaschema schema into using an older, known-working version
    #    of schema-salad:
    #    `schema-salad-doc schema_salad/metaschema/metaschem.yml > metaschema.orig.html`
    # 1. Render the metaschema schema into using proposed changed codebase
    #    `schema-salad-doc schema_salad/metaschema/metaschem.yml > metaschema.new.html`
    # 2. Confirm the other tests in this file pass using the new code/mistune,
    #    adjusting the test strings if the changes are truly innocent.
    # 3. Check the `diff` between the saved HTML pages to check for obvious problems
    #    `diff metaschema.orig.html metaschema.new.html`
    # 4. Check the HTML in both Firefox and Chrome, especially near areas
    #    of differences in the diff
    # 5. If the changes are agreeable, then update the hash below
    hasher = hashlib.sha256()
    hasher.update(metaschema_doc.encode("utf-8"))
    assert (
        hasher.hexdigest()
        == "6fdb6cc7a6c29538da5ba8778d6557d7e0a6ace0a0a4c18fc99e154265adf1bd"
    )
