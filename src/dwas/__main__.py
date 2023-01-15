import importlib.util
import logging
from argparse import (
    ArgumentParser,
    BooleanOptionalAction,
    Namespace,
    _AppendAction,
)
from contextvars import copy_context
from importlib.metadata import version
from typing import Any, List, Optional

from . import _pipeline
from ._config import Config
from ._exceptions import BaseDwasException, FailedPipelineException
from ._logging import setup_logging

LOGGER = logging.getLogger(__name__)


class _SplitAppendAction(_AppendAction):
    def __call__(
        self,
        parser: ArgumentParser,
        namespace: Namespace,
        values: Any,
        option_string: Optional[str] = None,
    ) -> None:
        items = getattr(namespace, self.dest, None)
        if items is None:
            items = []
        setattr(
            namespace,
            self.dest,
            [*items, *[v.strip() for v in values.split(",")]],
        )


def _parse_args(args: Optional[List[str]] = None) -> Namespace:
    parser = ArgumentParser()
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {version('dwas')}"
    )

    parser.add_argument("--config", default="./dwasfile.py")
    parser.add_argument(
        "-s",
        "--step",
        action=_SplitAppendAction,
        dest="steps",
        help="which step(s) to run",
    )
    parser.add_argument(
        "-o",
        "--only",
        action=_SplitAppendAction,
        dest="only_steps",
        help="Only run the specified step(s), even if they have dependencies",
    )
    parser.add_argument(
        "-e",
        "--except",
        action=_SplitAppendAction,
        dest="except_steps",
        help="Don't run the following step(s), even if they are required",
    )
    parser.add_argument(
        "-l",
        "--list",
        action="store_true",
        dest="list_only",
        help="Only list all available steps. Don't execute",
    )
    parser.add_argument(
        "--list-dependencies",
        action="store_true",
        help="When listing, also show step dependencies",
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=0, help="Be more verbose"
    )
    parser.add_argument(
        "-q", "--quiet", action="count", default=0, help="Be more quiet"
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        help=(
            "Number of jobs to run in parallel, 0 uses the number of cpus on"
            " the machine (default: %(default)d)"
        ),
        default=1,
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--setup-only",
        action="store_true",
        help="Only run setup actions, don't run",
    )
    group.add_argument(
        "--no-setup",
        action="store_true",
        help="Don't run setup actions, only the rest",
    )

    parser.add_argument(
        "--ff",
        "--fail-fast",
        dest="fail_fast",
        action="store_true",
        help="Stop at the first error",
    )

    parser.add_argument(
        "-c",
        "--clean",
        action="store_true",
        help="Clear the cache before running",
    )

    parser.add_argument(
        "--colors",
        action=BooleanOptionalAction,
        help=(
            "Force or prevent a colored output"
            " (default: true if stdin is a tty, false otherwise)"
        ),
    )
    parser.add_argument(
        "--cache-path",
        help="Directory where to store the persistent cache (default: %(default)s)",
        default="./.dwas",
    )
    parser.add_argument(
        "--skip-missing-interpreters",
        action="store_true",
        help="Don't report a missing interpreter as a failure, and skip the step instead",
    )

    return parser.parse_args(args)


def _load_user_config(
    pipeline: _pipeline.Pipeline, config_file: str
) -> _pipeline.Pipeline:
    _pipeline.set_pipeline(pipeline)

    spec = importlib.util.spec_from_file_location("dwasfile", config_file)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)

    try:
        spec.loader.exec_module(module)
    except FileNotFoundError as exc:
        raise BaseDwasException(
            f"Unable to load {config_file}: no such file or directory"
        ) from exc
    except SyntaxError as exc:
        offset = ""
        if exc.offset is not None:
            offset = f"\n\t\t{' ' * (exc.offset - 1)}^"

        raise BaseDwasException(
            f"Unable to load {config_file}: syntax error:\n"
            f"\t{exc.filename}:{exc.lineno}\n\n\t\t{exc.text}{offset}"
        ) from exc
    except ImportError as exc:
        raise BaseDwasException(
            f"Unable to load {config_file}: {exc}"
        ) from exc

    return pipeline


def _execute_pipeline(
    config: Config,
    pipeline_config: str,
    steps: Optional[List[str]],
    only_steps: Optional[List[str]],
    except_steps: Optional[List[str]],
    clean: bool,
    list_only: bool,
    list_dependencies: bool,
) -> None:
    pipeline = _pipeline.Pipeline(config)

    context = copy_context()
    pipeline = context.run(_load_user_config, pipeline, pipeline_config)
    LOGGER.debug("Pipeline definition found at %s", pipeline_config)

    if list_only or list_dependencies:
        pipeline.list_all_steps(
            steps, only_steps, except_steps, list_dependencies
        )
        return

    pipeline.execute(steps, only_steps, except_steps, clean=clean)


def main(sys_args: Optional[List[str]] = None) -> None:
    args = _parse_args(sys_args)
    verbosity = args.verbose - args.quiet
    config = Config(
        args.cache_path,
        verbosity,
        args.colors,
        args.jobs,
        args.skip_missing_interpreters,
        args.no_setup,
        args.setup_only,
        args.fail_fast,
    )
    setup_logging(logging.INFO - 10 * verbosity, config.colors)

    try:
        _execute_pipeline(
            config,
            args.config,
            args.steps,
            args.only_steps,
            args.except_steps,
            args.clean,
            args.list_only,
            args.list_dependencies,
        )
    except BaseDwasException as exc:
        if config.verbosity >= 1 and not isinstance(
            exc, FailedPipelineException
        ):
            LOGGER.debug(exc, exc_info=exc)
        LOGGER.error("%s", exc)
        raise SystemExit(exc.exit_code) from exc
