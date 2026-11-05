from __future__ import annotations

import os
import re
import shlex
from pathlib import Path

SKILL = "SKILL.md"
VERBS = re.compile(
    r"\b(?:mv|cp|rm|rmdir|del|erase|rd|move|copy|mi|cpi|ri|rni|ren"
    r"|Move-Item|Copy-Item|Remove-Item|Rename-Item)\b",
    re.IGNORECASE,
)
WRITES = re.compile(
    r"write|open\([^)]*,\s*(?:mode\s*=\s*)?['\"][^'\"]*[wax+]|['\"]\+?>|Set-Content"
    r"|Add-Content|Out-File|unlink|rename|replace\(|rmtree|shutil|os\.remove|rmSync"
    r"|Remove-Item|Move-Item|Copy-Item",
    re.IGNORECASE,
)
LITERAL = re.compile(r"[^\s'\"`;|&<>(){}=,]*SKILL\.md")
IO_FILE = re.compile(
    r"\[(?:System\.)?IO\.File\]::(?:Write|Append|Create|Copy|Move|Delete|Replace|Open)",
    re.IGNORECASE,
)
HEREDOC = re.compile(r"(?<!<)<<(?!<)-?\s*(['\"]?)([A-Za-z_][\w.-]*)\1")
MARK = "\0heredoc"
PUNCT = "();<>|&\n"
OP = "\0"
SHELLS = {
    "bash": "bash",
    "sh": "bash",
    "pwsh": "powershell",
    "powershell": "powershell",
}
WRAPPERS = {"sudo", "env", "command", "exec", "time", "nohup", "nice"}
PS_CD = {"cd", "chdir", "sl", "set-location", "pushd", "push-location"}
PS_WRITE = {
    "set-content",
    "sc",
    "add-content",
    "ac",
    "out-file",
    "new-item",
    "ni",
    "tee-object",
    "tee",
    "clear-content",
    "clc",
}
PS_DELETE = {"remove-item", "ri", "rm", "del", "erase", "rd", "rmdir"}
PS_MOVE = {"move-item", "mi", "move", "mv", "rename-item", "rni", "ren"}
PS_COPY = {"copy-item", "cpi", "copy", "cp"}
PS_SWITCHES = {
    "-recurse",
    "-r",
    "-force",
    "-passthru",
    "-whatif",
    "-confirm",
    "-container",
    "-nonewline",
    "-append",
    "-noclobber",
}
PS_PATHS = ("-path", "-literalpath", "-lp", "-pspath", "-filepath")
DEPTH = 6
HERE_STRING = re.compile(r"@([\"'])[ \t]*\r?\n(?:.*?\r?\n)?\1@", re.DOTALL)


def required_procedures(path: str | None, cwd: str | None) -> set[str]:
    if not path:
        return set()
    target = Path(path)
    if not target.is_absolute() and cwd:
        target = Path(cwd) / target
    if target.name != "SKILL.md":
        return set()
    return {"skill:update"} if target.exists() else {"skill:new", "skill:update"}


def shell_targets(command: str, cwd: str | None, shell: str) -> list[str]:
    if SKILL not in command and not VERBS.search(command):
        return []
    parse = _powershell if shell == "powershell" else _bash
    found = parse(command, Path(cwd) if cwd else Path.cwd())
    return list(
        dict.fromkeys(os.path.normpath(path) for path in found if path.name == SKILL)
    )


def _path(text: str, base: Path) -> Path:
    text = os.path.expandvars(text)
    if os.name == "nt" and re.match(r"/[A-Za-z](?:/|$)", text):
        text = text[1] + ":/" + text[3:]
    path = Path(text).expanduser()
    return path if path.is_absolute() else base / path


def _expand(path: Path) -> list[Path]:
    for index, part in enumerate(path.parts):
        if any(char in part for char in "*?["):
            pattern = str(Path(*path.parts[index:]))
            return sorted(Path(*path.parts[:index]).glob(pattern)) or [path]
    return [path]


def _skills(path: Path, depth: int = DEPTH) -> list[Path]:
    if path.name == SKILL:
        return [path]
    try:
        if path.is_symlink():
            return []
        with os.scandir(path) as entries:
            children = list(entries)
    except OSError:
        return []
    for entry in children:
        if entry.name == SKILL and entry.is_file(follow_symlinks=False):
            return [Path(entry.path)]
    for entry in children if depth else []:
        if entry.name != ".git" and entry.is_dir(follow_symlinks=False):
            found = _skills(Path(entry.path), depth - 1)
            if found:
                return found
    return []


def _onto(source: Path, skill: Path, destination: Path) -> Path:
    if skill == source:
        return destination / SKILL if destination.is_dir() else destination
    relative = skill.relative_to(source)
    if destination.is_dir():
        return destination / source.name / relative
    return destination / relative


def _transfer(sources: list[Path], destination: Path | None, moved: bool) -> list[Path]:
    targets = [] if destination is None else [destination]
    for source in sources:
        for skill in _skills(source):
            if moved:
                targets.append(skill)
            if destination is not None:
                targets.append(_onto(source, skill, destination))
    return targets


def _heredocs(command: str) -> tuple[str, list[str]]:
    kept: list[str] = []
    bodies: list[str] = []
    pending: list[tuple[str, list[str]]] = []

    def mark(match: re.Match[str]) -> str:
        index = len(bodies) + len(pending)
        pending.append((match[2], []))
        return f"<< {MARK}{index}"

    for line in command.split("\n"):
        if pending:
            delimiter, collected = pending[0]
            if line.strip() == delimiter:
                bodies.append("\n".join(collected))
                pending.pop(0)
            else:
                collected.append(line)
            continue
        kept.append(HEREDOC.sub(mark, line))
    bodies.extend("\n".join(collected) for _, collected in pending)
    return "\n".join(kept), bodies


def _bash(command: str, base: Path) -> list[Path]:
    text, bodies = _heredocs(command)
    lexer = shlex.shlex(text, posix=True, punctuation_chars=PUNCT)
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:
        return []
    targets: list[Path] = []
    stack: list[Path] = []
    words: list[str] = []
    outputs: list[str] = []
    inputs: list[str] = []
    redirect = ""
    for token in [*tokens, ";"]:
        if redirect:
            if ">" in redirect and not token.isdigit() and token != "-":
                outputs.append(token)
            elif redirect.endswith("<<<"):
                inputs.append(token)
            elif token.startswith(MARK):
                inputs.append(bodies[int(token.removeprefix(MARK))])
            redirect = ""
        elif token and set(token) <= set(PUNCT):
            if "<" in token or ">" in token:
                if words and words[-1].isdigit():
                    words.pop()
                redirect = token
                continue
            targets += [_path(output, base) for output in outputs]
            base, found = _command(words, inputs, base)
            targets += found
            for char in token:
                if char == "(":
                    stack.append(base)
                elif char == ")" and stack:
                    base = stack.pop()
            words, outputs, inputs = [], [], []
        else:
            words.append(token)
    return targets


def _operands(arguments: list[str]) -> list[str]:
    operands: list[str] = []
    options = True
    for argument in arguments:
        if options and argument == "--":
            options = False
        elif not (options and argument.startswith("-") and argument != "-"):
            operands.append(argument)
    return operands


def _code(name: str, arguments: list[str]) -> tuple[str, list[str]]:
    for index, argument in enumerate(arguments[:-1]):
        rest = arguments[index + 1 :]
        if name in {"pwsh", "powershell"}:
            if len(argument) > 1 and "-command".startswith(argument.lower()):
                return "powershell", [" ".join(rest)]
        elif name == "node":
            if argument in {"-e", "-p", "--eval", "--print"}:
                return "code", rest[:1]
        elif re.fullmatch(r"-\w*[eE]" if name == "perl" else r"-\w*c", argument):
            return "bash" if name in {"bash", "sh"} else "code", rest[:1]
    return "", []


def _interpreted(
    name: str, arguments: list[str], inputs: list[str], base: Path
) -> list[Path]:
    kind, sources = _code(name, arguments)
    if not kind:
        kind, sources = SHELLS.get(name, "code"), inputs
    targets: list[Path] = []
    for source in sources:
        if kind == "bash":
            targets += _bash(source, base)
        elif kind == "powershell":
            targets += _powershell(source, base)
        elif SKILL in source and WRITES.search(source):
            targets += [_path(literal, base) for literal in LITERAL.findall(source)]
    return targets


def _command(
    words: list[str], inputs: list[str], base: Path
) -> tuple[Path, list[Path]]:
    while words and (words[0] in WRAPPERS or re.match(r"[A-Za-z_]\w*=", words[0])):
        words = words[1:]
    if not words:
        return base, []
    name = Path(words[0]).name.lower().removesuffix(".exe")
    arguments = words[1:]
    if name in {"cd", "pushd"}:
        return _path(next(iter(_operands(arguments)), "~"), base), []
    if name in SHELLS or re.fullmatch(r"py|python3?(?:\.\d+)?|node|perl", name):
        found = _interpreted(name, arguments, inputs, base)
        if name != "perl":
            return base, found
    else:
        found = []
    here = base
    if name == "git":
        while len(arguments) > 1 and arguments[0].startswith("-"):
            if arguments[0] == "-C":
                here = _path(arguments[1], here)
            arguments = arguments[2 if arguments[0] in {"-C", "-c"} else 1 :]
        if not arguments or arguments[0] not in {"mv", "rm"}:
            return base, []
        name, arguments = arguments[0], arguments[1:]
    paths = [
        path
        for operand in _operands(arguments)
        for path in _expand(_path(operand, here))
    ]
    if name in {"tee", "touch", "truncate"}:
        return base, paths
    if name in {"sed", "perl"}:
        in_place = any(
            re.match(r"--in-place|-(?!-)\S*i", argument) for argument in arguments
        )
        return base, found + (paths if in_place else [])
    if name == "rm":
        return base, [skill for path in paths for skill in _skills(path)]
    if name not in {"mv", "cp", "install", "ln"}:
        return base, []
    directory = None
    for index, argument in enumerate(arguments[:-1]):
        if argument == "-t":
            directory = arguments[index + 1]
    for argument in arguments:
        if argument.startswith("--target-directory="):
            directory = argument.partition("=")[2]
    destination = None
    if directory is not None:
        destination = _path(directory, here)
        paths = [path for path in paths if path != destination]
    elif len(paths) > 1:
        destination = paths.pop()
    return base, _transfer(paths, destination, name == "mv")


def _ps_tokens(command: str) -> list[str]:
    tokens: list[str] = []
    word, quote, active = "", "", False
    chars = iter(re.sub(r"`\r?\n", " ", command))
    for char in chars:
        if quote:
            if char == quote:
                quote = ""
            elif char == "`" and quote == '"':
                word += next(chars, "")
            else:
                word += char
        elif char in "'\"":
            quote, active = char, True
        elif char == "`":
            word, active = word + next(chars, ""), True
        elif char in " \t\r;|&\n(){}>":
            if char == ">" and word in {"1", "2", "3", "4", "5", "6", "*"}:
                active = False
            if active:
                tokens.append(word)
            word, active = "", False
            if char not in " \t\r":
                tokens.append(OP + char)
        else:
            word, active = word + char, True
    if active:
        tokens.append(word)
    return tokens


def _powershell(command: str, base: Path) -> list[Path]:
    command = HERE_STRING.sub("''", command)
    targets: list[Path] = []
    if IO_FILE.search(command):
        targets += [_path(literal, base) for literal in LITERAL.findall(command)]
    words: list[str] = []
    outputs: list[str] = []
    redirect = False
    for token in [*_ps_tokens(command), OP + ";"]:
        if token == OP + ">":
            redirect = True
        elif redirect and not token.startswith(OP):
            outputs.append(token)
            redirect = False
        elif token.startswith(OP):
            redirect = False
            targets += [_path(output, base) for output in outputs]
            base, found = _ps_command(words, base)
            targets += found
            words, outputs = [], []
        else:
            words.append(token)
    return targets


def _ps_command(words: list[str], base: Path) -> tuple[Path, list[Path]]:
    if len(words) > 1 and words[1] == "=":
        words = words[2:]
    if not words:
        return base, []
    name = words[0].lower()
    if name not in PS_CD | PS_WRITE | PS_DELETE | PS_MOVE | PS_COPY:
        return _command(words, [], base)
    named: dict[str, str] = {}
    positional: list[str] = []
    arguments = iter(words[1:])
    for argument in arguments:
        if argument.startswith("-") and len(argument) > 1:
            key, colon, value = argument.partition(":")
            key = key.lower()
            if not colon and key not in PS_SWITCHES:
                value = next(arguments, "")
            named[key] = value
        else:
            positional.append(argument)
    if named.get("-whatif", "$false").lower() != "$false":
        return base, []

    def paths(values: list[str]) -> list[Path]:
        return [
            path
            for value in values
            for part in value.split(",")
            if part.strip()
            for path in _expand(_path(part.strip(), base))
        ]

    given = [named[key] for key in PS_PATHS if key in named]
    if name in PS_CD:
        return (paths(given or positional[:1]) or [Path.home()])[0], []
    if name in PS_DELETE:
        return base, [
            skill for path in paths(given + positional) for skill in _skills(path)
        ]
    sources = paths(given or positional[:1])
    if name in PS_WRITE:
        if "-name" in named:
            sources = [path / named["-name"] for path in sources or [base]]
        return base, sources
    rest = positional if given else positional[1:]
    if name in {"rename-item", "rni", "ren"}:
        new_name = named.get("-newname") or next(iter(rest), "")
        destination = sources[0].parent / new_name if sources and new_name else None
    else:
        values = [named["-destination"]] if "-destination" in named else rest[:1]
        destination = next(iter(paths(values)), None)
    return base, _transfer(sources, destination, name not in PS_COPY)
