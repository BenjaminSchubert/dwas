import shutil
import sys
from contextlib import contextmanager
from contextvars import copy_context
from datetime import datetime
from threading import Event, Lock, Thread
from typing import Dict, Iterator, List

from colorama import Cursor, Fore, ansi

from . import _io
from ._timing import format_timedelta


class StepSummary:
    def __init__(self, all_steps: List[str]) -> None:
        self._running_steps: Dict[str, datetime] = {}
        self._lock = Lock()

        self._start = datetime.now()

        self._n_success = 0
        self._n_failure = 0
        self._waiting = all_steps

    def mark_running(self, step: str) -> None:
        with self._lock:
            self._running_steps[step] = datetime.now()
            self._waiting.remove(step)

    def mark_success(self, step: str) -> None:
        with self._lock:
            del self._running_steps[step]
            self._n_success += 1

    def mark_failure(self, step: str) -> None:
        with self._lock:
            del self._running_steps[step]
            self._n_failure += 1

    def lines(self) -> List[str]:
        update_at = datetime.now()

        term_width = shutil.get_terminal_size().columns
        headline = (
            f" {Fore.YELLOW}Runtime: {format_timedelta(update_at - self._start)} "
            f"["
            f"{len(self._waiting)}/"
            f"{Fore.CYAN}{len(self._running_steps)}{Fore.YELLOW}/"
            f"{Fore.GREEN}{self._n_success}{Fore.YELLOW}/"
            f"{Fore.RED}{self._n_failure}{Fore.YELLOW}"
            f"]{Fore.RESET} "
        ).center(
            # 40 comes from the number of color codes * 5, as this is what is added
            # to the real length of the array
            term_width + 40,
            "~",
        )

        waiting_line = (
            f"[-:--:--] {Fore.YELLOW}waiting: {' '.join(self._waiting)}"
        )
        if len(waiting_line) > term_width:
            waiting_line = waiting_line[: term_width + 5 - 3] + "..."

        return (
            [headline]
            + [
                f"[{format_timedelta(update_at - since)}] {Fore.CYAN}{step}: running{Fore.RESET}"
                for step, since in self._running_steps.items()
            ]
            + [f"{waiting_line}{Fore.RESET}"]
        )


class Frontend:
    def __init__(self, summary: StepSummary) -> None:
        self._summary = summary

        def _refresh_in_context() -> None:
            with _io.redirect_streams(
                sys.__stdout__, sys.__stderr__
            ), _io.log_file(None):
                self._refresh()

        self._refresh_thread = Thread(
            target=copy_context().run, args=[_refresh_in_context]
        )
        self._stop = Event()

        self._pipe_plexer = _io.PipePlexer(write_on_flush=False)

    @contextmanager
    def activate(self) -> Iterator[None]:
        with _io.redirect_streams(
            self._pipe_plexer.stdout, self._pipe_plexer.stderr
        ):
            self._refresh_thread.start()

            try:
                yield
            finally:
                self._stop.set()
                self._refresh_thread.join()

    def _refresh(self) -> None:
        previous_progress_height = 0
        previous_last_line_length = 0

        def refresh(skip_summary: bool = False) -> None:
            nonlocal previous_progress_height
            nonlocal previous_last_line_length

            # Erase the current line
            if previous_last_line_length != 0:
                sys.stderr.write(
                    Cursor.BACK(previous_last_line_length) + ansi.clear_line()
                )

            # Erase the previous summary lines
            if previous_progress_height >= 2:
                sys.stderr.write(
                    f"{Cursor.UP(1)}{ansi.clear_line()}"
                    * (previous_progress_height - 1)
                )

            # Force a flush, to ensure that if the next line is printed on
            # stdout, we pass the erasing first
            sys.stderr.flush()

            self._pipe_plexer.flush(force_write=True)

            if skip_summary:
                previous_last_line_length = 0
                previous_progress_height = 0
            else:
                summary = self._summary.lines()

                sys.stderr.write(
                    ansi.clear_line() + f"\n{ansi.clear_line()}".join(summary)
                )
                previous_progress_height = len(summary)
                if previous_progress_height:
                    previous_last_line_length = len(summary[-1])

            sys.stderr.flush()

        refresh()
        while not self._stop.is_set():
            self._stop.wait(0.5)
            refresh()

        refresh(True)
