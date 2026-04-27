# Node — AST Data Structure

This document explains how pyV stores the parsed document as an in-memory tree, the fields on each node, the tree operations available, and the serialisation format. A worked example traces a real Markdown snippet from source to full AST.

---

## Overview

After lexing and parsing, the document is represented as an **n-ary tree of `Node` objects**. Each `Node` carries:

1. A **type string** (e.g., `'paragraph'`, `'heading'`, `'link'`) that identifies what kind of content it represents.
2. **Typed fields** for common attributes (`literal`, `destination`, `level`, …).
3. **Dynamic fields** set ad-hoc for specialised node types (e.g., `list_type`, `checked`, `custom_id`).
4. A **doubly-linked sibling chain** (prev/next) plus a parent pointer, enabling O(1) insertion and removal.

---

## Linked-List Tree Layout

```
Node
├── parent  ──────────────────► parent Node
├── first_child ─────────────► first child Node ──next──► second child Node ──next──► …
└── last_child  ─────────────► last child Node
                                 └── prev ◄────────────── second-to-last Node
```

This layout is identical to the CommonMark reference implementation (cmark). It allows:

- `append_child(child)` — O(1), updates `last_child` and sibling links.
- `unlink()` — O(1), patches prev/next siblings and parent.
- `insert_after(sibling)` — O(1), used when a definition list is discovered after its term paragraph already exists.

---

## `Node` Fields

### Always-present (set in `__init__`)

| Field | Type | Default | Description |
|---|---|---|---|
| `type` | `str` | *(required)* | Node type string |
| `parent` | `Node \| None` | `None` | Parent node |
| `first_child` | `Node \| None` | `None` | First child node |
| `last_child` | `Node \| None` | `None` | Last child node |
| `prev` | `Node \| None` | `None` | Previous sibling |
| `next` | `Node \| None` | `None` | Next sibling |
| `string_content` | `str` | `''` | Raw inline text, consumed by InlineParser |
| `literal` | `str \| None` | `None` | Final literal content (code, text, math) |
| `destination` | `str \| None` | `None` | URL for links/images/media |
| `title` | `str \| None` | `None` | Caption for media / title for details |
| `info` | `str \| None` | `None` | Language info for fenced code |
| `level` | `int \| None` | `None` | Heading level (1–6) |
| `is_open` | `bool` | `True` | Whether parser can still append children |

### Dynamic fields (set by parser on specific node types)

| Field | Set on node types | Type | Description |
|---|---|---|---|
| `custom_id` | `heading` | `str` | Value from `{#id}` anchor syntax |
| `label` | `footnote_def`, `footnote_ref` | `str` | Footnote label string |
| `checked` | `task_checkbox` | `bool` | Whether task checkbox is checked |
| `list_type` | `list` | `str` | `'bullet'` or `'ordered'` |
| `list_start` | `list` | `int \| None` | Starting number for ordered lists |
| `indent` | `list` | `int` | Source indentation for nesting logic |
| `is_fenced` | `code_block` | `bool` | Always `True` for fenced blocks |
| `fence_char` | `code_block` | `str` | Opening fence character |
| `fence_length` | `code_block` | `int` | Opening fence run length |
| `headers_done` | `table` | `bool` | `True` after `TABLE_SEP` seen |

---

## Node Types Reference

| Node Type | Description | Key Fields |
|---|---|---|
| `document` | Root of every AST | children |
| `heading` | ATX heading h1–h6 | `level`, `custom_id`, inline children |
| `paragraph` | Block of inline content | inline children |
| `thematic_break` | Horizontal rule | *(no data)* |
| `block_quote` | Blockquote container | `paragraph` children |
| `list` | Ordered or bullet list | `list_type`, `list_start`, `indent`, `item` children |
| `item` | List item | `paragraph` / `list` children |
| `code_block` | Fenced or indented code | `info`, `literal` |
| `math_block` | Block LaTeX math (`$$`) | `literal` |
| `mermaid_block` | Mermaid diagram | `literal` |
| `details` | Details/summary block | `title`, `literal` or children |
| `table` | Table root | `table_row` children |
| `table_row` | A table row | `table_header` / `table_cell` children |
| `table_header` | A header cell (`<th>`) | inline children |
| `table_cell` | A body cell (`<td>`) | inline children |
| `html_block` | Raw block HTML | `literal` |
| `footnote_def` | Footnote definition | `label`, `paragraph` children |
| `def_list` | Definition list | `def_term` / `def_item` children |
| `def_term` | Definition term (`<dt>`) | inline children |
| `def_item` | Definition item (`<dd>`) | `paragraph` children |
| `link` | Hyperlink | `destination`, inline children (label) |
| `image` | Image | `destination`, inline children (alt) |
| `audio` | Audio embed | `destination`, `title` |
| `video` | Video embed | `destination`, `title` |
| `strong` | Bold text | inline children |
| `emph` | Italic text | inline children |
| `mark` | Highlighted text | inline children |
| `u` | Underline | inline children |
| `del` | Strikethrough | inline children |
| `sub` | Subscript | inline children |
| `sup` | Superscript | inline children |
| `code` | Inline code | `literal` |
| `math_inline` | Inline LaTeX math | `literal` |
| `html_inline` | Raw inline HTML | `literal` |
| `text` | Plain text leaf | `literal` |
| `hardbreak` | Hard line break (`<br>`) | *(no data)* |
| `softbreak` | Soft line break (`<br>`) | *(no data)* |
| `emoji` | Emoji shortcode | `literal` |
| `task_checkbox` | Task list checkbox | `checked` |
| `footnote_ref` | Inline footnote ref | `label` |

---

## `to_dict()` Serialisation

`Node.to_dict()` returns a plain Python dict that is JSON-serialisable. The schema:

```python
{
    "type": str,
    "literal": str | None,
    "destination": str | None,
    "title": str | None,
    "info": str | None,
    "level": int | None,
    "string_content": str,      # empty after InlineParser runs
    "children": [               # list of child dicts (recursive)
        { ... }
    ],
    # plus any dynamic fields set on the node, e.g.:
    "custom_id": str | None,
    "label": str | None,
    "checked": bool | None,
    "list_type": str | None,
    "list_start": int | None,
}
```

Only fields that are non-None / non-empty are included in the dict.

---

## Walker Generator

`node.walker()` is a generator that yields `(node, entering: bool)` pairs in depth-first order:

- `entering=True` → yielded when first entering the node (before children).
- `entering=False` → yielded when leaving the node (after all children).

This mirrors the CommonMark event-based walker pattern and is how `process_inlines` and the renderer traverse the tree.

---

## Worked Example

### Input Markdown

```markdown
## Getting Started {#start}

Install with **pip** and run `python compiler.py doc.md`.
```

### After `Lexer.tokenize()`

```
Token(ATX_HEADING, '## Getting Started {#start}',
      meta={'level': 2, 'content': 'Getting Started', 'custom_id': 'start'})
Token(BLANK, '')
Token(PARAGRAPH, 'Install with **pip** and run `python compiler.py doc.md`.')
```

### After `Parser._incorporate_token()` (block AST, before inline expansion)

```
Node(document)
├── Node(heading)
│     level = 2
│     custom_id = 'start'
│     string_content = 'Getting Started'
│     is_open = False
└── Node(paragraph)
      string_content = 'Install with **pip** and run `python compiler.py doc.md`.'
      is_open = True  →  closed by end-of-tokens walk
```

### After `Parser.process_inlines()`

```
Node(document)
├── Node(heading)  level=2  custom_id='start'
│     └── Node(text)  literal='Getting Started'
└── Node(paragraph)
      ├── Node(text)     literal='Install with '
      ├── Node(strong)
      │     └── Node(text)  literal='pip'
      ├── Node(text)     literal=' and run '
      ├── Node(code)     literal='python compiler.py doc.md'
      └── Node(text)     literal='.'
```

### `to_dict()` output

```json
{
    "type": "document",
    "children": [
        {
            "type": "heading",
            "level": 2,
            "custom_id": "start",
            "children": [
                { "type": "text", "literal": "Getting Started" }
            ]
        },
        {
            "type": "paragraph",
            "children": [
                { "type": "text",   "literal": "Install with " },
                {
                    "type": "strong",
                    "children": [
                        { "type": "text", "literal": "pip" }
                    ]
                },
                { "type": "text",   "literal": " and run " },
                { "type": "code",   "literal": "python compiler.py doc.md" },
                { "type": "text",   "literal": "." }
            ]
        }
    ]
}
```

### Final HTML output

```html
<h2 id="start">Getting Started</h2>
<p>Install with <strong>pip</strong> and run <code>python compiler.py doc.md</code>.</p>
```
