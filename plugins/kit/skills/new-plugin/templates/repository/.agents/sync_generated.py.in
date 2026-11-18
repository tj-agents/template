#!/usr/bin/env python3
"""Generate a plugin repository's host discovery entries, marketplaces and installable payloads.

Vendored from the kit repository and pinned by `.agents/plugins/kit.json`: change it in kit, never here.
"""

from __future__ import annotations

import argparse
from html import unescape
import json
import os
from pathlib import Path, PurePosixPath
from string import punctuation
from urllib.parse import unquote
import posixpath
import re
import shutil
import stat


KIT_VERSION = "1.4.2"
FRONTMATTER = re.compile(r"\A---\n(?P<header>.*?)\n---\n(?P<body>.*)\Z", re.DOTALL)
NAME = re.compile(r"^[a-z][a-z0-9-]*$")
KIND = re.compile(r"^[a-z]+$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/([a-z][a-z0-9-]*)$")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
URL_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
BARE_SKILL_REFERENCE = re.compile(r"`([a-z][a-z0-9-]+)`\s+skill(?:'s)?")
SKILL_DIRECTORY_REFERENCE = re.compile(r"<skill-directory>/([^\s`'\")\]]+)")
REQUIRED_METADATA = ("name", "description", "kind", "domain", "profile", "applicability", "requires", "provenance")
REPOSITORY_TYPES = ("stack", "tool", "utility")
RESERVED_AGENT_DIRS = {"continuation", "plugins", "tiers", "tests", "hooks"}
IGNORED_PARTS = {"__pycache__"}
IGNORED_SUFFIXES = {".pyc"}
HOSTS = ("claude", "codex")
ADAPTER_ROOTS = {"claude": ".claude/skills", "codex": ".codex/skills"}
MANIFEST_ROOT = ".agents/plugins/manifests"
MARKETPLACE_OUTPUTS = {"claude": ".claude-plugin/marketplace.json", "codex": ".agents/plugins/marketplace.json"}
MARKETPLACE_FIELDS = {"claude": {"name", "description", "owner"}, "codex": {"name", "interface"}}
CODEX_POLICY = {"installation": "INSTALLED_BY_DEFAULT", "authentication": "ON_INSTALL"}
GENERATED_ROOTS = (
    ".claude/skills",
    ".codex/skills",
    "plugins",
    ".claude-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
    ".agents/INDEX.md",
)
TIER_MATCHERS = ("files", "globs", "content", "remote")
PAYLOAD_FIELDS = {"payloads", "dependencies", "compatibilitySkillAliases"}

WINDOWS_PATH_UPPERCASE_RANGES = (
    (0x0061, 0x007A, 1, -32),
    (0x00E0, 0x00F6, 1, -32),
    (0x00F8, 0x00FE, 1, -32),
    (0x00FF, 0x00FF, 1, 121),
    (0x0101, 0x012F, 2, -1),
    (0x0133, 0x0137, 2, -1),
    (0x013A, 0x0148, 2, -1),
    (0x014B, 0x0177, 2, -1),
    (0x017A, 0x017E, 2, -1),
    (0x0180, 0x0180, 1, 195),
    (0x0183, 0x0185, 2, -1),
    (0x0188, 0x0188, 1, -1),
    (0x018C, 0x018C, 1, -1),
    (0x0192, 0x0192, 1, -1),
    (0x0195, 0x0195, 1, 97),
    (0x0199, 0x0199, 1, -1),
    (0x019A, 0x019A, 1, 163),
    (0x019E, 0x019E, 1, 130),
    (0x01A1, 0x01A5, 2, -1),
    (0x01A8, 0x01A8, 1, -1),
    (0x01AD, 0x01AD, 1, -1),
    (0x01B0, 0x01B0, 1, -1),
    (0x01B4, 0x01B6, 2, -1),
    (0x01B9, 0x01B9, 1, -1),
    (0x01BD, 0x01BD, 1, -1),
    (0x01BF, 0x01BF, 1, 56),
    (0x01C6, 0x01C6, 1, -2),
    (0x01C9, 0x01C9, 1, -2),
    (0x01CC, 0x01CC, 1, -2),
    (0x01CE, 0x01DC, 2, -1),
    (0x01DD, 0x01DD, 1, -79),
    (0x01DF, 0x01EF, 2, -1),
    (0x01F3, 0x01F3, 1, -2),
    (0x01F5, 0x01F5, 1, -1),
    (0x01F9, 0x021F, 2, -1),
    (0x0223, 0x0233, 2, -1),
    (0x023C, 0x023C, 1, -1),
    (0x0242, 0x0242, 1, -1),
    (0x0247, 0x024F, 2, -1),
    (0x0250, 0x0250, 1, 10783),
    (0x0251, 0x0251, 1, 10780),
    (0x0253, 0x0253, 1, -210),
    (0x0254, 0x0254, 1, -206),
    (0x0256, 0x0257, 1, -205),
    (0x0259, 0x0259, 1, -202),
    (0x025B, 0x025B, 1, -203),
    (0x0260, 0x0260, 1, -205),
    (0x0263, 0x0263, 1, -207),
    (0x0268, 0x0268, 1, -209),
    (0x0269, 0x0269, 1, -211),
    (0x026B, 0x026B, 1, 10743),
    (0x026F, 0x026F, 1, -211),
    (0x0271, 0x0271, 1, 10749),
    (0x0272, 0x0272, 1, -213),
    (0x0275, 0x0275, 1, -214),
    (0x027D, 0x027D, 1, 10727),
    (0x0280, 0x0280, 1, -218),
    (0x0283, 0x0283, 1, -218),
    (0x0288, 0x0288, 1, -218),
    (0x0289, 0x0289, 1, -69),
    (0x028A, 0x028B, 1, -217),
    (0x028C, 0x028C, 1, -71),
    (0x0292, 0x0292, 1, -219),
    (0x0371, 0x0373, 2, -1),
    (0x0377, 0x0377, 1, -1),
    (0x037B, 0x037D, 1, 130),
    (0x03AC, 0x03AC, 1, -38),
    (0x03AD, 0x03AF, 1, -37),
    (0x03B1, 0x03C1, 1, -32),
    (0x03C3, 0x03CB, 1, -32),
    (0x03CC, 0x03CC, 1, -64),
    (0x03CD, 0x03CE, 1, -63),
    (0x03D7, 0x03D7, 1, -8),
    (0x03D9, 0x03EF, 2, -1),
    (0x03F2, 0x03F2, 1, 7),
    (0x03F8, 0x03F8, 1, -1),
    (0x03FB, 0x03FB, 1, -1),
    (0x0430, 0x044F, 1, -32),
    (0x0450, 0x045F, 1, -80),
    (0x0461, 0x0481, 2, -1),
    (0x048B, 0x04BF, 2, -1),
    (0x04C2, 0x04CE, 2, -1),
    (0x04CF, 0x04CF, 1, -15),
    (0x04D1, 0x0523, 2, -1),
    (0x0561, 0x0586, 1, -48),
    (0x1D79, 0x1D79, 1, 35332),
    (0x1D7D, 0x1D7D, 1, 3814),
    (0x1E01, 0x1E95, 2, -1),
    (0x1EA1, 0x1EFF, 2, -1),
    (0x1F00, 0x1F07, 1, 8),
    (0x1F10, 0x1F15, 1, 8),
    (0x1F20, 0x1F27, 1, 8),
    (0x1F30, 0x1F37, 1, 8),
    (0x1F40, 0x1F45, 1, 8),
    (0x1F51, 0x1F57, 2, 8),
    (0x1F60, 0x1F67, 1, 8),
    (0x1F70, 0x1F71, 1, 74),
    (0x1F72, 0x1F75, 1, 86),
    (0x1F76, 0x1F77, 1, 100),
    (0x1F78, 0x1F79, 1, 128),
    (0x1F7A, 0x1F7B, 1, 112),
    (0x1F7C, 0x1F7D, 1, 126),
    (0x1F80, 0x1F87, 1, 8),
    (0x1F90, 0x1F97, 1, 8),
    (0x1FA0, 0x1FA7, 1, 8),
    (0x1FB0, 0x1FB1, 1, 8),
    (0x1FB3, 0x1FB3, 1, 9),
    (0x1FC3, 0x1FC3, 1, 9),
    (0x1FD0, 0x1FD1, 1, 8),
    (0x1FE0, 0x1FE1, 1, 8),
    (0x1FE5, 0x1FE5, 1, 7),
    (0x1FF3, 0x1FF3, 1, 9),
    (0x214E, 0x214E, 1, -28),
    (0x2170, 0x217F, 1, -16),
    (0x2184, 0x2184, 1, -1),
    (0x24D0, 0x24E9, 1, -26),
    (0x2C30, 0x2C5E, 1, -48),
    (0x2C61, 0x2C61, 1, -1),
    (0x2C65, 0x2C65, 1, -10795),
    (0x2C66, 0x2C66, 1, -10792),
    (0x2C68, 0x2C6C, 2, -1),
    (0x2C73, 0x2C73, 1, -1),
    (0x2C76, 0x2C76, 1, -1),
    (0x2C81, 0x2CE3, 2, -1),
    (0x2D00, 0x2D25, 1, -7264),
    (0xA641, 0xA65F, 2, -1),
    (0xA663, 0xA66D, 2, -1),
    (0xA681, 0xA697, 2, -1),
    (0xA723, 0xA72F, 2, -1),
    (0xA733, 0xA76F, 2, -1),
    (0xA77A, 0xA77C, 2, -1),
    (0xA77F, 0xA787, 2, -1),
    (0xA78C, 0xA78C, 1, -1),
    (0xFF41, 0xFF5A, 1, -32),
)
WINDOWS_PATH_UPPERCASE = {
    value: value + delta
    for start, end, step, delta in WINDOWS_PATH_UPPERCASE_RANGES
    for value in range(start, end + 1, step)
}


def package_component(value: str, where: str) -> None:
    reserved = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    reserved.update(f"{prefix}{number}" for prefix in ("COM", "LPT") for number in "123456789\u00b9\u00b2\u00b3")
    stem = value.split(".", 1)[0].rstrip(" ").upper()
    if (
        not value or value in (".", "..") or value.endswith((" ", "."))
        or any(ord(character) < 32 or character in '<>:"\\|?*' for character in value)
        or stem in reserved
    ):
        raise ValueError(f"{where}: Windows-unsafe path component {value!r}")

def package_relative(value: str, where: str, *, native: bool = False) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{where}: expected a nonempty relative path")
    relative = value
    if native:
        relative = relative.removeprefix("./").removesuffix("/")
    path = PurePosixPath(relative)
    if (
        not relative or "\\" in relative or ":" in relative or "\x00" in relative
        or path.is_absolute() or ".." in path.parts
        or path.as_posix() != relative or relative == "."
    ):
        raise ValueError(f"{where}: unsafe relative path {value!r}")
    for component in path.parts:
        package_component(component, where)
    return relative

def package_identities(files: dict[str, bytes]) -> None:
    identities: dict[bytes, tuple[str, bool]] = {}
    for key, data in files.items():
        package_relative(key, "shipped file map")
        if not isinstance(data, bytes):
            raise ValueError(f"{key}: shipped file contents must be bytes")
        nodes = [(key, True)] + [
            (ancestor.as_posix(), False) for ancestor in PurePosixPath(key).parents
            if ancestor.as_posix() != "."
        ]
        for path, is_file in nodes:
            identity = path.translate(WINDOWS_PATH_UPPERCASE).encode("utf-16-le", "surrogatepass")
            previous = identities.get(identity)
            if previous is not None:
                spelling, previous_is_file = previous
                if spelling != path:
                    raise ValueError(f"{key}: Windows path identity collision: {spelling!r}, {path!r}")
                if previous_is_file != is_file:
                    raise ValueError(f"{key}: shipped file map contains a file/directory conflict")
            identities[identity] = (path, is_file)

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def load(path: Path):
    try:
        return json.loads(read(path))
    except FileNotFoundError:
        raise ValueError(f"Missing {path.as_posix()}") from None
    except json.JSONDecodeError as error:
        raise ValueError(f"{path.as_posix()}: invalid JSON ({error.msg})") from None


def dump(value) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def ignored(path: PurePosixPath | Path) -> bool:
    return bool(IGNORED_PARTS.intersection(path.parts)) or path.suffix in IGNORED_SUFFIXES


def is_link_or_junction(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    if is_junction is not None and is_junction():
        return True
    if os.name != "nt":
        return False
    try:
        attributes = path.lstat().st_file_attributes
    except FileNotFoundError:
        return False
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def package_text(files: dict[str, bytes], path: str) -> str:
    if path not in files:
        raise ValueError(f"{path}: missing shipped file")
    try:
        return files[path].decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeError as error:
        raise ValueError(f"{path}: invalid UTF-8 ({error})") from None


def package_present(files: dict[str, bytes], path: str) -> bool:
    return path in files or any(key.startswith(path + "/") for key in files)


def package_target(
    files: dict[str, bytes], package: str, directory: str, value: str, where: str
) -> str:
    if (
        not value or "\\" in value or ":" in value or "\x00" in value
        or PurePosixPath(value).is_absolute()
    ):
        raise ValueError(f"{where}: unsafe local reference {value!r}")
    target = posixpath.normpath(posixpath.join(directory, value))
    prefix = f"plugins/{package}"
    if target != prefix and not target.startswith(prefix + "/"):
        raise ValueError(f"{where}: reference leaves package: {value!r}")
    package_relative(target, where)
    if not package_present(files, target):
        raise ValueError(f"{where}: reference is not shipped: {value!r}")
    return target


def package_markdown_value(value: str) -> str:
    return unescape(re.sub(
        r"\\(.)",
        lambda match: match[1] if match[1] in punctuation else match[0],
        value,
    ))


def package_code_end(text: str, start: int) -> int | None:
    opening = re.match(r"`+", text[start:])
    if opening is None:
        return None
    length = len(opening[0])
    for closing in re.finditer(r"`+", text[start + length:]):
        if len(closing[0]) == length:
            end = start + length + closing.end()
            try:
                package_inline_boundary(text, start, end)
            except ValueError:
                return None
            return end
    return None


def package_quote_line(line: str, count: int | None = None) -> tuple[int, str] | None:
    quotes = 0
    while count is None or quotes < count:
        marker = re.match(r" {0,3}>[ \t]?", line)
        if marker is None:
            if count is not None:
                return None
            break
        line = line[marker.end():]
        quotes += 1
    return quotes, line


def package_inline_boundary(text: str, start: int, end: int) -> None:
    if re.search(
        r"\n[ \t]*\n|\n[ \t]*(?:#{1,6}(?:[ \t]|$)|>|(?:[-+*]|\d{1,9}[.)])[ \t]+|`{3,}|~{3,}|(?:[-*_][ \t]*){3,}(?:\n|$)|[=-]+[ \t]*(?:\n|$)|<)",
        text[start:end],
    ):
        raise ValueError("ambiguous multiline inline token crosses a block boundary")


def package_tag_end(text: str, start: int) -> int | None:
    match = re.match(
        r"""</[A-Za-z][A-Za-z0-9-]*[ \t\n]*>|<[A-Za-z][A-Za-z0-9-]*(?:[ \t\n]+[A-Za-z_:][A-Za-z0-9_.:-]*(?:[ \t\n]*=[ \t\n]*(?:[^ \t\n"'=<>`]+|'[^']*'|"[^"]*"))?)*[ \t\n]*/?>""",
        text[start:],
    )
    if match is None:
        return None
    end = start + match.end()
    package_inline_boundary(text, start, end)
    return end


def package_comment_end(text: str, start: int) -> int | None:
    if text.startswith("<!-->", start):
        return start + 5
    if text.startswith("<!--->", start):
        return start + 6
    if text.startswith("<!--", start):
        closing = text.find("-->", start + 4)
        if closing >= 0:
            end = closing + 3
            package_inline_boundary(text, start, end)
            return end
    return None


def package_html_block(body: str, previous_blank: bool) -> str | None:
    value = body.lstrip(" ")
    if len(body) - len(value) > 3:
        return None
    special = re.match(r"(?i)<(script|pre|style|textarea)(?:[ \t>]|$)", value)
    if special:
        return r"(?i)</" + special[1] + r"[ \t]*>"
    for opening, ending in (("<!--", "-->"), ("<?", r"\?>"), ("<![CDATA[", r"\]\]>")):
        if value.startswith(opening):
            return ending
    if re.match(r"<![A-Z]", value):
        return ">"
    tags = (
        "address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|"
        "dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|"
        "frame|frameset|h1|h2|h3|h4|h5|h6|head|header|hr|html|iframe|legend|"
        "li|link|main|menu|menuitem|nav|noframes|ol|optgroup|option|p|param|"
        "search|section|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul"
    )
    if re.match(r"(?i)</?(?:" + tags + r")(?:[ \t/>]|$)", value):
        return ""
    end = package_tag_end(value, 0)
    if previous_blank and end is not None and not value[end:].strip():
        return ""
    return None


def package_active_markdown(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    characters = list(text)
    fence: tuple[str, int, int, int] | None = None
    indented: tuple[int, int] | None = None
    html_block: tuple[str, int, int] | None = None
    list_widths: list[int] = []
    list_quotes = 0
    label_limit = -1
    index = 0

    def mask(start: int, end: int) -> None:
        for position in range(start, end):
            if characters[position] != "\n":
                characters[position] = " "

    while index < len(text):
        line_start = text.rfind("\n", 0, index) + 1
        if index == line_start:
            end = text.find("\n", index)
            end = len(text) if end < 0 else end + 1
            line = text[index:end].removesuffix("\n")
            if html_block is not None:
                ending, quotes, width = html_block
                quoted = package_quote_line(line, quotes)
                if quoted is not None:
                    content = quoted[1]
                    indent = len(content) - len(content.lstrip(" "))
                    if not content.strip():
                        if not ending:
                            html_block = None
                        else:
                            mask(index, end)
                            index = end
                            continue
                    elif indent >= width:
                        if ending and re.search(ending, content[width:]):
                            html_block = None
                        mask(index, end)
                        index = end
                        continue
                    else:
                        html_block = None
                else:
                    html_block = None
            if fence is not None:
                delimiter, length, quotes, width = fence
                quoted = package_quote_line(line, quotes)
                if quoted is not None:
                    content = quoted[1]
                    indent = len(content) - len(content.lstrip(" "))
                    if not content.strip() or indent >= width:
                        closing = content[width:]
                        if re.fullmatch(r" {0,3}" + re.escape(delimiter) + "{" + str(length) + r",}[ \t]*", closing):
                            fence = None
                        mask(index, end)
                        index = end
                        continue
                fence = None
            quotes, content = package_quote_line(line)
            indent = len(content) - len(content.lstrip(" "))
            if quotes != list_quotes:
                list_widths = []
                list_quotes = quotes
            if content.strip():
                while list_widths and indent < list_widths[-1]:
                    list_widths.pop()
            marker = re.match(r" {0,3}(?:[-+*]|\d{1,9}[.)])[ \t]+", content)
            if marker is not None:
                width = marker.end()
                list_widths.append(width)
                body = content[width:]
            else:
                width = list_widths[-1] if list_widths else 0
                body = content[width:]
            previous_start = text.rfind("\n", 0, max(0, index - 1)) + 1
            previous_blank = index == 0 or not "".join(characters[previous_start:index]).strip()
            if indented is not None:
                if not content.strip() or (quotes, width) == indented and indent >= width + 4:
                    mask(index, end)
                    index = end
                    continue
                indented = None
            if marker is None and indent >= width + 4 and previous_blank:
                indented = quotes, width
                mask(index, end)
                index = end
                continue
            html_ending = package_html_block(body, previous_blank)
            if html_ending is not None:
                if not html_ending or not re.search(html_ending, body):
                    html_block = html_ending, quotes, width
                mask(index, end)
                index = end
                continue
            opening = re.match(r" {0,3}(`{3,}|~{3,})([^\n]*)$", body)
            if opening is not None and (opening[1][0] != "`" or "`" not in opening[2]):
                fence = opening[1][0], len(opening[1]), quotes, width
                mask(index, end)
                index = end
                continue
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == "<":
            end = package_tag_end(text, index)
            if end is not None:
                index = end
                continue
            end = package_comment_end(text, index)
            if end is not None:
                mask(index, end)
                characters[index] = "x"
                index = end
                continue
        if text[index] == "[":
            end = package_label_end(text, index)
            if end is not None:
                label_limit = max(label_limit, end)
                if text[end + 1:end + 2] == "(":
                    package_destination(text, end + 2, ")")
                elif text[end + 1:end + 2] == ":":
                    prefix = package_quote_line(text[line_start:index])[1]
                    marker = re.match(r" {0,3}(?:[-+*]|\d{1,9}[.)])[ \t]+", prefix)
                    prefix = prefix[marker.end():] if marker else prefix
                    if not prefix.strip():
                        package_destination(text, end + 2, None)
        if text[index] == "`":
            end = package_code_end(text, index)
            if end is not None:
                if index > label_limit:
                    mask(index, end)
                    characters[index] = "x"
                index = end
                continue
            index += len(re.match(r"`+", text[index:])[0])
            continue
        index += 1
    return "".join(characters)


def package_label_end(text: str, start: int) -> int | None:
    depth = 1
    index = start + 1
    while index < len(text):
        character = text[index]
        if character == "\\":
            index += 2
            continue
        if character == "<":
            end = package_tag_end(text, index)
            if end is None:
                end = package_comment_end(text, index)
            if end is not None:
                index = end
                continue
        if character == "`":
            end = package_code_end(text, index)
            if end is not None:
                index = end
                continue
            index += len(re.match(r"`+", text[index:])[0])
            continue
        if character == "[":
            depth += 1
        elif character == "]":
            depth -= 1
            if depth == 0:
                try:
                    package_inline_boundary(text, start, index + 1)
                except ValueError:
                    return None
                return index
        index += 1
    return None


def package_destination(text: str, start: int, closing: str | None) -> tuple[str, int] | None:
    index = start
    while index < len(text) and text[index].isspace():
        index += 1
    begin = index
    if index < len(text) and text[index] == "<":
        index += 1
        begin = index
        while index < len(text):
            if text[index] == "\\":
                index += 2
                continue
            if text[index] in ("\n", "<"):
                return None
            if text[index] == ">":
                value = text[begin:index]
                index += 1
                break
            index += 1
        else:
            return None
    else:
        depth = 0
        while index < len(text):
            character = text[index]
            if character == "\\":
                index += 2
                continue
            if character.isspace():
                break
            if character == "(":
                depth += 1
            elif character == ")":
                if depth == 0:
                    break
                depth -= 1
            index += 1
        if depth:
            return None
        value = text[begin:index]
    end = index
    if closing is None:
        line_end = text.find("\n", index)
        if line_end < 0:
            line_end = len(text)
        suffix = text[index:line_end].strip()
        if not suffix:
            return value, line_end
        if suffix[0] not in ('"', "'", "("):
            return None
    while index < len(text) and text[index].isspace():
        index += 1
    title_start = None
    if index > end and index < len(text) and text[index] in ('"', "'", "("):
        title_start = index
        delimiter = ")" if text[index] == "(" else text[index]
        index += 1
        while index < len(text) and text[index] != delimiter:
            index += 2 if text[index] == "\\" else 1
        if index >= len(text):
            return None
        index += 1
        title_end = index
        if closing is None:
            line_end = text.find("\n", index)
            if line_end < 0:
                line_end = len(text)
            if text[index:line_end].strip():
                return None
            package_inline_boundary(text, title_start, title_end)
            return value, line_end
        while index < len(text) and text[index].isspace():
            index += 1
    if closing is not None and index < len(text) and text[index] == closing:
        if title_start is not None:
            package_inline_boundary(text, title_start, title_end)
        return value, index + 1
    return None


def package_label_destinations(
    text: str, start: int, end: int, definitions: dict[str, str], ambiguous: set[str]
) -> list[str]:
    images: list[str] = []
    index = start
    while index < end:
        character = text[index]
        if character == "\\":
            index += 2
            continue
        if character == "`":
            closing = package_code_end(text, index)
            index = closing if closing is not None else index + len(re.match(r"`+", text[index:])[0])
            continue
        if character == "<":
            closing = package_tag_end(text, index)
            if closing is None:
                closing = package_comment_end(text, index)
            if closing is not None:
                index = closing
                continue
            closing = text.find(">", index + 1, end)
            if closing >= 0:
                value = text[index + 1:closing]
                if URL_SCHEME.match(value) and not any(character.isspace() for character in value):
                    raise ValueError("ambiguous nested active link in label")
        if character != "[":
            index += 1
            continue
        closing = package_label_end(text, index)
        if closing is None or closing >= end:
            index += 1
            continue
        label = text[index + 1:closing]
        after = closing + 1
        parsed = package_destination(text, after + 1, ")") if text[after:after + 1] == "(" else None
        value = None
        if parsed is not None:
            value, after = parsed
        else:
            while after < end and text[after].isspace():
                after += 1
            if text[after:after + 1] == "[":
                reference_end = package_label_end(text, after)
                if reference_end is not None and reference_end < end:
                    label = text[after + 1:reference_end] or label
                    after = reference_end + 1
            label = " ".join(package_markdown_value(label).split()).casefold()
            if label in ambiguous:
                raise ValueError(f"ambiguous reference definition cannot interrupt paragraph: {label!r}")
            value = definitions.get(label)
        if value is None:
            index += 1
            continue
        if index == 0 or text[index - 1] != "!":
            raise ValueError("ambiguous nested active link in label")
        images.append(value)
        index = after
    return images


def package_destinations(text: str):
    text = package_active_markdown(text)
    definitions: dict[str, str] = {}
    ambiguous: set[str] = set()
    spans: dict[int, int] = {}
    paragraph = False
    context = (0, 0)
    list_width = 0
    offset = 0
    consumed = 0
    for line in text.splitlines(keepends=True):
        quotes, content = package_quote_line(line)
        indent = len(content) - len(content.lstrip(" "))
        marker = re.match(r" {0,3}(?:[-+*]|\d{1,9}[.)])[ \t]+", content)
        if marker is not None:
            list_width = marker.end()
            paragraph = False
        elif content.strip() and indent < list_width:
            list_width = 0
        current = quotes, list_width
        if current != context:
            paragraph = False
            context = current
        body = content[list_width:]
        body_start = offset + len(line) - len(body)
        match = re.match(r" {0,3}\[((?:\\.|[^\]\\\n])+)\]:", body)
        if offset < consumed:
            offset += len(line)
            continue
        if match is not None:
            parsed = package_destination(text, body_start + match.end(), None)
            if parsed is not None:
                value, end = parsed
                label = " ".join(package_markdown_value(match[1]).split()).casefold()
                if paragraph:
                    ambiguous.add(label)
                else:
                    definitions.setdefault(label, value)
                spans[offset] = end
                consumed = end
                offset += len(line)
                continue
        if not body.strip() or re.match(
            r" {0,3}(?:#{1,6}(?:[ \t]|$)|(?:[-*_][ \t]*){3,}$|[=-]+[ \t]*$)", body
        ):
            paragraph = False
        else:
            paragraph = True
        offset += len(line)
    index = 0
    while index < len(text):
        if index in spans:
            index = max(index + 1, spans[index])
            continue
        if text[index] == "\\":
            index += 2
            continue
        if text[index] == "`":
            end = package_code_end(text, index)
            index = end if end is not None else index + len(re.match(r"`+", text[index:])[0])
            continue
        if text[index] == "<":
            tag_end = package_tag_end(text, index)
            if tag_end is not None:
                index = tag_end
                continue
            end = text.find(">", index + 1)
            if end >= 0:
                value = text[index + 1:end]
                if URL_SCHEME.match(value) and not any(character.isspace() for character in value):
                    yield value
                    index = end + 1
                    continue
        if text[index] != "[":
            index += 1
            continue
        end = package_label_end(text, index)
        if end is None:
            index += 1
            continue
        label = text[index + 1:end]
        label_start, label_end = index + 1, end
        after = end + 1
        if after < len(text) and text[after] == "(":
            parsed = package_destination(text, after + 1, ")")
            if parsed is not None:
                value, after = parsed
                yield from package_label_destinations(text, label_start, label_end, definitions, ambiguous)
                yield value
                index = after
                continue
        while after < len(text) and text[after].isspace():
            after += 1
        if after < len(text) and text[after] == "[":
            reference_end = package_label_end(text, after)
            if reference_end is not None:
                label = text[after + 1:reference_end] or label
                end = reference_end
        label = " ".join(package_markdown_value(label).split()).casefold()
        if label in ambiguous:
            raise ValueError(f"ambiguous reference definition cannot interrupt paragraph: {label!r}")
        if label in definitions:
            yield from package_label_destinations(text, label_start, label_end, definitions, ambiguous)
            yield definitions[label]
            index = end + 1
        else:
            index += 1


def package_links(text: str):
    for destination in package_destinations(text):
        value = package_markdown_value(destination)
        if value.startswith("#"):
            continue
        if re.match(r"(?i)^(?:[a-z]:|file:)", value):
            yield value
            continue
        if URL_SCHEME.match(value):
            continue
        value = unquote(value, errors="strict").split("#", 1)[0]
        if value:
            yield value

def load_config(root: Path) -> dict:
    config = load(root / ".agents/plugins/kit.json")
    if not isinstance(config, dict):
        raise ValueError(".agents/plugins/kit.json: must be a JSON object")
    if config.get("schema_version") != 1:
        raise ValueError(".agents/plugins/kit.json: schema_version must be 1")
    if config.get("kit") != KIT_VERSION:
        raise ValueError(
            f".agents/plugins/kit.json pins kit {config.get('kit')} but this generator is kit {KIT_VERSION}; "
            "run kit:update"
        )
    if config.get("type") not in REPOSITORY_TYPES:
        raise ValueError(f".agents/plugins/kit.json: type must be one of {', '.join(REPOSITORY_TYPES)}")
    match = REPOSITORY.fullmatch(str(config.get("repository", "")))
    if match is None:
        raise ValueError(".agents/plugins/kit.json: repository must be owner/name with a lowercase name")
    unknown = set(config) - {"schema_version", "kit", "type", "repository"}
    if unknown:
        raise ValueError(f".agents/plugins/kit.json: unknown fields {sorted(unknown)}")
    return {**config, "namespace": match.group(1)}


def metadata(body: str, source: str) -> dict[str, str]:
    match = FRONTMATTER.match(body)
    if match is None:
        raise ValueError(f"{source}: missing frontmatter")
    values: dict[str, str] = {}
    for line in match.group("header").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    for field in REQUIRED_METADATA:
        if not values.get(field):
            raise ValueError(f"{source}: missing {field}")
    for field in ("name", "profile"):
        if not NAME.fullmatch(values[field]):
            raise ValueError(f"{source}: {field} must be a lowercase name")
    if not KIND.fullmatch(values["kind"]):
        raise ValueError(f"{source}: kind must be one lowercase word")
    return values


def is_skill_folder(path: Path) -> bool:
    return path.is_dir() and not ignored(path) and not is_link_or_junction(path) and (path / "SKILL.md").is_file()


def load_skill(root: Path, plugin: str, kind: str, directory: Path, name: str, namespace: str) -> dict:
    path = directory / "SKILL.md"
    relative = path.relative_to(root).as_posix()
    raw = path.read_bytes()
    if b"\xef\xbb\xbf" in raw:
        raise ValueError(f"{relative}: embedded UTF-8 BOM")
    body = raw.decode("utf-8").replace("\r\n", "\n")
    values = metadata(body, relative)
    if values["name"] != name:
        raise ValueError(f"{relative}: name must be {name}, its folder path below the kind folder joined by hyphens")
    if values["kind"] != kind:
        raise ValueError(f"{relative}: kind must equal its kind folder")
    if values["domain"] != namespace:
        raise ValueError(f"{relative}: domain must be {namespace}")
    members = {item.name for item in directory.iterdir() if is_skill_folder(item)}
    files: list[str] = []
    for item in sorted(directory.rglob("*")):
        part = item.relative_to(directory)
        if ignored(part) or part.parts[0] in members:
            continue
        if is_link_or_junction(item):
            raise ValueError(f"{item.relative_to(root).as_posix()}: links are not shipped")
        if item.is_file() and item != path:
            files.append(part.as_posix())
    return {
        "plugin": plugin,
        "name": values["name"],
        "kind": kind,
        "body": body,
        "metadata": values,
        "directory": directory.relative_to(root).as_posix(),
        "files": files,
    }


def collect_skills(
    root: Path, plugin: str, kind: str, directory: Path, family: tuple[str, ...], namespace: str, skills: dict[str, dict]
) -> None:
    location = directory.relative_to(root).as_posix()
    if is_link_or_junction(directory):
        raise ValueError(f"{location}: links are not shipped")
    if not directory.is_dir() or not NAME.fullmatch(directory.name):
        raise ValueError(f"{location}: kind and family folders hold only skill folders and family folders")
    parts = (*family, directory.name)
    if (directory / "SKILL.md").is_file():
        skill = load_skill(root, plugin, kind, directory, "-".join(parts), namespace)
        if skill["name"] in skills:
            raise ValueError(f"{plugin}: duplicate skill {skill['name']}")
        skills[skill["name"]] = skill
        members = [item for item in sorted(directory.iterdir()) if is_skill_folder(item)]
    else:
        members = sorted(path for path in directory.iterdir() if not ignored(path))
        if not members:
            raise ValueError(f"{location}: a family folder holds skill folders")
    for member in members:
        collect_skills(root, plugin, kind, member, parts, namespace, skills)


def discover(root: Path, namespace: str) -> dict[str, dict[str, dict]]:
    agents = root / ".agents"
    plugins: dict[str, dict[str, dict]] = {}
    for plugin_dir in sorted(path for path in agents.iterdir() if path.is_dir() and not ignored(path)):
        if plugin_dir.name in RESERVED_AGENT_DIRS:
            continue
        plugin = plugin_dir.name
        if not NAME.fullmatch(plugin):
            raise ValueError(f".agents/{plugin}: a plugin folder must be a lowercase name")
        skills: dict[str, dict] = {}
        for kind_dir in sorted(path for path in plugin_dir.iterdir() if not ignored(path)):
            if not kind_dir.is_dir() or not NAME.fullmatch(kind_dir.name):
                raise ValueError(f".agents/{plugin}/{kind_dir.name}: only kind folders belong in a plugin folder")
            for entry in sorted(path for path in kind_dir.iterdir() if not ignored(path)):
                collect_skills(root, plugin, kind_dir.name, entry, (), namespace, skills)
        if not skills:
            raise ValueError(f".agents/{plugin}: a plugin folder needs at least one skill")
        plugins[plugin] = skills
    if not plugins:
        raise ValueError("No plugin folder with skills under .agents/")
    return plugins


def validate_payloads(payloads: dict, plugins: dict[str, dict[str, dict]]) -> dict[str, str]:
    if not isinstance(payloads, dict):
        raise ValueError(".agents/plugins/payloads.json: must be a JSON object")
    unknown = set(payloads) - PAYLOAD_FIELDS
    if unknown:
        raise ValueError(f".agents/plugins/payloads.json: unknown fields {sorted(unknown)}")
    declarations = payloads.get("payloads")
    if not isinstance(declarations, dict) or not declarations:
        raise ValueError(".agents/plugins/payloads.json: payloads must be a nonempty object")
    publications = {}
    for package, owners in sorted(declarations.items()):
        if not isinstance(package, str) or not NAME.fullmatch(package):
            raise ValueError(f".agents/plugins/payloads.json: invalid package {package!r}")
        if (
            not isinstance(owners, list)
            or len(owners) != 1
            or not isinstance(owners[0], str)
            or owners[0] not in plugins
        ):
            raise ValueError(f".agents/plugins/payloads.json: {package} must select exactly one canonical source")
        publications[package] = owners[0]
    for source in plugins:
        if publications.get(source) != source:
            raise ValueError(f".agents/plugins/payloads.json: {source} must retain its identity publication")
    dependencies = payloads.get("dependencies", {})
    if not isinstance(dependencies, dict):
        raise ValueError(".agents/plugins/payloads.json: dependencies must be an object")
    for plugin, needs in dependencies.items():
        if plugin not in plugins or not isinstance(needs, list) or not all(isinstance(need, str) for need in needs) or len(needs) != len(set(needs)):
            raise ValueError(f".agents/plugins/payloads.json: invalid dependencies for {plugin}")
        for need in needs:
            if (
                (need not in publications and not re.fullmatch(r"[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*", need))
                or publications.get(need) == plugin
            ):
                raise ValueError(f".agents/plugins/payloads.json: {plugin} cannot depend on {need}")
    compatibility_aliases = payloads.get("compatibilitySkillAliases", {})
    if not isinstance(compatibility_aliases, dict):
        raise ValueError(".agents/plugins/payloads.json: compatibilitySkillAliases must be an object")
    for plugin, aliases in compatibility_aliases.items():
        if plugin not in plugins or not isinstance(aliases, dict):
            raise ValueError(f".agents/plugins/payloads.json: invalid compatibility aliases for {plugin}")
        skills = plugins[plugin]
        for alias, declaration in aliases.items():
            if not isinstance(declaration, dict) or set(declaration) != {"replacedBy", "removeAfter"}:
                raise ValueError(f"{plugin}:{alias}: an alias declares exactly replacedBy and removeAfter")
            target = str(declaration["replacedBy"]).removeprefix(f"{plugin}:")
            if (
                alias not in skills
                or declaration["replacedBy"] != f"{plugin}:{target}"
                or target not in skills
                or target in aliases
            ):
                raise ValueError(f"{plugin}:{alias}: an alias must forward to another skill of the same plugin")
            if not DATE.fullmatch(str(declaration["removeAfter"])):
                raise ValueError(f"{plugin}:{alias}: removeAfter must be YYYY-MM-DD")
            if skills[alias]["metadata"]["profile"] != skills[target]["metadata"]["profile"]:
                raise ValueError(f"{plugin}:{alias}: an alias keeps its replacement's profile")
    return publications


def validate_publication_dependencies(publications: dict, dependencies: dict, marketplace: str) -> None:
    for source, needs in dependencies.items():
        for need in needs:
            if "/" not in need:
                continue
            owner, package = need.split("/", 1)
            if owner == marketplace and (
                package not in publications or publications[package] == source
            ):
                raise ValueError(f".agents/plugins/payloads.json: {source} cannot depend on {need}")


def publication_aliases(package: str, aliases: dict) -> dict:
    return {
        name: {
            "replacedBy": f"{package}:{declaration['replacedBy'].split(':', 1)[1]}",
            "removeAfter": declaration["removeAfter"],
        }
        for name, declaration in aliases.items()
    }


def validate_tiers(root: Path, plugins: dict, repository: str) -> None:
    tier_dir = root / ".agents/tiers"
    present = sorted(path.name for path in tier_dir.iterdir()) if tier_dir.is_dir() else []
    expected = sorted(f"{plugin}.json" for plugin in plugins)
    if present != expected:
        raise ValueError(f".agents/tiers must hold exactly {', '.join(expected)}")
    for plugin in plugins:
        source = f".agents/tiers/{plugin}.json"
        tier = load(root / source)
        if not isinstance(tier, dict):
            raise ValueError(f"{source}: must be a JSON object")
        if tier.get("schema_version") not in (1, 2, 3):
            raise ValueError(f"{source}: schema_version must be 1, 2 or 3")
        if tier.get("tier") != plugin:
            raise ValueError(f"{source}: tier must be {plugin}")
        owners = tier.get("owner_repository")
        owners = [owners] if isinstance(owners, str) else owners or []
        if repository.lower() not in {str(owner).lower() for owner in owners}:
            raise ValueError(f"{source}: owner_repository must name {repository}")
        detect = tier.get("detect")
        if tier.get("applies") == "always":
            if detect is not None:
                raise ValueError(f"{source}: an always-applicable tier declares no detect markers")
        elif tier.get("applies") == "stack-present":
            if tier.get("schema_version") == 3:
                if not isinstance(detect, dict) or not detect:
                    raise ValueError(f"{source}: a stack-present tier needs a detect predicate")
                continue
            if not isinstance(detect, dict) or not any(detect.get(field) for field in TIER_MATCHERS):
                raise ValueError(f"{source}: a stack-present tier needs at least one detect marker")
            if set(detect) - set(TIER_MATCHERS):
                raise ValueError(f"{source}: unknown detect matchers {sorted(set(detect) - set(TIER_MATCHERS))}")
        else:
            raise ValueError(f"{source}: applies must be always or stack-present")


def load_manifests(root: Path, plugins: dict, repository: str) -> tuple[dict, dict]:
    expected = sorted([f"{plugin}.json" for plugin in plugins] + ["marketplace.json"])
    manifests: dict[str, dict] = {}
    templates: dict[str, dict] = {}
    for host in HOSTS:
        host_dir = root / MANIFEST_ROOT / host
        present = sorted(path.name for path in host_dir.iterdir()) if host_dir.is_dir() else []
        if present != expected:
            raise ValueError(f"{MANIFEST_ROOT}/{host} must hold exactly {', '.join(expected)}")
        manifests[host] = {plugin: load(host_dir / f"{plugin}.json") for plugin in plugins}
        templates[host] = load(host_dir / "marketplace.json")
        if not isinstance(templates[host], dict):
            raise ValueError(f"{MANIFEST_ROOT}/{host}/marketplace.json: must be a JSON object")
        if any(not isinstance(manifest, dict) for manifest in manifests[host].values()):
            raise ValueError(f"{MANIFEST_ROOT}/{host}: each plugin manifest must be a JSON object")
        if set(templates[host]) != MARKETPLACE_FIELDS[host]:
            raise ValueError(
                f"{MANIFEST_ROOT}/{host}/marketplace.json declares exactly {sorted(MARKETPLACE_FIELDS[host])}; "
                "its plugin entries are generated"
            )
    if not NAME.fullmatch(str(templates["claude"]["name"])) or templates["claude"]["name"] != templates["codex"]["name"]:
        raise ValueError("Claude and Codex marketplaces must share one lowercase name")
    if not templates["codex"]["interface"].get("displayName") or not templates["claude"]["owner"].get("name"):
        raise ValueError("Marketplaces need an owner name and a display name")
    for plugin in plugins:
        claude, codex = manifests["claude"][plugin], manifests["codex"][plugin]
        for field in ("name", "description", "author", "repository", "skills", "keywords"):
            if not codex.get(field) or codex.get(field) != claude.get(field):
                raise ValueError(f"{plugin}: Claude and Codex manifests disagree on {field}")
        if codex["name"] != plugin or codex["skills"] != "./skills/":
            raise ValueError(f"{plugin}: manifests must keep the {plugin} identity and the ./skills/ path")
        if codex["repository"] != f"https://github.com/{repository}":
            raise ValueError(f"{plugin}: manifest repository must be https://github.com/{repository}")
        if "version" in claude:
            raise ValueError(f"{plugin}: the Claude manifest stays commit-versioned and omits version")
        if not SEMVER.fullmatch(str(codex.get("version", ""))):
            raise ValueError(f"{plugin}: the Codex manifest declares a semantic version")
        interface = codex.get("interface") or {}
        if not claude.get("displayName") or claude["displayName"] != interface.get("displayName"):
            raise ValueError(f"{plugin}: Claude and Codex manifests disagree on display name")
        if not interface.get("category"):
            raise ValueError(f"{plugin}: the Codex manifest interface declares a category")
    return manifests, templates


def adapter_name(skill: dict, single_plugin: bool) -> str:
    return skill["name"] if single_plugin else f"{skill['plugin']}-{skill['name']}"


def adapter_body(skill: dict, adapter_dir: str, canonical_dir: str | None = None) -> str:
    source = f"{canonical_dir or skill['directory']}/SKILL.md"
    relative = posixpath.relpath(f"/{source}", f"/{adapter_dir}")
    match = FRONTMATTER.match(skill["body"])
    title = next((line for line in match.group("body").splitlines() if line.startswith("# ")), f"# {skill['name']}")
    return (
        f"---\n{match.group('header')}\n---\n\n{title}\n\n"
        f"Read and follow the [canonical definition]({relative}) in full.\n"
        "This discovery entry is generated; edit the referenced `.agents/` definition.\n"
    )


def references(body: str):
    yield from package_links(body)
    for target in SKILL_DIRECTORY_REFERENCE.findall(body):
        yield target.rstrip(".,;:")


def validate_skill_references(plugins: dict[str, dict[str, dict]]) -> None:
    qualified = re.compile(
        r"(?<![-/\w])(" + "|".join(re.escape(plugin) for plugin in sorted(plugins)) + r"):(?!:)([a-z][a-z0-9-]+)"
    )
    for plugin, skills in plugins.items():
        for skill in skills.values():
            for namespace, name in qualified.findall(skill["body"]):
                if name not in plugins[namespace]:
                    raise ValueError(f"{plugin}:{skill['name']}: unknown skill reference {namespace}:{name}")
            for name in BARE_SKILL_REFERENCE.findall(skill["body"]):
                if name not in skills:
                    raise ValueError(f"{plugin}:{skill['name']}: unknown skill reference `{name}` skill")


def validate_file_references(
    root: Path,
    plugins: dict,
    canonical_locations: dict[tuple[str, str], list[str]],
    adapter_locations: list[tuple[dict, str, str, bool, bool]],
    output: dict,
) -> None:
    root_resolved = root.resolve()

    for path in sorted(output):
        parts = PurePosixPath(path).parts
        if len(parts) < 3 or parts[0] != "plugins" or not path.endswith(".md"):
            continue
        package = parts[1]
        directory = PurePosixPath(path).parent.as_posix()
        for target in sorted(set(package_links(package_text(output, path)))):
            package_target(output, package, directory, target, path)

    def validate(
        plugin: str,
        skill: dict,
        body: str,
        source_dir: str,
        shipped_dir: str,
        source_exists: bool,
        generated_required: bool,
    ) -> None:
        where = f"{plugin}:{skill['name']}"
        for target in sorted(set(references(body))):
            if generated_required:
                package = PurePosixPath(shipped_dir).parts[1]
                package_target(output, package, shipped_dir, target, where)
            if (
                not target or "\\" in target or ":" in target or "\x00" in target
                or PurePosixPath(target).is_absolute()
            ):
                raise ValueError(f"{where}: unsafe local reference {target!r}")
            if source_exists:
                source = posixpath.normpath(posixpath.join(source_dir, target))
                source_path = PurePosixPath(source)
                if source_path.is_absolute() or source == ".." or source.startswith("../"):
                    raise ValueError(f"{where}: {target} does not resolve from {source_dir}")
                candidate = root / source
                resolved = candidate.resolve()
                if resolved != root_resolved and root_resolved not in resolved.parents:
                    raise ValueError(f"{where}: {target} does not resolve from {source_dir}")
                if not candidate.exists():
                    raise ValueError(f"{where}: {target} does not resolve from {source_dir}")

    for plugin, skills in plugins.items():
        for skill in skills.values():
            for directory in canonical_locations[(plugin, skill["name"])]:
                validate(plugin, skill, skill["body"], skill["directory"], directory, True, True)
    for skill, body, directory, source_exists, generated_required in adapter_locations:
        validate(skill["plugin"], skill, body, directory, directory, source_exists, generated_required)


def harness_body(root: Path, package: str, marketplace: str, output: dict[str, bytes]) -> str | None:
    relative = f"{MANIFEST_ROOT}/harness/{package}.json"
    path = root / relative
    if not path.exists():
        return None
    try:
        body = read(path)
        manifest = json.loads(body)
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError(f"{relative}: unreadable JSON ({error})") from None
    if not isinstance(manifest, dict):
        raise ValueError(f"{relative}: must be a JSON object")
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        raise ValueError(f"{relative}: schema_version must be 1")
    if manifest.get("plugin") != f"{marketplace}/{package}":
        raise ValueError(f"{relative}: plugin must be {marketplace}/{package}")
    roots = manifest.get("source_roots")
    if not isinstance(roots, list) or not roots or not all(isinstance(value, str) and value for value in roots):
        raise ValueError(f"{relative}: source_roots must be a nonempty list of paths")
    if len(roots) != len(set(roots)):
        raise ValueError(f"{relative}: source_roots must be unique")
    for value in roots:
        source = PurePosixPath(value)
        if (
            "\\" in value or ":" in value or "\x00" in value
            or source.is_absolute() or ".." in source.parts
            or source.as_posix() != value or len(source.parts) < 2
            or source.parts[0] != ".agents"
        ):
            raise ValueError(f"{relative}: unsafe canonical source root {value!r}")
        target = f"plugins/{package}/{value}"
        if target not in output and not any(name.startswith(target + "/") for name in output):
            raise ValueError(f"{relative}: source root {value!r} is not shipped in {package}")
    return body


def build(root: Path) -> dict[str, bytes]:
    config = load_config(root)
    namespace, repository = config["namespace"], config["repository"]
    plugins = discover(root, namespace)
    payloads = load(root / ".agents/plugins/payloads.json")
    publications = validate_payloads(payloads, plugins)
    validate_tiers(root, plugins, repository)
    manifests, templates = load_manifests(root, publications, repository)
    validate_skill_references(plugins)
    aliases = payloads.get("compatibilitySkillAliases", {})
    dependencies = payloads.get("dependencies", {})
    validate_publication_dependencies(publications, dependencies, templates["claude"]["name"])
    single_plugin = len(plugins) == 1

    output: dict[str, bytes] = {}
    canonical_locations: dict[tuple[str, str], list[str]] = {}
    adapter_locations: list[tuple[dict, str, str, bool, bool]] = []

    def emit(relative: str, data: str | bytes) -> None:
        key = PurePosixPath(relative).as_posix()
        if key in output:
            raise ValueError(f"Duplicate generated output: {key}")
        output[key] = data.encode("utf-8") if isinstance(data, str) else data

    def emit_skill(directory: str, skill: dict, body: str) -> None:
        emit(f"{directory}/SKILL.md", body)
        for file in skill["files"]:
            emit(f"{directory}/{file}", (root / skill["directory"] / file).read_bytes())

    repository_index = [
        f"# {namespace} capabilities",
        "",
        "Generated from `.agents/<plugin>/<kind>/<family>/<member>/SKILL.md`; a skill's name is its folder path below "
        "the kind folder joined by hyphens.",
        "",
    ]
    for source, skills in plugins.items():
        ordered = sorted(skills.values(), key=lambda item: (item["kind"], item["name"]))
        for skill in ordered:
            for adapter_root in ADAPTER_ROOTS.values():
                adapter_dir = f"{adapter_root}/{adapter_name(skill, single_plugin)}"
                host_adapter = adapter_body(skill, adapter_dir)
                emit_skill(adapter_dir, skill, host_adapter)
                adapter_locations.append((skill, host_adapter, adapter_dir, True, False))
        entries = [f"- `{skill['name']}` — {skill['kind']} — {skill['metadata']['profile']}" for skill in ordered]
        repository_index += [f"## {source}", ""]
        repository_index += [f"{entry} — `{skill['directory']}/SKILL.md`" for entry, skill in zip(entries, ordered)]
        repository_index.append("")

    for package, source in publications.items():
        skills = plugins[source]
        ordered = sorted(skills.values(), key=lambda item: (item["kind"], item["name"]))
        package_aliases = publication_aliases(package, aliases.get(source, {}))
        for skill in ordered:
            canonical_dir = f"plugins/{package}/{skill['directory']}"
            package_adapter_dir = f"plugins/{package}/skills/{skill['name']}"
            package_adapter = adapter_body(skill, package_adapter_dir, canonical_dir)
            emit_skill(canonical_dir, skill, skill["body"])
            emit_skill(package_adapter_dir, skill, package_adapter)
            canonical_locations.setdefault((source, skill["name"]), []).append(canonical_dir)
            adapter_locations.append((skill, package_adapter, package_adapter_dir, False, True))

        entries = [f"- `{skill['name']}` — {skill['kind']} — {skill['metadata']['profile']}" for skill in ordered]
        emit(f"plugins/{package}/INDEX.md", "\n".join([f"# {package} package capabilities", "", *entries, ""]))
        profiles: dict[str, list[str]] = {}
        for skill in ordered:
            if skill["name"] not in package_aliases:
                profiles.setdefault(skill["metadata"]["profile"], []).append(skill["name"])
        selection = {
            "plugin": package,
            "dependencies": dependencies.get(source, []),
            "profiles": {profile: sorted(names) for profile, names in sorted(profiles.items())},
            "compatibilitySkillAliases": package_aliases,
            "skills": [
                {
                    "name": skill["name"],
                    "kind": skill["kind"],
                    "profile": skill["metadata"]["profile"],
                    "applicability": split_tags(skill["metadata"]["applicability"]),
                    "requires": split_tags(skill["metadata"]["requires"]),
                    "provenance": split_tags(skill["metadata"]["provenance"]),
                }
                for skill in sorted(ordered, key=lambda item: item["name"])
            ],
        }
        emit(f"plugins/{package}/selection.json", dump(selection))
        emit(f"plugins/{package}/tier.json", read(root / f".agents/tiers/{source}.json"))
        harness = harness_body(root, package, templates["claude"]["name"], output)
        if harness is not None:
            emit(f"plugins/{package}/harness.json", harness)
        for host in HOSTS:
            emit(f"plugins/{package}/.{host}-plugin/plugin.json", read(root / MANIFEST_ROOT / host / f"{package}.json"))

    emit(".agents/INDEX.md", "\n".join(repository_index))
    claude_entries, codex_entries = [], []
    for package in publications:
        claude, codex = manifests["claude"][package], manifests["codex"][package]
        category = codex["interface"]["category"]
        claude_entries.append(
            {
                "name": package,
                "source": f"./plugins/{package}",
                "description": claude["description"],
                "category": category,
                "keywords": claude["keywords"],
            }
        )
        codex_entries.append(
            {
                "name": package,
                "source": {"source": "local", "path": f"./plugins/{package}"},
                "policy": CODEX_POLICY,
                "category": category,
            }
        )
    emit(MARKETPLACE_OUTPUTS["claude"], dump({**templates["claude"], "plugins": claude_entries}))
    emit(MARKETPLACE_OUTPUTS["codex"], dump({**templates["codex"], "plugins": codex_entries}))
    package_identities(output)
    validate_file_references(root, plugins, canonical_locations, adapter_locations, output)
    return output


def split_tags(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def generated_root_paths(root: Path) -> list[Path]:
    resolved_root = root.resolve()
    result: list[Path] = []
    for value in GENERATED_ROOTS:
        relative = PurePosixPath(value)
        ancestor = resolved_root
        for part in relative.parts:
            ancestor = ancestor / part
            if is_link_or_junction(ancestor):
                raise ValueError(f"Generated root must not be or sit under a link or junction: {value}")
        path = resolved_root.joinpath(*relative.parts).resolve()
        if path == resolved_root or not path.is_relative_to(resolved_root):
            raise ValueError(f"Generated root escapes the repository: {value}")
        result.append(path)
    return result


def existing_files(root: Path) -> set[str]:
    result: set[str] = set()
    for value in GENERATED_ROOTS:
        path = root / value
        if path.is_dir():
            result.update(
                item.relative_to(root).as_posix()
                for item in path.rglob("*")
                if item.is_file() and not ignored(item.relative_to(root))
            )
        elif path.is_file():
            result.add(value)
    return result


def synchronize(root: Path, check: bool) -> int:
    output = build(root)
    expected = set(output)
    actual = existing_files(root)
    if check:
        stale = sorted(path for path in expected & actual if (root / path).read_bytes() != output[path])
        problems = [("MISSING", sorted(expected - actual)), ("STALE", stale), ("EXTRA", sorted(actual - expected))]
        for label, paths in problems:
            for path in paths:
                print(f"{label}: {path}")
        if any(paths for _, paths in problems):
            return 1
        print(f"generated outputs current: {len(expected)} files")
        return 0
    for path in generated_root_paths(root):
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    for relative, data in output.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    print(f"generated {len(expected)} files")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        return synchronize(args.root.resolve(), args.check)
    except ValueError as error:
        print(f"error: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
