import pytest

from dwas._dependency_injection import call_with_parameters
from dwas._exceptions import BaseDwasException


def test_accepts_keyword_or_positional_arguments():
    def func(arg1):
        return arg1

    assert call_with_parameters(func, {"arg1": "hello!"}) == "hello!"


def test_accepts_keyword_only_arguments():
    def func(*, arg1):
        return arg1

    assert call_with_parameters(func, {"arg1": "hello!"}) == "hello!"


def test_fails_if_argument_cant_be_passed_by_keyword():
    def func(arg1, /):
        return arg1  # pragma: nocover

    with pytest.raises(BaseDwasException) as excwrp:
        call_with_parameters(func, {"arg1": "hello!"})

    assert "test_dependency_injection.py:" in str(excwrp.value)
    assert "Unsupported parameter type for function 'func'" in str(
        excwrp.value
    )


def test_fails_if_argument_cant_be_passed_by_keyword_with_class():
    class TestClass:
        def __call__(self, arg1, /):
            return arg1  # pragma: nocover

    with pytest.raises(BaseDwasException) as excwrp:
        call_with_parameters(TestClass(), {"arg1": "hello!"})

    assert "test_dependency_injection.py:" in str(excwrp.value)
    assert (
        "Unsupported parameter type for function 'TestClass.__call__'"
        in str(excwrp.value)
    )


def test_fails_if_argument_is_not_passed():
    def func(arg1):
        return arg1  # pragma: nocover

    with pytest.raises(BaseDwasException) as excwrp:
        call_with_parameters(func, {})

    assert "test_dependency_injection.py:" in str(excwrp.value)
    assert "Parameter 'arg1' was not provided" in str(excwrp.value)


def test_uses_default_if_no_value_passed():
    def func(arg1="hello"):
        return arg1

    assert call_with_parameters(func, {}) == "hello"
