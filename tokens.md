# Token Reference

All tokens are defined in `regex_rules.py`. The `Token` class is also defined there and imported by `lexer.py` and `parser.py`.

---

## Token Class

```python
class Token:
    __slots__ = ("type", "value", "meta", "indent")

    def __init__(self, type_: str, value: str, meta: dict | None = None, indent: int = 0):
        self.type   = type_    # one of the string constants below
        self.value  = value    # raw text of the matched line or span
        self.meta   = meta or {}  # structured metadata extracted from the match
        self.indent = indent   # number of leading spaces on the original line
```

---

## Block Token Constants

Produced by the `Lexer.tokenize()` (Phase 1) from a full Markdown line.

| Constant | Value | Description |
|---|---|---|
| `BLANK` | `"BLANK"` | Empty or whitespace-only line |
| `PARAGRAPH` | `"PARAGRAPH"` | Plain text line (catch-all) |
| `ATX_HEADING` | `"ATX_HEADING"` | `# Heading` (levels 1–6) |
| `THEMATIC_BREAK` | `"THEMATIC_BREAK"` | `---`, `***`, or `___` |
| `BLOCKQUOTE` | `"BLOCKQUOTE"` | Line starting with `>` |
| `BULLET_LIST` | `"BULLET_LIST"` | Line starting with `*`, `+`, or `-` |
| `ORDERED_LIST` | `"ORDERED_LIST"` | Line starting with `1.` / `1)` etc. |
| `CODE_FENCE` | `"CODE_FENCE"` | Opening `` ``` `` or `~~~` fence |
| `CODE_FENCE_END` | `"CODE_FENCE_END"` | Closing fence matching opener |
| `MATH_FENCE` | `"MATH_FENCE"` | Opening `$$` on its own line |
| `MATH_FENCE_END` | `"MATH_FENCE_END"` | Closing `$$` on its own line |
| `MERMAID_FENCE` | `"MERMAID_FENCE"` | Opening `:::mermaid` |
| `MERMAID_CLOSE` | `"MERMAID_CLOSE"` | Closing `:::` |
| `FOOTNOTE_DEF` | `"FOOTNOTE_DEF"` | `[^label]: text` |
| `DEF_LIST_MARKER` | `"DEF_LIST_MARKER"` | `: definition text` |
| `TABLE_ROW` | `"TABLE_ROW"` | `| cell | cell |` |
| `TABLE_SEP` | `"TABLE_SEP"` | `| --- | --- |` |
| `HTML_BLOCK` | `"HTML_BLOCK"` | Raw HTML opening tag block |
| `RAW_CONTENT` | `"RAW_CONTENT"` | Content line inside any fenced block |

---

## Inline Token Constants

Produced by `Lexer.tokenize_inline()` (Phase 2) from a single text span.

| Constant | Value | Syntax | Example |
|---|---|---|---|
| `IL_IMAGE` | `"IL_IMAGE"` | `![alt](url)` | `![logo](img.png)` |
| `IL_LINK` | `"IL_LINK"` | `[label](url)` | `[click](https://...)` |
| `IL_STRONG` | `"IL_STRONG"` | `**text**` or `__text__` | `**bold**` |
| `IL_EMPH` | `"IL_EMPH"` | `*text*` or `_text_` | `*italic*` |
| `IL_MARK` | `"IL_MARK"` | `==text==` | `==highlight==` |
| `IL_UNDERLINE` | `"IL_UNDERLINE"` | `++text++` | `++underline++` |
| `IL_DEL` | `"IL_DEL"` | `~~text~~` | `~~strike~~` |
| `IL_SUB` | `"IL_SUB"` | `~text~` | `H~2~O` |
| `IL_SUP` | `"IL_SUP"` | `^text^` | `x^2^` |
| `IL_CODE` | `"IL_CODE"` | `` `code` `` | `` `print()` `` |
| `IL_MATH` | `"IL_MATH"` | `$equation$` | `$E=mc^2$` |
| `IL_FOOTNOTE_REF` | `"IL_FOOTNOTE_REF"` | `[^label]` | `[^1]` |
| `IL_EMOJI` | `"IL_EMOJI"` | `:name:` | `:smile:` |
| `IL_TASK` | `"IL_TASK"` | `[ ]` or `[x]` or `[X]` | `[x]` |
| `IL_HTML` | `"IL_HTML"` | `<tag>` or `</tag>` | `<br>` |
| `IL_EMAIL_LINK` | `"IL_EMAIL_LINK"` | `<user@host>` | `<me@example.com>` |
| `IL_URI_LINK` | `"IL_URI_LINK"` | `<scheme:...>` | `<https://x.com>` |
| `IL_ENTITY` | `"IL_ENTITY"` | `&name;` or `&#N;` | `&amp;` |
| `IL_HARDBREAK` | `"IL_HARDBREAK"` | Two spaces then `\n` | `  \n` |
| `IL_SOFTBREAK` | `"IL_SOFTBREAK"` | Single `\n` | `\n` |
| `IL_ESCAPED` | `"IL_ESCAPED"` | `\X` (any char) | `\*` |
| `IL_TEXT` | `"IL_TEXT"` | Any plain text | `hello` |

---

## Regex Patterns

### `block_token_pattern`

A single compiled regex with named groups. The `Lexer` calls `.match(stripped_line)` and reads `lastgroup` to identify the token type.

| Named Group | Pattern | Matches |
|---|---|---|
| `thematic_break` | `(?:\*[ \t]*){3,}` \| `(?:_[ \t]*){3,}` \| `(?:-[ \t]*){3,}` | `---`, `***`, `___` |
| `bullet_list` | `^\s*[*+-]\s+` | `- item`, `* item` |
| `ordered_list` | `^\s*(\d{1,9})[.)]\s+` | `1. item`, `2) item` |
| `atx_heading` | `^#{1,6}(?:[ \t]+\|$)` | `## Heading` |
| `code_fence` | `^`{3,}(?!.*`)` \| `^~{3,}` | ```` ``` ```` , `~~~` |
| `math_fence` | `^\$\$[ \t]*$` | `$$` alone on a line |
| `mermaid_fence` | `^:::[ \t]+mermaid[ \t]*$` | `:::mermaid` |
| `mermaid_close` | `^:::[ \t]*$` | `:::` alone |
| `footnote_def` | `^\[\^([^\]]+)\]:[ \t]*(.*)` | `[^1]: text` |
| `def_list_marker` | `^:[ \t]+(.*)` | `: definition` |

### `inline_token_pattern`

A single compiled regex with alternation groups (no named groups — order determines priority).

| Priority | Pattern | Token assigned by |
|---|---|---|
| 1 | `!\[.*?\]\(.*?\)` | `IL_IMAGE` |
| 2 | `\[.*?\]\(.*?\)` | `IL_LINK` |
| 3 | `\*\*.*?\*\*` \| `__.*?__` | `IL_STRONG` |
| 4 | `\*.*?\*` \| `_.*?_` | `IL_EMPH` |
| 5 | `==.*?==` | `IL_MARK` |
| 6 | `\+\+.*?\+\+` | `IL_UNDERLINE` |
| 7 | `~~.*?~~` | `IL_DEL` |
| 8 | `~.*?~` | `IL_SUB` |
| 9 | `\^.*?\^` | `IL_SUP` |
| 10 | `` `+.*?`+ `` | `IL_CODE` |
| 11 | `\$.*?\$` | `IL_MATH` |
| 12 | `\[\^[^\]]+\]` | `IL_FOOTNOTE_REF` |
| 13 | `:[a-zA-Z0-9_\-]+:` | `IL_EMOJI` |
| 14 | `^(\[[ xX]\]\|\\[ \])` | `IL_TASK` |
| 15 | `<[A-Za-z/].*?>` | `IL_HTML` / `IL_EMAIL_LINK` / `IL_URI_LINK` |
| 16 | `&[#a-zA-Z0-9]+;` | `IL_ENTITY` |
| 17 | `  \n` | `IL_HARDBREAK` |
| 18 | `\\.` | `IL_ESCAPED` |
| 19 | `\n` | `IL_SOFTBREAK` |
| 20 | plain text run | `IL_TEXT` |
| 21 | single special char | `IL_TEXT` (fallback) |

### Miscellaneous Regexes

| Name | Pattern | Used for |
|---|---|---|
| `re_heading_id` | `\{#([^}]+)\}\s*$` | Extract `{#custom-id}` from heading text |
| `re_line_ending` | `\r\n\|\n\|\r` | Split raw text into lines |
| `re_table_sep` | `^\|[ \t\-:\|]+\|[ \t]*$` | Detect `\|---\|---\|` separator rows |
| `re_footnote` | `^\[\^([^\]]+)\]:[ \t]*(.*)` | Extract footnote label + content |
| `re_deflist` | `^:[ \t]+(.*)` | Extract definition list content |
| `re_ol_num` | `\d+` | Extract start number from ordered list marker |

### HTML Block Open Patterns (`reHtmlBlockOpen`)

A list of compiled regexes tested against the stripped line. First match wins.

| # | Pattern | Matches |
|---|---|---|
| 1 | `^<(?:script\|pre\|textarea\|style)(?:\s\|>\|$)` | Raw HTML containers |
| 2 | `^<!--` | HTML comment |
| 3 | `^<?` | Processing instruction |
| 4 | `^<![A-Za-z]` | DOCTYPE |
| 5 | `^<!\[CDATA\[` | CDATA section |
| 6 | `^</?block-tag(?:\s\|/?>\|$)` | All standard block-level HTML tags |
| 7 | `^(?:<Tag\|</Tag\s*>)\s*$` | Standalone open/close custom tags |

---

## Other Constants

| Name | Value | Purpose |
|---|---|---|
| `CODE_INDENT` | `4` | Minimum indent for an indented code block (reserved, not yet used) |
