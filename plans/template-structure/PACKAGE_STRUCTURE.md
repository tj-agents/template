# Shared package structure implementation contract

This is a proposed implementation, not a production module. The parent owns readiness, review, release placement and subsequent serialized writing. Authored implementation belongs in the existing generator template; the mirrored root generator remains derived. This reference is the only file written by this investigation.

The shared layer reads package structure, not Core runtime policy. It follows native manifest skill roots, paired discovery inventories, canonical definitions and shipped resources. Kit's starter layout enforcement remains separate. Core source maps, hooks, lanes, catalogs, selection and runtime behavior retain their current owner.

## Proposed generator implementation

The additional imports shown are Python standard-library imports. Insert these functions in `.agents/kit/utility/new-plugin/templates/repository/.agents/sync_generated.py.in` before `build`. They use the generator's existing imports/constants: `Path`, `PurePosixPath`, `os`, `posixpath`, `re`, `json`, `FRONTMATTER`, `NAME`, `KIND`, `URL_SCHEME`, `SKILL_DIRECTORY_REFERENCE`, `HOSTS`, `MARKETPLACE_OUTPUTS`, `MANIFEST_ROOT` and `is_link_or_junction`.

```python
from html import unescape
from string import punctuation
from urllib.parse import unquote


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

def package_text(files: dict[str, bytes], path: str) -> str:
    if path not in files:
        raise ValueError(f"{path}: missing shipped file")
    try:
        return files[path].decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeError as error:
        raise ValueError(f"{path}: invalid UTF-8 ({error})") from None


def package_object(files: dict[str, bytes], path: str) -> dict:
    try:
        value = json.loads(package_text(files, path))
    except json.JSONDecodeError as error:
        raise ValueError(f"{path}: invalid JSON ({error.msg})") from None
    if not isinstance(value, dict):
        raise ValueError(f"{path}: must be a JSON object")
    return value


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

def package_metadata(files: dict[str, bytes], path: str) -> tuple[dict[str, str], str]:
    text = package_text(files, path)
    match = FRONTMATTER.match(text)
    if match is None:
        raise ValueError(f"{path}: missing frontmatter")
    fields = ("name", "description", "kind", "domain")
    values: dict[str, str] = {}
    for line in match.group("header").splitlines():
        key, separator, value = line.partition(":")
        key = key.strip()
        if separator and key in fields:
            if key in values:
                raise ValueError(f"{path}: duplicate {key}")
            values[key] = value.strip()
    for field in fields:
        if not values.get(field):
            raise ValueError(f"{path}: missing {field}")
    for field in ("name", "domain"):
        if not NAME.fullmatch(values[field]):
            raise ValueError(f"{path}: invalid {field} {values[field]!r}")
    if not KIND.fullmatch(values["kind"]):
        raise ValueError(f"{path}: invalid kind {values['kind']!r}")
    return values, match.group("body")


def validate_package_harness(
    files: dict[str, bytes], manifest: dict, package: str, marketplace: str, where: str,
    *, source_projections: dict[tuple[str, str], str] | None = None,
) -> None:
    if not isinstance(manifest, dict):
        raise ValueError(f"{where}: must be a JSON object")
    if type(manifest.get("schema_version")) is not int or manifest["schema_version"] != 1:
        raise ValueError(f"{where}: schema_version must be 1")
    if manifest.get("plugin") != f"{marketplace}/{package}":
        raise ValueError(f"{where}: plugin must be {marketplace}/{package}")
    roots = manifest.get("source_roots")
    if (
        not isinstance(roots, list) or not roots
        or not all(isinstance(value, str) and value for value in roots)
    ):
        raise ValueError(f"{where}: source_roots must be a nonempty list of paths")
    if len(roots) != len(set(roots)):
        raise ValueError(f"{where}: source_roots must be unique")
    for value in roots:
        relative = package_relative(value, where)
        source = PurePosixPath(relative)
        if len(source.parts) < 2 or source.parts[0] != ".agents":
            raise ValueError(f"{where}: unsafe canonical source root {value!r}")
        if package_present(files, f"plugins/{package}/{relative}"):
            continue
        projections = source_projections or {}
        candidates = [
            source for owner, source in projections
            if owner == package and (relative == source or relative.startswith(source + "/"))
        ]
        if len(candidates) > 1:
            raise ValueError(f"{where}: ambiguous projection for source root {value!r}")
        if not candidates:
            raise ValueError(f"{where}: source root {value!r} is not shipped in {package}")
        source = candidates[0]
        destination = projections[(package, source)] + relative[len(source):]
        if not package_present(files, f"plugins/{package}/{destination}"):
            raise ValueError(f"{where}: source root {value!r} is not shipped in {package}")


def validate_packages(
    files: dict[str, bytes], *, extended_adapter_names: tuple[str, ...] = (),
    source_projections: tuple[tuple[str, str, str], ...] = (),
) -> None:
    package_identities(files)
    if (
        not isinstance(extended_adapter_names, (list, tuple))
        or not all(isinstance(name, str) and NAME.fullmatch(name) for name in extended_adapter_names)
        or len(extended_adapter_names) != len(set(extended_adapter_names))
    ):
        raise ValueError("extended_host_adapters: expected unique skill names")

    marketplaces: dict[str, dict] = {}
    rosters: dict[str, dict[str, str]] = {}
    for host in HOSTS:
        where = MARKETPLACE_OUTPUTS[host]
        marketplace = package_object(files, where)
        if not isinstance(marketplace.get("name"), str) or not NAME.fullmatch(marketplace["name"]):
            raise ValueError(f"{where}: invalid marketplace name")
        entries = marketplace.get("plugins")
        if not isinstance(entries, list) or not entries:
            raise ValueError(f"{where}: plugins must be a nonempty list")
        roster: dict[str, str] = {}
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError(f"{where}: plugin entry must be an object")
            name = entry.get("name")
            if not isinstance(name, str) or not NAME.fullmatch(name) or name in roster:
                raise ValueError(f"{where}: invalid or duplicate plugin name {name!r}")
            source = entry.get("source")
            if host == "codex":
                if not isinstance(source, dict) or source.get("source") != "local":
                    raise ValueError(f"{where}: {name} needs a local package source")
                source = source.get("path")
            target = package_relative(source, f"{where}: {name} source", native=True)
            if target != f"plugins/{name}":
                raise ValueError(f"{where}: {name} source must be ./plugins/{name}")
            roster[name] = target
        marketplaces[host] = marketplace
        rosters[host] = roster
    if marketplaces["claude"]["name"] != marketplaces["codex"]["name"]:
        raise ValueError("Native marketplaces disagree on name")
    if rosters["claude"] != rosters["codex"]:
        raise ValueError("Native marketplaces disagree on package inventory")
    roster = rosters["claude"]
    shipped_packages = {
        PurePosixPath(path).parts[1] for path in files
        if path.startswith("plugins/") and len(PurePosixPath(path).parts) >= 2
    }
    if shipped_packages != set(roster):
        raise ValueError("Shipped packages disagree with marketplace inventory")
    if not isinstance(source_projections, (list, tuple)):
        raise ValueError("resources: source projections must be a list or tuple")
    projections: dict[tuple[str, str], str] = {}
    for entry in source_projections:
        if not isinstance(entry, (list, tuple)) or len(entry) != 3:
            raise ValueError("resources: each projection needs package, source and destination")
        package, source, destination = entry
        if not isinstance(package, str) or package not in roster:
            raise ValueError(f"resources: unknown projection package {package!r}")
        source = package_relative(source, f"resources: {package} source")
        destination = package_relative(destination, f"resources: {package} destination")
        if not source.startswith(".agents/"):
            raise ValueError(f"resources: {package} projection source must be canonical")
        if (package, source) in projections:
            raise ValueError(f"resources: duplicate source projection {package}:{source}")
        for (owner, previous), target in projections.items():
            if owner != package:
                continue
            if source.startswith(previous + "/") or previous.startswith(source + "/"):
                raise ValueError(f"resources: ambiguous source projections for {package}:{source}")
            if destination == target:
                raise ValueError(f"resources: conflicting destination {package}:{destination}")
        if not package_present(files, f"plugins/{package}/{destination}"):
            raise ValueError(f"resources: {package} destination {destination!r} is not shipped")
        projections[(package, source)] = destination

    adapters: dict[tuple[str, str, str], tuple[str, dict, str, str]] = {}
    canonical_metadata: dict[str, tuple[dict, str]] = {}
    extension_identities: dict[str, set[tuple[str, bytes]]] = {}
    for package, prefix in sorted(roster.items()):
        manifests = {
            host: package_object(files, f"{prefix}/.{host}-plugin/plugin.json")
            for host in HOSTS
        }
        for field in ("name", "description", "author", "repository", "keywords"):
            if manifests["claude"].get(field) != manifests["codex"].get(field):
                raise ValueError(f"{prefix}: native manifests disagree on {field}")
        roots: dict[str, str] = {}
        inventories: dict[str, set[str]] = {}
        for host, manifest in manifests.items():
            where = f"{prefix}/.{host}-plugin/plugin.json"
            if manifest.get("name") != package:
                raise ValueError(f"{where}: name must be {package}")
            if not isinstance(manifest.get("description"), str) or not manifest["description"].strip():
                raise ValueError(f"{where}: description must be nonempty")
            root = package_relative(manifest.get("skills"), f"{where}: skills", native=True)
            if PurePosixPath(root).parts[0] == ".agents":
                raise ValueError(f"{where}: skills root must be a native adapter root")
            roots[host] = f"{prefix}/{root}"
            entries = {
                path for path in files
                if path.startswith(roots[host] + "/")
                and len(PurePosixPath(path).relative_to(roots[host]).parts) == 2
                and path.endswith("/SKILL.md")
            }
            if not entries:
                raise ValueError(f"{where}: skills root has no discovery entries")
            names: set[str] = set()
            for path in sorted(entries):
                meta, body = package_metadata(files, path)
                name = meta["name"]
                if PurePosixPath(path).parent.name != name or name in names:
                    raise ValueError(f"{path}: duplicate or mismatched discovery name")
                names.add(name)
                directory = posixpath.dirname(path)
                targets = [
                    package_target(files, package, directory, value, path)
                    for value in package_links(package_text(files, path))
                ]
                matches = []
                for target in targets:
                    if target.startswith(prefix + "/.agents/") and target.endswith("/SKILL.md"):
                        if target not in canonical_metadata:
                            canonical_metadata[target] = package_metadata(files, target)
                        if canonical_metadata[target][0]["name"] == name:
                            matches.append(target)
                if len(matches) != 1:
                    raise ValueError(f"{path}: needs exactly one link to its canonical definition")
                canonical = matches[0]
                shared, shared_body = canonical_metadata[canonical]
                for field in ("name", "kind", "domain"):
                    if meta[field] != shared[field]:
                        raise ValueError(f"{path}: canonical {field} disagrees")
                adapters[(package, host, name)] = (path, meta, body, canonical)
                identity = canonical.removeprefix(prefix + "/")
                extension_identities.setdefault(name, set()).add((identity, files[canonical]))
            inventories[host] = names
        if inventories["claude"] != inventories["codex"]:
            raise ValueError(f"{prefix}: native discovery inventories disagree")
        for name in inventories["claude"]:
            if adapters[(package, "claude", name)][3] != adapters[(package, "codex", name)][3]:
                raise ValueError(f"{prefix}:{name}: native entries disagree on canonical definition")
        harness = f"{prefix}/harness.json"
        if harness in files:
            validate_package_harness(
                files, package_object(files, harness), package,
                marketplaces["claude"]["name"], harness,
                source_projections=projections,
            )

    for name in extended_adapter_names:
        identities = extension_identities.get(name)
        if not identities:
            raise ValueError(f"extended_host_adapters: unknown skill {name}")
        if len(identities) != 1:
            raise ValueError(f"extended_host_adapters: ambiguous canonical identity for {name}")

    for canonical, (meta, body) in canonical_metadata.items():
        package = PurePosixPath(canonical).parts[1]
        directory = posixpath.dirname(canonical)
        for value in package_links(package_text(files, canonical)):
            package_target(files, package, directory, value, canonical)

    extended = set(extended_adapter_names)
    for (package, host, name), (path, meta, body, canonical) in adapters.items():
        shared, shared_body = canonical_metadata[canonical]
        directory = posixpath.dirname(path)
        if name not in extended:
            if meta["description"] != shared["description"]:
                raise ValueError(f"{path}: canonical description disagrees")
            title = next(
                (line for line in shared_body.splitlines() if line.startswith("# ")),
                f"# {name}",
            )
            relative = posixpath.relpath(canonical, directory)
            kit = (
                f"{title}\n\n"
                f"Read and follow the [canonical definition]({relative}) in full.\n"
                "This discovery entry is generated; edit the referenced `.agents/` definition."
            )
            core = (
                f"{title}\n\n"
                f"Read and follow the [canonical shared definition]({relative}) in full.\n"
                f"This entry point supplies only {host.capitalize()} discovery metadata; "
                "the shared procedure is authored once under `.agents/`."
            )
            if body.strip() not in (kit, core):
                raise ValueError(f"{path}: undeclared adapter extension")
        for context in (path, canonical):
            for value in SKILL_DIRECTORY_REFERENCE.findall(package_text(files, context)):
                package_target(files, package, directory, value.rstrip(".,;:"), context)


def package_safe_path(path: Path) -> Path:
    absolute = Path(os.path.abspath(path))
    for ancestor in (*reversed(absolute.parents), absolute):
        if is_link_or_junction(ancestor):
            raise ValueError(f"{absolute}: must not be or sit under a link or junction")
    return absolute


def package_read_file(path: Path) -> bytes:
    path = package_safe_path(path)
    if not path.is_file():
        raise ValueError(f"{path}: expected a regular file")
    try:
        return path.read_bytes()
    except OSError as error:
        raise ValueError(f"{path}: unreadable ({error})") from None


def package_files(root: Path) -> dict[str, bytes]:
    root = package_safe_path(root)
    plugins = package_safe_path(root / "plugins")
    if not plugins.is_dir():
        raise ValueError(f"{plugins}: missing package directory")
    files: dict[str, bytes] = {}

    def visit(directory: Path) -> None:
        try:
            entries = sorted(directory.iterdir())
        except OSError as error:
            raise ValueError(f"{directory}: unreadable directory ({error})") from None
        for entry in entries:
            package_safe_path(entry)
            if entry.is_dir():
                visit(entry)
            else:
                relative = entry.relative_to(root).as_posix()
                files[relative] = package_read_file(entry)

    visit(plugins)
    for relative in MARKETPLACE_OUTPUTS.values():
        files[relative] = package_read_file(root / relative)
    return files


def package_extensions(root: Path) -> tuple[str, ...]:
    path = package_safe_path(root / ".agents/plugins/sources.json")
    if not path.exists():
        return ()
    relative = ".agents/plugins/sources.json"
    source = package_object({relative: package_read_file(path)}, relative)
    names = source.get("extended_host_adapters", [])
    if (
        not isinstance(names, list)
        or not all(isinstance(name, str) and NAME.fullmatch(name) for name in names)
        or len(names) != len(set(names))
    ):
        raise ValueError(f"{relative}: extended_host_adapters must hold unique skill names")
    return tuple(names)


def package_source_projections(root: Path) -> tuple[tuple[str, str, str], ...]:
    path = package_safe_path(root / ".agents/plugins/sources.json")
    if not path.exists():
        return ()
    relative = ".agents/plugins/sources.json"
    source = package_object({relative: package_read_file(path)}, relative)
    resources = source.get("resources", [])
    if not isinstance(resources, list):
        raise ValueError(f"{relative}: resources must be a list")
    projections = []
    for entry in resources:
        if not isinstance(entry, dict) or not all(
            isinstance(entry.get(field), str) and entry[field]
            for field in ("plugin", "source", "destination")
        ):
            raise ValueError(f"{relative}: resource needs plugin, source and destination paths")
        if entry["source"].startswith(".agents/"):
            projections.append((entry["plugin"], entry["source"], entry["destination"]))
    return tuple(projections)
```

The first actual Core probe exposed a structural distinction: engineering declares .agents/workflows but ships it at workflows; machine declares .agents/catalog/catalog.schema.json but ships that file under catalog/. The parent accepted narrow explicit resource projections from the existing source map's plugin/source/destination declarations. The common helper first tries direct physically shipped canonical roots, then requires exactly one checked projection and resolves its suffix under the shipped destination. Duplicate/conflicting/ambiguous mappings fail. Canonical adapter links never use projections and still require actual shipped .agents files. Absent declarations cannot magically resolve missing source roots. Resources' contents and harness requires remain opaque. This later shared slice extracts the envelope helper; the current Template publication writer remains on its strict direct-shipping design.

Only ordinary generated wrapper bodies are compared. Extended wording, model/effort fields, hook strings, native interface fields and harness requires contents remain opaque. A package-local canonical target need not use the published package name or domain. Canonical inventory is the set reached by paired native discovery entries, not a schema inferred from every resource named SKILL.md.

Core's exact ordinary wrapper bodies, after frontmatter, are:

```text
# Pair agent instruction files

Read and follow the [canonical shared definition](../../.agents/base/policy/agent-files/SKILL.md) in full.
This entry point supplies only Claude discovery metadata; the shared procedure is authored once under `.agents/`.
```

```text
# Pair agent instruction files

Read and follow the [canonical shared definition](../../.agents/base/policy/agent-files/SKILL.md) in full.
This entry point supplies only Codex discovery metadata; the shared procedure is authored once under `.agents/`.
```

## Caller wiring and harness reuse

At the end of existing generator build, after source-reference validation:

```python
    validate_file_references(root, plugins, canonical_locations, adapter_locations, output)
    validate_packages(output)
    return output
```

The publication successor may already change canonical_locations to lists. Retain that caller's actual arguments; this slice only adds validate_packages before return.

Extract the previously accepted harness envelope predicates into validate_package_harness above. The publication helper becomes the following complete caller and keeps returning the exact authored text:

```python
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
    validate_package_harness(output, manifest, package, marketplace, relative)
    return body
```

Add this complete function to the canonical check script:

```python
def check_packages(root: Path) -> list[str]:
    try:
        generator.validate_packages(
            generator.package_files(root),
            extended_adapter_names=generator.package_extensions(root),
            source_projections=generator.package_source_projections(root),
        )
    except (ValueError, OSError) as error:
        return [str(error)]
    return []
```

Replace its main with:

```python
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--packages-only", action="store_true")
    arguments = parser.parse_args()
    root = arguments.root.absolute()
    problems = check_packages(root) if arguments.packages_only else check(root.resolve())
    for problem in problems:
        print(problem, file=sys.stderr)
    if arguments.packages_only:
        label = "package structure"
        success = "valid"
    else:
        label = f"kit {new_plugin.kit_version()}"
        success = "conforms"
    if problems:
        print(f"{root.name}: invalid {label}: {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print(f"{root.name}: {label} {success}")
    return 0
```

Default check retains its pre-generation behavior: build validates proposed output, without comparing it to stale generated files. Packages-only validates actual on-disk distribution and bypasses Kit starter checks. Both use exactly the same pure validator.

## Runtime binding and source ownership

Add only `persistent-workflow-binding.json` to `.agents/kit/utility/check/standard.json`'s allowed agents_files. Add `/.agents/persistent-workflow-binding.json` to the authored repository .gitignore.in. Mirror the vendored root copy through the normal process.

Do not parse binding contents. Verify that check allows the file, Git ignores an untracked binding, and build emits no binding file. A directory with that name, similarly named files, and other unknown .agents JSON files remain rejected. The default authored-source checker retains unknown-source enforcement; common package references never fall back to any authored checkout. Core authored source classifications remain with Core's generator.

## Executable design probe

This complete fixture/probe block is run after importing the current generator template and executing only the first implementation block into that module's namespace. It creates in-memory bytes; actual Core is read-only. It does not import or interpret Core runtime policy.

```python
def fixture() -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    def put(path, value):
        files[path] = value.encode("utf-8")
    def js(path, value):
        put(path, json.dumps(value))
    for host, target in MARKETPLACE_OUTPUTS.items():
        source = "./plugins/example"
        if host == "codex":
            source = {"source": "local", "path": source}
        js(target, {"name": "example-agents", "plugins": [{"name": "example", "source": source}]})
    canonical = "plugins/example/.agents/shared/policy/example/SKILL.md"
    header = "---\nname: example\ndescription: A shared procedure.\nkind: policy\ndomain: behavior\n---\n"
    put(canonical, header + "\n# Example\n\nUse `<skill-directory>/../../resources/tool.py`.\n")
    put("plugins/example/resources/tool.py", "print('fixture')\n")
    put("plugins/example/.agents/workflows/runtime.py", "pass\n")
    for host in HOSTS:
        root = "skills" if host == "claude" else "codex-skills"
        js(f"plugins/example/.{host}-plugin/plugin.json", {
            "name": "example", "description": "An example.", "skills": f"./{root}/",
            "hooks": f"./hooks/{host}.json", "interface": {"hostSpecific": host},
        })
        body = (
            "\n# Example\n\n"
            "Read and follow the [canonical shared definition]"
            "(../../.agents/shared/policy/example/SKILL.md) in full.\n"
            f"This entry point supplies only {host.capitalize()} discovery metadata; "
            "the shared procedure is authored once under `.agents/`.\n"
        )
        put(f"plugins/example/{root}/example/SKILL.md", header + body)
    js("plugins/example/harness.json", {
        "schema_version": 1, "plugin": "example-agents/example",
        "source_roots": [".agents/shared", ".agents/workflows/runtime.py"],
        "requires": {"opaque": {"doNotInterpret": True}},
    })
    return files


def rejected(files, expected, *, extensions=(), projections=()):
    try:
        validate_packages(files, extended_adapter_names=extensions, source_projections=projections)
    except ValueError as error:
        assert expected in str(error), (expected, str(error))
    else:
        raise AssertionError(f"Expected rejection containing {expected!r}")


files = fixture()
validate_packages(files)
projected = dict(files)
projected["plugins/example/workflows/runtime.py"] = projected.pop(
    "plugins/example/.agents/workflows/runtime.py"
)
projection = (("example", ".agents/workflows", "workflows"),)
rejected(projected, "source root '.agents/workflows/runtime.py' is not shipped")
validate_packages(projected, source_projections=projection)
rejected(projected, "duplicate source projection", projections=projection + projection)
rejected(projected, "ambiguous source projections", projections=projection + (
    ("example", ".agents/workflows/runtime.py", "workflows/runtime.py"),
))
rejected(projected, "conflicting destination", projections=projection + (
    ("example", ".agents/other", "workflows"),
))
rejected(projected, "unknown projection package", projections=(("missing", ".agents/workflows", "workflows"),))
rejected(projected, "unsafe relative path", projections=(("example", ".agents/workflows", "../workflows"),))
rejected(projected, "is not shipped", projections=(("example", ".agents/workflows", "missing"),))
direct = dict(files)
direct["plugins/example/workflows/unrelated.py"] = b"pass\n"
validate_packages(direct, source_projections=projection)
kit = dict(files)
for host in HOSTS:
    root = "skills" if host == "claude" else "codex-skills"
    path = f"plugins/example/{root}/example/SKILL.md"
    header = package_text(kit, path).split("---\n", 2)[1]
    kit[path] = (
        f"---\n{header}---\n\n# Example\n\n"
        "Read and follow the [canonical definition]"
        "(../../.agents/shared/policy/example/SKILL.md) in full.\n"
        "This discovery entry is generated; edit the referenced `.agents/` definition.\n"
    ).encode()
validate_packages(kit)
extended = dict(files)
for root in ("skills", "codex-skills"):
    path = f"plugins/example/{root}/example/SKILL.md"
    extended[path] = extended[path].replace(
        b"description: A shared procedure.", b"description: Host-specific invocation."
    ) + b"\nUse the host's native invocation.\n"
rejected(extended, "canonical description disagrees")
validate_packages(extended, extended_adapter_names=("example",))
rejected(files, "unknown skill missing", extensions=("missing",))
missing = dict(files)
del missing["plugins/example/resources/tool.py"]
rejected(missing, "reference is not shipped")
escaped = dict(files)
path = "plugins/example/skills/example/SKILL.md"
escaped[path] = escaped[path].replace(b"../../.agents/shared", b"../../../.agents/shared")
rejected(escaped, "reference leaves package")
unsafe = dict(files)
path = "plugins/example/.codex-plugin/plugin.json"
manifest = json.loads(unsafe[path])
manifest["skills"] = "../author-source/"
unsafe[path] = json.dumps(manifest).encode()
rejected(unsafe, "unsafe relative path")
malformed = dict(files)
malformed[MARKETPLACE_OUTPUTS["codex"]] = b"[]"
rejected(malformed, "must be a JSON object")
ambiguous = dict(files)
for key, data in files.items():
    if key.startswith("plugins/example/"):
        ambiguous[key.replace("plugins/example/", "plugins/other/", 1)] = data
for host, target in MARKETPLACE_OUTPUTS.items():
    marketplace = json.loads(ambiguous[target])
    source = "./plugins/other" if host == "claude" else {"source": "local", "path": "./plugins/other"}
    marketplace["plugins"].append({"name": "other", "source": source})
    ambiguous[target] = json.dumps(marketplace).encode()
    path = f"plugins/other/.{host}-plugin/plugin.json"
    manifest = json.loads(ambiguous[path])
    manifest["name"] = "other"
    ambiguous[path] = json.dumps(manifest).encode()
path = "plugins/other/harness.json"
harness = json.loads(ambiguous[path])
harness["plugin"] = "example-agents/other"
ambiguous[path] = json.dumps(harness).encode()
canonical = "plugins/other/.agents/shared/policy/example/SKILL.md"
ambiguous[canonical] += b"\nDifferent canonical source.\n"
rejected(ambiguous, "ambiguous canonical identity", extensions=("example",))
virtual = dict(files)
canonical = "plugins/example/.agents/shared/policy/example/SKILL.md"
virtual["plugins/example/resources/canonical/policy/example/SKILL.md"] = virtual.pop(canonical)
rejected(virtual, "reference is not shipped", projections=(
    ("example", ".agents/shared", "resources/canonical"),
))
conflict = dict(files)
conflict["plugins/example/skills"] = b"not a directory"
rejected(conflict, "file/directory conflict")
def canonical_link(link: str) -> dict[str, bytes]:
    value = dict(files)
    canonical = "plugins/example/.agents/shared/policy/example/SKILL.md"
    value[canonical] += ("\n" + link + "\n").encode()
    return value


for link in (
    '[outside](../../../../../outside.md "local resource")',
    '[outside](<../../../../../outside file.md> "local resource")',
    '[outside][secret]\n\n[secret]: ../../../../../outside.md "local resource"',
    '[secret][]\n\n[secret]: <../../../../../outside file.md> (local resource)',
    '[secret]\n\n[secret]: ../../../../../outside.md',
    '[outside][secret]\n\n[secret]:\n  ../../../../../outside.md',
    '[image](../../../../../outside.md (local resource))',
    '[outside](%2e%2e/%2e%2e/%2e%2e/%2e%2e/%2e%2e/outside.md)',
    '[outside](..&#47;..&#47;..&#47;..&#47;..&#47;outside.md)',
):
    rejected(canonical_link(link), "reference leaves package")
for link in (
    '[private](file:///C:/private/secret.md)',
    '[private](<file:///C:/private/secret%20file.md> "local file")',
    '<file:///C:/private/secret.md>',
    '[private][secret]\n\n[secret]: file://server/share/secret.md "local file"',
    '[private](FILE:/C:/private/secret.md)',
    '[private](C:private/secret.md)',
):
    rejected(canonical_link(link), "unsafe local reference")
for link in (
    '[tool](../../../../resources/tool.py "local resource")',
    "[tool](../../../../resources/tool.py 'local resource')",
    '[tool](../../../../resources/tool.py (local resource))',
    '[tool][script]\n\n[script]: ../../../../resources/tool.py "local resource"',
    '[script][]\n\n[script]: ../../../../resources/tool.py',
    '[script]\n\n[script]: ../../../../resources/tool.py',
    '[tool][SCRIPT]\n\n[script]:\n  ../../../../resources/tool.py',
    '[space](<../../../../resources/document with spaces.md> "local resource")',
    '[space][document]\n\n[document]: <../../../../resources/document with spaces.md> "local resource"',
    '[space](../../../../resources/document%20with%20spaces.md)',
    r'[paren](../../../../resources/doc\(with\).md "local resource")',
    '[docs](https://example.org/readme "external documentation")',
    '[docs][external]\n\n[external]: https://example.org/readme "external documentation"',
    '<https://example.org/readme>',
    '[anchor](#local-section "this document")',
):
    value = canonical_link(link)
    value["plugins/example/resources/document with spaces.md"] = b"A shipped document.\n"
    value["plugins/example/resources/doc(with).md"] = b"A shipped document.\n"
    validate_packages(value)
import hashlib
import struct

table = list(range(65536))
seen = set()
for start, end, step, delta in WINDOWS_PATH_UPPERCASE_RANGES:
    assert 0 <= start <= end <= 65535
    assert step in (1, 2) and (end - start) % step == 0 and delta
    for point in range(start, end + 1, step):
        assert point not in seen and 0 <= point + delta <= 65535
        seen.add(point)
        table[point] = point + delta
assert len(WINDOWS_PATH_UPPERCASE_RANGES) == 134 and len(seen) == 973
assert WINDOWS_PATH_UPPERCASE == {point: mapped for point, mapped in enumerate(table) if point != mapped}
assert all(table[table[point]] == table[point] for point in range(65536))
assert all(table[point] == point for point in range(0xD800, 0xE000))
assert hashlib.sha256(struct.pack("<65536H", *table)).hexdigest() == "41c26bc7a12bdaeb26025c93118697c7e3ef81ee048b00fe5cce2a472e0e0742"
unicode_pairs = (
    ("Stra\u00dfe.md", "STRASSE.md", False),
    ("\u00df.md", "\u1e9e.md", False),
    ("sigma-\u03c3.md", "sigma-\u03c2.md", False),
    ("I.md", "\u0131.md", False),
    ("\u212a.md", "K.md", False),
    ("\u00e9.md", "e\u0301.md", False),
    ("\ufb00.md", "ff.md", False),
    ("\U00010400.md", "\U00010428.md", False),
    ("\U000104b0.md", "\U000104d8.md", False),
    ("\U0001e900.md", "\U0001e922.md", False),
    ("emoji-\U0001f600.md", "emoji-\U0001f601.md", False),
    ("Greek-\u1f80.md", "Greek-\u1f88.md", True),
    ("Latin-\u00c4.md", "Latin-\u00e4.md", True),
    ("Cyrillic-\u0410.md", "Cyrillic-\u0430.md", True),
    ("SKILL.md", "skill.md", True),
    ("emoji-\U0001f600-A.md", "emoji-\U0001f600-a.md", True),
)
for left, right, collision in unicode_pairs:
    assert (left.translate(WINDOWS_PATH_UPPERCASE).encode("utf-16-le", "surrogatepass")
            == right.translate(WINDOWS_PATH_UPPERCASE).encode("utf-16-le", "surrogatepass")) == collision
    for suffix in ("", "/leaf.txt"):
        value = dict(files)
        value[f"plugins/example/resources/{left}{suffix}"] = b"first content"
        value[f"plugins/example/resources/{right}{suffix}"] = b"second content"
        if collision:
            rejected(value, "Windows path identity collision")
        else:
            validate_packages(value)
            assert value[f"plugins/example/resources/{left}{suffix}"] == b"first content"
            assert value[f"plugins/example/resources/{right}{suffix}"] == b"second content"
    if collision:
        value = dict(files)
        value[f"plugins/example/resources/{left}"] = b"file"
        value[f"plugins/example/resources/{right}/leaf.txt"] = b"child"
        rejected(value, "Windows path identity collision")
rejected({**files, "plugins/example/resources/tool.py/leaf.txt": b"child"}, "file/directory conflict")
for left, right in (
    ("emoji-\U0001f600.md", "emoji-\U0001f600.md"),
    ("\U00010400.md", "\ud801\udc00.md"),
    ("\U0001f600-A.md", "\ud83d\ude00-a.md"),
    ("\ud801-A.md", "\ud801-a.md"),
):
    assert left.translate(WINDOWS_PATH_UPPERCASE).encode("utf-16-le", "surrogatepass") == right.translate(WINDOWS_PATH_UPPERCASE).encode("utf-16-le", "surrogatepass")
print("Pinned Unicode portable identities and table integrity: PASS")
if os.name == "nt":
    import ctypes
    import functools
    import tempfile
    native = ctypes.WinDLL("ntdll").RtlUpcaseUnicodeChar
    native.argtypes = [ctypes.c_uint16]
    native.restype = ctypes.c_uint16
    assert [native(point) for point in range(65536)] == table
    ordinal = ctypes.WinDLL("kernel32").CompareStringOrdinal
    ordinal.argtypes = [ctypes.c_wchar_p, ctypes.c_int, ctypes.c_wchar_p, ctypes.c_int, ctypes.c_int]
    ordinal.restype = ctypes.c_int
    def compare_units(left, right):
        result = ordinal(chr(left), 1, chr(right), 1, 1)
        assert result in (1, 2, 3)
        return result - 2
    ordered = sorted(range(65536), key=functools.cmp_to_key(compare_units))
    classes = {}
    group = 0
    for position, point in enumerate(ordered):
        if position and compare_units(ordered[position - 1], point):
            group += 1
        previous = classes.setdefault(table[point], group)
        assert previous == group
    assert len(classes) == group + 1
    with tempfile.TemporaryDirectory(prefix="kit-pinned-identity-") as directory:
        location = Path(directory)
        for position, (left, right, collision) in enumerate(unicode_pairs):
            for kind in ("file", "directory"):
                pair = location / f"{position}-{kind}"
                pair.mkdir()
                first, second = pair / left, pair / right
                if kind == "directory":
                    first.mkdir()
                    if collision:
                        assert second.exists() and first.samefile(second)
                    else:
                        second.mkdir()
                        assert not first.samefile(second)
                    first, second = first / "leaf.txt", second / "leaf.txt"
                first.write_bytes(b"first content")
                second.write_bytes(b"second content")
                assert first.samefile(second) == collision
                assert first.read_bytes() == (b"second content" if collision else b"first content")
                assert second.read_bytes() == b"second content"
    print("Windows native BMP equivalence and temporary filesystem qualification: PASS")
else:
    print("POSIX fixed Unicode identity fixtures: PASS")

for alias in (
    "plugins/example/.agents/shared/policy/example/skill.md",
    "plugins/example/Resources/extra.py",
    "plugins/example/RESOURCES",
):
    value = dict(files)
    value[alias] = b"different bytes"
    rejected(value, "Windows path identity collision")
for component in ("SKILL.md.", "tool.py ", "CON", "aux.txt", "COM1.log", "LPT9", "COM\u00b9.txt", "LPT\u00b2.log", "COM\u00b3", "bad|name"):
    value = dict(files)
    value[f"plugins/example/resources/{component}"] = b"unsafe filename"
    rejected(value, "Windows-unsafe path component")
rejected(canonical_link('[tool](../../../../resources/tool.py.)'), "Windows-unsafe path component")
for text in (
    "```markdown\n[secret]: https://example.org/docs\n```\n[outside][secret]\n[secret]: ../../../../../outside.md",
    "<!--\n[secret]: https://example.org/docs\n-->\n[outside][secret]\n[secret]: ../../../../../outside.md",
    "<!--\n```markdown\n[secret]: https://example.org/docs\n-->\n[outside][secret]\n[secret]: ../../../../../outside.md",
    "```markdown\n<!-- ignored comment opener\n```\n[outside](../../../../../outside.md)",
    "```markdown\n` unmatched code span inside fence\n```\n[outside](../../../../../outside.md)",
    "<!-- ` code span in comment -->\n[outside](../../../../../outside.md)",
    "> ```markdown\n> [example](../../../../../example.md)\n[outside](../../../../../outside.md)",
    "- ```markdown\n  [example](../../../../../example.md)\n[outside](../../../../../outside.md)",
    "[read `]`](../../../../../outside.md)",
):
    rejected(canonical_link(text), "reference")
rejected(canonical_link("[read `]`](file:///C:/private/secret.md)"), "unsafe local reference")
for text in (
    "`[outside](../../../../../outside.md)`",
    "``[outside](file:///C:/private/secret.md)``",
    "```markdown\n[example](../../../../../outside.md)\n[secret]: file:///C:/private/secret.md\n```",
    "~~~markdown\n[example](../../../../../outside.md)\n~~~",
    "> ```markdown\n> [example](../../../../../outside.md)\n> ```",
    "- ```markdown\n  [example](../../../../../outside.md)\n  ```",
    "    [example](../../../../../outside.md)\n    [secret]: file:///C:/private/secret.md",
    "- Example:\n\n      [example](../../../../../outside.md)",
    "<!--\n[example](../../../../../outside.md)\n```markdown\n-->",
    "`<!-- [example](file:///C:/private/secret.md) ``` `",
    "[read `]`](../../../../resources/tool.py)",
    "```markdown\n[secret]: ../../../../../inactive.md\n```\n[tool][secret]\n\n[secret]: ../../../../resources/tool.py",
):
    validate_packages(canonical_link(text))
for text in (
    "    [inactive](../../../../../example.md)\n\n[outside](../../../../../outside.md)",
    "> ```markdown\n> [inactive](../../../../../example.md)\n> ```\n[outside](../../../../../outside.md)",
    "- ```markdown\n  [inactive](../../../../../example.md)\n  ```\n[outside](../../../../../outside.md)",
    "<!--\n```markdown\n-->\n[outside](../../../../../outside.md)",
):
    rejected(canonical_link(text), "reference leaves package")
for component in ("COM\u00b9.txt", "LPT\u00b2.log", "COM\u00b3"):
    assert "?" not in component and any(ord(character) > 127 for character in component)
    value = dict(files)
    value[f"plugins/example/resources/{component}"] = b"reserved superscript filename"
    rejected(value, "Windows-unsafe path component")
for text in (
    "<div>\n[secret]: https://example.org/docs\n</div>\n\n[outside][secret]\n\n[secret]: ../../../../../outside.md",
    "<pre>\n```markdown\n[secret]: https://example.org/docs\n</pre>\n[outside][secret]\n\n[secret]: ../../../../../outside.md",
    "<!--\n<div>\n```markdown\n-->\n[outside][secret]\n\n[secret]: ../../../../../outside.md",
    "> [secret]: ../../../../../outside.md\n\n[outside][secret]",
    "- [secret]: ../../../../../outside.md\n\n[outside][secret]",
    '[read <span title="]">label</span>](../../../../../outside.md)',
):
    rejected(canonical_link(text), "reference leaves package")
for text in (
    "paragraph\n[secret]: https://example.org/docs\n\n[outside][secret]\n\n[secret]: ../../../../../outside.md",
    "`example`\n[secret]: https://example.org/docs\n\n[outside][secret]\n\n[secret]: ../../../../../outside.md",
    "paragraph\n[secret]: ../../../../../outside.md\n\n[outside][secret]",
):
    rejected(canonical_link(text), "ambiguous reference definition")
rejected(canonical_link('[read <span title="]">label</span>](file:///C:/private/secret.md)'), "unsafe local reference")
for text in (
    "<div>\n[example](../../../../../outside.md)\n[secret]: file:///C:/private/secret.md\n</div>",
    "<pre>\n```markdown\n[example](../../../../../outside.md)\n</pre>",
    "<script>\n[example](file:///C:/private/secret.md)\n</script>",
    "<![CDATA[\n```markdown\n[example](../../../../../outside.md)\n]]>",
    "<?example\n[example](../../../../../outside.md)\n?>",
    "> <div>\n> [example](../../../../../outside.md)\n> </div>",
    "- <div>\n  [example](../../../../../outside.md)\n  </div>",
    "> [secret]: ../../../../resources/tool.py\n\n[tool][secret]",
    "- [secret]: ../../../../resources/tool.py\n\n[tool][secret]",
    '[read <span title="]">label</span>](../../../../resources/tool.py)',
    "<div>\n[secret]: ../../../../../inactive.md\n</div>\n\n[tool][secret]\n\n[secret]: ../../../../resources/tool.py",
    'paragraph <span title="[secret]: ../../../../../inactive.md">example</span>',
):
    validate_packages(canonical_link(text))
for text in (
    "<div>\n` unmatched code\n```markdown\n</div>\n\n[outside](../../../../../outside.md)",
    "> <div>\n> [inactive](../../../../../example.md)\n[outside](../../../../../outside.md)",
    "- <div>\n  [inactive](../../../../../example.md)\n[outside](../../../../../outside.md)",
    "<!--\n<pre>\n-->\n[outside](../../../../../outside.md)",
):
    rejected(canonical_link(text), "reference leaves package")
for text in (
    "prose <!--> [outside](../../../../../outside.md)",
    "prose <!---> [outside](../../../../../outside.md)",
    "prose <!-- incomplete [outside](../../../../../outside.md)",
    'prose <span title="`">[outside](../../../../../outside.md)`</span>',
    "prose <span title='`'>[outside](../../../../../outside.md)`</span>",
    'prose <span title="<!--">[outside](../../../../../outside.md)</span>',
    "prose <span title='<!--'>[outside](../../../../../outside.md)</span>",
    "prose <!-- ordinary example --> [outside](../../../../../outside.md)",
):
    rejected(canonical_link(text), "reference leaves package")
for text in (
    "prose <!-- incomplete [private](file:///C:/private/secret.md)",
    "prose <!--> [private](file:///C:/private/secret.md)",
    'prose <span title="<!--">[private](file:///C:/private/secret.md)</span>',
    'prose <span title="`">[private](file:///C:/private/secret.md)`</span>',
):
    rejected(canonical_link(text), "unsafe local reference")
for text in (
    "prose <!--> [tool](../../../../resources/tool.py)",
    "prose <!---> [tool](../../../../resources/tool.py)",
    "prose <!-- incomplete [tool](../../../../resources/tool.py)",
    'prose <span title="`">[tool](../../../../resources/tool.py)`</span>',
    'prose <span title="<!--">[tool](../../../../resources/tool.py)</span>',
    'prose <span title="[example](../../../../../inactive.md)`<!--">plain</span>',
    "prose <!-- [example](../../../../../inactive.md) --> valid",
    "prose <!-- [example](file:///C:/private/secret.md)\ncontinued --> valid",
    "prose `<span title='<!--'>[example](../../../../../inactive.md)</span>`",
    "<!--> [example](../../../../../inactive.md)",
    "<!-- incomplete [example](file:///C:/private/secret.md)",
    "[read <!-->label](../../../../resources/tool.py)",
):
    validate_packages(canonical_link(text))
for boundary in ("", "# heading", "- list item", "1. list item", "> quote", "```markdown", "~~~markdown", "---", "***", "===", "<div>"):
    for destination in ("../../../../../outside.md", "file:///C:/private/secret.md"):
        active = f"[outside]({destination})"
        for text in (
            f"prose <!--\n{boundary}\n{active}\n-->",
            f'prose <span title="\n{boundary}\n{active}\n">done</span>',
            f"[read <!--\n{boundary}\n{active}\n-->label](../../../../resources/tool.py)",
        ):
            for ending in ("\n", "\r\n", "\r"):
                variant = text.replace("\n", ending)
                try:
                    list(package_links(variant))
                except ValueError as error:
                    assert "ambiguous multiline inline token" in str(error)
                else:
                    raise AssertionError("Direct inline parsing accepted an ambiguous boundary")
                rejected(canonical_link(variant), "ambiguous multiline inline token")
        code_boundary = boundary
        if boundary.startswith(("```", "~~~")):
            code_boundary += "\ninactive example\n" + boundary[:3]
        if boundary == "<div>":
            code_boundary += "\ninactive example\n</div>\n"
        code = f"prose `\n{code_boundary}\n{active}\n`"
        expected = "unsafe local reference" if destination.startswith("file:") else "reference leaves package"
        for ending in ("\n", "\r\n", "\r"):
            variant = code.replace("\n", ending)
            assert destination in list(package_links(variant))
            rejected(canonical_link(variant), expected)
for text in (
    "prose <!-- ordinary\nsoft continuation --> [tool](../../../../resources/tool.py)",
    'prose <span title="ordinary\nsoft continuation">[tool](../../../../resources/tool.py)</span>',
    "prose <span\n title='ordinary'>[tool](../../../../resources/tool.py)</span>",
    "[read <span title='ordinary\nsoft continuation'>label</span>](../../../../resources/tool.py)",
    "prose `ordinary\nsoft continuation [example](../../../../../inactive.md)`",
    "The launcher **exits non-zero** on failure and prints `Launched codex-cli <version> from <path> on\n<selection>` on success.",
    "<!--\n# heading\n[example](../../../../../inactive.md)\n-->",
    '<div title="\n# heading\n[example](file:///C:/private/secret.md)\n">done</div>',
    "```markdown\nprose <!--\n# heading\n[example](../../../../../inactive.md)\n-->\n```",
):
    baseline = list(package_links(text))
    for ending in ("\n", "\r\n", "\r"):
        variant = text.replace("\n", ending)
        assert list(package_links(variant)) == baseline
        validate_packages(canonical_link(variant))
for boundary in ("# heading", "- list item", "> quote"):
    text = f"prose `example\n{boundary}\n[outside](../../../../../outside.md)\n`"
    for ending in ("\n", "\r\n", "\r"):
        rejected(canonical_link(text.replace("\n", ending)), "reference leaves package")
rejected(canonical_link(
    "prose `example\n```markdown\n[inactive](../../../../../inactive.md)\n```\n"
    "[outside](../../../../../outside.md)\n`"
), "reference leaves package")
for inner, definitions in (
    ("[private](file:///C:/private/secret.md)", ""),
    ("[outside](../../../../../outside.md)", ""),
    ("[private][secret]", "\n\n[secret]: file:///C:/private/secret.md"),
    ("[outside][secret]", "\n\n[secret]: ../../../../../outside.md"),
    ("<file:///C:/private/secret.md>", ""),
):
    text = f"[outer {inner}](../../../../resources/tool.py)" + definitions
    rejected(canonical_link(text), "ambiguous nested active link in label")
for inner, definitions in (
    ("![private](file:///C:/private/secret.md)", ""),
    ("![outside](../../../../../outside.md)", ""),
    ("![private][secret]", "\n\n[secret]: file:///C:/private/secret.md"),
    ("![outside][secret]", "\n\n[secret]: ../../../../../outside.md"),
):
    text = f"[outer {inner}](../../../../resources/tool.py)" + definitions
    expected = "unsafe local reference" if "file:" in text else "reference leaves package"
    rejected(canonical_link(text), expected)
for boundary in ("", "# heading", "> quote", "- list item", "```markdown", "---", "***"):
    body = boundary
    if boundary.startswith("```"):
        body += "\ninactive example\n```"
    for inner, definitions, expected in (
        ("[outside](../../../../../outside.md)", "", "reference leaves package"),
        ("[private](file:///C:/private/secret.md)", "", "unsafe local reference"),
        ("[outside][secret]", "\n\n[secret]: ../../../../../outside.md", "reference leaves package"),
        ("<file:///C:/private/secret.md>", "", "unsafe local reference"),
    ):
        text = f"[outer\n{body}\n{inner}\n](../../../../resources/tool.py)" + definitions
        for ending in ("\n", "\r\n", "\r"):
            variant = text.replace("\n", ending)
            assert list(package_links(variant))
            rejected(canonical_link(variant), expected)
for text in (
    "[outer [plain bracket]](../../../../resources/tool.py)",
    "[outer `[private](file:///C:/private/secret.md)`](../../../../resources/tool.py)",
    "[outer <!-- [private](file:///C:/private/secret.md) --> label](../../../../resources/tool.py)",
    '[outer <span title="[private](file:///C:/private/secret.md)">label</span>](../../../../resources/tool.py)',
    "[outer\nsoft break](../../../../resources/tool.py)",
    "[outer [tool](../../../../resources/tool.py)] literal outer",
    "[outer ![tool](../../../../resources/tool.py)](../../../../resources/tool.py)",
    "[outer ![tool][image]](../../../../resources/tool.py)\n\n[image]: ../../../../resources/tool.py",
    "[outer ![image][]](../../../../resources/tool.py)\n\n[image]: ../../../../resources/tool.py",
    "[outer ![image]](../../../../resources/tool.py)\n\n[image]: ../../../../resources/tool.py",
    "[outer ![tool][image]][outer]\n\n[image]: ../../../../resources/tool.py\n[outer]: ../../../../resources/tool.py",
):
    baseline = list(package_links(text))
    for ending in ("\n", "\r\n", "\r"):
        variant = text.replace("\n", ending)
        assert list(package_links(variant)) == baseline
        validate_packages(canonical_link(variant))
for text in (
    "[outer [tool](../../../../resources/tool.py)](../../../../../literal-outer.md)",
    "[outer [tool][script]](../../../../resources/tool.py)\n\n[script]: ../../../../resources/tool.py",
    "[outer <https://example.org/docs>](../../../../resources/tool.py)",
):
    rejected(canonical_link(text), "ambiguous nested active link in label")
for boundary in ("", "# heading", "> quote", "- list item", "```markdown", "~~~markdown", "***", "---", "==="):
    for destination in ("../../../../../outside.md", "file:///C:/private/secret.md"):
        for opening, closing in (('"', '"'), ("'", "'"), ("(", ")")):
            title = f"{opening}\n{boundary}\n[private]({destination})\n{closing}"
            for text in (
                f"[outer](../../../../resources/tool.py {title})",
                f"[outer]: ../../../../resources/tool.py {title}\n\n[outer]",
            ):
                for ending in ("\n", "\r\n", "\r"):
                    variant = text.replace("\n", ending)
                    try:
                        list(package_links(variant))
                    except ValueError as error:
                        assert "ambiguous multiline inline token" in str(error)
                    else:
                        raise AssertionError(("Interrupted title consumed an active destination", variant))
                    rejected(canonical_link(variant), "ambiguous multiline inline token")
for opening, closing in (('"', '"'), ("'", "'"), ("(", ")")):
    title = f"{opening}ordinary\nsoft continuation{closing}"
    for text in (
        f"[outer](../../../../resources/tool.py {title})",
        f"[outer]: ../../../../resources/tool.py {title}\n\n[outer]",
    ):
        for ending in ("\n", "\r\n", "\r"):
            variant = text.replace("\n", ending)
            assert list(package_links(variant)) == ["../../../../resources/tool.py"]
            validate_packages(canonical_link(variant))
for text in (
    '[outer](../../../../resources/tool.py "literal\n[private](file:///C:/private/secret.md)")',
    "[outer]: ../../../../resources/tool.py 'literal\n[private](../../../../../outside.md)'\n\n[outer]",
    '`[outer](../../../../resources/tool.py "\\n# heading\\n[private](file:///C:/private/secret.md)\\n")`',
    '```markdown\n[outer](../../../../resources/tool.py "\n# heading\n[private](file:///C:/private/secret.md)\n")\n```',
):
    validate_packages(canonical_link(text))
for text in (
    "[ordinary](../../../../resources/tool.py \"unfinished\n```markdown\n[private](file:///C:/private/secret.md)\n```",
    "[ordinary](../../../../resources/tool.py \"unfinished\n```markdown\n\" [private](file:///C:/private/secret.md)\n```",
    "prose [ordinary]: ../../../../resources/tool.py \"unfinished\n```markdown\n\" [private](file:///C:/private/secret.md)\n```",
    "<!--\n[outer](../../../../resources/tool.py \"\n# heading\n[private](file:///C:/private/secret.md)\n\")\n-->",
    "<div>\n[outer]: ../../../../resources/tool.py \"\n# heading\n[private](file:///C:/private/secret.md)\n\"\n</div>",
    "prose <!-- [outer](../../../../../outside.md 'ordinary') -->",
    'prose <span title="[outer](file:///C:/private/secret.md)">example</span>',
):
    for ending in ("\n", "\r\n", "\r"):
        validate_packages(canonical_link(text.replace("\n", ending)))
print("Guarded inline/reference titles and soft-break controls (LF/CRLF/CR): PASS")
print("Label boundary, document references and nested image controls: PASS")
print("Opaque multiline inline boundary family and soft-break controls (LF/CRLF/CR): PASS")
print("Inline HTML token precedence and comment-boundary fixtures: PASS")
print("Raw HTML, paragraph definition and tag-label neighbors: PASS")
print("Active Markdown context, code-span label and Unicode device neighbors: PASS")
print("PKG-D1 structured references and PKG-D2 portable paths: PASS")
print("Synthetic fixtures: PASS")
core = Path(r"C:/Users/TommySeery/source/repos/tj-agents/core")
validate_packages(
    package_files(core), extended_adapter_names=package_extensions(core),
    source_projections=package_source_projections(core),
)
print("Actual Core read-only packages: PASS")
from unittest.mock import patch

def helper_rejected(call, expected):
    try:
        call()
    except ValueError as error:
        assert expected in str(error), (expected, str(error))
    else:
        raise AssertionError(f"Expected rejection containing {expected!r}")

with patch.dict(globals(), {"is_link_or_junction": lambda path: path == core / "plugins"}):
    helper_rejected(lambda: package_files(core), "link or junction")
with patch.dict(globals(), {"package_read_file": lambda path: b"[]"}):
    helper_rejected(lambda: package_extensions(core), "must be a JSON object")
with patch.dict(globals(), {"package_read_file": lambda path: b'{"extended_host_adapters": "review"}'}):
    helper_rejected(lambda: package_extensions(core), "unique skill names")
with patch.dict(globals(), {"package_read_file": lambda path: b'{"resources": "not a list"}'}):
    helper_rejected(lambda: package_source_projections(core), "resources must be a list")
with patch.dict(globals(), {"package_read_file": lambda path: b"{}"}):
    assert package_extensions(core) == ()
    assert package_source_projections(core) == ()
print("Snapshot guard and optional declaration fixtures: PASS")
```

Run the following self-contained driver from the owning Kit worktree with python -B. It loads the current template read-only, executes this document's first proposed implementation block and fixture block, and exercises the proposed caller. It leaves production modules and Core untouched.

```python
from pathlib import Path
import importlib.util
from importlib.machinery import SourceFileLoader
import re
import sys
import textwrap
from types import SimpleNamespace

root = Path.cwd()
source = root / ".agents/kit/utility/new-plugin/templates/repository/.agents/sync_generated.py.in"
loader = SourceFileLoader("package_structure_proposal", str(source))
module = importlib.util.module_from_spec(importlib.util.spec_from_loader(loader.name, loader))
loader.exec_module(module)
reference = root / "plans/template-structure/PACKAGE_STRUCTURE.md"
blocks = re.findall(r"```python\n(.*?)\n```", reference.read_text(encoding="utf-8"), re.S)
exec(compile(blocks[0], str(reference) + ":implementation", "exec"), module.__dict__)
probe = next(block for block in blocks if block.startswith("def fixture()"))
exec(compile(probe, str(reference) + ":probe", "exec"), module.__dict__)
for block in blocks:
    snippet = textwrap.dedent(block)
    if snippet.startswith("validate_file_references("):
        snippet = "def proposed_build_tail():\n" + textwrap.indent(snippet, "    ")
    compile(snippet, str(reference) + ":snippet", "exec")
print("All proposed Python blocks parse in their intended context: PASS")
module.validate_packages(module.build(root))
print("Current Kit in-memory generated package: PASS")
context = {
    "generator": module, "argparse": module.argparse, "Path": Path, "sys": sys,
    "new_plugin": SimpleNamespace(kit_version=lambda: module.KIT_VERSION),
}
for marker in ("def check_packages(", "def main()"):
    exec(next(block for block in blocks if block.startswith(marker)), context)
saved = sys.argv
try:
    sys.argv = ["proposed-check.py", "--packages-only", "--root", str(module.core)]
    assert context["main"]() == 0
finally:
    sys.argv = saved
print("Proposed packages-only caller against actual Core: PASS")
```

Source evidence: current Kit generator helpers and check main; Core scripts/sync_plugin_packages.py expected_adapter_body; Core plugins/base/{skills,codex-skills}/agent-files/SKILL.md; Core .agents/plugins/sources.json extension declarations; all three native manifests and optional harnesses. Core root HEAD observed 1bb1c130b2d1762bce07b599bb0fbb7e311c6749. Feature-RepositoryConfiguration was inspected only as read-only source context.

## Independent review corrections

PKG-D1 replaces the simple Markdown link regex with a structured destination scanner. It supports titled inline links, angle destinations with spaces, balanced and escaped parentheses, full/collapsed/shortcut references with normalized labels and external autolinks. It decodes Markdown punctuation escapes and HTML entities; local percent-encoded paths are decoded before package resolution. File-scheme and drive destinations remain local and are rejected, including titled/reference/autolink forms. Ordinary external documentation and fragment-only links remain external. Unused reference definitions are not rendered links. This parser is deliberately confined to the supported Markdown link forms; it does not interpret script command paths or runtime policy.

PKG-D1 now masks inactive blocks sequentially before collecting definitions: fenced and indented examples, simple quote/list containers, HTML comments and CommonMark raw HTML blocks. Masking preserves line positions; an inline code example retains a neutral paragraph marker. Fences inside comments/HTML and code spans inside inactive blocks cannot change later active scanning. Label matching treats matched code spans and syntactically valid inline HTML tags as opaque, including a closing bracket inside an attribute value.

Reference definitions at a blank/block boundary, including simple quote/list definitions, remain globally available. A parsed definition encountered within an active paragraph is recorded as ambiguous rather than allowed to shadow a real definition. A link using that label fails explicitly, even if a later definition would otherwise be usable. This conservative contract does not claim a complete CommonMark renderer. Unrecognized inline syntax remains scanned for local links; uncertainty about a recognized paragraph definition produces rejection rather than an external-target fallback. The fixture block preserves inactive examples and checks active links immediately after those contexts. Rich Core runtime prose remains opaque.

The final inline correction follows CommonMark 0.31.2 section 6.6 (`https://spec.commonmark.org/0.31.2/#raw-html`): an inline comment may end immediately as `<!-->` or `<!--->`, or use a complete `<!-- ... -->` pair. An unfinished inline opener remains active text. A valid raw tag is consumed at its starting `<` before attribute-contained backticks or comment openers can affect scanning; its following body is still scanned. This ordering also applies within link labels. Line-leading HTML comments remain governed by the separate block end condition, including unfinished block examples. Complete multiline inline comments and raw tags are rejected as ambiguous before masking if they cross a blank line or a continuation line beginning with block-looking heading, list, quote, fence, thematic/setext or HTML syntax. Ordinary soft-break continuation is supported. The guard deliberately treats these prefixes at any indentation as uncertain; it does not try to reconstruct arbitrary container/block grammar inside an inline token. Line-leading HTML blocks and fenced/indented examples are handled before inline scanning and remain valid. This is a bounded safety contract, not a general renderer.

The final multiline family uses the same package_inline_boundary guard from code, complete tag and comment endpoints, including endpoint calls during label recognition. Its ValueError is an explicit structural rejection rather than a guessed inactive context. Fixtures exercise escaping paths and file URIs across all supported interruption prefixes, labels, ordinary multiline comments/tags/code, actual HTML blocks, and an active link after a closed fence. Unfinished inline tokens remain active text; code endpoints now reuse that same guard to disqualify crossing candidate spans and return None, leaving their text active; tag/comment endpoints retain explicit ambiguity rejection. These conservative constraints are intentional package-authoring limits and belong in permanent acceptance tests.

The code endpoint now searches for a matching delimiter and invokes package_inline_boundary before accepting it. A boundary failure returns None rather than masking the candidate, preserving the prior literal/unclosed behavior. The opaque-token matrix includes code spans at every interruption prefix and every LF/CRLF/CR ending; it asserts destination visibility and package rejection for code cases, rather than requiring a guard exception. Fence/HTML controls place the active link after their real closing boundary. The old partial code-only boundary expression is removed; no new helper or parser family is introduced.

The initial direct propagation of this guard exited 1 after the synthetic matrix passed: actual Core plugins/machine/.agents/machine/utility/handoff-codex/SKILL.md contains the valid soft-break prose ?The launcher **exits non-zero** on failure and prints `Launched codex-cli <version> from <path> on? followed by ?<selection>` on success.? Disqualifying the candidate span keeps that Core package acceptable while exposing any active local destination beyond a real interruption. The exact prose is included as a valid control for all three newline endings. The corrected driver exits 0; no success is attributed to the failed direct-propagation run.

The final label correction applies package_inline_boundary when a candidate closing bracket is found. Crossing candidates return None, like code spans, so a later active destination is scanned rather than consumed as label text. Unresolved plain-bracket candidates advance one character rather than skipping their body. This preserves ordinary nested brackets and soft-break labels while preventing blank/headings/lists/quotes/fences/thematic boundaries from hiding downstream links.

Before consuming a confirmed inline or resolved reference outer link, package_label_destinations scans its label with the same document-level definitions and ambiguity maps. Matched code, comments and raw tags stay opaque. A nested active ordinary inline/reference/autolink makes the apparent outer link ambiguous and raises explicitly. This intentionally rejects even safe nested ordinary links when an apparent outer destination exists, including an escaping outer target that CommonMark would render literally; the contract does not guess full nested-link precedence. A plain unresolved outer bracket may contain a safe ordinary link and remains supported. Nested images are supported: their inline/full/collapsed/shortcut destinations are checked alongside the confirmed outer destination, using document definitions rather than a reparsed fragment. Image alt text remains label text. Fixtures cover valid nested image links and unsafe image destinations, as well as the conservative safe ordinary-link cases. No fragment recursion, renderer, runtime or dependency is introduced.

Complete titles now use the same package_inline_boundary guard. package_destination captures the exact title span and checks it only after confirming the enclosing inline closing delimiter or the reference-definition end of line. An uncertain complete title raises explicitly; neither caller can record a consumed outer span or suppress its active-looking interior. Incomplete ordinary link text returns None and does not turn a later real fenced example into a title error.

Active scanning validates these apparent complete candidates before later block masking can erase a fence-interrupted title. Inline candidates require a matched outer label followed by `(`; reference-definition candidates require a colon and an otherwise empty quote/list-stripped opening-line prefix. Earlier code/comment/raw-HTML contexts are processed first, so their examples and tag attributes remain opaque. A first endpoint-only probe exited 1 because a fence removed the remainder of the title before destination parsing; bounded opening-context validation corrected that sequencing. Ordinary soft-break titles, all three title delimiters, LF/CRLF/CR, earlier inactive contexts and incomplete link text followed by a real fence have focused fixtures. No identity helper changed; the actual implementation correction affects package_destination and package_active_markdown only, adding fourteen source lines relative to frozen 2b57.

The combined Cpp probe executes the existing final Python driver from plans/template-structure/CPP_PACKAGE_COMPATIBILITY.md through python -I -B -. It exited 0 against exact revision 38d3b060d42c32921580d49949b411395e7eb245, retained 149 resource/profile files, produced 348 projected files from 263 baseline files, added 85 files/419696 bytes, and closed all nine packages independently. Its source-link guards, standalone gpp/native-root/alias fixtures and malformed-input checks passed. Cpp reference bytes were verified unchanged. Git warned that its global ignore file could not be read; the exact-object in-memory probe still exited 0. This is proposal shape evidence, not native host or current remote acceptance.

The same boundary family normalizes CRLF and lone CR to LF before active scanning. package_text extends its existing CRLF normalization to lone CR; package_active_markdown adds one normalization line for direct callers and emitted-resource strings. These are one changed helper line and one added helper line, with no new helper/API. Family negatives, direct package_links calls, ordinary soft-break controls and code interruption neighbors run with LF, CRLF and CR; line-leading block examples remain supported for every ending.

The four confirmed inline repros and their short-comment, single-quoted-attribute, valid shipped-link, inactive-attribute, multiline-comment, code-example and line-leading-block neighbors are permanent acceptance candidates. The final driver prints a distinct inline token/comment-boundary pass marker.

PKG-D2 rejects Windows-unsafe components, including trailing dots/spaces, invalid characters/control bytes and reserved device stems, including COM/LPT superscript digits represented with explicit ASCII Unicode escapes. Before any output, file-map validation assigns the pinned Windows reference uppercase identity as UTF-16 bytes to every file and implied directory. Differing spellings and file/directory conflicts fail regardless of bytes. Canonical adapter links still use exact physically shipped paths; no case-insensitive fallback is introduced.

The fixture block contains the exact reviewed titled escaping link, angle/space and full/collapsed/shortcut reference variants, absolute file-scheme variants, valid external/titled/reference links, valid shipped paths with spaces/parentheses, differing SKILL.md/skill.md bytes, trailing-dot aliases, directory aliases and reserved components.

## PKG-D2 Unicode identity correction

Root selected an inline reference baseline after casefold incorrectly merged valid native filename pairs. The reviewed observation is Windows build 26200.9448; ntdll.dll and kernelbase.dll report 10.0.26100.9278. The 134 ASCII ranges reconstruct all 65536 WCHAR entries, including 973 nonidentity mappings, from RtlUpcaseUnicodeChar. Exhaustive BMP CompareStringOrdinal ignore-case equivalence classes agree with that table. The LF-normalized declaration above is 141 lines and 4163 ASCII bytes, SHA256 dab0575edcb5aa824c84dbdff349016687a105e999e396626c5a392f2de90923. Its expanded little-endian uint16 table SHA256 is 41c26bc7a12bdaeb26025c93118697c7e3ef81ee048b00fe5cce2a472e0e0742.

Production uses that fixed table identically on Windows and POSIX, independent of locale and Python Unicode data. Translate changes only checked BMP entries; surrogate units and supplementary scalar values stay unchanged. Encoding the translated result as UTF-16 little-endian with surrogatepass makes its equality exactly the table's WCHAR-unit equality, including explicitly represented surrogate pairs. No new production import/helper, native API dependency, external resource, runtime setting or Unicode normalization is introduced. File spelling, implied-ancestor and file/directory conflict behavior remains intact. The qualified Markdown/title helpers and component guards are unchanged.

This defines a tested reference baseline rather than universal filesystem semantics. Microsoft's CompareStringOrdinal contract uses the operating system uppercase table; FsRtlAreNamesEqual also permits a supplied table. It does not guarantee the same aliases for every OS version, formatter, volume upcase table or case-sensitive directory. Future Windows native-table or filesystem-fixture drift fails qualification and requires a reviewed baseline/table change; production never silently adopts host-dependent mappings. Official API provenance is learn.microsoft.com/windows/win32/api/stringapiset/nf-stringapiset-comparestringordinal, learn.microsoft.com/windows-hardware/drivers/ddi/wdm/nf-wdm-rtlupcaseunicodechar and learn.microsoft.com/windows-hardware/drivers/ddi/ntifs/nf-ntifs-_fsrtl_advanced_fcb_header-fsrtlarenamesequal. Unicode full mapping/casefold semantics are documented at unicode.org/faq/casemap_charprop.html. Python length-preserving uppercase differed at 244 BMP entries in the read-only observation; Microsoft's recommended exFAT table differed at 109 entries, including final sigma, so neither replaces the qualified reference.

Permanent acceptance includes sixteen scalar Unicode filename pairs as resource siblings with distinct bytes, implied directories and colliding file/directory spellings; ASCII/Greek/Latin/Cyrillic aliases; supplementary scripts and emoji; canonical-equivalent but physically distinct spelling; and four equal-scalar/surrogate controls. Table checks cover bounds, allowed steps, nonzero deltas, disjoint expanded entries, exact mapping cardinality/hash, idempotence and unchanged surrogates. Windows-only qualification compares all native BMP mappings and ordinal equivalence classes, then probes file and directory identities in a disposable temporary directory; POSIX uses the same fixed-table cases without native calls. These are design fixtures until integrated into permanent production tests.

The Stage 2 Unicode correction adds 145 source lines and deletes two relative to frozen c290, plus 110 fixture lines: 257 substantive added/deleted source/fixture lines, with the corresponding 147-line generator mirror diff reported separately. The complete later validator remains 1117 implementation lines with 608 design-fixture lines. The identity-only used subset is its 141-line table plus three existing functions (46 AST-span lines), or 195 lines with stated separators before wiring/test setup; its focused portable fixture regions comprise 110 new Unicode/table/native/filesystem lines and 13 existing direct alias/component lines, before fixture setup. The nineteen-function reference closure remains 585 function-span lines; its required table/imports/separators bring the used source subset to 769 lines. This does not hide release wiring, setup, documentation or mirrors; root owns the actual candidate diff and chosen 1.4.1 -> 1.4.2 -> 1.5 topology.

On October 12, 2026 the shared/Core driver, exact d0b42f2382e477c48ee7d062005b1813d712bee6 Template 1.4 overlay, and unchanged combined Cpp driver all exited 0 after this correction. Shared fixtures printed both pinned-Unicode/table-integrity and Windows-native-BMP/temporary-filesystem PASS markers, alongside every previously qualified title/label/opaque-token/newline control. Core/current Kit/packages-only probes remained green. The exact publication overlay produced 219 files and verified source bytes unchanged against HEAD. Cpp retained exact 38d3b060d42c32921580d49949b411395e7eb245 shape, 263 -> 348 projected files, +85 files/+419696 bytes, 149 preserved resource/profile files and nine independently closed packages; its existing global-ignore permission warning remained nonfatal. The current host executed Windows qualification; no POSIX-host execution is claimed. POSIX permanent qualification runs the same fixed Unicode/table cases without the native branch. All proposed functions except package_identities were AST-identical to c290; no component or Markdown/title helper changed. These remain design-driver results rather than passing permanent production tests.

## Remaining production validation

The probe is design evidence only. Add permanent focused tests for malformed UTF-8/metadata/marketplaces/manifests/harness roots, mismatched paired identities/inventories, resource context, declared/undeclared/ambiguous extensions, absent extension config, and link/junction snapshot rejection. Exercise the packages-only CLI with temporary filesystem fixtures, plus default check's pre-generation behavior and unknown authored-entry rejection.

Verify runtime binding allowance/ignore/nonshipping and rejection of nearby unknown names. Run existing full unittest discovery, generation freshness and template byte equality after actual implementation. Live actual Core is supplemental acceptance, not a mandatory network/local-Core dependency for permanent tests.

Measured concrete proposal against the existing Template 1.4.0 generator/check source: 1117 implementation/helper lines added; harness helper replacement adds 1 and deletes 23; check_packages adds 10; check main replacement adds 12 and deletes 4; build adds one validator call. The complete fixture/probe block has 608 lines. This is 1776 proposed substantive added/deleted code and fixture lines before standard/ignore/version/documentation edits and permanent-test integration formatting. The standalone 39-line development driver and 29-line exact-object overlay driver are design evidence, not shipped runtime/test code. The root vendored generator mirror repeats 1142 proposed added/deleted lines, and root .gitignore repeats one; report this 1143-line mirror separately. Generated package resource copies repeat their source changes and are excluded from authored substantive size.

The concrete proposal exceeds the 1000-line assessment trigger; this requires an atomicity/scope assessment rather than a module-length cap. The validator, native snapshot caller and safety fixtures form one atomic structural contract: generation must reject unsafe portable identities before writing; filesystem validation must apply the same closed-map/native-root rules; projections/extensions are necessary for actual Core compatibility. The complete shared validator remains one coherent contract, but a smaller independent delivery boundary is viable: first harden the existing 1.4 generator reference checks and its output map, then add native metadata/harness/package-only validation. The first delivery must wire package_component/package_relative/package_identities into build before output, replace the old MARKDOWN_LINK portion of references with package_links while preserving the existing placeholder-reference path, and apply package_target to physically shipped plugin contexts in validate_file_references. Source-only local adapters retain their existing source resolution. Include all parser dependencies actually used by that wiring and focused active/inactive/escape/file-scheme/portable-alias generation fixtures; do not add unused native-manifest, projection, snapshot or caller helpers. This produces an independently functional generator safety outcome with meaningful negatives, while leaving the existing 1.4 native behavior and strict harness helper intact. The successor then adds the shared manifest/canonical/harness/extension validator, native snapshot safety and packages-only caller, reusing the already exercised parser/path helpers. That alternative requires concrete first-delivery wiring and an actual diff measurement before execution; the present 1776 count covers the complete proposal rather than claiming either split count. Parent chooses delivery topology after qualification. No companion-module extraction is needed. Binding allowlist/ignore/nonshipping remains the small explicitly authorized opaque-artifact correction. The parent will reassess the actual implemented diff size rather than claim a final production count from this proposal. No Core runtime/schema/configuration/hooks/lane/catalog changes; no CI ownership changes. Existing harness envelope code is reused rather than duplicated. Root chose the delivery topology 1.4.1 portable identities, then 1.4.2 qualified references, then 1.5 native structural validation; this reference contains the complete later shared contract, and root owns each actual measured slice.

The first-slice extraction through package_links excludes package_object and includes exactly nineteen used functions: package_component, package_relative, package_identities, package_text, package_present, package_target, package_markdown_value, package_code_end, package_quote_line, package_inline_boundary, package_tag_end, package_comment_end, package_html_block, package_active_markdown, package_label_end, package_destination, package_label_destinations, package_destinations and package_links. AST dependency closure from package_links/package_identities/package_target alone gives eighteen functions and 578 function-span lines; package_text adds seven used decoding lines for scanning all emitted plugins/**/*.md. The nineteen-function extraction therefore has 585 function-span lines; the live pinned table adds its 141-line declaration. Adding the three imports and two-line function/import/table separators gives 769 authored helper/table lines and a 769-line root mirror before wiring changes. package_object, native metadata/harness/extension/projection helpers and filesystem snapshots are excluded from this first subset. Publication identity for an emitted plugin path is PurePosixPath(shipped_dir).parts[1]; retain the existing placeholder loop and source-only adapter resolution. The emitted Markdown loop uses package_text/package_links/package_target, and build uses package_identities, so every extracted helper has a live dependency path.

The existing focused safety-fixture region from canonical_link through the synthetic pass markers contains 445 lines, including the Unicode qualification block and latest inline neighbors. It must be adapted to the independently wired 1.4 generator checks and generation negatives rather than calling the later full validate_packages API. Its fixture setup, assertions and generator wiring must be measured in the actual first-delivery diff; neither 769 nor 445 claims a complete delivery count. All nineteen helpers and the table must be reached by the first-delivery build/reference path; the later common validator must reuse them. The current helper/table/fixture-region subtotal is 1214 lines before setup and wiring; the complete 1776-line proposal requires the recorded scope assessment.

If the measured first-delivery diff exceeds the assessment trigger after setup/wiring/documentation, a further coherent boundary is viable: first publish only portable output identity enforcement using package_component/package_relative/package_identities called from build before output is written; these three live helpers total 46 function-span lines and use the 141-line pinned declaration. Their identity-only extraction is 187 nonseparator lines, or 195 source lines with two blank separator lines after the table and each function, before build wiring and permanent-test integration. Meaningful generation negatives cover unsafe components, case-equivalent file/directory identities and file/directory conflicts. Then publish the qualified Markdown/reference closure reusing those portable helpers, preserving source-only adapters/placeholders and scanning emitted Markdown. The native metadata/harness/extensions/snapshot/packages-only layer follows separately. This is an independent functional safety outcome rather than dead helpers or a partial advertised common validator. Root must measure each actual candidate including setup, wiring, documentation and mirrors separately and choose topology; the current 1214 helper/table/fixture-region subtotal is not a complete first-delivery diff and no approved prior source PR is rewritten.

Execution on October 12, 2026 after PKG-D1/PKG-D2 correction: the self-contained driver executed through python -I -B - and exited 0, printing:

```text
Guarded inline/reference titles and soft-break controls (LF/CRLF/CR): PASS
Label boundary, document references and nested image controls: PASS
Opaque multiline inline boundary family and soft-break controls (LF/CRLF/CR): PASS
Inline HTML token precedence and comment-boundary fixtures: PASS
Raw HTML, paragraph definition and tag-label neighbors: PASS
Active Markdown context, code-span label and Unicode device neighbors: PASS
PKG-D1 structured references and PKG-D2 portable paths: PASS
Synthetic fixtures: PASS
Actual Core read-only packages: PASS
Snapshot guard and optional declaration fixtures: PASS
All proposed Python blocks parse in their intended context: PASS
Current Kit in-memory generated package: PASS
core: package structure valid
Proposed packages-only caller against actual Core: PASS
```

The exact Template 1.4.0 overlay was also executed through python -I -B - and exited 0. It reads the frozen producer object and checks source-byte equality before evaluating the proposed shared helpers in memory. It makes no production or Git configuration changes.

```python
from pathlib import Path
import re, subprocess, types

reference = Path("plans/template-structure/PACKAGE_STRUCTURE.md")
blocks = re.findall(r"```python\n(.*?)\n```", reference.read_text(encoding="utf-8"), re.S)
publication = Path(r"C:/Users/TommySeery/source/repos/tj-agents/kit/.worktrees/Refactor-TemplatePublication")
git = ["git", "-c", "safe.directory=" + publication.as_posix()]
commit = subprocess.check_output(git + ["rev-parse", "HEAD"], cwd=publication, text=True).strip()
assert commit == "d0b42f2382e477c48ee7d062005b1813d712bee6", commit
sourcepath = publication / ".agents/kit/utility/new-plugin/templates/repository/.agents/sync_generated.py.in"
sourcebytes = subprocess.check_output(
    git + ["show", commit + ":.agents/kit/utility/new-plugin/templates/repository/.agents/sync_generated.py.in"],
    cwd=publication,
)
assert sourcepath.read_bytes() == sourcebytes
module = types.ModuleType("publication_design_overlay")
module.__file__ = str(sourcepath)
exec(compile(sourcebytes, str(sourcepath), "exec"), module.__dict__)
assert module.KIT_VERSION == "1.4.0", module.KIT_VERSION
exec(compile(blocks[0], str(reference) + ":implementation", "exec"), module.__dict__)
helper = next(block for block in blocks if block.startswith("def harness_body("))
exec(compile(helper, str(reference) + ":harness", "exec"), module.__dict__)
output = module.build(publication)
module.validate_packages(output)
assert len(output) == 219, len(output)
print("Exact Template 1.4 overlay: PASS")
print("Publication HEAD: " + commit)
print("Generated files: " + str(len(output)))
print("Production source unchanged against exact HEAD: PASS")
```

Earlier attempts exited 1: the first exposed missing direct Core harness roots, which led to the accepted explicit-projection correction; two driver/fixture issues were then corrected before the final exit-0 run. The current correction initially exposed an outdated fixture expectation for the newly explicit paragraph-definition ambiguity rejection; its assertion was corrected. The first exact-object overlay stopped at Git dubious-ownership; the successful rerun used command-local safe.directory only. The multiline-family attempt initially had an invalid control expectation for an inactive link inside a real fence; the corrected control checks the active link after the closing fence. No success is attributed to those failed attempts.

Read-only baseline commands: git log -1 --format=%H; git branch --show-current; git status --short -- plugins .agents/plugins/marketplace.json .claude-plugin/marketplace.json. Core root was main at 1bb1c130b2d1762bce07b599bb0fbb7e311c6749; status reported no changed inspected generated paths and exited 0. Git warned that its global ignore file could not be read. No Core generation-freshness check, remote-baseline check or native host acceptance was run; this is a local shape example, not current published acceptance. The independent settings worktree was read-only context and was not mutated.

Only this design reference was written. Production implementation and permanent tests are not present yet. Parent review/readiness and the later serialized production writer remain required.


The corrected proposal is frozen for independent compatibility/security reassessment. This is design-driver evidence, not passing permanent production tests or native acceptance. The writer stops after recording the final artifact hash externally.
