from __future__ import annotations

import contextlib
import faulthandler
import io
import os
import sys
import threading

import pytest

from dwas._subproc import ProcessManager

TIMEOUT_S = 20


def _run(command: list[str]) -> str:
    manager = ProcessManager()
    capture = io.StringIO()
    exception: BaseException | None = None
    done = threading.Event()

    def worker() -> None:
        nonlocal exception

        with contextlib.redirect_stdout(capture):
            try:
                manager.run(command, env=dict(os.environ))
            except BaseException as exc:  # noqa: BLE001
                exception = exc
            finally:
                done.set()

    threading.Thread(target=worker, daemon=True).start()

    if not done.wait(TIMEOUT_S):
        faulthandler.dump_traceback()
        manager.kill()
        pytest.fail(
            f"ProcessManager.run did not complete within {TIMEOUT_S}s — deadlock suspected"
        )

    if exception is not None:
        raise exception

    return capture.getvalue()


def _assert_output_matches(actual: str, expected: str) -> None:
    if len(actual) != len(expected):
        raise AssertionError(
            f"length mismatch: got {len(actual)}, expected {len(expected)}"
        )
    for i, (a, e) in enumerate(zip(actual, expected)):
        if a != e:
            raise AssertionError(
                f"divergence at {i}: got {actual[i - 20 : i + 20]!r},"
                f" expected {expected[i - 20 : i + 20]!r}"
            )


def test_handles_invalid_utf8_output():
    output = _run(
        [
            sys.executable,
            "-u",
            "-c",
            "import sys; sys.stdout.buffer.write(b'a' + b'\\xff' * 70_000)",
        ]
    )
    _assert_output_matches(output, "a" + "\ufffd" * 70_000)


def test_split_utf8_char_across_chunk_boundary_preserves_output():
    output = _run(
        [
            sys.executable,
            "-u",
            "-c",
            "import sys; sys.stdout.buffer.write(b'a' + b'\\xc3\\xa9' * 34_000)",
        ]
    )
    _assert_output_matches(output, "a" + "é" * 34_000)
