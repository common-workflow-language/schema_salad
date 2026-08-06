"""Tests of the runtime support functions for generated parsers."""

from schema_salad.runtime import save_relative_uri

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
    """A reference below the popped scope is relativized without a leading slash."""
    uri = "file:///wf.cwl#second_step/log"
    assert save_relative_uri(uri, BASE, False, 2, True) == "log"


def test_save_relative_uri_no_ref_scope() -> None:
    """Without ref_scope the base fragment already ends in a slash.

    E.g. how CWL's `scatter: input_2` is saved relative to its step.
    """
    uri = "file:///wf.cwl#second_step/input_2"
    base = "file:///wf.cwl#second_step"
    assert save_relative_uri(uri, base, False, None, True) == "input_2"
