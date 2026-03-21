# Markdown to HTML Compiler

A Python-based Markdown compiler that parses Markdown syntax into an Abstract Syntax Tree (AST), converts it to JSON intermediate representation (IR), and renders it to HTML with extensive formatting support.

## Project Overview

This project implements a **top-down recursive descent parser** that processes Markdown files with extensions and converts them into styled HTML output. It uses regex-based lexical analysis combined with an iterative state machine to build the parse tree.

## Architecture

```
Input (Markdown) 
    ↓
[Parser] - Block & Inline Parsing → AST (Node Tree)
    ↓
[Node] - Tree representation with JSON serialization
    ↓
[HtmlRenderer] - JSON IR → HTML tags
    ↓
Output (HTML file + JSON IR)
```

## Features

### Block-Level Elements
- **Headings** (ATX style: `# H1` to `###### H6`) with custom IDs (`{#custom-id}`)
- **Paragraphs**
- **Blockquotes** (`> text`)
- **Code Blocks** (fenced with ``` or ~~~ with language info)
- **Thematic Breaks** (`***`, `---`, `___`)
- **Lists** (bullet and ordered)
- **HTML Blocks** (raw HTML passthrough)
- **Footnote Definitions** (`[^label]: content`)
- **Definition Lists** (`:  definition`)
- **Math Blocks** (`$$..$$`)
- **Mermaid Diagrams** (`::: mermaid`)

### Inline Elements
- **Text Formatting**
  - Bold: `**text**` or `__text__`
  - Italic: `*text*` or `_text_`
  - Strikethrough: `~~text~~`
  - Underline: `++text++`
  - Mark/Highlight: `==text==`
  - Subscript: `~text~`
  - Superscript: `^text^`
  
- **Links & Images**
  - Links: `[label](url)`
  - Images: `![alt](url)`
  - Email autolinks: `<user@example.com>`
  - URL autolinks: `<https://example.com>`
  
- **Code & Math**
  - Inline code: `` `code` ``
  - Inline math: `$equation$`
  
- **Other**
  - Footnote references: `[^label]`
  - Emoji shortcuts: `:emoji_name:`
  - Task checkboxes: `[x]` or `[ ]`
  - HTML entities: `&amp;`
  - Hard breaks: two spaces + newline
  - Soft breaks: newline
  - Escaped characters: `\*`

## File Structure

### Core Modules

- **`parser.py`** - Main parsing logic
  - `Parser` class: Block-level parsing with two-phase approach (Phase 1: blocks, Phase 2: inlines)
  - `InlineParser` class: Processes inline tokens using regex patterns
  
- **`node.py`** - AST node representation
  - `Node` class: Tree structure with parent-child relationships, JSON serialization
  
- **`html_renderer.py`** - HTML output generation
  - `HtmlRenderer` class: Converts JSON IR to styled HTML with proper escaping
  
- **`regex_rules.py`** - Pattern definitions
  - Block-level token patterns
  - Inline token patterns
  - HTML block detection rules
  - Special regex patterns (heading IDs, line endings)
  
- **`compiler.py`** - Entry point
  - Orchestrates parsing, JSON generation, and HTML rendering
  - Arguments: input markdown file
  - Outputs: `.html` and `.json` files
  
- **`template.html`** - HTML template
  - Base template with styling
  - Placeholders: `__TITLE__` and `__BODY_HTML__`
  - Includes KaTeX CDN for math rendering

## Usage

```bash
python3 compiler.py input.md
```

**Output:**
- `input.html` - Rendered HTML file
- `input.json` - JSON intermediate representation (for debugging/inspection)

### Example

**Input (`example.md`):**
```markdown
# Hello World

This is a **bold** text with *italic* emphasis.

- Item 1
- Item 2
```

```python
def hello():
    print("world")
```

**Output:** 
- `example.html` - Beautiful styled webpage
- `example.json` - AST representation for analysis

## Parser Type Details

This is a **top-down recursive descent parser** with the following characteristics:

- **Single-pass, line-by-line processing**: Processes input sequentially
- **Two-phase parsing**: 
  1. Block structure parsing to create document hierarchy
  2. Inline element parsing within blocks
- **Regex-based pattern matching**: Uses combined regex with named groups
- **State machine approach**: Maintains parsing state across line processing
- **AST generation**: Builds Abstract Syntax Tree before rendering

## Dependencies

- Python 3.6+
- No external packages required (uses only standard library: `re`, `json`, `sys`, `os`, `html`, `urllib.parse`)

## JSON Intermediate Representation

The JSON output contains the complete AST structure:

```json
{
  "type": "document",
  "children": [
    {
      "type": "heading",
      "level": 1,
      "children": [
        {
          "type": "text",
          "literal": "Title"
        }
      ]
    },
    ...
  ]
}
```

This JSON can be:
- Inspected for debugging
- Used by external tools
- Transformed into different output formats

## Styling

The HTML output includes:
- Responsive design (max-width: 800px)
- Professional typography with system fonts
- Table styling with borders
- Code block syntax (ready for highlighting integration)
- Math rendering support via KaTeX

## Extensions Supported

- **Custom heading IDs**: `# Heading {#custom-id}`
- **Task lists**: `[x] Completed task`
- **Footnotes**: `[^1]` with definitions `[^1]: Footnote content`
- **Definition lists**: Terms with `: definition` entries
- **Math blocks**: `$$formula$$`
- **Mermaid diagrams**: `::: mermaid ... :::`

## Limitations & Notes

- Focus on block and inline structure parsing
- HTML escaping for security
- No external plugins/extensions framework
- Designed for educational purposes in compiler lab

## Future Enhancements

- Syntax highlighting for code blocks
- Smart typography (typographical quotes, em-dashes)
- Table of contents generation
- Citation/bibliography support
- Custom rendering backends beyond HTML

## Author

Pranav - Compiler Lab Project
