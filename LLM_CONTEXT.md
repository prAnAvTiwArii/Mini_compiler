# LLM Context: Markdown to HTML Compiler Project

## Quick Summary

This is a **Markdown-to-HTML compiler** implemented in Python. It parses Markdown with extensions (footnotes, math, definition lists, etc.) using a **top-down recursive descent parser**, converts it to an AST via Node objects, serializes to JSON, and renders to formatted HTML.

**Entry point:** `python3 compiler.py <markdown_file>`

## Parsing Pipeline

```
Input Markdown String
          ↓
   Parser.parse(text)
     (2-phase process)
          ↓
Phase 1: Block Parsing (Parser.incorporate_line)
- Line-by-line processing with regex pattern matching
- Detects: headings, code blocks, lists, blockquotes, math, footnotes, definitions
- Builds hierarchical block structure
- Stores inline content as string_content for Phase 2
          ↓
Phase 2: Inline Parsing (InlineParser.parse_inlines)
- Processes stored inline content with regex tokenization
- Creates nodes for: emphasis, strong, links, images, code, math, HTML, entities
- Populates AST with semantic meaning
          ↓
   Node Tree (AST)
          ↓
  node.to_json()
          ↓
  JSON IR (Intermediate Representation)
          ↓
 HtmlRenderer.render_json_ir()
          ↓
   Final HTML Output
```

## Key Classes & Responsibilities

### Parser (`parser.py`)
- **`__init__`**: Initializes document node and inline parser
- **`parse(text)`**: Main entry point - orchestrates two-phase parsing
- **`incorporate_line(line)`**: Phase 1 - identifies block types and builds structure
  - Uses `block_token_pattern` regex with named groups
  - Creates and manages node hierarchy
  - Handles block state (open/closed)
- **`process_inlines(node)`**: Triggers Phase 2 inline parsing
- **`_close_tip_if_paragraph()`**: Utility to close paragraph nodes

**State Variables:**
- `doc`: Root Node (document type)
- `tip`: Current open node being populated
- `current_line`: Line being processed
- `indent`: Indentation level
- `blank`: Whether line is empty
- `line_number`: For debugging/tracking

### InlineParser (`parser.py`)
- **`parse(block_node)`**: Entry for inline processing
- **`parse_inlines(block)`**: Tokenizes block.string_content using `inline_token_pattern`
- **`peek()`**: Peek at current character
- **`match(pattern)`**: Match regex at current position
- Creates child nodes for all inline elements (text, strong, emph, links, etc.)

**Supported Inline Nodes:**
- `text` (plain text)
- `strong`, `emph` (emphasis variants)
- `link`, `image` (with destination property)
- `code` (inline code)
- `mark`, `u`, `del`, `sub`, `sup` (formatting)
- `math_inline` (LaTeX equations)
- `footnote_ref` (references to footnotes)
- `emoji` (emoji shortcodes)
- `task_checkbox` (with checked property)
- `html_inline` (raw HTML)
- `hardbreak`, `softbreak` (line breaks)

### Node (`node.py`)
- **Tree structure**: parent, first_child, last_child, prev, next (doubly-linked)
- **Properties:**
  - `type`: node category (heading, paragraph, etc.)
  - `string_content`: raw text for block nodes (processed in Phase 2)
  - `literal`: text content for leaf nodes
  - `level`: heading level (1-6)
  - `destination`: link/image URL
  - `title`: link/image alt text
  - `custom_id`: heading ID from {#id}
  - `is_open`: whether block accepts new children
- **Methods:**
  - `append_child(child)`: Add child node
  - `unlink()`: Remove from tree
  - `insert_after(sibling)`: Structural manipulation
  - `to_json()`: Serializes to JSON string or dict

### HtmlRenderer (`html_renderer.py`)
- **Processes JSON IR** (from node.to_json())
- **`render_json_ir(ir_dict)`**: Main entry
- **`_render_node(node, tight=False)`**: Recursive rendering
- **`escape(text)`**: HTML entity escaping (prevents XSS)
- Handles all node types with proper HTML tags:
  - Block: `<h1-6>`, `<p>`, `<blockquote>`, `<ul>`, `<ol>`, `<div>`, etc.
  - Inline: `<strong>`, `<em>`, `<code>`, `<a>`, `<img>`, etc.
  - Special: Math via KaTeX, footnotes, custom IDs

## Regex Patterns (`regex_rules.py`)

### Block Token Pattern
Combined regex with named groups detecting:
- `thematic_break`: `***` or `---` or `___`
- `bullet_list`: `* `, `+ `, `- ` items
- `ordered_list`: `1. ` numbered items
- `atx_heading`: `# ` to `###### ` headings
- `code_fence`: ``` or ~~~ (3+ characters)
- `math_fence`: `$$`
- `mermaid_fence`: `::: mermaid`
- `mermaid_close`: `:::`
- `footnote_def`: `[^label]: content`
- `def_list_marker`: `: definition`

### Inline Token Pattern
Matches (in order of precedence):
1. Images: `![alt](url)`
2. Links: `[label](url)`
3. Strong: `**text**` or `__text__`
4. Emphasis: `*text*` or `_text_`
5. Highlight: `==text==`
6. Underline: `++text++`
7. Strikethrough: `~~text~~`
8. Subscript: `~text~`
9. Superscript: `^text^`
10. Code: `` `code` ``
11. Math: `$equation$`
12. Footnote refs: `[^label]`
13. Emojis: `:name:`
14. Task checkboxes: `[x]` or `[ ]`
15. HTML tags: `<tag>`
16. Email autolinks: `<email@example.com>`
17. URL autolinks: `<https://url>`
18. HTML entities: `&amp;`
19. Hard breaks: two spaces + newline
20. Escaped chars: `\*`
21. Plain text and single special chars

### Special Patterns
- `reHeadingID`: `{#custom-id}` in headings
- `reLineEnding`: `\r\n`, `\n`, or `\r` normalization
- `reHtmlBlockOpen`: 7 rules for HTML block detection

## Compiler Entry Point (`compiler.py`)

```python
def main():
    # 1. Read markdown file from argv[1]
    # 2. Parser().parse(text) → AST
    # 3. ast.to_json() → JSON IR
    # 4. HtmlRenderer().render_json_ir(ir) → HTML body
    # 5. Load template.html
    # 6. Replace __TITLE__ and __BODY_HTML__
    # 7. Write output.<md>.html and output.<md>.json
```

**Output Files:**
- `<name>.html`: Final rendered HTML (from template)
- `<name>.json`: JSON IR for inspection/debugging

## Template System (`template.html`)

- Standard HTML5 structure
- Placeholders: `__TITLE__` (from filename) and `__BODY_HTML__` (from renderer)
- Includes KaTeX CDN for math rendering
- CSS styling for body, tables, code blocks, etc.
- Responsive design (max-width: 800px)

## Block Parsing Logic (Key Algorithm)

For each line:

1. **Strip leading whitespace** → measure indent
2. **Match against `block_token_pattern`** → determine block type
3. **Handle block-specific rules:**
   - Blockquote: `>` prefix → create/append to bq node
   - Heading: `#` prefix → create heading, close paragraph
   - Code fence: ``` → open code block in state, wait for closing fence
   - List item: `* ` or `1. ` → create list item
   - Footnote: `[^label]:` → create footnote_def node
   - Definition: `:  ` → convert previous paragraph to def term
4. **Manage node state:**
   - Update `self.tip` (current open node)
   - Set `is_open = True` for blocks accepting children
   - Close blocks when new block starts at same or lower indent

## Inline Parsing Logic

For each block with `string_content`:

1. **Tokenize** using `inline_token_pattern.finditer()`
2. **For each token**, check type by pattern:
   - Images/links: extract label and URL, create node
   - Formatting: check delimiters, extract content
   - Code: count backticks, strip matching count
   - Autolinks: detect email vs URL, add mailto: prefix
   - Special nodes: math, emoji, footnote refs
   - Fallback: plain text node
3. **Append nodes** to parent block node

## Important Design Decisions

1. **Two-phase parsing**: Separates structural parsing from content parsing
2. **String deferral**: Block parsing stores inline content as string_content, processed later
3. **Regex-based lexing**: No traditional tokenizer; patterns handle tokenization
4. **Single regex per phase**: Combined patterns for efficiency
5. **Named groups**: Used to identify token type without secondary matching
6. **Node tree first**: JSON and HTML generated from validated AST
7. **JSON intermediate**: Enables non-HTML backends and inspection

## Common Modifications

### Add a new block type:
1. Add pattern to `block_token_pattern` in `regex_rules.py`
2. Add condition in `Parser.incorporate_line()`
3. Create node with appropriate properties
4. Add rendering logic to `HtmlRenderer._render_node()`

### Add a new inline element:
1. Add pattern to `inline_token_pattern` in `regex_rules.py`
2. Add condition in `InlineParser.parse_inlines()`
3. Extract content and create node
4. Add rendering case in `HtmlRenderer._render_node()`

### Change HTML output:
1. Modify `HtmlRenderer._render_node()` for specific node type
2. Adjust `template.html` styling

## Debugging Tips

- Check `output.json` to see AST structure
- Verify `block_token_pattern.match()` output for parsing issues
- Use `node.to_json(as_dict=True)` to inspect node properties
- Add print statements in `incorporate_line()` or `parse_inlines()` to trace execution

## Testing Files

The workspace includes:
- `test.md`: Sample markdown input
- `test.html`: Expected HTML output
- `test.json`: Expected JSON IR

## Performance Notes

- Linear time complexity: O(n) where n = input length
- Single-pass block parsing
- Regex overhead for pattern matching (acceptable for markdown-sized inputs)
- No heavy dependencies (pure Python stdlib)

---

**Last Updated:** March 2026
**Project Type:** Compiler Lab - Educational Markdown Compiler
