"""Test examples."""
import datetime
import os
from io import StringIO
from typing import Any, Dict, cast

from pytest import CaptureFixture
from ruamel.yaml.comments import CommentedMap, CommentedSeq

import schema_salad.main
import schema_salad.schema
from schema_salad.jsonld_context import makerdf
from schema_salad.ref_resolver import Loader, file_uri, uri_file_path
from schema_salad.sourceline import SourceLine, cmap
from schema_salad.utils import ContextType, stdout, yaml_no_ts

from .util import get_data


def test_schemas() -> None:
    loader = Loader({})

    path = get_data("tests/EDAM.owl")
    assert path
    ra, _ = loader.resolve_all(
        cmap(
            {
                "$schemas": [file_uri(path)],
                "$namespaces": {"edam": "http://edamontology.org/"},
                "edam:has_format": "edam:format_1915",
            }
        ),
        "",
    )

    assert {
        "$schemas": [file_uri(path)],
        "$namespaces": {"edam": "http://edamontology.org/"},
        "http://edamontology.org/has_format": "http://edamontology.org/format_1915",
    } == ra


def test_self_validate() -> None:
    path = get_data("metaschema/metaschema.yml")
    assert path
    assert 0 == schema_salad.main.main(argsl=[path])
    assert 0 == schema_salad.main.main(argsl=[path, path])


def test_print_rdf(capfdbinary: CaptureFixture[bytes]) -> None:
    """Test --print-rdf."""
    schema_path = get_data("tests/test_schema/CommonWorkflowLanguage.yml")
    document_path = get_data("tests/test_real_cwl/bio-cwl-tools/bamtools_stats.cwl")
    assert schema_path and document_path
    assert 0 == schema_salad.main.main(
        argsl=["--print-rdf", schema_path, document_path]
    )
    captured = capfdbinary.readouterr()
    assert captured.out


def test_print_pre_schema(capfdbinary: CaptureFixture[bytes]) -> None:
    """Test --print-pre only schema."""
    schema_path = get_data("tests/test_schema/CommonWorkflowLanguage.yml")
    assert schema_path
    assert 0 == schema_salad.main.main(argsl=["--print-pre", schema_path])
    captured = capfdbinary.readouterr()
    assert captured.out


def test_print_pre(capfdbinary: CaptureFixture[bytes]) -> None:
    """Test --print-pre."""
    schema_path = get_data("tests/test_schema/CommonWorkflowLanguage.yml")
    document_path = get_data("tests/test_real_cwl/bio-cwl-tools/bamtools_stats.cwl")
    assert schema_path and document_path
    assert 0 == schema_salad.main.main(
        argsl=["--print-pre", schema_path, document_path]
    )
    captured = capfdbinary.readouterr()
    assert captured.out


def test_print_schema_index(capfdbinary: CaptureFixture[bytes]) -> None:
    """Test --print-index only with a schema."""
    schema_path = get_data("tests/test_schema/CommonWorkflowLanguage.yml")
    assert schema_path
    assert 0 == schema_salad.main.main(argsl=["--print-index", schema_path])
    captured = capfdbinary.readouterr()
    assert captured.out


def test_print_index(capfdbinary: CaptureFixture[bytes]) -> None:
    """Test --print-index."""
    schema_path = get_data("tests/test_schema/CommonWorkflowLanguage.yml")
    document_path = get_data("tests/test_real_cwl/bio-cwl-tools/bamtools_stats.cwl")
    assert schema_path and document_path
    assert 0 == schema_salad.main.main(
        argsl=["--print-index", schema_path, document_path]
    )
    captured = capfdbinary.readouterr()
    assert captured.out


def test_print_schema_metadata(capfdbinary: CaptureFixture[bytes]) -> None:
    """Test --print-metadata only for a schema."""
    schema_path = get_data("tests/test_schema/CommonWorkflowLanguage.yml")
    assert schema_path
    assert 0 == schema_salad.main.main(argsl=["--print-metadata", schema_path])
    captured = capfdbinary.readouterr()
    assert captured.out


def test_print_metadata(capfdbinary: CaptureFixture[bytes]) -> None:
    """Test --print-metadata."""
    schema_path = get_data("tests/test_schema/CommonWorkflowLanguage.yml")
    document_path = get_data("tests/test_real_cwl/bio-cwl-tools/bamtools_stats.cwl")
    assert schema_path and document_path
    assert 0 == schema_salad.main.main(
        argsl=["--print-metadata", schema_path, document_path]
    )
    captured = capfdbinary.readouterr()
    assert captured.out


def test_avro_regression() -> None:
    path = get_data("tests/Process.yml")
    assert path
    assert 0 == schema_salad.main.main(argsl=[path])


def test_jsonld_ctx() -> None:
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


def test_idmap() -> None:
    ldr = Loader({})
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
    assert isinstance(ra, CommentedMap)

    assert "http://example2.com/#stuff" == ra["id"]
    for item in ra["inputs"]:
        if item["a"] == 2:
            assert "http://example2.com/#stuff/zing" == item["id"]
        else:
            assert "http://example2.com/#stuff/zip" == item["id"]
    assert ["http://example2.com/#stuff/out"] == ra["outputs"]
    assert {"n": 9} == ra["other"]


def test_scoped_ref() -> None:
    ldr = Loader({})
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


def test_examples() -> None:
    for a in ["field_name", "ident_res", "link_res", "vocab_res"]:
        path = get_data(f"metaschema/{a}_schema.yml")
        assert path
        ldr, _, _, _ = schema_salad.schema.load_schema(path)
        path2 = get_data(f"metaschema/{a}_src.yml")
        assert path2
        yaml = yaml_no_ts()
        with open(path2) as src_fp:
            src = ldr.resolve_all(yaml.load(src_fp), "", checklinks=False)[0]
        path3 = get_data(f"metaschema/{a}_proc.yml")
        assert path3
        with open(path3) as src_proc:
            proc = yaml.load(src_proc)
        assert proc == src


def test_yaml_float_test() -> None:
    assert yaml_no_ts().load("float-test: 2e-10")["float-test"] == 2e-10


def test_typedsl_ref() -> None:
    ldr = Loader({})
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


def test_secondaryFile_dsl_ref() -> None:
    ldr = Loader({})
    ldr.add_context({"secondaryFiles": {"secondaryFilesDSL": True}})

    ra, _ = ldr.resolve_all(cmap({"secondaryFiles": ".foo"}), "")
    assert {"secondaryFiles": {"pattern": ".foo", "required": None}} == ra

    ra, _ = ldr.resolve_all(cmap({"secondaryFiles": ".foo?"}), "")
    assert {"secondaryFiles": {"pattern": ".foo", "required": False}} == ra

    ra, _ = ldr.resolve_all(cmap({"secondaryFiles": [".foo"]}), "")
    assert {"secondaryFiles": [{"pattern": ".foo", "required": None}]} == ra

    ra, _ = ldr.resolve_all(cmap({"secondaryFiles": [".foo?"]}), "")
    assert {"secondaryFiles": [{"pattern": ".foo", "required": False}]} == ra


def test_scoped_id() -> None:
    ldr = Loader({})
    ctx = {
        "id": "@id",
        "location": {"@id": "@id", "@type": "@id"},
        "bar": "http://example.com/bar",
        "ex": "http://example.com/",
    }  # type: ContextType
    ldr.add_context(ctx)

    ra, _ = ldr.resolve_all(
        cmap({"id": "foo", "bar": {"id": "baz"}}), "http://example.com"
    )
    assert {
        "id": "http://example.com/#foo",
        "bar": {"id": "http://example.com/#foo/baz"},
    } == ra

    g = makerdf(None, ra, ctx)
    g.serialize(destination=stdout(), format="n3")

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
    g.serialize(destination=stdout(), format="n3")

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
    g.serialize(destination=stdout(), format="n3")

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
    g.serialize(destination=stdout(), format="n3")


def test_rdf_datetime() -> None:
    """Affirm that datetime objects can be serialized in makerdf()."""
    ldr = Loader({})
    ctx: ContextType = {
        "id": "@id",
        "location": {"@id": "@id", "@type": "@id"},
        "bar": "http://example.com/bar",
        "ex": "http://example.com/",
    }
    ldr.add_context(ctx)

    ra: CommentedMap = cast(
        CommentedMap,
        ldr.resolve_all(
            cmap(
                {
                    "id": "foo",
                    "bar": {"id": "baz"},
                }
            ),
            "http://example.com",
        )[0],
    )
    ra["s:dateCreated"] = datetime.datetime(2020, 10, 8)

    g = makerdf(None, ra, ctx)
    g.serialize(destination=stdout(), format="n3")
    g2 = makerdf(None, CommentedSeq([ra]), ctx)
    g2.serialize(destination=stdout(), format="n3")


def test_yaml_datetime() -> None:
    """Affirm that yaml_no_ts prevents the creation of datetime objects."""
    example: Dict[str, Any] = {
        "id": "foo",
        "bar": {"id": "baz"},
    }
    example["s:dateCreated"] = datetime.datetime(2020, 10, 8)
    yaml = yaml_no_ts()
    stream = StringIO()
    yaml.dump(example, stream)
    stream2 = StringIO(stream.getvalue())
    example2 = yaml.load(stream2)
    assert isinstance(example2["s:dateCreated"], str)


def test_subscoped_id() -> None:
    ldr = Loader({})
    ctx = {
        "id": "@id",
        "bar": {"subscope": "bar"},
    }  # type: ContextType
    ldr.add_context(ctx)

    ra, _ = ldr.resolve_all(
        cmap({"id": "foo", "bar": {"id": "baz"}}), "http://example.com"
    )
    assert {
        "id": "http://example.com/#foo",
        "bar": {"id": "http://example.com/#foo/bar/baz"},
    } == ra


def test_mixin() -> None:
    base_url = file_uri(os.path.join(os.getcwd(), "tests"))
    ldr = Loader({})
    path = get_data("tests/mixin.yml")
    assert path
    ra = ldr.resolve_ref(cmap({"$mixin": path, "one": "five"}), base_url=base_url)
    assert {"id": "four", "one": "five"} == ra[0]
    ldr = Loader({"id": "@id"})

    ra = ldr.resolve_all(
        cmap([{"id": "a", "m": {"$mixin": path}}, {"id": "b", "m": {"$mixin": path}}]),
        base_url=base_url,
    )
    assert [
        {"id": base_url + "#a", "m": {"id": base_url + "#a/four", "one": "two"}},
        {"id": base_url + "#b", "m": {"id": base_url + "#b/four", "one": "two"}},
    ] == ra[0]


def test_fragment() -> None:
    ldr = Loader({"id": "@id"})
    path = get_data("tests/frag.yml#foo2")
    assert path
    b = ldr.resolve_ref(path)[0]
    assert isinstance(b, CommentedMap)
    assert {"id": b["id"], "bar": "b2"} == b


def test_file_uri() -> None:
    # Note: this test probably won't pass on Windows.  Someone with a
    # windows box should add an alternate test.
    assert "file:///foo/bar%20baz/quux" == file_uri("/foo/bar baz/quux")
    assert os.path.normpath("/foo/bar baz/quux") == uri_file_path(
        "file:///foo/bar%20baz/quux"
    )
    assert "file:///foo/bar%20baz/quux%23zing%20zong" == file_uri(
        "/foo/bar baz/quux#zing zong"
    )
    assert "file:///foo/bar%20baz/quux#zing%20zong" == file_uri(
        "/foo/bar baz/quux#zing zong", split_frag=True
    )
    assert os.path.normpath("/foo/bar baz/quux#zing zong") == uri_file_path(
        "file:///foo/bar%20baz/quux#zing%20zong"
    )


def test_sourceline() -> None:
    ldr = Loader({"id": "@id"})
    path = get_data("tests/frag.yml")
    assert path
    b, _ = ldr.resolve_ref(path)

    class TestExp(Exception):
        pass

    try:
        with SourceLine(b, 1, TestExp, False):
            raise Exception("Whoops")
    except TestExp as e:
        assert str(e).endswith("frag.yml:3:3: Whoops"), e
    except Exception as exc:
        assert False, exc


def test_cmap() -> None:
    # Test bugfix that cmap won't fail when given a CommentedMap with no lc.data
    cmap(CommentedMap((("foo", "bar"), ("baz", ["quux"]))))
    cmap(CommentedSeq(("foo", [], "bar")))


def test_blank_node_id() -> None:
    # Test that blank nodes are passed through and not considered
    # relative paths.  Blank nodes (also called anonymous ids) are
    # URIs starting with "_:".  They are randomly generated
    # placeholders mainly used internally where an id is needed but
    # was not given.

    ldr = Loader({})
    ctx = {"id": "@id"}  # type: ContextType
    ldr.add_context(ctx)

    ra, _ = ldr.resolve_all(cmap({"id": "_:foo"}), "http://example.com")
    assert {"id": "_:foo"} == ra


def test_can_use_Any() -> None:
    """Test that 'type: Any' can be used"""
    path = get_data("tests/test_schema/cwltest-schema.yml")
    assert path
    (
        document_loader,
        avsc_names,
        schema_metadata,
        metaschema_loader,
    ) = schema_salad.schema.load_schema(path)


def test_nullable_links() -> None:
    ldr = schema_salad.ref_resolver.Loader({})
    ctx = {"link": {"@type": "@id"}}  # type: ContextType
    ldr.add_context(ctx)

    ra, _ = ldr.resolve_all(cmap({"link": None}), "http://example.com", checklinks=True)
    assert {"link": None} == ra
