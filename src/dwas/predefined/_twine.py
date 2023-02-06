import logging
from typing import List, Optional

# XXX: All imports here should be done from the top level. If we need it,
#      users might need it
from .. import Step, StepRunner, build_parameters, set_defaults

LOGGER = logging.getLogger(__name__)


@set_defaults(
    {
        "dependencies": ["twine"],
        "additional_arguments": ["check", "--strict"],
    }
)
class Twine(Step):
    def __init__(self) -> None:
        self.__name__ = "twine"

    def __call__(
        self, step: StepRunner, additional_arguments: List[str]
    ) -> None:
        sdists = step.get_artifacts("sdists")
        wheels = step.get_artifacts("wheels")
        if not sdists and not wheels:
            # pylint: disable=broad-exception-raised
            raise Exception(
                "No sdists or wheels provided: this step expects at least one"
                " of them to be provided by a previous step"
            )

        if not step.config.colors and "--no-color" not in additional_arguments:
            additional_arguments = ["--no-color", *additional_arguments]

        step.run(["twine", *additional_arguments, *sdists, *wheels])


def twine(*, additional_arguments: Optional[List[str]] = None) -> Step:
    """
    Run `twine`_ against the provided packages.

    By default, it will depend on :python:`["twine"]`, when registered with
    :py:func:`dwas.register_managed_step`.

    This step will ask the steps it requires for :term:`artifacts<artifact>` named ``sdists`` and
    ``wheels`` and will run against those.

    :param additional_arguments: Additional arguments to pass to the ``twine``
                                 invocation.
                                 Defaults to :python:`["check", "--strict"]`.
    :return: The step so that you can add additional parameters to it if needed.

    :Examples:

        Examples here assume that you use the :py:func:`package` step like:

        .. code-block::

            # This creates a 'package' step
            dwas.register_managed_step(dwas.predefined.package())

        In order to make sure your distribution files are ready to be published:

        .. code-block::

            dwas.register_managed_step(
                dwas.predefined.twine(),
                name="twine:check",
                requires=["package"],
            )

        And if you want to be able to use ``dwas twine:publish`` to publish:

        .. code-block::

            dwas.register_managed_step(
                dwas.predefined.twine(
                    additional_arguments=[
                        "upload",
                        "--verbose",
                        # This is not required, if you don't want to gpg-sign your
                        # distribution files
                        "--sign",
                        "--non-interactive",
                    ],
                ),
                name="twine:upload",
                passenv=["TWINE_REPOSITORY", "TWINE_USERNAME", "TWINE_PASSWORD"],
                requires=["package", "twine:check"],
                run_by_default=False,
            )
    """
    return build_parameters(additional_arguments=additional_arguments)(Twine())
