# LLM Context — Mini_Compiler Markdown-to-HTML Compiler

This document is a complete, self-contained description of the Mini_Compiler project. Reading this file alone is sufficient to understand every design decision, data flow, data structure, and extension point in the codebase.

---

## 1. What the Project Does

Mini_Compiler is a single-pass, hand-written Markdown-to-HTML compiler that ships with a highly interactive **Web UI Visualizer**. It takes a Markdown file as input and produces:

1. A full HTML page rendered on the frontend.
2. A JSON payload containing the intermediate Abstract Syntax Tree (AST), deep analytics, and lexer token arrays.

The compiler supports standard CommonMark-style Markdown plus many extended features: tables, footnotes, definition lists, fenced math blocks ($$), Mermaid diagrams (:::mermaid), details/summary blocks (:::details), task checkboxes, custom heading IDs, inline math ($…$), subscript/superscript, highlight, underline, video embeds (@[…](…)), and audio embeds (&[…](…)).

---

## 2. File-by-File Description

### `lex_token.py`

**Purpose:** Central definitions file. Everything the lexer needs is here.

**Contents:**

- **`Token` class** — a lightweight dataclass using `__slots__` for memory efficiency.
  - `type: str` — one of the constant strings defined in this file.
  - `value: str` — the raw matched text from the source.
  - `meta: dict` — structured data extracted from the match (e.g., `{'level': 2, 'content': 'Hello'}`).
  - `indent: int` — leading-space count of the source line (used for list nesting).

- **Block token constants** (20 constants) — uppercase strings like `PARAGRAPH`, `ATX_HEADING`, `CODE_FENCE`, etc.

- **Inline token constants** (24 constants) — prefixed with `IL_`, e.g., `IL_STRONG`, `IL_LINK`, `IL_MATH`.

- **`block_token_pattern`** — a single compiled regex with named groups. Each group name maps to a block token type. The lexer matches each stripped line against this pattern and reads `match.lastgroup` to identify the token type.

- **`inline_token_pattern`** — a compiled regex with many capture groups, used with `finditer()` to split an inline string into a flat sequence of inline tokens.

- **Helper regexes** — `re_heading_id` (extracts `{#id}` from headings), `re_line_ending`, `re_table_sep`, `re_footnote`, `re_deflist`, `re_ol_num`.

- **`reHtmlBlockOpen`** — a list of 7 compiled regexes that detect the opening of a block-level HTML element, matching the CommonMark spec.

---

### `lexer.py`

**Purpose:** Converts raw Markdown text into a flat list of `Token` objects. Contains both block-level and inline-level tokenisation in a single `Lexer` class.

**`Lexer.tokenize(text: str) -> list[Token]`** — Block tokeniser.

Algorithm:
1. Split text on line endings (`\r\n`, `\n`, `\r`). If the text ends with `\n`, remove the trailing empty element.
2. Iterate line by line. For each line compute `stripped` (lstrip), `indent` (len diff), `blank` (stripped is empty).
3. Match `stripped` against `block_token_pattern` to get a named group (`bg = match.lastgroup`).
4. **Fence state machine:** A boolean `in_fence` flag plus `fence_block_type`, `fence_char`, `fence_length` track open fenced blocks. While inside a fence, lines are emitted as `RAW_CONTENT` tokens until the matching closing fence is found.
5. For each non-fence line, one of the following tokens is emitted (checked in priority order):
   - `BLANK` for empty lines.
   - `BLOCKQUOTE` for lines starting with `>`.
   - `ATX_HEADING` — extracts level (number of `#`), content (stripped, trailing `#` removed), and optional `{#id}` custom anchor.
   - `THEMATIC_BREAK` — `---`, `***`, `___` variants.
   - `FOOTNOTE_DEF` — `[^label]: content`.
   - `DEF_LIST_MARKER` — `: definition`.
   - `CODE_FENCE` — opening backtick or tilde fence; sets fence state.
   - `MATH_FENCE` — opening `$$`; sets fence state.
   - `MERMAID_FENCE` — opening `:::mermaid`; sets fence state.
   - `DETAILS_FENCE` — opening `:::details Title`; sets fence state.
   - `BULLET_LIST` — `- / * / +` list items; meta includes `list_type='bullet'` and `content`.
   - `ORDERED_LIST` — `1. / 1)` items; meta includes `list_type='ordered'`, `list_start`, and `content`.
   - `TABLE_SEP` / `TABLE_ROW` — lines starting and ending with `|`.
   - `HTML_BLOCK` — lines matching any of the 7 `reHtmlBlockOpen` patterns.
   - `PARAGRAPH` — everything else.

**`Lexer.tokenize_inline(text: str) -> list[Token]`** — Inline tokeniser.

Uses `inline_token_pattern.finditer(text)`. For each match:
1. Calls `_classify_inline(raw)` — a chain of `startswith`/`endswith` checks to determine the token type.
2. Calls `_inline_meta(type_, raw)` — a dispatch dict mapping token types to static extractor methods that return structured `meta` dicts.

**Inline meta extractors:**

| Method | Token types | Extracted fields |
|---|---|---|
| `_meta_media` | AUDIO, VIDEO, IMAGE | `label`, `dest` |
| `_meta_link` | LINK | `label`, `dest` |
| `_meta_strip_strong` | STRONG, MARK, UNDERLINE, DEL | `text` (content without 2-char delimiters) |
| `_meta_strip_emph` | EMPH, SUB, SUP, MATH | `text` (content without 1-char delimiters) |
| `_meta_code` | CODE | `text` (content stripped of leading/trailing backtick runs) |
| `_meta_footnote_ref` | FOOTNOTE_REF | `label` |
| `_meta_autolink` | EMAIL_LINK, URI_LINK | `dest` |
| `_meta_task` | TASK | `checked` (bool) |
| `_meta_escaped` | ESCAPED | `char` |

---

### `node.py`

**Purpose:** Defines the `Node` class — the fundamental data structure of the AST.

A `Node` is a node in an n-ary tree, implemented as a **doubly-linked list of siblings** plus a parent pointer. This avoids Python list resizing overhead and allows O(1) insertion via `insert_after`.

**Fields:**

| Field | Type | Description |
|---|---|---|
| `type` | `str` | Node type string, e.g. `'paragraph'`, `'heading'`, `'link'` |
| `parent` | `Node \| None` | Parent node |
| `first_child` | `Node \| None` | First child |
| `last_child` | `Node \| None` | Last child |
| `prev` | `Node \| None` | Previous sibling |
| `next` | `Node \| None` | Next sibling |
| `string_content` | `str` | Raw text content, consumed by InlineParser |
| `literal` | `str \| None` | Final literal content (code, math, text) |
| `destination` | `str \| None` | URL for links/images/media |
| `title` | `str \| None` | Caption/title for media |
| `info` | `str \| None` | Info string for fenced code blocks (language name) |
| `level` | `int \| None` | Heading level (1–6) |
| `is_open` | `bool` | Whether the parser can still append to this node |

**Dynamic attributes** (set ad-hoc on specific node types):

| Attribute | Node types | Description |
|---|---|---|
| `custom_id` | heading | Value of `{#id}` anchor |
| `label` | footnote_def, footnote_ref | Footnote label string |
| `checked` | task_checkbox | Whether task is checked |
| `list_type` | list | `'bullet'` or `'ordered'` |
| `list_start` | list | Starting number for ordered lists |
| `indent` | list | Source indentation (for nesting detection) |
| `is_fenced` | code_block | Always `True` for fenced code |
| `fence_char` | code_block | Opening fence character (`` ` `` or `~`) |
| `fence_length` | code_block | Opening fence length |
| `headers_done` | table | Whether the separator row has been seen |

**Methods:**

- `append_child(child)` — unlinks `child` from its current tree, then appends it as the new last child.
- `unlink()` — removes this node from its parent and siblings, zeroing all pointers.
- `insert_after(sibling)` — inserts `sibling` immediately after `self` in the sibling chain.
- `walker()` — generator yielding `(node, entering: bool)` pairs in depth-first pre/post order.
- `to_dict()` — recursively serialises the subtree to a plain Python dict (JSON-serialisable).

---

### `parser.py`

**Purpose:** Builds the full AST from the token stream. Contains two classes.

#### `InlineParser`

Converts a flat list of inline tokens into inline AST child nodes attached to a parent block node.

**State:** Holds a `Lexer` instance (for recursive inline tokenisation of nested content like link labels and formatted text), a `dispatch` dict mapping token types to handler methods, and a `tag_map` dict mapping token types to AST node type strings.

**`parse(block_node)`:** Strips `block_node.string_content`, calls `Lexer.tokenize_inline()`, calls `_build_nodes()`, then clears `string_content`.

**`_token_to_node(tok)`:** Looks up `tok.type` in `dispatch`, falls back to `parse_text`. Each handler returns a `Node` or `None`.

**Handlers:**

| Method | Token types handled | Behaviour |
|---|---|---|
| `parse_media` | AUDIO, VIDEO | Creates node with `destination` and `title` |
| `parse_image` | IMAGE | Creates image node; recursively tokenises alt text as children |
| `parse_link` | LINK | Creates link node; recursively tokenises label as children |
| `parse_formatted_text` | STRONG, EMPH, MARK, UNDERLINE, DEL, SUB, SUP | Creates typed node; recursively tokenises inner text as children |
| `parse_literal` | MATH, CODE, EMOJI, HTML | Creates typed node with `literal` field |
| `parse_footnote_ref` | FOOTNOTE_REF | Creates `footnote_ref` node with `label` |
| `parse_task` | TASK | Creates `task_checkbox` node with `checked` bool |
| `parse_autolink` | EMAIL_LINK, URI_LINK | Creates `link` node; EMAIL gets `mailto:` prefix; URI gets percent-encoded |
| `parse_entity` | ENTITY | Creates `text` node with HTML-unescaped character |
| `parse_break` | HARDBREAK, SOFTBREAK | Creates `hardbreak` or `softbreak` node |
| `parse_escaped` | ESCAPED | Creates `text` node with the escaped character |
| `parse_text` | IL_TEXT (default) | Creates `text` node with raw value |

#### `Parser`

Top-down, left-to-right block-level parser. Maintains a "tip" pointer — the currently open deepest node — and incorporates one block token at a time.

**State:**
- `doc` — root `Node('document')`
- `tip` — the currently open node (where new children are attached)
- `inline_parser` — shared `InlineParser` instance
- `_lexer` — shared `Lexer` instance

**`parse(text)`:**
1. Tokenise with `Lexer.tokenize(text)`.
2. Call `_incorporate_token()` for every token.
3. Walk `tip` up to root, closing all open nodes.
4. Call `process_inlines(doc)` to expand all `string_content` fields.
5. Return `doc`.

**`_incorporate_token(tok)`** handles every block token type:

| Token | Action |
|---|---|
| RAW_CONTENT | Appends `tok.value + '\n'` to `tip.string_content` |
| CODE_FENCE_END / MATH_FENCE_END / MERMAID_CLOSE | Closes `tip` |
| HTML_BLOCK (continuation) | Appends to `tip.literal`; BLANK closes it |
| BLANK | Closes `tip` if open |
| BLOCKQUOTE | Opens/continues a `block_quote` node; appends a `paragraph` child |
| ATX_HEADING | Creates `heading` node; closes immediately (`is_open=False`) |
| FOOTNOTE_DEF | Creates `footnote_def` node; optional inline paragraph child |
| DEF_LIST_MARKER | Promotes preceding `paragraph` to `def_term`; creates `def_list`/`def_item` structure |
| THEMATIC_BREAK | Creates `thematic_break` node; closes immediately |
| CODE_FENCE | Creates `code_block` or `mermaid_block` node; opens fence |
| MATH_FENCE | Creates `math_block` node; opens fence |
| MERMAID_FENCE | Creates `mermaid_block` node; opens fence |
| DETAILS_FENCE | Creates `details` node; opens fence |
| BULLET_LIST / ORDERED_LIST | Delegates to `_handle_list_item()` |
| TABLE_SEP | Sets `tip.headers_done = True` on the open `table` node |
| TABLE_ROW | Opens/continues a `table` node; creates `table_row` + `table_header`/`table_cell` children |
| HTML_BLOCK | Creates `html_block` node with raw literal; opens for continuation |
| PARAGRAPH | Appends to open paragraph's `string_content` or opens a new `paragraph` |

**`_handle_list_item(indent, list_type, list_start, content)`:**

Walks the ancestor chain looking for an open `list` node. Handles three cases:
1. Deeper indent than existing list → create nested list inside last item.
2. Same indent and same type → reuse existing list.
3. Same indent but different type → close existing list, create sibling list.
4. No existing list found → create new list, appended to `doc` or current open container.

Finally, always creates a new `item` node + `paragraph` child and sets `tip` to the paragraph.

**`process_inlines(doc)`:**

Walks the full AST. For nodes of type `paragraph`, `heading`, `table_cell`, `table_header`, `def_term`, `details`: calls `inline_parser.parse(node)` which consumes `string_content` and attaches inline children. For `code_block`, `math_block`, `mermaid_block`: moves `string_content` to `literal`.

---

### `html_renderer.py`

**Purpose:** Takes `Node.to_dict()` output (a dict tree) and emits an HTML string.

**`render(ir_dict)`:** Resets `self.buffer = []`, calls `_render_node(ir_dict)`, returns `''.join(self.buffer)`.

**`escape(text)`:** HTML-escapes `&`, `<`, `>`, `"`, `'`.

**`_text_content(node)`:** Recursively extracts plain text from a node subtree (used for `alt` attributes on images).

**`_render_node(node, tight=False)`:** A large `if/elif` dispatch on `node['type']`. The `tight` flag suppresses `<p>` wrapping inside list items.

---

### `app.py`

**Purpose:** Web UI Server and API Entry point.

1. Hosts the Flask web server (`app.py`).
2. Provides the `/compile` JSON API endpoint.
3. Instantiates `Lexer()` and `Parser()` on incoming Markdown requests.
4. Generates D3-compatible visual tree payloads via `ASTVisualizer` and `CSTVisualizer`.
5. Calculates statistical data via `AnalyticsGenerator`.
6. Renders final HTML output and serves the SPA via `index.html`.

---

## 3. Data Flow Summary

```
Raw Markdown text
    │
    ├─► Lexer.tokenize()
    │       └─► list[Token]  (block tokens, flat)
    │
    ├─► Parser._incorporate_token() × N
    │       └─► Node tree (block-level AST, string_content unfilled)
    │
    ├─► Parser.process_inlines()
    │       └─► InlineParser.parse() per content node
    │               └─► Lexer.tokenize_inline()
    │                       └─► list[Token]  (inline tokens)
    │               └─► Node subtree attached as children
    │
    ├─► Node.to_dict()
    │       └─► dict tree (JSON-serialisable)
    │
    └─► HtmlRenderer.render()
            └─► HTML string
```

---

## 4. Extension Points

- **New block type:** Add a constant in `lex_token.py`, add a named group to `block_token_pattern`, handle the group name in `Lexer.tokenize()`, incorporate the token in `Parser._incorporate_token()`, and render it in `HtmlRenderer._render_node()`.
- **New inline type:** Add a constant in `lex_token.py`, add an alternation to `inline_token_pattern`, add a branch in `Lexer._classify_inline()`, add a meta extractor to `Lexer._inline_meta()`, add a handler in `InlineParser.dispatch`, and render it in `HtmlRenderer._render_node()`.
- **Custom rendering:** Subclass `HtmlRenderer` and override `_render_node()` for specific node types.
