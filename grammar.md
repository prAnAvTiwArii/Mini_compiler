# Grammar Rules

Defined in `parser.py`. The `Parser` class consumes a `list[Token]` from `Lexer.tokenize()` and builds an AST of `Node` objects.

---

## Formal Context-Free Grammar

Written in YACC/BNF notation. Terminal symbols are the token constants from `regex_rules.py` (all-caps). Non-terminals are lowercase. `ε` denotes the empty production.

```yacc
/* ── Top level ──────────────────────────────────────────────────── */

document
    : block_list
    ;

block_list
    : block_list block
    | ε
    ;

block
    : paragraph_block
    | heading_block
    | thematic_break_block
    | blockquote_block
    | code_fence_block
    | math_fence_block
    | mermaid_fence_block
    | bullet_list_block
    | ordered_list_block
    | table_block
    | html_block_block
    | footnote_def_block
    | def_list_block
    | BLANK
    ;


/* ── Block productions ──────────────────────────────────────────── */

paragraph_block
    : paragraph_line_list
    ;

paragraph_line_list
    : paragraph_line_list PARAGRAPH
    | PARAGRAPH
    ;

heading_block
    : ATX_HEADING
    ;

thematic_break_block
    : THEMATIC_BREAK
    ;

blockquote_block
    : blockquote_line_list
    ;

blockquote_line_list
    : blockquote_line_list BLOCKQUOTE
    | BLOCKQUOTE
    ;

code_fence_block
    : CODE_FENCE raw_line_list CODE_FENCE_END
    | CODE_FENCE CODE_FENCE_END
    ;

math_fence_block
    : MATH_FENCE raw_line_list MATH_FENCE_END
    | MATH_FENCE MATH_FENCE_END
    ;

mermaid_fence_block
    : MERMAID_FENCE raw_line_list MERMAID_CLOSE
    | MERMAID_FENCE MERMAID_CLOSE
    | CODE_FENCE raw_line_list CODE_FENCE_END   /* ` ```mermaid ` variant */
    ;

raw_line_list
    : raw_line_list RAW_CONTENT
    | RAW_CONTENT
    ;

bullet_list_block
    : bullet_list_block bullet_list_item
    | bullet_list_item
    ;

bullet_list_item
    : BULLET_LIST
    ;

ordered_list_block
    : ordered_list_block ordered_list_item
    | ordered_list_item
    ;

ordered_list_item
    : ORDERED_LIST
    ;

table_block
    : table_header_rows TABLE_SEP table_body_rows
    | table_header_rows TABLE_SEP
    ;

table_header_rows
    : table_header_rows TABLE_ROW
    | TABLE_ROW
    ;

table_body_rows
    : table_body_rows TABLE_ROW
    | TABLE_ROW
    ;

html_block_block
    : HTML_BLOCK html_continuation_list BLANK
    | HTML_BLOCK html_continuation_list
    | HTML_BLOCK BLANK
    | HTML_BLOCK
    ;

html_continuation_list
    : html_continuation_list html_continuation_line
    | html_continuation_line
    ;

html_continuation_line
    : PARAGRAPH
    | ATX_HEADING
    | BULLET_LIST
    | ORDERED_LIST
    /* any non-blank, non-fence token continues an open html_block */
    ;

footnote_def_block
    : FOOTNOTE_DEF
    ;

def_list_block
    : def_term def_item_list
    ;

def_term
    : PARAGRAPH           /* the paragraph token immediately before ':' lines */
    ;

def_item_list
    : def_item_list DEF_LIST_MARKER
    | DEF_LIST_MARKER
    ;


/* ── Inline productions (Phase 2, applied to string_content) ─────── */

inline_content
    : inline_content inline_node
    | ε
    ;

inline_node
    : IL_IMAGE
    | IL_LINK
    | IL_STRONG
    | IL_EMPH
    | IL_MARK
    | IL_UNDERLINE
    | IL_DEL
    | IL_SUB
    | IL_SUP
    | IL_CODE
    | IL_MATH
    | IL_FOOTNOTE_REF
    | IL_EMOJI
    | IL_TASK
    | IL_HTML
    | IL_EMAIL_LINK
    | IL_URI_LINK
    | IL_ENTITY
    | IL_HARDBREAK
    | IL_SOFTBREAK
    | IL_ESCAPED
    | IL_TEXT
    ;
```

> **Note on operator precedence / disambiguation:**
> List nesting (bullet inside ordered, deeper indents) is resolved dynamically by `_handle_list_item()` using the `indent` field on each token rather than by grammar rules. The CFG above treats each list item as a flat terminal; see the [List section](#bulletlist--orderedlist) below for the full nesting algorithm.

---

## Pipeline

```
Raw text
  ↓  Lexer.tokenize()           → list[Token]  (Phase 1 — block tokens)
  ↓  Parser._incorporate_token() → Node tree   (Phase 1.5 — block AST)
  ↓  Parser.process_inlines()   → Node tree    (Phase 2 — inline AST)
```

---

## Block Grammar Rules

Each rule shows: the token consumed → the Node(s) produced → any special conditions.

### BLANK

```
BLANK → (no node)
```
If the current tip is an open node it is closed. HTML blocks are also closed by a blank line.

---

### PARAGRAPH

```
PARAGRAPH → paragraph node (string_content accumulates)
```
- If the current tip is already an **open** `paragraph`, the line's value is appended with `\n`.
- Otherwise a new `paragraph` node is created and appended to the document (or to the current open `block_quote`/`item`).

---

### ATX_HEADING

```
ATX_HEADING → heading(level, string_content, custom_id?)
```
Meta keys used: `level` (int 1–6), `content` (str), `custom_id` (str | None).
The heading is always appended directly to the document root. Any open paragraph tip is closed first.

---

### THEMATIC_BREAK

```
THEMATIC_BREAK → thematic_break
```
Appended to document root. Any open paragraph is closed first.

---

### BLOCKQUOTE

```
BLOCKQUOTE → block_quote → paragraph(string_content)
```
- If an open `block_quote` is already the tip, the new paragraph is added inside it.
- Otherwise a new `block_quote` is created at the document root and the paragraph nested inside.

---

### CODE_FENCE / CODE_FENCE_END

```
CODE_FENCE     → code_block | mermaid_block   (if info == "mermaid")
RAW_CONTENT    → (appended to code_block.string_content)
CODE_FENCE_END → (closes the open code_block/mermaid_block)
```
Meta keys: `fence_char` (`` ` `` or `~`), `fence_length` (int), `info` (language string), `block_type`.

---

### MATH_FENCE / MATH_FENCE_END

```
MATH_FENCE     → math_block
RAW_CONTENT    → (appended to math_block.string_content)
MATH_FENCE_END → (closes the open math_block)
```

---

### MERMAID_FENCE / MERMAID_CLOSE

```
MERMAID_FENCE  → mermaid_block
RAW_CONTENT    → (appended to mermaid_block.string_content)
MERMAID_CLOSE  → (closes the open mermaid_block)
```

---

### BULLET_LIST / ORDERED_LIST

```
BULLET_LIST | ORDERED_LIST → list → item → paragraph(string_content)
```

List nesting rules (handled by `_handle_list_item`):

| Condition | Action |
|---|---|
| No open list found | Create new `list` node at document / current open container |
| Open list found, same type, same indent | Reuse existing list, add new `item` |
| Open list found, different type | Close old list, create new `list` |
| New indent > current list indent | Create nested `list` inside last `item` |
| New indent < current list indent | Close current list |

Meta keys: `list_type` (`"bullet"` or `"ordered"`), `list_start` (int, ordered only), `content`.

---

### TABLE_ROW / TABLE_SEP

```
TABLE_ROW → table → table_row → table_header | table_cell
TABLE_SEP → (marks headers_done = True on the current table)
```
- First batch of rows (before `TABLE_SEP`) produce `table_header` cells.
- Rows after `TABLE_SEP` produce `table_cell` cells.
- A new `table` is created if the tip is not already an open table.

---

### HTML_BLOCK

```
HTML_BLOCK → html_block (literal = raw line, is_open = True)
```
Subsequent non-blank lines are appended to `html_block.literal`. A `BLANK` token closes the block.

---

### FOOTNOTE_DEF

```
FOOTNOTE_DEF → footnote_def(label) → paragraph(string_content)?
```
If the token has inline `content`, a child `paragraph` is created immediately.

---

### DEF_LIST_MARKER

```
DEF_LIST_MARKER → def_list → [def_term, def_item → paragraph]
```
- If the current tip is a `paragraph`, it is converted to `def_term` and a `def_list` is inserted after it.
- A new `def_item → paragraph` is appended for each marker.

---

### RAW_CONTENT

```
RAW_CONTENT → (string_content of current code_block | math_block | mermaid_block)
```
Only consumed when `tip` is one of the three fenced block types.

---

## Inline Grammar Rules

Applied by `InlineParser.parse()` via `Lexer.tokenize_inline()` during Phase 2. Each inline token maps to a child `Node` on the containing block node.

| Token | Node produced | Key attributes |
|---|---|---|
| `IL_IMAGE` | `image` | `destination`, `title` (= alt text), child `text` |
| `IL_LINK` | `link` | `destination`, child `text` |
| `IL_STRONG` | `strong` | child `text` |
| `IL_EMPH` | `emph` | child `text` |
| `IL_MARK` | `mark` | child `text` |
| `IL_UNDERLINE` | `u` | child `text` |
| `IL_DEL` | `del` | child `text` |
| `IL_SUB` | `sub` | child `text` |
| `IL_SUP` | `sup` | child `text` |
| `IL_CODE` | `code` | `literal` (backtick-stripped, trimmed) |
| `IL_MATH` | `math_inline` | `literal` |
| `IL_FOOTNOTE_REF` | `footnote_ref` | `label` |
| `IL_EMOJI` | `emoji` | `literal` (raw `:name:`) |
| `IL_TASK` | `task_checkbox` | `checked` (bool) |
| `IL_EMAIL_LINK` | `link` | `destination = "mailto:" + dest` |
| `IL_URI_LINK` | `link` | `destination` (percent-encoded) |
| `IL_HTML` | `html_inline` | `literal` |
| `IL_ENTITY` | `text` | `literal` (HTML-unescaped) |
| `IL_HARDBREAK` | `hardbreak` | — |
| `IL_SOFTBREAK` | `softbreak` | — |
| `IL_ESCAPED` | `text` | `literal = meta['char']` |
| `IL_TEXT` | `text` | `literal` |

---

## Nodes that receive inline parsing (Phase 2)

`process_inlines()` walks the completed block AST. Inline parsing is applied to nodes whose `string_content` is set:

| Node type | Inline-parsed? |
|---|---|
| `paragraph` | ✓ |
| `heading` | ✓ |
| `table_cell` | ✓ |
| `table_header` | ✓ |
| `def_term` | ✓ |
| `code_block` | ✗ — `string_content` moved to `literal` as-is |
| `math_block` | ✗ — same |
| `mermaid_block` | ✗ — same |
