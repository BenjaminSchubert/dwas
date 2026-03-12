from __future__ import annotations

import inspect

import pytest

from .mixins import BaseLinterTest, BaseStepTest


def get_all_subclasses(cls: type) -> list[type]:
    all_subclasses = []
    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))
    return all_subclasses


@pytest.mark.parametrize("kls", (BaseStepTest, BaseLinterTest))
def test_test_classes_implement_all_abstract_methods(kls: type) -> None:
    # Otherwise, pytest just ignores them, and we might lose tests
    abstract_classes = [
        k
        for k in get_all_subclasses(kls)
        if inspect.isabstract(k) and k.__name__.startswith("Test")
    ]

    assert abstract_classes == [], "Some classes are missing implementations"
