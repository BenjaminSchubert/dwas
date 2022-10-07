import pytest

from dwas._steps.parametrize import (
    DefaultsAlreadySetException,
    ParameterConflictException,
    extract_parameters,
    parametrize,
    set_defaults,
)


def f_noop():
    def noop():
        pass  # pragma: nocover

    return noop


def test_single_argument():
    func = parametrize("a", ("one", "two"))(f_noop())
    assert extract_parameters(func) == [
        ("one", {"a": "one"}),
        ("two", {"a": "two"}),
    ]


def test_multiple_arguments():
    func = parametrize(["a", "b"], [["one", "two"], ["three", "four"]])(
        f_noop()
    )
    assert extract_parameters(func) == [
        ("one,two", {"a": "one", "b": "two"}),
        ("three,four", {"a": "three", "b": "four"}),
    ]


def test_parameters_are_merged_in_product():
    func = parametrize("a", ["one", "two"])(
        parametrize("b", ["one", "two"])(f_noop())
    )
    assert extract_parameters(func) == [
        ("one,one", {"a": "one", "b": "one"}),
        ("one,two", {"a": "one", "b": "two"}),
        ("two,one", {"a": "two", "b": "one"}),
        ("two,two", {"a": "two", "b": "two"}),
    ]


@pytest.mark.parametrize(
    ("id1", "id2", "expected"), (("", None, "two"), (None, "", "one"))
)
def test_parameters_with_empty_id_keep_emtpy_on_merge(id1, id2, expected):
    func = parametrize("a", ["one"], ids=[id1])(
        parametrize("b", ["two"], ids=[id2])(f_noop())
    )
    assert extract_parameters(func) == [(expected, {"a": "one", "b": "two"})]


def test_can_specify_id():
    func = parametrize("cache", [True, False], ids=["cache", "nocache"])(
        f_noop()
    )
    assert extract_parameters(func) == [
        ("cache", {"cache": True}),
        ("nocache", {"cache": False}),
    ]


def test_cannot_override_parameters():
    with pytest.raises(ParameterConflictException):
        parametrize("one", ["one"])(
            parametrize(("one", "two"), (["one", "two"],))(f_noop())
        )


def test_can_set_only_default_parameters():
    func = set_defaults({"one": "one"})(f_noop())
    assert extract_parameters(func) == [("", {"one": "one"})]


def test_parameters_are_merged_with_defaults():
    func = parametrize(("one", "three"), [("one", "three")])(
        set_defaults({"one": "two", "two": "two"})(f_noop())
    )
    assert extract_parameters(func) == [
        ("", {"one": "one", "two": "two", "three": "three"})
    ]


def test_cannot_set_defaults_twice():
    with pytest.raises(DefaultsAlreadySetException):
        set_defaults({})(set_defaults({})(f_noop()))
