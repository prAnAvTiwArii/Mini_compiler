# LLM Context: Markdown to HTML Compiler Project

## Project Overview
This project is a sophisticated **Markdown-to-HTML Compiler** implemented in Python. Beyond standard compilation, it features a modern, interactive web interface (Flask) that visualizes the full 5-phase compiler pipeline, along with two distinct tree visualizations: an **Abstract Syntax Tree (AST)** and a **Concrete Syntax Tree (CST/Parse Tree)**.

## Project Goal
The primary goal is to demonstrate formal compiler design principles (lexing, parsing, semantics, IR, and codegen) while providing a "glass box" view of how Markdown is transformed into HTML.

---

## The Compiler & Visualization Pipeline

1.  **Phase 1: Lexical Analysis** (`lexer.py`): Scans raw Markdown and produces a 1D stream of `Token` objects.
2.  **Phase 2: Syntax Analysis (AST Parsing)** (`parser.py`): A top-down recursive descent parser that builds a hierarchical **Abstract Syntax Tree (AST)**.
3.  **Phase 2.5: CST Generation** (`cst_visualizer.py`): Maps the AST back to the formal grammar rules defined in `grammar.txt` to produce a **Concrete Syntax Tree (Parse Tree)**. 
    *   *Design Note*: This tree is structured to be **vertical** (max 2 children per node) using right-recursive chaining.
4.  **Phase 3: Semantic Analysis** (`semantic_analyzer.py`): Validates the AST (heading levels, footnote references, security safe-links) and collects document statistics.
5.  **Phase 4: IR Generation** (`node.py`): Serializes the AST into a structured **JSON Intermediate Representation (IR)**.
6.  **Phase 5: Code Generation** (`html_renderer.py`): Transforms the JSON IR into final, valid HTML.

---

## Directory Structure

```text
pyV/
├── app.py                  # Main entry point for the Flask Web UI (Routes: /, /compile, /parse-tree)
├── compiler.py             # CLI entry point for the compiler
├── lexer.py                # Phase 1: Lexical Analysis logic
├── parser.py               # Phase 2: Block and Inline Parsing logic
├── semantic_analyzer.py    # Phase 3: Semantic Analysis & Validation
├── html_renderer.py        # Phase 5: HTML Code Generation logic
├── node.py                 # AST Node definitions & Phase 4: IR logic
├── grammar.txt             # Formal Grammar definition (Right-Recursive / Vertical Chaining)
├── regex_rules.py          # Centralized repository of regex patterns
├── ast_visualizer.py       # Utility for D3.js AST visualization (Horizontal layout)
├── cst_visualizer.py       # Utility for D3.js CST visualization (Vertical layout, Chained nodes)
├── markdowns/              # Source content (.md files)
├── outputs/                # Generated compiler output (.html and .json)
├── static/                 # Web assets (CSS, JS)
└── templates/              # HTML Templates (index.html, template.html)
```

---

## Formal Grammar & Tree Layout (`grammar.txt`)
The project uses a specific grammar design to ensure visualizations are readable:
- **Vertical Chaining**: To avoid "flat/wide" trees in D3.js, the grammar was restructured from flat lists (`A -> B B B`) to right-recursive chains (`A -> B A'`).
- **Max 2 Children**: Each non-terminal in the CST typically has at most 2 children, creating a deep "spine" structure reminiscent of binary trees or LALR derivation paths.
- **Rules**: Defines strict derivations for `Document`, `BlockList`, `InlineList`, `Heading`, `List`, `Table`, etc.

---

## Technical Features

### Lexical Analysis (`lexer.py`)
- Lazy sub-tokenization for inline elements.
- State tracking for fenced blocks (Code, Math, Mermaid).

### Semantic Analysis (`semantic_analyzer.py`)
- **Heading Hierarchy**: Warns if skipping levels (e.g., H1 followed immediately by H3).
- **Security Check**: Blocks `javascript:` and `data:` URIs in links/images.
- **Footnotes**: Validates that every reference has a corresponding definition.

### Visualizations (`D3.js`)
- **AST**: A horizontal, hierarchical tree showing the abstract structure.
- **CST**: A vertical, top-down tree showing the formal grammatical expansion.
- **Interactivity**: Both trees support node clicking for expand/collapse, global Expand/Collapse All buttons, and smooth transitions.

---

## Web UI & API
- **`/compile`**: Full pipeline execution returning tokens, AST, analysis, IR, and HTML.
- **`/parse-tree`**: Specific endpoint for generating the CST JSON.
- **Premium Design**: Dark-themed "modern dev tool" aesthetic with glassmorphism, micro-animations, and real-time compilation (Ctrl+Enter).

---

## How to Interact
- **Compiling**: Paste markdown → Click Compile.
- **Navigating**: Use tabs to switch between pipeline stages.
- **Refactoring**: If modifying grammar, update `grammar.txt` first, then ensure `cst_visualizer.py` reflects the new chaining logic.

**Last Updated:** March 2026

