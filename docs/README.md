# pyV — Markdown to HTML Compiler

A hand-written, single-pass Markdown-to-HTML compiler written in pure Python. No third-party dependencies. Supports an extended Markdown dialect including tables, footnotes, definition lists, math blocks, Mermaid diagrams, details/summary, task lists, and custom multimedia embeds.

---

## Project Structure

```
pyV/
├── compiler.py        # Entry point — CLI driver
├── lex_token.py       # Token class, all token-type constants, and all regex patterns
├── lexer.py           # Lexer — block and inline tokenisation
├── parser.py          # InlineParser + Parser — builds the AST
├── node.py            # Node — the AST node / linked-list data structure
├── html_renderer.py   # HtmlRenderer — walks the AST dict and emits HTML
├── template.html      # HTML page template (replaces __TITLE__ and __BODY_HTML__)
├── style.css          # Default stylesheet
└── docs/              # Project documentation
```

### File responsibilities

| File | Responsibility |
|---|---|
| `lex_token.py` | Defines the `Token` dataclass, every block and inline token-type constant, and every compiled regex used by the lexer. |
| `lexer.py` | `Lexer` class. `tokenize(text)` splits a Markdown string into a flat list of block `Token` objects. `tokenize_inline(text)` splits an inline string into a flat list of inline `Token` objects. |
| `parser.py` | `InlineParser` converts inline token lists into inline AST sub-trees. `Parser` drives the full pipeline: calls `Lexer.tokenize()`, incorporates each block token into the growing AST, then calls `InlineParser` on every content node. |
| `node.py` | `Node` — a doubly-linked n-ary tree node. Holds typed fields (`type`, `literal`, `destination`, `level`, …) and supports `to_dict()` serialisation. |
| `html_renderer.py` | `HtmlRenderer` accepts the `to_dict()` output (a plain Python dict tree) and recursively renders it to an HTML string. |
| `compiler.py` | CLI: reads a `.md` file, runs the full pipeline, injects the result into `template.html`, and writes `.html` + `.json` output files. |

---

## Requirements

- Python 3.10 or later (uses `X | Y` union type hints)
- No third-party packages

---

## How to Run

```bash
python3 compiler.py <path/to/file.md>
```

### Example

```bash
python3 compiler.py README.md
```

This will produce two output files in the current working directory:

| Output file | Contents |
|---|---|
| `README.html` | Full HTML page (template + rendered body) |
| `README.json` | JSON representation of the intermediate AST |

### Template

`template.html` must exist in the same directory as `compiler.py`. It must contain the placeholders `__TITLE__` and `__BODY_HTML__`, which the compiler replaces with the document title (derived from the file name) and the rendered HTML body respectively.

---

## Pipeline Overview

```
.md file
   │
   ▼
Lexer.tokenize()          — produces flat list[Token] (block tokens)
   │
   ▼
Parser._incorporate_token()  — builds block-level AST (Node tree)
   │
   ▼
Parser.process_inlines()     — calls InlineParser on every content node
   │
   ▼
Node.to_dict()               — serialises AST to plain dict (JSON-serialisable)
   │
   ▼
HtmlRenderer.render()        — walks dict tree, emits HTML string
   │
   ▼
template.html injection      — wraps body in full HTML page
   │
   ▼
.html + .json output files
```

---

## Supported Markdown Features

### Block-level

| Feature | Syntax |
|---|---|
| ATX Headings (h1–h6) | `# … ######` |
| Paragraph | Plain text lines |
| Thematic break | `---`, `***`, `___` |
| Blockquote | `> text` |
| Bullet list (nested) | `- item`, `* item`, `+ item` |
| Ordered list (nested) | `1. item`, `1) item` |
| Fenced code block | ` ``` lang … ``` ` or `~~~ lang … ~~~` |
| Math block | `$$` … `$$` |
| Mermaid diagram | `:::mermaid … :::` or ` ```mermaid … ``` ` |
| Details / summary | `:::details Title … :::` |
| Table | `\| col \| col \|` with `\|---\|---\|` separator |
| Footnote definition | `[^label]: text` |
| Definition list | term paragraph + `: definition` |
| Raw HTML block | Block-level HTML tags passed through verbatim |

### Inline-level

| Feature | Syntax |
|---|---|
| Bold | `**text**` or `__text__` |
| Italic | `*text*` or `_text_` |
| Highlight | `==text==` |
| Underline | `++text++` |
| Strikethrough | `~~text~~` |
| Subscript | `~text~` |
| Superscript | `^text^` |
| Inline code | `` `code` `` |
| Inline math | `$equation$` |
| Link | `[label](url)` |
| Image | `![alt](url)` |
| Video embed | `@[caption](url)` |
| Audio embed | `&[caption](url)` |
| Footnote reference | `[^label]` |
| Emoji shortcode | `:emoji:` |
| Task checkbox | `[x]` / `[ ]` |
| Email autolink | `<user@example.com>` |
| URL autolink | `<https://example.com>` |
| HTML entity | `&amp;`, `&#42;`, `&#x2A;` |
| Hard line break | Two trailing spaces before newline |
| Escaped character | `\*`, `\_`, etc. |
| Inline HTML | `<span>`, `<br>`, etc. |

### Custom ID on headings

```markdown
## My Section {#my-anchor}
```

Renders as `<h2 id="my-anchor">My Section</h2>`.
