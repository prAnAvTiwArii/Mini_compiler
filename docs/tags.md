# Marky: HTML Tags Mapping & Output Specification

The `html_renderer.py` module consumes the JSON Intermediate Representation (IR) constructed by the Parser and emits native HTML tags. The compiler prioritizes semantic HTML5 syntax.

This document details every mapped HTML tag, what component emits it, and its specific rendering parameters.

---

## 1. Document & Block Containers

| Markdown Source | Intermediate Node | Output HTML | Rendering Notes |
| :--- | :--- | :--- | :--- |
| *Top-level File* | `document` | `<html><body>...</body></html>` | Handled by `template.html` wrapper. Renderer outputs the inner `<body/>`. |
| `Paragraph Text` | `paragraph` | `<p>...</p>` | Does **not** wrap standalone text elements if they are emitted inside specific blocks (e.g. tightly packed list items). |
| `# Heading 1` | `heading` (level: 1) | `<h1 id="heading-1">...</h1>` | Automatically derives the `id` from textual content for anchor navigation. Supports levels `<h1/>` through `<h6/>`. |
| `> Quote` | `blockquote` | `<blockquote>...</blockquote>` | Can recursively contain nested paragraphs, lists, and other block nodes. |
| `---` | `thematic_break` | `<hr />` | Zero-width horizontal line separator. |

---

## 2. Lists & Defs

| Markdown Source | Node Type | Output HTML |
| :--- | :--- | :--- |
| `- item` | `list` (type: bullet) | `<ul>...</ul>` |
| `1. item` | `list` (type: ordered) | `<ol>...</ol>` |
| `(list child)` | `item` | `<li>...</li>` |
| `Term` `: Desc`| `def_list` | `<dl> <dt>Term</dt> <dd>Desc</dd> </dl>` |

*Checkboxes (`[x]` or `[ ]`) inside items are transformed into raw `<input type="checkbox" checked>` fields rather than `<li/>` variants, allowing dynamic checklists using standardized forms.*

---

## 3. Tables

Table rendering organizes linear parsed nodes into strict `<thead>` and `<tbody>` grouping elements to adhere to modern accessibility and CSS requirements.

| AST Node | Output HTML | Rendering Notes |
| :--- | :--- | :--- |
| `table` | `<table>...</table>`| The base wrapper. |
| (Header Row) | `<thead>...</thead>`| Wrapping `<tr>` if child nodes of that row are `<th>`. |
| (Body Rows) | `<tbody>...</tbody>`| Wrapping subsequent `<tr>` blocks. |
| `table_row` | `<tr>...</tr>` | Represents a horizontal chunk of items. |
| `table_header` | `<th>...</th>` | Table header cell. |
| `table_cell` | `<td>...</td>` | Standard table cell. |

---

## 4. Fenced Blocks & Media

| Concept | Output HTML | Rendering Notes |
| :--- | :--- | :--- |
| **Code Box** | `<pre><code class="language-X">...</code></pre>` | The syntax-highlighting class explicitly relies on the `info` property appended to the fence. Extracted text is heavily escaped to prevent injection. |
| **Math Eqn** | `<div class="math math-display">...</div>` | Contains raw LaTeX text which is deferred for rendering by `katex.js` loaded inside `template.html`. |
| **Mermaid** | `<pre class="mermaid">...</pre>` | Contains raw structural map interpreted directly via the `mermaid.esm.js` plugin module block. |
| **Details** | `<details><summary>Title</summary><p>...p></details>` | Uses the custom `:::details Title` format. The Title routes immediately to `<summary/>`, whilst inner elements iteratively populate the `<p/>` block natively. |
| **Image**| `<img src="X" alt="Y" title="Z" />` | Self-closing standard element. |
| **Video**| `<video controls><source src="X"/>Y</video>`| Wraps standard web-video streams embedding the alt text as native captioning within the tag constraint. |
| **Audio**| `<audio controls><source src="X"/>Y</audio>`| Identical functionality to Video. |

---

## 5. Inline Formatting

The `InlineParser` identifies spans converting string values into explicitly wrapped formats.

- `<strong>` / `<em>`: Bold and italics (`**` and `*`).
- `<mark>`: Highlighting text (`==`).
- `<u>`: Deep underline (`++`).
- `<s>`: Strikethrough text via `<del>` logic (`~~`).
- `<sup>` / `<sub>`: Position relative shifts (`^` and `~`).
- `<code>`: Formatted inline terminal fonts based on ``` backquotes.
- `<a href="X">Y</a>`: Outward URL anchors. Escapes bad/malformed internal routes.
- `<br />`: Explicit line breakage forced via double spacing (`IL_HARDBREAK`).

### 5.1 Native HTML Passthroughs

Components evaluated as `IL_HTML` bypass renderer translation mechanisms. These native tags are appended linearly as text objects, permitting their interpretation directly by the recipient browser. Supported valid passthroughs include:
`<b>`, `<i>`, `<var>`, `<q>`, `<caption>`, `<tfoot>`, `<track>`, `<object>`.
