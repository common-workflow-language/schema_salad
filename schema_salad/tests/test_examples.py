from __future__ import absolute_import, print_function

import os

import six

import ruamel.yaml
from ruamel.yaml.comments import CommentedMap, CommentedSeq
import schema_salad.main
import schema_salad.ref_resolver
import schema_salad.schema
from schema_salad.jsonld_context import makerdf
from schema_salad.sourceline import SourceLine, cmap

from .util import get_data


def test_schemas():
    loader = schema_salad.ref_resolver.Loader({})

    ra, _ = loader.resolve_all(
        cmap(
            {
                u"$schemas": [
                    schema_salad.ref_resolver.file_uri(get_data("tests/EDAM.owl"))
                ],
                u"$namespaces": {u"edam": u"http://edamontology.org/"},
                u"edam:has_format": u"edam:format_1915",
            }
        ),
        "",
    )

    assert {
        u"$schemas": [schema_salad.ref_resolver.file_uri(get_data("tests/EDAM.owl"))],
        u"$namespaces": {u"edam": u"http://edamontology.org/"},
        u"http://edamontology.org/has_format": u"http://edamontology.org/format_1915",
    } == ra


def test_self_validate():
    assert 0 == schema_salad.main.main(argsl=[get_data("metaschema/metaschema.yml")])
    assert 0 == schema_salad.main.main(
        argsl=[
            get_data("metaschema/metaschema.yml"),
            get_data("metaschema/metaschema.yml"),
        ]
    )


def test_avro_regression():
    assert 0 == schema_salad.main.main(argsl=[get_data("tests/Process.yml")])


def test_jsonld_ctx():
    ldr, _, _, _ = schema_salad.schema.load_schema(
        cmap(
            {
                "$base": "Y",
                "name": "X",
                "$namespaces": {"foo": "http://example.com/foo#"},
                "$graph": [
                    {"name": "ExampleType", "type": "enum", "symbols": ["asym", "bsym"]}
                ],
            }
        )
    )

    ra, _ = ldr.resolve_all(cmap({"foo:bar": "asym"}), "X")

    assert ra == {"http://example.com/foo#bar": "asym"}


def test_idmap():
    ldr = schema_salad.ref_resolver.Loader({})
    ldr.add_context(
        {
            "inputs": {
                "@id": "http://example.com/inputs",
                "mapSubject": "id",
                "mapPredicate": "a",
            },
            "outputs": {"@type": "@id", "identity": True},
            "id": "@id",
        }
    )

    ra, _ = ldr.resolve_all(
        cmap(
            {
                "id": "stuff",
                "inputs": {"zip": 1, "zing": 2},
                "outputs": ["out"],
                "other": {"n": 9},
            }
        ),
        "http://example2.com/",
    )

    assert "http://example2.com/#stuff" == ra["id"]
    for item in ra["inputs"]:
        if item["a"] == 2:
            assert "http://example2.com/#stuff/zing" == item["id"]
        else:
            assert "http://example2.com/#stuff/zip" == item["id"]
    assert ["http://example2.com/#stuff/out"] == ra["outputs"]
    assert {"n": 9} == ra["other"]


def test_scoped_ref():
    ldr = schema_salad.ref_resolver.Loader({})
    ldr.add_context(
        {
            "scatter": {"@type": "@id", "refScope": 0},
            "source": {"@type": "@id", "refScope": 2},
            "in": {"mapSubject": "id", "mapPredicate": "source"},
            "out": {"@type": "@id", "identity": True},
            "inputs": {"mapSubject": "id", "mapPredicate": "type"},
            "outputs": {"mapSubject": "id"},
            "steps": {"mapSubject": "id"},
            "id": "@id",
        }
    )

    ra, _ = ldr.resolve_all(
        cmap(
            {
                "inputs": {"inp": "string", "inp2": "string"},
                "outputs": {"out": {"type": "string", "source": "step2/out"}},
                "steps": {
                    "step1": {
                        "in": {"inp": "inp", "inp2": "#inp2", "inp3": ["inp", "inp2"]},
                        "out": ["out"],
                        "scatter": "inp",
                    },
                    "step2": {
                        "in": {"inp": "step1/out"},
                        "scatter": "inp",
                        "out": ["out"],
                    },
                },
            }
        ),
        "http://example2.com/",
    )

    assert {
        "inputs": [
            {"id": "http://example2.com/#inp", "type": "string"},
            {"id": "http://example2.com/#inp2", "type": "string"},
        ],
        "outputs": [
            {
                "id": "http://example2.com/#out",
                "type": "string",
                "source": "http://example2.com/#step2/out",
            }
        ],
        "steps": [
            {
                "id": "http://example2.com/#step1",
                "scatter": "http://example2.com/#step1/inp",
                "in": [
                    {
                        "id": "http://example2.com/#step1/inp",
                        "source": "http://example2.com/#inp",
                    },
                    {
                        "id": "http://example2.com/#step1/inp2",
                        "source": "http://example2.com/#inp2",
                    },
                    {
                        "id": "http://example2.com/#step1/inp3",
                        "source": [
                            "http://example2.com/#inp",
                            "http://example2.com/#inp2",
                        ],
                    },
                ],
                "out": ["http://example2.com/#step1/out"],
            },
            {
                "id": "http://example2.com/#step2",
                "scatter": "http://example2.com/#step2/inp",
                "in": [
                    {
                        "id": "http://example2.com/#step2/inp",
                        "source": "http://example2.com/#step1/out",
                    }
                ],
                "out": ["http://example2.com/#step2/out"],
            },
        ],
    } == ra


def test_examples():
    for a in ["field_name", "ident_res", "link_res", "vocab_res"]:
        ldr, _, _, _ = schema_salad.schema.load_schema(
            get_data("metaschema/%s_schema.yml" % a)
        )
        with open(get_data("metaschema/%s_src.yml" % a)) as src_fp:
            src = ldr.resolve_all(
                ruamel.yaml.round_trip_load(src_fp), "", checklinks=False
            )[0]
        with open(get_data("metaschema/%s_proc.yml" % a)) as src_proc:
            proc = ruamel.yaml.safe_load(src_proc)
        assert proc == src


def test_yaml_float_test():
    assert ruamel.yaml.safe_load("float-test: 2e-10")["float-test"] == 2e-10


def test_typedsl_ref():
    ldr = schema_salad.ref_resolver.Loader({})
    ldr.add_context(
        {
            "File": "http://example.com/File",
            "null": "http://example.com/null",
            "array": "http://example.com/array",
            "type": {"@type": "@vocab", "typeDSL": True},
        }
    )

    ra, _ = ldr.resolve_all(cmap({"type": "File"}), "")
    assert {"type": "File"} == ra

    ra, _ = ldr.resolve_all(cmap({"type": "File?"}), "")
    assert {"type": ["null", "File"]} == ra

    ra, _ = ldr.resolve_all(cmap({"type": "File[]"}), "")
    assert {"type": {"items": "File", "type": "array"}} == ra

    ra, _ = ldr.resolve_all(cmap({"type": "File[]?"}), "")
    assert {"type": ["null", {"items": "File", "type": "array"}]} == ra


def test_secondaryFile_dsl_ref():
    ldr = schema_salad.ref_resolver.Loader({})
    ldr.add_context({"secondaryFiles": {"secondaryFilesDSL": True}})

    ra, _ = ldr.resolve_all(cmap({"secondaryFiles": ".foo"}), "")
    assert {"secondaryFiles": {"pattern": ".foo", "required": None}} == ra

    ra, _ = ldr.resolve_all(cmap({"secondaryFiles": ".foo?"}), "")
    assert {"secondaryFiles": {"pattern": ".foo", "required": False}} == ra

    ra, _ = ldr.resolve_all(cmap({"secondaryFiles": [".foo"]}), "")
    assert {"secondaryFiles": [{"pattern": ".foo", "required": None}]} == ra

    ra, _ = ldr.resolve_all(cmap({"secondaryFiles": [".foo?"]}), "")
    assert {"secondaryFiles": [{"pattern": ".foo", "required": False}]} == ra


def test_scoped_id():
    ldr = schema_salad.ref_resolver.Loader({})
    ctx = {
        "id": "@id",
        "location": {"@id": "@id", "@type": "@id"},
        "bar": "http://example.com/bar",
        "ex": "http://example.com/",
    }
    ldr.add_context(ctx)

    ra, _ = ldr.resolve_all(
        cmap({"id": "foo", "bar": {"id": "baz"}}), "http://example.com"
    )
    assert {
        "id": "http://example.com/#foo",
        "bar": {"id": "http://example.com/#foo/baz"},
    } == ra

    g = makerdf(None, ra, ctx)
    print (g.serialize(format="n3"))

    ra, _ = ldr.resolve_all(
        cmap({"location": "foo", "bar": {"location": "baz"}}),
        "http://example.com",
        checklinks=False,
    )
    assert {
        "location": "http://example.com/foo",
        "bar": {"location": "http://example.com/baz"},
    } == ra

    g = makerdf(None, ra, ctx)
    print (g.serialize(format="n3"))

    ra, _ = ldr.resolve_all(
        cmap({"id": "foo", "bar": {"location": "baz"}}),
        "http://example.com",
        checklinks=False,
    )
    assert {
        "id": "http://example.com/#foo",
        "bar": {"location": "http://example.com/baz"},
    } == ra

    g = makerdf(None, ra, ctx)
    print (g.serialize(format="n3"))

    ra, _ = ldr.resolve_all(
        cmap({"location": "foo", "bar": {"id": "baz"}}),
        "http://example.com",
        checklinks=False,
    )
    assert {
        "location": "http://example.com/foo",
        "bar": {"id": "http://example.com/#baz"},
    } == ra

    g = makerdf(None, ra, ctx)
    print (g.serialize(format="n3"))


def test_subscoped_id():
    ldr = schema_salad.ref_resolver.Loader({})
    ctx = {"id": "@id", "bar": {"subscope": "bar"}}
    ldr.add_context(ctx)

    ra, _ = ldr.resolve_all(
        cmap({"id": "foo", "bar": {"id": "baz"}}), "http://example.com"
    )
    assert {
        "id": "http://example.com/#foo",
        "bar": {"id": "http://example.com/#foo/bar/baz"},
    } == ra


def test_mixin():
    base_url = schema_salad.ref_resolver.file_uri(os.path.join(os.getcwd(), "tests"))
    ldr = schema_salad.ref_resolver.Loader({})
    ra = ldr.resolve_ref(
        cmap({"$mixin": get_data("tests/mixin.yml"), "one": "five"}), base_url=base_url
    )
    assert {"id": "four", "one": "five"} == ra[0]
    ldr = schema_salad.ref_resolver.Loader({"id": "@id"})

    ra = ldr.resolve_all(
        cmap(
            [
                {"id": "a", "m": {"$mixin": get_data("tests/mixin.yml")}},
                {"id": "b", "m": {"$mixin": get_data("tests/mixin.yml")}},
            ]
        ),
        base_url=base_url,
    )
    assert [
        {"id": base_url + "#a", "m": {"id": base_url + u"#a/four", "one": "two"}},
        {"id": base_url + "#b", "m": {"id": base_url + u"#b/four", "one": "two"}},
    ] == ra[0]


def test_fragment():
    ldr = schema_salad.ref_resolver.Loader({"id": "@id"})
    b, _ = ldr.resolve_ref(get_data("tests/frag.yml#foo2"))
    assert {"id": b["id"], "bar": "b2"} == b


def test_file_uri():
    # Note: this test probably won't pass on Windows.  Someone with a
    # windows box should add an alternate test.
    assert "file:///foo/bar%20baz/quux" == schema_salad.ref_resolver.file_uri(
        "/foo/bar baz/quux"
    )
    assert os.path.normpath(
        "/foo/bar baz/quux"
    ) == schema_salad.ref_resolver.uri_file_path("file:///foo/bar%20baz/quux")
    assert (
        "file:///foo/bar%20baz/quux%23zing%20zong"
        == schema_salad.ref_resolver.file_uri("/foo/bar baz/quux#zing zong")
    )
    assert (
        "file:///foo/bar%20baz/quux#zing%20zong"
        == schema_salad.ref_resolver.file_uri(
            "/foo/bar baz/quux#zing zong", split_frag=True
        )
    )
    assert os.path.normpath(
        "/foo/bar baz/quux#zing zong"
    ) == schema_salad.ref_resolver.uri_file_path(
        "file:///foo/bar%20baz/quux#zing%20zong"
    )


def test_sourceline():
    ldr = schema_salad.ref_resolver.Loader({"id": "@id"})
    b, _ = ldr.resolve_ref(get_data("tests/frag.yml"))

    class TestExp(Exception):
        pass

    try:
        with SourceLine(b, 1, TestExp, False):
            raise Exception("Whoops")
    except TestExp as e:
        assert str(e).endswith("frag.yml:3:3: Whoops"), e
    except Exception as exc:
        assert False, exc

    if six.PY2:
        try:
            with SourceLine(b, 1, TestExp, True):
                raise Exception("Whoops")
        except TestExp as e:
            assert (
                str(e)
                .splitlines()[0]
                .endswith("frag.yml:3:3: Traceback (most recent call last):")
            ), str(e)
        except Exception as exc:
            assert False, exc


def test_cmap():
    # Test bugfix that cmap won't fail when given a CommentedMap with no lc.data
    cmap(CommentedMap((("foo", "bar"), ("baz", ["quux"]))))
    cmap(CommentedSeq(("foo", [], "bar")))


def test_blank_node_id():
    # Test that blank nodes are passed through and not considered
    # relative paths.  Blank nodes (also called anonymous ids) are
    # URIs starting with "_:".  They are randomly generated
    # placeholders mainly used internally where an id is needed but
    # was not given.

    ldr = schema_salad.ref_resolver.Loader({})
    ctx = {"id": "@id"}
    ldr.add_context(ctx)

    ra, _ = ldr.resolve_all(cmap({"id": "_:foo"}), "http://example.com")
    assert {"id": "_:foo"} == ra
