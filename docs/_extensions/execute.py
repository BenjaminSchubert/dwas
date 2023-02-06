import os
import shlex
import subprocess
from typing import Any, Dict, List

from docutils import nodes
from docutils.parsers import rst
from docutils.parsers.rst.directives import nonnegative_int, unchanged
from sphinx.addnodes import document
from sphinx.application import Sphinx
from sphinx.errors import ExtensionError


class execute(nodes.Element):  # pylint: disable=invalid-name
    pass


class ExecuteDirective(rst.Directive):
    has_content = False
    final_argument_whitespace = True
    required_arguments = 1

    option_spec = {"returncode": nonnegative_int, "cwd": unchanged}

    def run(self) -> List[nodes.Element]:
        env = self.state.document.settings.env

        node = execute()
        node["command"] = self.arguments[0].strip()
        node["returncode"] = self.options.get("returncode", 0)

        if "cwd" in self.options:
            _, cwd = env.relfn2path(self.options["cwd"])
        else:
            cwd = None
        node["working_directory"] = cwd

        self.add_name(node)
        return [node]


def run_programs(
    app: Sphinx, doctree: document  # pylint: disable=unused-argument
) -> None:
    env = os.environ.copy()
    # Ensure we always have colors set for the output
    env["PY_COLORS"] = "1"

    for node in doctree.traverse(execute):
        proc = subprocess.run(
            shlex.split(node["command"]),
            cwd=node["working_directory"],
            check=False,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        if proc.returncode != node["returncode"]:
            raise ExtensionError(
                f"Command '{node['command']}' returned an unexpected error code"
                f" '{proc.returncode}'. Expected '{node['returncode']}'."
                f"\n\n{proc.stdout}",
                None,
            )

        # Add the prompt
        output = f"$ {node['command']}\n{proc.stdout}"
        new_node = nodes.literal_block(output, output)
        # Ensure we get colors
        new_node["language"] = "ansi"
        node.replace_self(new_node)


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_directive("command-output", ExecuteDirective)
    app.connect("doctree-read", run_programs)
    return {"parallel_read_safe": True}
