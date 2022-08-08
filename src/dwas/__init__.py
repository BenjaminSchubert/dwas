"""
Everything explicitly exposed here is part of the ``dwas`` public API.

In addition to what is here, ``dwas`` also exposed the following public modules:

.. autosummary:: dwas.predefined

.. warning::

    While ``dwas`` is not at version 1.0.0, it does not guarantee API stability.


"""
from ._config import Config
from ._exceptions import BaseDwasException
from ._steps import (
    DefaultsAlreadySetException,
    MismatchedNumberOfParametersException,
    ParameterConflictException,
    Step,
    StepHandler,
    StepWithArtifacts,
    StepWithDependentSetup,
    StepWithSetup,
    managed_step,
    parametrize,
    register_managed_step,
    register_step,
    register_step_group,
    set_defaults,
    step,
)

# XXX: The order here is important, it declares the order in which the entries
#      are documented in the public docs.
__all__ = [
    "StepHandler",
    "Step",
    "StepWithSetup",
    "StepWithDependentSetup",
    "StepWithArtifacts",
    "Config",
    "register_step",
    "register_managed_step",
    "register_step_group",
    "step",
    "managed_step",
    "parametrize",
    "set_defaults",
    "BaseDwasException",
    "DefaultsAlreadySetException",
    "MismatchedNumberOfParametersException",
    "ParameterConflictException",
]
