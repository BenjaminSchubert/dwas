from __future__ import annotations

import shutil
import sys
import time
from contextlib import contextmanager
from contextvars import copy_context
from datetime import timedelta
from threading import Event, Thread
from typing import TYPE_CHECKING, Iterator

from colorama import Cursor, Fore, Style, ansi

from . import _io
from ._timing import format_timedelta

if TYPE_CHECKING:
    from ._scheduler import Scheduler

ANSI_SHOW_CURSOR = f"{ansi.CSI}?25h"
ANSI_HIDE_CURSOR = f"{ansi.CSI}?25l"


class StepSummary:
    def __init__(self, scheduler: Scheduler, start_time: float) -> None:
        self._start_time = start_time
        self._scheduler = scheduler

    def _counter(self, value: int, color: str) -> str:
        return f"{color}{Style.BRIGHT}{value}{Style.NORMAL}{Fore.YELLOW}"

    def lines(self) -> list[str]:
        update_at = time.monotonic()

        term_width = shutil.get_terminal_size().columns

        time_since_start = format_timedelta(
            timedelta(seconds=update_at - self._start_time)
        )
        n_non_runnable = (
            len(self._scheduler.cancelled)
            + len(self._scheduler.skipped)
            + len(self._scheduler.blocked)
        )

        headline = (
            f" {Fore.YELLOW}Runtime: {time_since_start} "
            f"["
            f"{len(self._scheduler.waiting)}/"
            f"{self._counter(len(self._scheduler.running), Fore.CYAN)}/"
            f"{self._counter(len(self._scheduler.success), Fore.GREEN)}/"
            f"{self._counter(len(self._scheduler.failed), Fore.RED)}/"
            f"{self._counter(n_non_runnable, Fore.YELLOW)}"
            f"]{Fore.RESET} "
        ).center(
            # 86 comes from the number of color codes * 5, as this is what is added
            # to the real length of the array
            term_width + 86,
            "~",
        )

        additional_info: list[str] = []
        if self._scheduler.ready:
            ready_line = (
                f"[-:--:--] {Fore.YELLOW}{Style.BRIGHT}ready: "
                + " ".join(self._scheduler.ready)
            )
            if len(ready_line) > term_width:
                ready_line = ready_line[: term_width + 8 - 3] + "..."
            ready_line += Fore.RESET + Style.NORMAL
            additional_info.append(ready_line)

        if self._scheduler.waiting:
            waiting_line = f"[-:--:--] {Fore.YELLOW}waiting: {' '.join(self._scheduler.waiting)}"
            if len(waiting_line) > term_width:
                waiting_line = waiting_line[: term_width + 5 - 3] + "..."
            waiting_line += Fore.RESET
            additional_info.append(waiting_line)

        return (
            [headline]
            + [
                f"[{format_timedelta(timedelta(seconds=update_at - since))}]"
                f" {Fore.CYAN}{step}: running{Fore.RESET}"
                for step, since in self._scheduler.running.items()
            ]
            + additional_info
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
        try:
            sys.stderr.write(ANSI_HIDE_CURSOR)

            with _io.redirect_streams(
                self._pipe_plexer.stdout, self._pipe_plexer.stderr
            ):
                self._refresh_thread.start()

                try:
                    yield
                finally:
                    self._stop.set()
                    self._refresh_thread.join()
        finally:
            sys.stderr.write(ANSI_SHOW_CURSOR)
            sys.stderr.flush()

    def _refresh(self) -> None:
        previous_summary_height = 0
        previous_summary_last_line_length = 0
        previous_line_length = None

        def refresh(*, skip_summary: bool = False) -> None:
            nonlocal previous_summary_height
            nonlocal previous_summary_last_line_length
            nonlocal previous_line_length

            # Erase the current line
            if previous_summary_last_line_length != 0:
                sys.stderr.write(
                    Cursor.BACK(previous_summary_last_line_length)
                    + ansi.clear_line()
                )

            # Erase the previous summary lines
            if previous_summary_height >= 2:
                sys.stderr.write(
                    f"{Cursor.UP(1)}{ansi.clear_line()}"
                    * (previous_summary_height - 1)
                )

            # Move the cursor back to where we were if the last line did not end
            # with a '\n'
            if previous_line_length:
                sys.stderr.write(
                    f"{Cursor.UP(1)}{Cursor.FORWARD(previous_line_length)}"
                )

            # Force a flush, to ensure that if the next line is printed on
            # stdout, we pass the erasing first
            sys.stderr.flush()

            new_previous_line_length = self._pipe_plexer.flush(
                force_write=True
            )
            # Only update if there was something actually written
            if new_previous_line_length is not None:
                previous_line_length = new_previous_line_length

            if skip_summary:
                previous_summary_last_line_length = 0
                previous_summary_height = 0
            else:
                summary = self._summary.lines()

                sys.stderr.write(
                    ("" if not previous_line_length else "\n")
                    + "\n".join(summary)
                )
                previous_summary_height = len(summary)
                if previous_summary_height:
                    previous_summary_last_line_length = len(summary[-1])

            sys.stderr.flush()

        refresh()
        while not self._stop.is_set():
            self._stop.wait(0.5)
            refresh()

        refresh(skip_summary=True)
