"""Find targeted writes to protected global host configuration."""

import ast
import json
import re
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
) -> list[Finding]:
    """Check known global-write sinks in authored and generated payload scripts.

    This is targeted sink and target analysis. It does not prove dynamic code safe.
    """
    approved = approved_installers(root, payloads, publications, generated)
    findings: list[Finding] = []
    for path in authored_scripts(root):
        findings.extend(
            scan(
                path.read_text(encoding="utf-8"),
                path.relative_to(root).as_posix(),
                path == root / "install.ps1",
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
) -> set[str]:
    source = root / "install.ps1"
    if not source.is_file():
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
        if generated.get(virtual) == installer:
            approved.add(virtual)
    approved.update(sources_installers(root, installer, generated))
    return approved


def sources_installers(
    root: Path, installer: bytes, generated: Mapping[str, bytes]
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
        if generated.get(virtual) == installer:
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


def authored_scripts(root: Path) -> Iterable[Path]:
    for directory in (".agents", ".claude", ".codex", ".github"):
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
    installer = root / "install.ps1"
    if installer.is_file():
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
    return findings


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
    for number, line in enumerate(source.splitlines(), start=1):
        match = ASSIGNMENT.match(line)
        if match:
            aliases[match.group(1).lower()] = substitute(match.group(2), aliases)
        expanded = substitute(line, aliases)
        if PERSISTENT_COMMAND.search(expanded) or POWER_SHELL_ENVIRONMENT.search(
            expanded
        ):
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


def persistent_command(value: str) -> bool:
    return bool(PERSISTENT_COMMAND.search(value))


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
