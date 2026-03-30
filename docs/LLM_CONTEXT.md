# LLM Context: The `Marky` Architecture

This document serves as an operational map for LLMs navigating the codebase. Before modifying regex, injecting new parsing containers, or manipulating HTML output, read the structural axioms below.

## Foundational Pipeline
`Marky` uses a rigorous pipeline to avoid standard Markdown parser regex-overlap bugs:
1. `lexer.py` (+ `lex_token.py`) → Parses Block lines into 1D `Token` arrays.
2. `parser.py` (Block Parser) → Forms a relational `Node` Abstract Syntax Tree (AST).
3. `parser.py` (Inline Parser) → Re-calls the Lexer specifically on the `.string_content` of valid AST Nodes to extract inline nodes (`**bold**`, `[link]()`).
4. `node.py` → Flattens the AST into a strict JSON IR via `to_dict()`.
5. `html_renderer.py` → Recursively maps JSON IR to semantic HTML tags directly into a string buffer.
6. `compiler.py` → Bootstraps the pipeline, injecting the buffered HTML into `template.html`.

---

## Modifying the Codebase

If you are asked to implement a new Markdown feature (e.g. `<aside>`, footers, or admonitions), you must enact changes synchronously across the following 5 phases:

### Phase 1: `lex_token.py`
Add your new regex group into the appropriate dictionary:
- If it's a structural container (like `:::warning`), add it to `block_token_pattern`. Define opening `WARNING_FENCE` and closing `WARNING_CLOSE` variables.
- If it's inline text styling (like `::highlight::`), append it to `inline_token_pattern` and define `IL_WARNING`. Capture specific textual components sequentially in groups to assign as metadata.

### Phase 2: `lexer.py`
- Modify the `_tokenize_block()` or `tokenize_inline()` function to identify your newly matched class. 
- Pack any captured Regex group data into the `meta` dictionary constraint of the instantiated `Token` object.

### Phase 3: `parser.py`
Intercept the token stream iterating over `tokens`.
- **For blocks:** Build the semantic container. i.e., `node = Node('warning')`. Append it to the document using `self.doc.append_child(node)`. Move the AST pointer if required via `self.tip = node`.
- **For inlines:** Map `IL_WARNING` in `_token_to_node` to yield `Node('warning')` capturing `m['text']`. **Crucially**: If the block container holds formatted text, you *must* add your node's literal string name to the Tuple array sweep inside `process_inlines()` or the internal string will never tokenize into inline structures!

### Phase 4: `node.py`
This is where LLMs frequently err.
The HTML Renderer receives *nothing* beyond what `node.py` serializes in the `to_dict()` routine. 
If your parsed Node has a unique property (e.g., `node.alert_level = 'high'`), you must explicitly append it to the `d` dictionary:
```python
if hasattr(self, 'alert_level'):
    d['alert_level'] = self.alert_level
```

### Phase 5: `html_renderer.py`
Finally, intercept your named `node_type == 'warning'` inside `_render_node()`. Consume `node.get('alert_level')` and append the structural `<aside class="high">...</aside>` HTML into `self.buffer`. Loop over `node.get("children", [])` emitting inner elements using `self._render_node(child)` recursive callbacks.

---

## Known Anti-Patterns & Pitfalls
- **`import token` vs `import lex_token`**: Python ships with a standard library `token` module. In an earlier iteration, `token.py` shadowed the standard library, severely breaking tools like `trace`. The file was renamed to `lex_token.py`. Do not re-introduce module shadowing!
- **Merging Fence Parsing**: Custom ` ``` ` code fences close conditionally depending on their initial length. Do not attempt to Regex the entire block—`lexer.py` controls closing conditions (`MERMAID_CLOSE`, `CODE_FENCE_END`) implicitly inside the iteration scope to guarantee safe bounds.
- **Auto-Render Scripts**: Math rendering previously conflicted between `auto-render.js` sweeping the DOM and explicit class iteration. LaTeX compilation is purposely locked inside a single `DOMContentLoaded` `katex.render` loop targeting `.math` elements inside `template.html`. Do not attach global sweeping scripts.
