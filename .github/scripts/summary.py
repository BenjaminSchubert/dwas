import argparse
import logging
from dataclasses import InitVar, dataclass, field
from typing import Any, List, cast
from xml.etree import ElementTree

from tabulate import tabulate

LOGGER = logging.getLogger(__name__)


@dataclass
class TestCase:
    classname: str
    name: str
    time: float

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
            TestCase(
                test.attrib["classname"],
                test.attrib["name"],
                float(test.attrib["time"]),
            )
            for test in tree.findall("testcase")
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


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")

    files = parser.parse_args().files

    LOGGER.info("Generate summary from %s.", files)

    testsuites = [
        TestSuite.from_junit(testsuite)
        for file in files
        for testsuite in ElementTree.parse(file).findall("testsuite")
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
        cast(Any, sorted(slowest_suite.tests, reverse=True)[:10]),
        headers="keys",
        tablefmt="github",
    )

    print(
        f"""\
## Test suites

{summary}

## Slowest tests for {slowest_suite.name}

{slowest_tests}
"""
    )


if __name__ == "__main__":
    main()
