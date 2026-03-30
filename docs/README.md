# Marky: Markdown to HTML Compiler

`Marky` is a zero-dependency, rigorously designed Python compiler bridging Markdown dialects to fully functioning, highly styled semantic HTML. Built with pedagogical intent, it rejects monolithic regular expressions and complex state machines in favor of an easily hackable, multi-staged pipeline architecture.

Everything from LaTeX compilation, Mermaid diagram integration, Table architectures, to native HTML5 interactive `<details>` lists are supported and documented openly.

---

## 1. Project Philosophy

The primary objective behind `Marky` is predictable extraction. 
Traditionally, Markdown files are swept utilizing unreadable chained lookahead regexes that fail on edge cases. 
`Marky` separates execution into two immutable paths:
- **Phase A (Block Parsing)**: Establishes container layout. Defines the structural hierarchy recursively (e.g. `Document > List > ListItem > Paragraph`). Nested parsing handles scoping cleanly without string mutation.
- **Phase B (Inline Parsing)**: Operates strictly _inside_ the string contents populated by Phase A. This ensures a bold `**text**` pattern inside a codeblock isn't errantly executed. 

---

## 2. Compilation Stages

Executing the program via `python3 compiler.py <filename>.md` enacts five strict stages:

1. **Tokenization (Line Evaluation)**
    `lexer.py` ingests the file, iterating line by line evaluating against extraction dictionaries in `lex_token.py`. Results in arrays of Block Tokens (`PARAGRAPH`, `MERMAID_FENCE`, etc.).
2. **Abstract Syntax Tree (AST)** 
    `parser.py` consumes the Token array, creating relational `node.py` objects binding properties like `parent`, `first_child`, and `next_sibling`.
3. **Inline Extraction**
    Once block derivation is finished, the parser sweeps across nodes containing literal strings. `InlineParser` calls back to `lexer.py` sweeping the text for exact formats (`IL_STRONG`, `IL_CODE`), swapping the raw string value with distinct node elements.
4. **Intermediate Representation (JSON IR)**
    To act as a structural source of truth, `compiler.py` enforces a `to_dict()` cycle cascading down the root AST. This generates a strict, human-readable `<filename>.json` layout describing the compilation path deeply.
5. **Renderer Translation**
    The `html_renderer.py` module climbs over the JSON dictionary, injecting values into matching semantic HTML element strings.
    The resulting body matches against `template.html`, picking up the `style.css` configurations and rendering to the target `.html` file natively!

---

## 3. How to Use Marky

### Prerequisites
- Python 3.9+ 
- No `pip` installations required. Standard library only (`json`, `sys`, `os`, `re`, `urllib`).

### Running the Compiler
To process a file, call the entry script with your markdown route:

```bash
python3 compiler.py docs/test.md
```

The system will parse `test.md` and yield two outputs located precisely in the working folder:
- `test.json`: The fully evaluated Abstract Syntax Tree dictionary map.
- `test.html`: The fully formatted HTML document.

Open `test.html` in your browser. Styles are linked organically from the `style.css` within the same package directory ensuring instant reloading dynamics.

---

## 4. File Roster

- **`compiler.py`**: Execution glue binding templates, parser commands, and IO writing together.
- **`lex_token.py`**: Mathematical, standalone evaluation regex rules isolating text characteristics safely.
- **`lexer.py`**: The mechanism sweeping strings to apply `lex_token.py` configurations generating `Token()` classes. 
- **`parser.py`**: AST Builder routing Tokens into Node clusters. 
- **`node.py`**: The raw generic container defining hierarchy (`to_dict()`, `walker()`, `parent`). 
- **`html_renderer.py`**: Mapping IR classes back to actual HTML format tags (e.g. `<img/>`, `<table>`).
- **`template.html`**: Browser boilerplate housing dynamic KaTeX scripts, module logic, and the `__BODY_HTML__` injection zone.
- **`style.css`**: Completely independent, highly polished CSS formatting guidelines emulating professional system-font oriented documentation sites.
- **`docs/`**: Library folder containing explicit technical breakdowns (`grammar.md`, `tokens.md`) and operational tests (`test.md`).
