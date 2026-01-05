import json
import re

import sublime
import sublime_plugin


def _strip_json_comments(src):
    """
    Strip // and /* */ style comments from JSON-with-comments content.

    - Preserves all non-comment characters, including whitespace.
    - Correctly handles comment-like sequences inside strings.

    This is intentionally small and self-contained so the package
    can be distributed on Package Control without extra dependencies.
    """
    out_chars = []

    in_string = False
    string_delim = ""
    escape = False
    in_line_comment = False
    in_block_comment = False
    i = 0
    length = len(src)

    while i < length:
        ch = src[i]
        nxt = src[i + 1] if i + 1 < length else ""

        if in_line_comment:
            # Consume until end of line, but keep the newline itself
            if ch in ("\n", "\r"):
                in_line_comment = False
                out_chars.append(ch)
            # else: skip comment text
            i += 1
            continue

        if in_block_comment:
            # Consume until closing */
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue

        # Not currently in a comment
        if in_string:
            out_chars.append(ch)
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == string_delim:
                in_string = False
            i += 1
            continue

        # Not in string, not in comment: look for start of comment or string
        if ch in ("'", '"'):
            in_string = True
            string_delim = ch
            out_chars.append(ch)
            i += 1
            continue

        if ch == "/" and nxt == "/":
            in_line_comment = True
            i += 2
            continue

        if ch == "/" and nxt == "*":
            in_block_comment = True
            i += 2
            continue

        # Regular character
        out_chars.append(ch)
        i += 1

    return "".join(out_chars)


class _Token(object):
    __slots__ = ("kind", "value")

    def __init__(self, kind, value):
        self.kind = kind  # "string" | "literal" | "punct" | "comment" | "ws"
        self.value = value


def _tokenize_json_with_comments(src):
    """
    Tokenize JSON-with-comments text.

    This is a *syntactic* tokenizer:
    - Strings are kept intact (including quotes and escapes).
    - Comments (// and /* */) are separate tokens.
    - Structural punctuation: { } [ ] : ,
    - Whitespace is grouped but usually ignored by the formatter.
    - Everything else is treated as a generic "literal" token.
    """
    # NOTE: Avoid type hints / annotations for Sublime Text 3 (Python 3.3) compatibility.
    tokens = []  # type: list[_Token]
    i = 0
    length = len(src)

    while i < length:
        ch = src[i]
        nxt = src[i + 1] if i + 1 < length else ""

        # Whitespace
        if ch.isspace():
            start = i
            i += 1
            while i < length and src[i].isspace():
                i += 1
            tokens.append(_Token("ws", src[start:i]))
            continue

        # String
        if ch in ("'", '"'):
            delim = ch
            start = i
            i += 1
            escape = False
            while i < length:
                c = src[i]
                if escape:
                    escape = False
                elif c == "\\":
                    escape = True
                elif c == delim:
                    i += 1
                    break
                i += 1
            tokens.append(_Token("string", src[start:i]))
            continue

        # Comments
        if ch == "/" and nxt == "/":
            start = i
            i += 2
            while i < length and src[i] not in ("\n", "\r"):
                i += 1
            tokens.append(_Token("comment", src[start:i]))
            continue

        if ch == "/" and nxt == "*":
            start = i
            i += 2
            while i < length - 1 and not (src[i] == "*" and src[i + 1] == "/"):
                i += 1
            if i < length - 1:
                i += 2  # include closing */
            tokens.append(_Token("comment", src[start:i]))
            continue

        # Structural punctuation
        if ch in "{}[]:,":
            tokens.append(_Token("punct", ch))
            i += 1
            continue

        # Literal (numbers, true/false/null, identifiers, etc.)
        start = i
        i += 1
        while i < length:
            c = src[i]
            c_next = src[i + 1] if i + 1 < length else ""
            if c.isspace():
                break
            if c in "{}[]:,":
                break
            if c == "/" and c_next in ("/", "*"):
                break
            if c in ("'", '"'):
                break
            i += 1
        tokens.append(_Token("literal", src[start:i]))

    return tokens


def _pretty_print_tokens_with_comments(tokens, newline_at_end):
    """
    Pretty-print token stream while preserving comments and strings.

    This is a structure-aware re-indenter; it does not attempt to change
    the order of tokens, only whitespace around them.
    """
    # NOTE: Avoid variable annotations for Sublime Text 3 (Python 3.3) compatibility.
    pieces = []  # type: list[str]
    indent = 0
    indent_step = 4

    def last_non_space_char():
        for part in reversed(pieces):
            for c in reversed(part):
                if not c.isspace():
                    return c
        return ""

    def write(text):
        pieces.append(text)

    def write_newline_and_indent():
        write("\n")
        write(" " * (indent * indent_step))

    def strip_trailing_whitespace():
        """Remove trailing whitespace (spaces/newlines) from pieces.

        This is mainly used to pull up a trailing // comment onto the
        previous value line, instead of leaving a blank line between.
        """
        while pieces:
            part = pieces[-1]
            # Find last non-space char in this piece
            i = len(part) - 1
            while i >= 0 and part[i].isspace():
                i -= 1

            if i == -1:
                # Entire piece is whitespace, drop it
                pieces.pop()
                continue

            if i == len(part) - 1:
                # No trailing whitespace here, nothing more to trim
                return

            # Trim trailing whitespace in this piece
            pieces[-1] = part[: i + 1]
            return

    def at_line_start():
        """Return True if we are at the start of a logical line (after newline + indent)."""
        saw_any = False
        for part in reversed(pieces):
            for c in reversed(part):
                saw_any = True
                if c == "\n":
                    # Found a newline before any non-space: we are at line start.
                    return True
                if not c.isspace():
                    # Non-space before a newline: not at line start.
                    return False
        # No content at all yet -> start of file == start of line
        return not saw_any

    for tok in tokens:
        kind = tok.kind
        val = tok.value

        if kind == "ws":
            # Ignore original whitespace; we fully control layout.
            continue

        if kind == "comment":
            prev_char = last_non_space_char()
            is_line_comment = val.lstrip().startswith("//")
            has_newline = ("\n" in val) or ("\r" in val)

            # 优先把简单的 // 注释放在字段同一行的末尾
            if (
                is_line_comment
                and not has_newline
                and prev_char not in ("", "\n")
            ):
                # 注释紧跟在前一个值/字段后面：去掉我们可能刚刚插入的换行+缩进
                strip_trailing_whitespace()
                # 保证前后有一个空格
                write(" ")
                write(val.strip())
                # 换行并缩进，为下一行的 key 做准备
                write_newline_and_indent()
            else:
                # 其他情况（独立行注释、多行块注释等）仍然单独成行
                if not pieces or prev_char != "\n":
                    write_newline_and_indent()

                # For block comments that span multiple lines, indent each line.
                lines = val.splitlines(True)  # keepends
                for idx, line in enumerate(lines):
                    if idx > 0:
                        write(" " * (indent * indent_step))
                    write(line)
                # Ensure we end on a newline for consistency
                if not (lines and lines[-1].endswith(("\n", "\r"))):
                    write("\n")
            continue

        if kind == "punct":
            ch = val
            if ch in "{[":
                # Opening brace/bracket
                prev = last_non_space_char()
                if prev == ":":
                    write(" ")
                write(ch)
                indent += 1
                write_newline_and_indent()
            elif ch in "}]":
                # Closing brace/bracket
                indent = max(indent - 1, 0)
                # If last non-space is an opening brace on same line, keep it compact: {} or []
                prev = last_non_space_char()
                if prev in "{[":
                    write(ch)
                else:
                    write_newline_and_indent()
                    write(ch)
            elif ch == ",":
                write(",")
                write_newline_and_indent()
            elif ch == ":":
                write(": ")
            continue

        # Strings and literals
        if kind in ("string", "literal"):
            # 如果不在行首，再考虑是否需要在前面补一个空格
            if not at_line_start():
                prev = last_non_space_char()
                if prev and prev not in "{[:,":  # add space between adjacent values
                    write(" ")
            write(val)
            continue

        # Fallback: just emit value as-is
        write(val)

    result = "".join(pieces)
    # Trim trailing whitespace lines
    result = result.rstrip()
    if newline_at_end:
        result += "\n"
    return result


def _iter_target_regions(view):
    """Yield the regions the command should operate on.

    - If there is a non-empty selection, operate on each selection.
    - Otherwise, operate on the entire buffer.
    """
    non_empty = [r for r in view.sel() if not r.empty()]
    if non_empty:
        return non_empty
    return [sublime.Region(0, view.size())]


def _format_json_with_comments(raw):
    """
    Take JSON-with-comments text and return (formatted_text, error_info).

    - First, validate the underlying JSON by stripping comments and parsing.
    - Then, pretty-print based on a token stream that preserves comments.
    - If error_info is not None, formatted_text will be the original text.
    - error_info is a dict with keys: 'message', 'lineno', 'colno', 'pos'
    """
    cleaned = _strip_json_comments(raw)
    try:
        data = json.loads(cleaned)
    except ValueError as exc:
        # Python 3.3 uses ValueError for JSON errors, not JSONDecodeError
        # Parse error message to extract line/column info
        # Format: "Expecting property name...: line X column Y (char Z)"
        error_msg = str(exc)
        error_info = {
            'message': error_msg,
            'lineno': None,
            'colno': None,
            'pos': None
        }
        
        # Try to parse line and column from error message
        # Pattern: "line X column Y (char Z)" or "line X column Y"
        match = re.search(r'line\s+(\d+)\s+column\s+(\d+)', error_msg, re.IGNORECASE)
        if match:
            error_info['lineno'] = int(match.group(1))
            error_info['colno'] = int(match.group(2))
        
        # Try to parse char position
        match = re.search(r'\(char\s+(\d+)\)', error_msg, re.IGNORECASE)
        if match:
            error_info['pos'] = int(match.group(1))
        
        return raw, error_info
    except Exception as exc:
        # For other exceptions, provide basic error info
        error_info = {
            'message': str(exc),
            'lineno': None,
            'colno': None,
            'pos': None
        }
        return raw, error_info

    # Parsing succeeded; now pretty-print while keeping comments.
    tokens = _tokenize_json_with_comments(raw)
    pretty = _pretty_print_tokens_with_comments(tokens, newline_at_end=raw.endswith("\n"))
    return pretty, None


class JsonWithCommentsPrettyCommand(sublime_plugin.TextCommand):
    """
    Pretty-format JSON that may contain comments.

    - Supports // line comments and /* */ block comments.
    - Works on the current selection(s) or the entire file if nothing is selected.
    - Uses Python's json module after stripping comments.
    """

    def run(self, edit):
        view = self.view
        error_infos = []
        
        # Clear any previous error phantoms and status
        view.erase_phantoms("json_with_comments_error")
        view.erase_status("json_with_comments_error")

        for region in list(_iter_target_regions(view)):
            original = view.substr(region)
            formatted, error_info = _format_json_with_comments(original)

            if error_info:
                # Calculate the actual position in the original text
                # The error position is in the cleaned (comment-stripped) text,
                # so we need to map it back to the original text
                error_info['region'] = region
                error_infos.append(error_info)
                continue

            if formatted != original:
                view.replace(edit, region, formatted)

        if error_infos:
            # Show error for the first error found
            error_info = error_infos[0]
            region = error_info['region']
            original = view.substr(region)
            
            # Build error message with line/column info (like Pretty JSON)
            error_msg_parts = []
            if error_info['lineno'] is not None and error_info['colno'] is not None:
                # JSONDecodeError uses 1-based line numbers
                line_num = error_info['lineno']
                col_num = error_info['colno']
                
                # Map from cleaned text position to original text position
                # We'll use a simple approximation: find the line in original text
                # that corresponds to the error line in cleaned text
                cleaned = _strip_json_comments(original)
                cleaned_lines = cleaned.splitlines(True)
                original_lines = original.splitlines(True)
                
                # Calculate approximate original line number
                # This is an approximation - exact mapping would require character-by-character tracking
                original_line_num = line_num
                if line_num <= len(cleaned_lines):
                    # Try to find matching line in original (simple heuristic)
                    # Count non-comment lines up to error line
                    comment_line_count = 0
                    for i, orig_line in enumerate(original_lines[:line_num]):
                        stripped = orig_line.strip()
                        if stripped.startswith("//") or "/*" in stripped:
                            comment_line_count += 1
                    original_line_num = line_num + comment_line_count
                    if original_line_num > len(original_lines):
                        original_line_num = line_num
                
                # Format error message like Pretty JSON: "Expecting property name...: line X column Y"
                error_msg = error_info['message']
                if "Expecting" in error_msg or "Invalid" in error_msg or "Unterminated" in error_msg:
                    # Extract the main error description
                    if ":" in error_msg:
                        main_msg = error_msg.split(":")[0]
                    else:
                        main_msg = error_msg
                    error_msg_parts.append("{}: line {} column {} (char {})".format(
                        main_msg, original_line_num, col_num, error_info.get('pos', '?')
                    ))
                else:
                    error_msg_parts.append("Line {} column {}: {}".format(
                        original_line_num, col_num, error_msg
                    ))
            elif error_info['lineno'] is not None:
                error_msg_parts.append("Line {}: {}".format(error_info['lineno'], error_info['message']))
            else:
                error_msg_parts.append(error_info['message'])
            
            error_message = "\n".join(error_msg_parts)
            
            # Clear any previous error phantoms
            view.erase_phantoms("json_with_comments_error")
            
            # Show in status bar (bottom left)
            status_msg = "JSON Error: line {} column {}".format(
                error_info.get('lineno', '?'), error_info.get('colno', '?')
            )
            view.set_status("json_with_comments_error", status_msg)
            
            # Try to locate and highlight the error line in the view
            error_phantom_pos = None
            error_col = None
            if error_info['lineno'] is not None:
                line_num = error_info['lineno'] - 1  # Convert to 0-based
                region_start = region.begin()
                
                # Get the line region in the view
                try:
                    # Get the row of the region start
                    start_row, start_col = view.rowcol(region_start)
                    target_row = start_row + line_num
                    
                    # Calculate line start position in the view
                    line_start = view.text_point(target_row, 0)
                    if line_start < view.size():
                        line_region = view.line(line_start)
                        # Select and scroll to the error line
                        view.sel().clear()
                        view.sel().add(line_region)
                        view.show(line_region, True)  # True = center the view
                        
                        # Use the end of the line for phantom position
                        error_phantom_pos = line_region.end()
                        
                        # Calculate error column position for arrow alignment
                        if error_info['colno'] is not None:
                            error_col = error_info['colno'] - 1  # Convert to 0-based
                except:
                    # If line calculation fails, use region end
                    error_phantom_pos = region.end()
                    view.sel().clear()
                    view.sel().add(region)
                    view.show(region)
            
            # Show error using phantom (inline error display, like lint plugins)
            if error_phantom_pos is not None:
                # Calculate arrow offset based on error column
                # Approximate: each character is about 0.5rem wide, but this is approximate
                arrow_offset = "1rem"  # Default offset
                if error_col is not None:
                    # Estimate column position (rough approximation)
                    arrow_offset = "{}rem".format(max(0.5, error_col * 0.5))
                
                # Create HTML content for the error phantom
                # Style similar to screenshot: red background box with white text, arrow pointing upward to error
                phantom_html = """
                <body id="json-with-comments-error">
                    <style>
                        div.error-wrapper {{
                            position: relative;
                            margin: 0.2rem 0;
                        }}
                        div.error {{
                            padding: 0.4rem 0.6rem;
                            border-radius: 0.25rem;
                            background-color: color(var(--redish) alpha(0.15));
                            border: 0.05rem solid color(var(--redish) alpha(0.4));
                            position: relative;
                            margin-top: 0.5rem;
                        }}
                        div.error::before {{
                            content: '';
                            position: absolute;
                            top: -0.5rem;
                            left: {};
                            width: 0;
                            height: 0;
                            border-left: 0.5rem solid transparent;
                            border-right: 0.5rem solid transparent;
                            border-bottom: 0.5rem solid color(var(--redish) alpha(0.15));
                            transform: translateX(-50%);
                            z-index: 1;
                        }}
                        div.error::after {{
                            content: '';
                            position: absolute;
                            top: -0.55rem;
                            left: {};
                            width: 0;
                            height: 0;
                            border-left: 0.5rem solid transparent;
                            border-right: 0.5rem solid transparent;
                            border-bottom: 0.5rem solid color(var(--redish) alpha(0.4));
                            transform: translateX(-50%);
                            z-index: 0;
                        }}
                        div.error-content {{
                            font-family: system;
                            font-size: 0.9rem;
                            color: color(var(--foreground) alpha(0.95));
                            line-height: 1.4;
                        }}
                    </style>
                    <div class="error-wrapper">
                        <div class="error">
                            <div class="error-content">{}</div>
                        </div>
                    </div>
                </body>
                """.format(
                    arrow_offset,
                    arrow_offset,
                    error_message.replace('<', '&lt;').replace('>', '&gt;').replace('&', '&amp;')
                )
                
                view.add_phantom(
                    "json_with_comments_error",
                    sublime.Region(error_phantom_pos, error_phantom_pos),
                    phantom_html,
                    sublime.LAYOUT_BLOCK
                )
            
            # Clear status after 8 seconds
            def clear_status():
                view.erase_status("json_with_comments_error")
            sublime.set_timeout(clear_status, 8000)


def plugin_loaded():
    # Called by Sublime Text when the plugin is loaded.
    pass


def plugin_unloaded():
    # Called by Sublime Text when the plugin is about to be unloaded.
    pass


