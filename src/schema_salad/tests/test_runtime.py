"""Test the runtime module."""

import pytest

from schema_salad.python_codegen_support import _expand_url
from schema_salad.runtime import LoadingOptions, save_relative_uri

BASE = "file:///wf.cwl#second_step/input_2"


def test_save_relative_uri_sibling_prefix() -> None:
    """A sibling id sharing a name prefix with the scope must not be truncated.

    E.g. in CWL, a step input sourced from a workflow input whose name
    starts with the step's own name:

        inputs:
          second_step_input: string        # id: ...#second_step_input
        steps:
          second_step:
            in:
              input_2: second_step_input   # id: ...#second_step/input_2

    Saving the `source` field (ref_scope=2) must yield "second_step_input",
    not "_input".
    """
    uri = "file:///wf.cwl#second_step_input"
    assert save_relative_uri(uri, BASE, False, 2, True) == "second_step_input"


def test_save_relative_uri_sibling_prefix_ref_scope_1() -> None:
    """Same as above for ref_scope=1 fields, e.g. a CWL Workflow outputSource.

        outputs:
          second:                          # id: ...#second
            outputSource: second_step/log

    must save as "second_step/log", not "_step/log".
    """
    uri = "file:///wf.cwl#second_step/log"
    base = "file:///wf.cwl#second"
    assert save_relative_uri(uri, base, False, 1, True) == "second_step/log"


def test_save_relative_uri_sibling() -> None:
    """An ordinary sibling reference is saved as its full fragment.

    E.g. CWL's `source: first_input` or `source: first_step/log`.
    """
    uri = "file:///wf.cwl#first_input"
    assert save_relative_uri(uri, BASE, False, 2, True) == "first_input"
    uri = "file:///wf.cwl#first_step/log"
    assert save_relative_uri(uri, BASE, False, 2, True) == "first_step/log"


def test_save_relative_uri_inside_scope() -> None:
    """A reference is relativized against the scope the loader resolves it in.

    For a ref_scope=2 field on "#second_step/input_2" that scope is the
    document root, so a step output keeps its step name.
    """
    uri = "file:///wf.cwl#second_step/log"
    assert save_relative_uri(uri, BASE, False, 2, True) == "second_step/log"


def test_save_relative_uri_packed() -> None:
    """In a packed document, only the enclosing process's name is stripped.

    E.g. `source: inp` on step input "#main/step/in" (ref_scope=2) and
    `outputSource: step/log` on workflow output "#main/out" (ref_scope=1).
    """
    uri = "file:///wf.cwl#main/inp"
    assert save_relative_uri(uri, "file:///wf.cwl#main/step/in", False, 2, True) == "inp"
    uri = "file:///wf.cwl#main/step/log"
    assert save_relative_uri(uri, "file:///wf.cwl#main/out", False, 1, True) == "step/log"


def test_save_relative_uri_scope_is_document_root() -> None:
    """When ref_scope pops every fragment segment, the full fragment is kept.

    E.g. a ref_scope=2 field whose own id is a single top-level fragment.
    """
    base = "file:///wf.cwl#input_2"
    uri = "file:///wf.cwl#first_input"
    assert save_relative_uri(uri, base, False, 2, True) == "first_input"
    uri = "file:///wf.cwl#input_2_other"
    assert save_relative_uri(uri, base, False, 2, True) == "input_2_other"


def test_save_relative_uri_no_ref_scope() -> None:
    """Without ref_scope the base fragment already ends in a slash.

    E.g. how CWL's `scatter: input_2` is saved relative to its step.
    """
    uri = "file:///wf.cwl#second_step/input_2"
    base = "file:///wf.cwl#second_step"
    assert save_relative_uri(uri, base, False, None, True) == "input_2"


@pytest.mark.parametrize(
    "uri,base,ref_scope",
    [
        ("file:///wf.cwl#second_step_input", BASE, 2),
        ("file:///wf.cwl#second_step/log", BASE, 2),
        ("file:///wf.cwl#first_input", "file:///wf.cwl#input_2", 2),
        ("file:///wf.cwl#second_step/log", "file:///wf.cwl#second", 1),
        ("file:///wf.cwl#main/inp", "file:///wf.cwl#main/step/in", 2),
        ("file:///wf.cwl#main/step_input", "file:///wf.cwl#main/step/in", 2),
        ("file:///wf.cwl#main/step/log", "file:///wf.cwl#main/out", 1),
        ("file:///wf.cwl#main/inp", "file:///wf.cwl#main/step/in", 5),
    ],
)
def test_save_relative_uri_round_trip(uri: str, base: str, ref_scope: int) -> None:
    """Loading a saved scoped reference gives back the original URI."""
    saved = save_relative_uri(uri, base, False, ref_scope, True)
    loading_options = LoadingOptions(no_link_check=True)
    assert _expand_url(saved, base, loading_options, False, False, ref_scope) == uri
