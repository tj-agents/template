"""Find targeted writes to protected global host configuration."""

import argparse
import ast
import json
import re
import sys
from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath
from typing import Any, NamedTuple

EXECUTABLE_SUFFIXES = {
    ".bat",
    ".bash",
    ".cjs",
    ".cmd",
    ".js",
    ".mjs",
    ".ps1",
    ".py",
    ".sh",
    ".ts",
    ".zsh",
}
WRITER_METHODS = {
    "mkdir",
    "replace",
    "rename",
    "rmdir",
    "touch",
    "unlink",
    "write",
    "write_bytes",
    "write_text",
}
SHELL_WRITERS = re.compile(
    r"\b(add-content|clear-content|copy-item|move-item|new-item|out-file|"
    r"remove-item|set-content|tee|touch|mkdir|cp|mv|rm|install)\b|(?:^|\s)>",
    re.IGNORECASE,
)
PERSISTENT_COMMAND = re.compile(
    r"\b(setx|git\s+config\s+--global|codex\s+(?:config|plugin\s+"
    r"(?:activate|deactivate|enable|disable|install|uninstall))|claude\s+plugin\s+"
    r"(?:activate|deactivate|enable|disable|install|uninstall))\b",
    re.IGNORECASE,
)
CLAUDE_PLUGIN_COMMAND = re.compile(r"\bclaude\s+plugin\s+\w+\b", re.IGNORECASE)
CODEX_PLUGIN_COMMAND = re.compile(r"\bcodex\s+plugin\s+\w+\b", re.IGNORECASE)
POWER_SHELL_ENVIRONMENT = re.compile(
    r"\[environment\]::setenvironmentvariable\s*\(", re.IGNORECASE
)
NATIVE_MUTATION_API = re.compile(
    r"\b(?:codex\.)?config\.(?:batchwrite|set|write)\s*\("
    r"|\bplugins?\.(?:activate|deactivate|enable|disable|install|uninstall)\s*\(",
    re.IGNORECASE,
)
ASSIGNMENT = re.compile(
    r"^\s*(?:\$|set\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$",
    re.IGNORECASE,
)
CODEX_HOME_ASSIGNMENT = re.compile(
    r"^\s*(?:\$env:|export\s+|set\s+)codex_home\s*=\s*(.+)$", re.IGNORECASE
)


class Finding(NamedTuple):
    path: str
    line: int
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: protected-global-write: {self.message}"


def check(
    root: Path,
    payloads: Mapping[str, Any],
    publications: Mapping[str, str],
    generated: Mapping[str, bytes],
    generated_paths: Mapping[str, Path] | None = None,
) -> list[Finding]:
    """Check known global-write sinks in authored and generated payload scripts.

    This is targeted sink and target analysis. It does not prove dynamic code safe.
    """
    approved = approved_installers(
        root, payloads, publications, generated, generated_paths
    )
    findings: list[Finding] = []
    for path in authored_scripts(root):
        findings.extend(
            scan(
                path.read_text(encoding="utf-8"),
                path.relative_to(root).as_posix(),
                path == root / "install.ps1" and regular_unlinked_file(path),
            )
        )
    for virtual, content in generated.items():
        virtual_path = PurePosixPath(virtual)
        if virtual_path.suffix.lower() not in EXECUTABLE_SUFFIXES:
            continue
        findings.extend(
            scan(
                content.decode("utf-8"),
                virtual,
                virtual in approved,
            )
        )
    return findings


def approved_installers(
    root: Path,
    payloads: Mapping[str, Any],
    publications: Mapping[str, str],
    generated: Mapping[str, bytes],
    generated_paths: Mapping[str, Path] | None,
) -> set[str]:
    source = root / "install.ps1"
    if not regular_unlinked_file(source):
        return set()
    installer = source.read_bytes()
    approved: set[str] = set()
    resources = payloads.get("resources", [])
    if not isinstance(resources, list):
        return approved
    for resource in resources:
        if not isinstance(resource, dict) or resource.get("source") != "install.ps1":
            continue
        package = resource.get("plugin")
        if not isinstance(package, str):
            continue
        owner = publications.get(package)
        if not isinstance(owner, str):
            continue
        destination = resource.get("destination")
        expected = f".agents/{owner}/resources/installer/install.ps1"
        if destination != expected:
            continue
        virtual = f"plugins/{package}/{expected}"
        if verified_installer(virtual, installer, generated, generated_paths):
            approved.add(virtual)
    approved.update(sources_installers(root, installer, generated, generated_paths))
    return approved


def sources_installers(
    root: Path,
    installer: bytes,
    generated: Mapping[str, bytes],
    generated_paths: Mapping[str, Path] | None,
) -> set[str]:
    manifest = root / ".agents/plugins/sources.json"
    if not manifest.is_file():
        return set()
    try:
        configuration = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    if not isinstance(configuration, dict):
        return set()
    scopes = configuration.get("scopes", [])
    resources = configuration.get("resources", [])
    if not isinstance(scopes, list) or not isinstance(resources, list):
        return set()
    plugins = {
        scope.get("plugin")
        for scope in scopes
        if isinstance(scope, dict) and isinstance(scope.get("plugin"), str)
    }
    approved: set[str] = set()
    for resource in resources:
        if (
            not isinstance(resource, dict)
            or resource.get("source") != "install.ps1"
            or not isinstance(plugin := resource.get("plugin"), str)
            or plugin not in plugins
        ):
            continue
        destination = resource.get("destination")
        expected = f".agents/{plugin}/resources/installer/install.ps1"
        if destination != expected or not owns_root_installer(root, plugin):
            continue
        virtual = f"plugins/{plugin}/{expected}"
        if verified_installer(virtual, installer, generated, generated_paths):
            approved.add(virtual)
    return approved


def owns_root_installer(root: Path, plugin: str) -> bool:
    harness = root / ".agents/plugins/harness" / f"{plugin}.json"
    if not harness.is_file():
        return False
    try:
        declaration = json.loads(harness.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(declaration, dict):
        return False
    identifier = declaration.get("plugin")
    source_roots = declaration.get("source_roots")
    return (
        isinstance(identifier, str)
        and identifier.rsplit("/", 1)[-1] == plugin
        and isinstance(source_roots, list)
        and "install.ps1" in source_roots
    )


def verified_installer(
    virtual: str,
    installer: bytes,
    generated: Mapping[str, bytes],
    generated_paths: Mapping[str, Path] | None,
) -> bool:
    if generated.get(virtual) != installer:
        return False
    return generated_paths is None or regular_unlinked_file(
        generated_paths.get(virtual)
    )


def regular_unlinked_file(path: Path | None) -> bool:
    if path is None or not path.is_file() or path.is_symlink():
        return False
    is_junction = getattr(path, "is_junction", None)
    if is_junction is not None and is_junction():
        return False
    try:
        return path.stat().st_nlink == 1
    except OSError:
        return False


def authored_scripts(root: Path) -> Iterable[Path]:
    for directory in (".agents", ".claude", ".codex", ".github", "scripts"):
        base = root / directory
        if base.is_dir():
            for path in base.rglob("*"):
                relative = path.relative_to(root)
                if (
                    path.is_file()
                    and path.suffix.lower() in EXECUTABLE_SUFFIXES
                    and not ignored_authored_path(relative)
                ):
                    yield path
    for installer in root.glob("install.*"):
        if installer.is_file() and installer.suffix.lower() in EXECUTABLE_SUFFIXES:
            yield installer


def ignored_authored_path(path: Path) -> bool:
    parts = set(path.parts)
    return (
        "tests" in parts
        or "__pycache__" in parts
        or path.parts[:2] in ((".claude", "skills"), (".codex", "skills"))
    )


def scan(source: str, path: str, approved: bool) -> list[Finding]:
    if approved:
        return []
    findings = native_api_findings(source, path)
    if path.endswith(".py"):
        findings.extend(scan_python(source, path))
    else:
        findings.extend(scan_shell(source, path))
    return sorted(findings, key=lambda finding: finding.line)


def native_api_findings(source: str, path: str) -> list[Finding]:
    return [
        Finding(path, number, "native configuration mutation API")
        for number, line in enumerate(source.splitlines(), start=1)
        if NATIVE_MUTATION_API.search(line)
    ]


def scan_python(source: str, path: str) -> list[Finding]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    functions = function_definitions(tree)
    isolated_functions = temporary_environment_functions(functions)
    aliases: dict[str, str] = {}
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            target, value_node = assignment_parts(node)
            if (
                isinstance(target, ast.Name)
                and value_node is not None
                and (value := assignment_value(value_node, aliases))
            ):
                aliases[target.id] = value
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node.func)
        arguments = " ".join(
            expression_text(argument, aliases) for argument in node.args
        )
        if name.endswith(".setenvironmentvariable") or name == "setenvironmentvariable":
            findings.append(Finding(path, node.lineno, "persistent user environment"))
        elif name.rsplit(".", 1)[-1] in {
            "run",
            "call",
            "check_call",
            "check_output",
            "popen",
            "system",
        }:
            if persistent_command(arguments):
                findings.append(
                    Finding(path, node.lineno, "persistent configuration command")
                )
        elif name == "open" and write_mode(node):
            if node.args and protected_target(expression_text(node.args[0], aliases)):
                findings.append(
                    Finding(path, node.lineno, "protected global configuration")
                )
        elif name.rsplit(".", 1)[-1] in WRITER_METHODS:
            receiver = (
                expression_text(node.func.value, aliases)
                if isinstance(node.func, ast.Attribute)
                else ""
            )
            if protected_target(receiver):
                findings.append(
                    Finding(path, node.lineno, "protected global configuration")
                )
        elif name.endswith(".setvalueex") and "environment" in arguments.lower():
            findings.append(Finding(path, node.lineno, "persistent user environment"))
        elif (
            name.rsplit(".", 1)[-1] == "request"
            and node.args
            and expression_text(node.args[0], aliases).lower() == "config/batchwrite"
            and containing_function(node, functions) not in isolated_functions
        ):
            findings.append(
                Finding(path, node.lineno, "native configuration mutation API")
            )
    return findings


def function_definitions(tree: ast.Module) -> dict[str, ast.FunctionDef]:
    return {
        node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }


def temporary_environment_functions(
    functions: Mapping[str, ast.FunctionDef],
) -> set[str]:
    temporary_parameters: dict[str, set[str]] = {name: set() for name in functions}
    changed = True
    while changed:
        changed = False
        for name, function in functions.items():
            values = temporary_values(function, temporary_parameters[name])
            for call in ast.walk(function):
                if not isinstance(call, ast.Call):
                    continue
                target = functions.get(call_name(call.func).rsplit(".", 1)[-1])
                if target is None:
                    continue
                parameter_names = function_parameters(target)
                for index, argument in enumerate(call.args):
                    if (
                        index < len(parameter_names)
                        and parameter_names[index] == "environment"
                        and temporary_expression(argument, values)
                        and "environment" not in temporary_parameters[target.name]
                    ):
                        temporary_parameters[target.name].add("environment")
                        changed = True
                for keyword in call.keywords:
                    if (
                        keyword.arg == "environment"
                        and temporary_expression(keyword.value, values)
                        and "environment" not in temporary_parameters[target.name]
                    ):
                        temporary_parameters[target.name].add("environment")
                        changed = True
    return {
        name
        for name, parameters in temporary_parameters.items()
        if "environment" in parameters
    }


def temporary_values(function: ast.FunctionDef, parameters: set[str]) -> set[str]:
    values = set(parameters)
    changed = True
    while changed:
        changed = False
        for node in ast.walk(function):
            if isinstance(node, (ast.With, ast.AsyncWith)):
                for item in node.items:
                    if (
                        isinstance(item.context_expr, ast.Call)
                        and call_name(item.context_expr.func).endswith(
                            "temporarydirectory"
                        )
                        and isinstance(item.optional_vars, ast.Name)
                        and item.optional_vars.id not in values
                    ):
                        values.add(item.optional_vars.id)
                        changed = True
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                target, value = assignment_parts(node)
                if (
                    isinstance(target, ast.Name)
                    and value is not None
                    and temporary_expression(value, values)
                    and target.id not in values
                ):
                    values.add(target.id)
                    changed = True
    return values


def temporary_expression(node: ast.expr, values: set[str]) -> bool:
    if isinstance(node, ast.Name):
        return node.id in values
    if isinstance(node, ast.BinOp):
        return temporary_expression(node.left, values) or temporary_expression(
            node.right, values
        )
    if isinstance(node, ast.Call):
        name = call_name(node.func)
        return (
            name.endswith("isolated_environment")
            or name in {"path", "pathlib.path"}
            or isinstance(node.func, ast.Attribute)
        ) and any(temporary_expression(argument, values) for argument in node.args)
    return False


def function_parameters(function: ast.FunctionDef) -> list[str]:
    return [
        argument.arg
        for argument in [
            *function.args.posonlyargs,
            *function.args.args,
            *function.args.kwonlyargs,
        ]
    ]


def containing_function(
    node: ast.Call, functions: Mapping[str, ast.FunctionDef]
) -> str | None:
    candidates = [
        function
        for function in functions.values()
        if function.lineno <= node.lineno <= (function.end_lineno or function.lineno)
    ]
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda function: (function.end_lineno or function.lineno) - function.lineno,
    ).name


def assignment_value(node: ast.expr, aliases: Mapping[str, str]) -> str:
    value = expression_text(node, aliases)
    return value if value else ""


def assignment_parts(
    node: ast.Assign | ast.AnnAssign,
) -> tuple[ast.expr | None, ast.expr | None]:
    if isinstance(node, ast.Assign):
        return (node.targets[0], node.value) if node.targets else (None, None)
    return node.target, node.value


def call_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id.lower()
    if isinstance(node, ast.Call):
        return call_name(node.func)
    if isinstance(node, ast.Attribute):
        return f"{call_name(node.value)}.{node.attr.lower()}".lstrip(".")
    return ""


def expression_text(node: ast.expr, aliases: Mapping[str, str]) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        left = expression_text(node.left, aliases)
        right = expression_text(node.right, aliases)
        return f"{left}/{right}"
    if isinstance(node, ast.Call):
        name = call_name(node.func)
        values = " ".join(expression_text(item, aliases) for item in node.args)
        return f"{name} {values}"
    if isinstance(node, ast.Attribute):
        return f"{expression_text(node.value, aliases)}.{node.attr}"
    if isinstance(node, (ast.List, ast.Tuple)):
        return " ".join(expression_text(item, aliases) for item in node.elts)
    return ""


def write_mode(node: ast.Call) -> bool:
    mode = node.args[1] if len(node.args) > 1 else None
    if mode is None:
        mode = next(
            (keyword.value for keyword in node.keywords if keyword.arg == "mode"),
            None,
        )
    return (
        isinstance(mode, ast.Constant)
        and isinstance(mode.value, str)
        and any(flag in mode.value for flag in "wax+")
    )


def scan_shell(source: str, path: str) -> list[Finding]:
    aliases: dict[str, str] = {}
    findings: list[Finding] = []
    temporary_codex_home = False
    for number, line in enumerate(source.splitlines(), start=1):
        match = ASSIGNMENT.match(line)
        if match:
            aliases[match.group(1).lower()] = substitute(match.group(2), aliases)
        codex_home = CODEX_HOME_ASSIGNMENT.match(line)
        if codex_home:
            temporary_codex_home = temporary_location(
                substitute(codex_home.group(1), aliases)
            )
        expanded = substitute(line, aliases)
        if persistent_command(
            expanded, temporary_codex_home
        ) or POWER_SHELL_ENVIRONMENT.search(expanded):
            findings.append(Finding(path, number, "persistent configuration command"))
        elif SHELL_WRITERS.search(expanded) and protected_target(expanded):
            findings.append(Finding(path, number, "protected global configuration"))
    return findings


def substitute(value: str, aliases: Mapping[str, str]) -> str:
    pattern = r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?|%([A-Za-z_][A-Za-z0-9_]*)%"
    result = value
    for _ in range(len(aliases) + 1):
        expanded = re.sub(pattern, lambda match: replace_name(match, aliases), result)
        if expanded == result:
            break
        result = expanded
    return result


def replace_name(match: re.Match[str], aliases: Mapping[str, str]) -> str:
    name = match.group(1) or match.group(2)
    return aliases.get(name.lower(), match.group(0))


def persistent_command(value: str, temporary_codex_home: bool = False) -> bool:
    if not PERSISTENT_COMMAND.search(value):
        return False
    if CLAUDE_PLUGIN_COMMAND.search(value) and re.search(
        r"--scope\s+local\b", value, re.IGNORECASE
    ):
        return False
    return not (
        CODEX_PLUGIN_COMMAND.search(value)
        and (temporary_codex_home or temporary_codex_environment(value))
    )


def temporary_codex_environment(value: str) -> bool:
    match = re.search(r"codex_home\s*=\s*([^\s;]+)", value, re.IGNORECASE)
    return match is not None and temporary_location(match.group(1))


def temporary_location(value: str) -> bool:
    normalized = value.replace("\\", "/").lower()
    return any(marker in normalized for marker in ("temp", "tmp", "mktemp"))


def protected_target(value: str) -> bool:
    normalized = value.replace("\\", "/").lower()
    protected_name = any(
        marker in normalized
        for marker in (
            ".claude",
            ".codex",
            ".gitconfig",
            "/.profile",
            "/.bashrc",
            "/.zshrc",
            "$profile",
        )
    )
    global_home = any(
        marker in normalized
        for marker in (
            "path.home",
            "expanduser",
            "~",
            "$home",
            "$env:home",
            "$env:userprofile",
            "%userprofile%",
            "/users/",
        )
    )
    return protected_name and (global_home or "$profile" in normalized)


def current_generated(root: Path) -> tuple[dict[str, bytes], dict[str, Path]]:
    generated: dict[str, bytes] = {}
    paths: dict[str, Path] = {}
    directory = root / "plugins"
    if not directory.is_dir():
        return generated, paths
    for path in directory.rglob("*"):
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            generated[relative] = path.read_bytes()
            paths[relative] = path
    return generated, paths


def payload_context(root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    path = root / ".agents/plugins/payloads.json"
    if not path.is_file():
        return {}, {}
    try:
        payloads = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}, {}
    if not isinstance(payloads, dict):
        return {}, {}
    declared = payloads.get("payloads", {})
    publications = (
        {
            package: owners[0]
            for package, owners in declared.items()
            if isinstance(package, str)
            and isinstance(owners, list)
            and len(owners) == 1
            and isinstance(owners[0], str)
        }
        if isinstance(declared, dict)
        else {}
    )
    return payloads, publications


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    arguments = parser.parse_args()
    root = arguments.root.resolve()
    payloads, publications = payload_context(root)
    generated, generated_paths = current_generated(root)
    findings = check(root, payloads, publications, generated, generated_paths)
    for finding in findings:
        print(finding, file=sys.stderr)
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
