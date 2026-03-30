# HTML Rendering Rules

Defined in `html_renderer.py`. The `HtmlRenderer` class walks a `to_dict()` tree produced by `Node` and emits HTML strings collected in `self.buffer`.

---

## Entry Point

```python
renderer = HtmlRenderer()
html = renderer.render(doc.to_dict())
```

`render()` resets the buffer, calls `_render_node(root_dict)`, and joins the buffer into a single string.

---

## Escaping

The `escape(text)` helper HTML-encodes five characters:

| Character | Encoded as |
|---|---|
| `&` | `&amp;` |
| `<` | `&lt;` |
| `>` | `&gt;` |
| `"` | `&quot;` |
| `'` | `&#x27;` |

This is applied to all user-provided text content **except** raw HTML literals and mermaid diagram source.

---

## `tight` mode

`_render_node(node, tight=False)` accepts a `tight` flag. When `tight=True`, `paragraph` nodes render their inline children **without** `<p>…</p>` wrappers. This is used for list items and table cells to avoid unwanted block wrapping.

---

## Node → HTML Rules

### Block Nodes

| Node type | Output HTML | Notes |
|---|---|---|
| `document` | *(renders children, no wrapper)* | Root node |
| `heading` | `<hN id="…">…</hN>\n` | `id` attr only if `custom_id` present |
| `paragraph` | `<p>…</p>\n` | Omitted in tight mode |
| `block_quote` | `<blockquote>\n…</blockquote>\n` | |
| `code_block` | `<pre><code class="language-X">\nLITERAL</code></pre>\n` | `class` omitted if no info string; content is escaped |
| `math_block` | `<div class="math math-display">\nLITERAL</div>\n` | Content is escaped; rendered by KaTeX |
| `mermaid_block` | `<pre class="mermaid">\nLITERAL</pre>\n` | Content is **not** escaped; rendered by Mermaid.js |
| `html_block` | *(literal emitted verbatim)* | No escaping |
| `thematic_break` | *(not implemented — no output)* | Falls through silently |
| `list` | `<ul>…</ul>\n` (bullet) or `<ol>…</ol>\n` (ordered) | |
| `item` | `<li>…</li>\n` | Children rendered in tight mode |
| `table` | `<table border="1">\n…</table>\n` | |
| `table_row` | `<tr>\n…</tr>\n` | |
| `table_header` | `<th>…</th>\n` | Children in tight mode |
| `table_cell` | `<td>…</td>\n` | Children in tight mode |
| `footnote_def` | `<div class="footnote" id="fn:LABEL">\n<p><strong>[LABEL]:</strong> …</p>\n</div>\n` | First child paragraph is inlined with the label prefix |
| `def_list` | `<dl>\n…</dl>\n` | |
| `def_term` | `<dt>…</dt>\n` | |
| `def_item` | `<dd>…</dd>\n` | |

### Inline Nodes

| Node type | Output HTML | Notes |
|---|---|---|
| `text` | `ESCAPED_LITERAL` | Plain escaped text |
| `strong` | `<strong>…</strong>` | |
| `emph` | `<em>…</em>` | |
| `mark` | `<mark>…</mark>` | |
| `u` | `<u>…</u>` | |
| `del` | `<del>…</del>` | |
| `sub` | `<sub>…</sub>` | |
| `sup` | `<sup>…</sup>` | |
| `code` | `<code>ESCAPED_LITERAL</code>` | |
| `math_inline` | `<span class="math math-inline">ESCAPED_LITERAL</span>` | Rendered by KaTeX |
| `link` | `<a href="DEST">…</a>` | `javascript:` destinations are cleared to `""` |
| `image` | *(not yet rendered — falls through)* | |
| `footnote_ref` | `<sup><a href="#fn:LABEL">^LABEL</a></sup>` | |
| `emoji` | `ESCAPED_LITERAL` | Raw `:name:` — no emoji substitution |
| `task_checkbox` | `<input type="checkbox" disabled[ checked]>` | `disabled` always; `checked` if `node.checked` is truthy |
| `hardbreak` | `<br />\n` | |
| `softbreak` | `<br />\n` | |
| `html_inline` | *(literal emitted verbatim)* | No escaping |

---

## Template Integration (`template.html`)

The compiler injects the rendered body into `template.html` by replacing `__BODY_HTML__` and `__TITLE__`. The template provides:

| Feature | Implementation |
|---|---|
| Math rendering | KaTeX `@0.16.8` via CDN; `<span class="math math-inline">` and `<div class="math math-display">` are targeted |
| Diagram rendering | Mermaid `@11` via CDN ESM; targets `<pre class="mermaid">` |
| Code font | Consolas/Monaco monospace via CSS |
| Table styling | `border-collapse: collapse` + `1px solid #ddd` borders |
| Blockquote styling | `4px solid #ccc` left border |

---

## Full Rendering Example

**Input Markdown:**
```markdown
## Hello {#hello}

This is **bold** and `code`.
```

**AST (dict):**
```json
{
  "type": "document",
  "children": [
    {
      "type": "heading",
      "level": 2,
      "custom_id": "hello",
      "children": [{"type": "text", "literal": "Hello"}]
    },
    {
      "type": "paragraph",
      "children": [
        {"type": "text",   "literal": "This is "},
        {"type": "strong", "children": [{"type": "text", "literal": "bold"}]},
        {"type": "text",   "literal": " and "},
        {"type": "code",   "literal": "code"},
        {"type": "text",   "literal": "."}
      ]
    }
  ]
}
```

**Output HTML:**
```html
<h2 id="hello">Hello</h2>
<p>This is <strong>bold</strong> and <code>code</code>.</p>
```
