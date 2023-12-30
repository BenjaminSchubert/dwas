# ruff: noqa:D100,D101,D102,D103,D105
import argparse
import logging
from dataclasses import InitVar, dataclass, field
from typing import Any, List, Literal, Optional
from xml.etree import ElementTree

from tabulate import tabulate

LOGGER = logging.getLogger(__name__)


@dataclass
class TestCase:
    classname: str
    name: str
    time: float
    state: Literal["success", "failure", "error", "skipped"]
    summary: Optional[str]

    @classmethod
    def from_junit(cls, tree: ElementTree.Element) -> "TestCase":
        children = tree.getchildren()
        assert len(children) <= 1

        state: Literal["success", "failure", "error", "skipped"] = "success"
        summary = None

        if children:
            child = children[0]
            if child.tag == "error":
                state = "error"
            elif child.tag == "failure":
                state = "failure"
            elif child.tag == "skipped":
                state = "skipped"
            else:
                raise AssertionError(f"unexpected tag: {child.tag}")

            summary = child.attrib["message"].replace("\n", "<br />")

        return TestCase(
            tree.attrib["classname"],
            tree.attrib["name"],
            float(tree.attrib["time"]),
            state=state,
            summary=summary,
        )

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented

        return (self.time, self.classname, self.name) < (
            other.time,
            other.classname,
            other.name,
        )


@dataclass
class TestSuite:
    name: str
    total: InitVar[int]
    successes: int = field(init=False)
    errors: int
    failures: int
    skipped: int
    time: float
    tests: List[TestCase]

    def __post_init__(self, total: int) -> None:
        self.successes = total - self.errors - self.failures - self.skipped

    @classmethod
    def from_junit(cls, tree: ElementTree.Element) -> "TestSuite":
        attrs = tree.attrib

        tests = [
            TestCase.from_junit(test) for test in tree.findall("testcase")
        ]

        return cls(
            name=attrs["name"],
            total=int(attrs["tests"]),
            errors=int(attrs["errors"]),
            failures=int(attrs["failures"]),
            skipped=int(attrs["skipped"]),
            time=float(attrs["time"]),
            tests=tests,
        )

    def __lt__(self, other: Any) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented

        return (self.time, self.name) < (other.time, other.name)


def get_failures_and_errors(testsuites: List[TestSuite]) -> str:
    reports = []

    for testsuite in testsuites:
        failing_tests = [
            t
            for t in testsuite.tests
            if t.state in ["error", "failure", "skipped"]
        ]

        if failing_tests:
            report = tabulate(
                [
                    (t.classname, t.name, t.state, t.summary)
                    for t in failing_tests
                ],
                headers=("Class name", "Name", "State", "Summary"),
                tablefmt="github",
            )
            reports.append(f"### {testsuite.name}\n\n{report}")

    if not reports:
        return ""

    return "## Error summary\n\n{}".format("\n\n".join(reports))


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")

    files = parser.parse_args().files

    LOGGER.info("Generate summary from %s.", files)

    testsuites = [
        TestSuite.from_junit(testsuite)
        for file in files
        for testsuite in ElementTree.parse(file).findall(  # noqa: S314
            "testsuite"
        )
    ]

    summary = tabulate(
        # Typing is wrong on tabulate here
        [
            (t.name, t.successes, t.errors, t.failures, t.skipped, t.time)
            for t in sorted(testsuites, reverse=True)
        ],
        headers=[
            "Test Suite",
            "Successes ✅",
            "Errors ❌",
            "Failures ❌",
            "Skipped ⚠️",
            "Time Taken [s]",
        ],
        tablefmt="github",
    )

    slowest_suite = max(testsuites)
    slowest_tests = tabulate(
        [
            (t.classname, t.name, t.time)
            for t in sorted(slowest_suite.tests, reverse=True)[:10]
        ],
        headers=("Class name", "Name", "time"),
        tablefmt="github",
    )

    errors = get_failures_and_errors(testsuites)

    print(  # noqa: T201
        f"""\
## Test suites

{summary}

## Slowest tests for {slowest_suite.name}

{slowest_tests}

{errors}
"""
    )


if __name__ == "__main__":
    main()
