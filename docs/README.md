# Mini_Compiler — Markdown to HTML Compiler & Visualizer

A hand-written, single-pass Markdown-to-HTML compiler written in pure Python. No third-party dependencies for the core compiler. It features an extended Markdown dialect including tables, footnotes, definition lists, math blocks, Mermaid diagrams, details/summary, task lists, and custom multimedia embeds.

Additionally, Mini_Compiler includes a **state-of-the-art interactive Web UI** designed with a scientific dark theme to visualize the entire compiler pipeline (Tokens, AST, Parse Tree, Analytics, IR JSON, and Generated HTML) in real-time.

---

## Project Structure

```
Mini_Compiler/
├── app.py             # Web UI Entry point — Flask Application
├── backend/           # Web Integrations & Visualizers
│   ├── ast_visualizer.py
│   ├── cst_visualizer.py
│   └── analytics.py
├── compiler/          # Core Compiler Pipeline
│   ├── lex_token.py   # Token class and constants
│   ├── lexer.py       # Lexer — block and inline tokenisation
│   ├── parser.py      # Parser — builds the AST
│   ├── node.py        # Node — AST data structure
│   └── html_renderer.py
├── frontend/          # Web Interface
│   ├── static/        # CSS (style.css, render.css)
│   └── templates/     # HTML (index.html, doc.html)
└── docs/              # Project documentation
```

### File responsibilities

| Component | Responsibility |
|---|---|
| **Compiler Core** | The `compiler/` directory contains the pure-Python text-to-AST-to-HTML logic. `Lexer` handles tokenisation, `Parser` builds the n-ary tree, and `HtmlRenderer` emits HTML. |
| **Backend API** | The `backend/` directory connects the core compiler to the frontend. It includes `ASTVisualizer` and `CSTVisualizer` for generating D3.js compatible payloads, and `AnalyticsGenerator` for deep token and tree metrics. |
| **Frontend UI** | The `frontend/` directory contains the Single Page Application (SPA). `index.html` offers a split-pane interactive compiler tool with a horizontal pipeline, smooth D3 animations, and colored tokens. |
| `app.py` | The Flask server that serves the UI and handles the `/compile` API endpoints to run the markdown pipeline dynamically. |

---

## Requirements

- Python 3.10 or later
- Flask (for the Web UI)

---

## How to Run

To launch the interactive compiler visualizer:

```bash
python3 app.py
```

Then, open your browser and navigate to `http://localhost:5001`. You will be greeted with the home page, where you can read the documentation or launch the interactive compiler by clicking **"Try It"**.

### Usage Features:
- **Interactive Parsing**: Type or upload Markdown on the left pane and watch the AST/HTML update on the right.
- **Token Drill-down**: The Tokens tab natively groups inline tokens inside block tokens.
- **Tree Animations**: Use the "Smoothness/Speed" slider to dynamically adjust the D3 AST and Parse tree rendering speed.
- **Advanced Diagnostics**: Track node distribution, text-to-code ratios, and tree depth.

---

## Pipeline Overview

```
.md file input
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
Analytics & Visualizers      — calculates tree depth, distribution, and D3 payloads
   │
   ▼
Node.to_dict()               — serialises AST to plain dict (IR JSON)
   │
   ▼
HtmlRenderer.render()        — walks dict tree, emits HTML string
   │
   ▼
Flask /compile Response      — pushes all pipeline phases to the frontend
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
