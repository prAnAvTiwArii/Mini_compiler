# Token Reference

This document describes every token type produced by the lexer, the syntax it recognises, and its regex pattern. Tokens are divided into two categories: **block tokens** (produced by `Lexer.tokenize()`) and **inline tokens** (produced by `Lexer.tokenize_inline()`).

---

## Block Tokens

Block tokens are produced by scanning a Markdown document line-by-line. Each line is lstripped to get `stripped`, and `indent = len(line) - len(stripped)` is recorded. The stripped line is matched against the master `block_token_pattern` (named-group regex) to identify the token type.

### Master Block Pattern

The named groups are tested in order. The first matching group determines `match.lastgroup`:

```python
block_token_pattern = re.compile(
    r'(?P<thematic_break>^(?:\*[ \t]*){3,}$|^(?:_[ \t]*){3,}$|^(?:-[ \t]*){3,}$)|'
    r'(?P<bullet_list>^\s*[*+-]\s+)|'
    r'(?P<ordered_list>^\s*(\d{1,9})[.)]\s+)|'
    r'(?P<atx_heading>^#{1,6}(?:[ \t]+|$))|'
    r'(?P<code_fence>^`{3,}(?!.*`)|^~{3,})|'
    r'(?P<math_fence>^\$\$[ \t]*$)|'
    r'(?P<mermaid_fence>^:::[ \t]+mermaid[ \t]*$)|'
    r'(?P<details_fence>^:::[ \t]*details(?:[ \t]+(.*))?[ \t]*$)|'
    r'(?P<mermaid_close>^:::[ \t]*$)|'
    r'(?P<footnote_def>^\[\^([^\]]+)\]:[ \t]*(.*))|'
    r'(?P<def_list_marker>^:[ \t]+(.*))'
)
```

### Block Token Table

| Token Constant | Named Group | Regex (within named group) | Syntax Example | Meta Fields |
|---|---|---|---|---|
| `BLANK` | *(no match, blank check)* | `len(stripped) == 0` | *(empty line)* | `{}` |
| `PARAGRAPH` | *(fallthrough)* | *(no other pattern matched)* | `Hello world` | `{}` |
| `ATX_HEADING` | `atx_heading` | `^#{1,6}(?:[ \t]+\|$)` | `## Title {#id}` | `level`, `content`, `custom_id` |
| `THEMATIC_BREAK` | `thematic_break` | `^(?:\*[ \t]*){3,}$\|^(?:_[ \t]*){3,}$\|^(?:-[ \t]*){3,}$` | `---` or `***` | `{}` |
| `BLOCKQUOTE` | *(startswith check)* | `stripped.startswith('>')` | `> quoted text` | `content` |
| `BULLET_LIST` | `bullet_list` | `^\s*[*+-]\s+` | `- item` | `list_type='bullet'`, `content` |
| `ORDERED_LIST` | `ordered_list` | `^\s*(\d{1,9})[.)]\s+` | `1. item` | `list_type='ordered'`, `list_start`, `content` |
| `CODE_FENCE` | `code_fence` | ``^`{3,}(?!.*`)\|^~{3,}`` | ` ```python ` | `fence_char`, `fence_length`, `info`, `block_type` |
| `CODE_FENCE_END` | `code_fence` | same as CODE_FENCE (closing match) | ` ``` ` | `{}` |
| `MATH_FENCE` | `math_fence` | `^\$\$[ \t]*$` | `$$` | `{}` |
| `MATH_FENCE_END` | `math_fence` | same as MATH_FENCE (closing match) | `$$` | `{}` |
| `MERMAID_FENCE` | `mermaid_fence` | `^:::[ \t]+mermaid[ \t]*$` | `:::mermaid` | `{}` |
| `MERMAID_CLOSE` | `mermaid_close` | `^:::[ \t]*$` | `:::` | `{}` |
| `DETAILS_FENCE` | `details_fence` | `^:::[ \t]*details(?:[ \t]+(.*))?[ \t]*$` | `:::details My Title` | `title` |
| `FOOTNOTE_DEF` | `footnote_def` | `^\[\^([^\]]+)\]:[ \t]*(.*)` | `[^1]: footnote text` | `label`, `content` |
| `DEF_LIST_MARKER` | `def_list_marker` | `^:[ \t]+(.*)` | `: definition` | `content` |
| `TABLE_ROW` | *(pipe check)* | `stripped.startswith('\|') and stripped.endswith('\|')` (not separator) | `\| a \| b \|` | `cells` (list of strings) |
| `TABLE_SEP` | *(pipe check + sep regex)* | `^\|[ \t\-:\|]+\|[ \t]*$` | `\|---\|---\|` | `{}` |
| `HTML_BLOCK` | *(reHtmlBlockOpen list)* | See 7-pattern list below | `<div>`, `<!--` | `{}` (raw value used) |
| `RAW_CONTENT` | *(inside fence)* | Any line while `in_fence == True` | *(code / math body lines)* | `{}` (raw value used) |

### HTML Block Detection Patterns (`reHtmlBlockOpen`)

These 7 patterns are tested in order against `stripped`. The first match makes the line an `HTML_BLOCK`:

| # | Pattern | Matches |
|---|---|---|
| 1 | `^<(?:script\|pre\|textarea\|style)(?:\s\|>\|$)` | `<script>`, `<pre>`, `<textarea>`, `<style>` opening |
| 2 | `^<!--` | HTML comment open |
| 3 | `^<?` | Processing instruction |
| 4 | `^<![A-Za-z]` | DOCTYPE / markup declaration |
| 5 | `^<!\[CDATA\[` | CDATA section |
| 6 | `^</?{block-tag}(?:\s\|/?>)` | Any CommonMark block-level HTML tag |
| 7 | `^(?:<Tag\|</Tag\s*>)\s*$` | Stand-alone custom tag on its own line |

### ATX Heading Custom ID

After extracting the heading content, the lexer applies a secondary regex:

```python
re_heading_id = re.compile(r'\{#([^}]+)\}\s*$')
```

If matched, the ID value is placed in `meta['custom_id']` and removed from `meta['content']`.

---

## Inline Tokens

Inline tokens are produced by `Lexer.tokenize_inline(text)` using `inline_token_pattern.finditer(text)`. The pattern uses numbered capture groups (not named groups). The token type is determined by `Lexer._classify_inline(raw)`.

### Master Inline Pattern

```python
inline_token_pattern = re.compile(
    r'(&\[.*?\]\(.*?\))|'        # Audio: &[caption](url)
    r'(@\[.*?\]\(.*?\))|'        # Video: @[caption](url)
    r'(!\[.*?\]\(.*?\))|'        # Image: ![alt](url)
    r'(\[.*?\]\(.*?\))|'         # Link: [label](url)
    r'(\*\*.*?\*\*|__.*?__)|'    # Strong: **text** or __text__
    r'(\*.*?\*|_.*?_)|'          # Emph: *text* or _text_
    r'(==.*?==)|'                # Highlight: ==text==
    r'(\+\+.*?\+\+)|'            # Underline: ++text++
    r'(~~.*?~~)|'                # Strikethrough: ~~text~~
    r'(~.*?~)|'                  # Subscript: ~text~
    r'(\^.*?\^)|'                # Superscript: ^text^
    r'(`+.*?`+)|'                # Code blocks inline
    r'(\$.*?\$)|'                # Inline Math: $equation$
    r'(\[\^[^\]]+\])|'           # Footnote Ref: [^label]
    r'(:[a-zA-Z0-9_\-]+:)|'      # Emoji Shortcode: :emoji:
    r'^(\[[ xX]\]|\[ \])|'       # Task list checkboxes at start: [x] or [ ]
    r'(<[A-Za-z/].*?>)|'         # HTML inline tags
    r'(<email@domain>)|'         # Email Autolink
    r'(<scheme:path>)|'          # URL Autolink
    r'(&[#a-zA-Z0-9]+;)|'        # HTML Entity
    r'(  \n)|'                   # Hard line break
    r'(\\.)|'                    # Escaped char
    r'(\n)|'                     # Newlines
    r'([^!\[\]*_`<&\n\\=+\~^$: ]+)|'  # Plain Text
    r'([!\[\]*_`<&\n\\=+\~^$: ])'     # Single special char fallback
)
```

### Inline Token Table

| Token Constant | Regex / Classification | Syntax Example | `meta` Fields | Output |
|---|---|---|---|---|
| `IL_AUDIO` | Starts `&[`, contains `](`, ends `)` | `&[My sound](audio.mp3)` | `label`, `dest` | `<audio>` |
| `IL_VIDEO` | Starts `@[`, contains `](`, ends `)` | `@[My video](video.mp4)` | `label`, `dest` | `<video>` |
| `IL_IMAGE` | Starts `![`, contains `](`, ends `)` | `![alt text](img.png)` | `label`, `dest` | `<img>` |
| `IL_LINK` | Starts `[`, contains `](`, ends `)` | `[click here](https://x.com)` | `label`, `dest` | `<a>` |
| `IL_STRONG` | Starts+ends `**` or `__` | `**bold**`, `__bold__` | `text` | `<strong>` |
| `IL_EMPH` | Starts+ends `*` or `_` | `*italic*`, `_italic_` | `text` | `<em>` |
| `IL_MARK` | Starts+ends `==` | `==highlight==` | `text` | `<mark>` |
| `IL_UNDERLINE` | Starts+ends `++` | `++underline++` | `text` | `<u>` |
| `IL_DEL` | Starts+ends `~~` | `~~strikethrough~~` | `text` | `<s>` |
| `IL_SUB` | Starts+ends `~` | `~subscript~` | `text` | `<sub>` |
| `IL_SUP` | Starts+ends `^` | `^superscript^` | `text` | `<sup>` |
| `IL_CODE` | Starts+ends `` ` `` (one or more) | `` `code` ``, ` `` code `` ` | `text` (backtick-stripped, trimmed) | `<code>` |
| `IL_MATH` | Starts+ends `$` | `$E=mc^2$` | `text` | `<span class="math math-inline">` |
| `IL_FOOTNOTE_REF` | Starts `[^`, ends `]` | `[^1]` | `label` | `<sup><a href="#fn:label">` |
| `IL_EMOJI` | Starts+ends `:` | `:smile:` | `{}` (value used) | escaped literal |
| `IL_TASK` | Value in `{'[ ]','[x]','[X]'}` | `[x]` | `checked` (bool) | `<input type="checkbox">` |
| `IL_EMAIL_LINK` | `<…>` with `@` in inner, no spaces | `<user@example.com>` | `dest` | `<a href="mailto:…">` |
| `IL_URI_LINK` | `<…>` with `:` in inner, no spaces | `<https://example.com>` | `dest` | `<a href="…">` |
| `IL_HTML` | Starts `<`, ends `>` (not email/uri) | `<span class="x">` | `{}` (value used) | raw HTML passed through |
| `IL_ENTITY` | Starts `&`, ends `;` | `&amp;`, `&#42;`, `&#x2A;` | `{}` (value HTML-unescaped) | unescaped character |
| `IL_HARDBREAK` | Exactly `'  \n'` (2 spaces + newline) | `text  ↵` | `{}` | `<br />` |
| `IL_SOFTBREAK` | Exactly `'\n'` | newline in inline text | `{}` | `<br />` |
| `IL_ESCAPED` | Starts `\`, length == 2 | `\*`, `\_` | `char` | literal character |
| `IL_TEXT` | Everything else (fallthrough) | `Hello world` | `{}` (value used) | HTML-escaped text |

---

## Classification Priority

The `_classify_inline` function tests conditions in strict top-to-bottom order. This means `&[` is tested before `![` before `[`, and `**` before `*`, ensuring longer/more-specific patterns win over shorter ones.

The inline regex pattern itself enforces the same priority through alternation order: the first capturing group that matches wins.
