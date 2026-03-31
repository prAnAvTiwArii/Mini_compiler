# LLM Context: pyV2 Markdown-to-HTML Compiler

## Overview
This repository contains a full-featured, sophisticated **Markdown-to-HTML Compiler** implemented in Python. It includes a modern, web-based interactive interface built with Flask that visualizes the entire 5-phase compiler pipeline, offering a "glass box" transparent view of the compilation process. This makes it an excellent educational and debugging tool for compiler theory, adapting standard compiler architecture to markdown compilation.

## Architecture and Compiler Pipeline
The compiler strictly follows a standard multi-phase compilation pipeline:

1. **Phase 1: Lexical Analysis** (`lexer.py` & `lex_token.py`): Scans raw Markdown characters and groups them into meaningful `Token` objects.
2. **Phase 2: Syntax Analysis (Parsing)** (`parser.py`): Parses the 1D token stream using top-down recursive descent to build a hierarchical Abstract Syntax Tree (AST).
3. **Phase 2.5: Parse Tree (CST) Generation** (`cst_visualizer.py` & `grammar.txt`): Maps the AST to formal context-free grammar rules to build a Concrete Syntax Tree (CST) for visualization.
4. **Phase 3: Semantic Analysis** (`semantic_analyzer.py`): Traverses the AST to validate logic that cannot be enforced by grammar alone (e.g., semantic validation, symbol table collection).
5. **Phase 4: Intermediate Representation (IR)** (`node.py`): Serializes the AST into a structured JSON IR representation.
6. **Phase 5: Code Generation** (`html_renderer.py`): Transforms the validated AST / IR into valid output HTML.

---

## Complete File Directory Breakdown & Deep Explanation

### Backend / Core Logic
- **`app.py`**: The main entry point for the Flask web application. It defines the HTTP routes (`/`, `/compile`, `/parse-tree`), handles API requests from the frontend, coordinates the execution of the entire compiler pipeline, and serves the static templates.
- **`compiler.py`**: The core orchestrator. This file defines a central `Compiler` class that ties together the lexer, parser, analyzer, and renderer into a single, cohesive processing pipeline. It can also act as the CLI entry point.

### Compiler Phases
- **`lex_token.py`**: Defines the data structures for Lexical Analysis. Contains the `Token` class and `TokenType` enumerations. Tokens are the atomic units passed between the lexer and parser.
- **`lexer.py`**: Implements the `Lexer` class. It reads raw Markdown text character-by-character (or line-by-line) and creates a token stream. It is state-aware, capable of tokenizing complex block structures like fenced code blocks, math blocks, and handling lazy inline sub-tokenization.
- **`parser.py`**: Implements the `Parser` class. It consumes the token stream to build the **Abstract Syntax Tree (AST)**. Designed primarily as a recursive-descent parser, it separates the concerns of parsing blocks (paragraphs, lists) and parsing inline elements (bold, links).
- **`node.py`**: Defines the standard AST Node structures used throughout the pipeline. Includes the base `Node` definition (typically implemented as a doubly-linked list or n-ary tree format with children arrays) and specific subclasses representing various Markdown elements. It forms the structure of the Intermediate Representation (IR).
- **`semantic_analyzer.py`**: Walks the AST to perform context-sensitive validation. Responsibilities include:
  - Checking heading hierarchies (preventing jumps from H1 to H3).
  - Security checks (blocking unsafe URIs like `javascript:`).
  - Validating footnotes (ensuring references match definitions).
  - Building a symbol table of links, headers, and specific document metadata.
- **`html_renderer.py`**: The Code Generator. Once the AST is semantically validated, this script traverses the tree using the Visitor pattern (or similar) to evaluate the nodes and construct the final, well-formatted HTML output string.

### Formal Grammar & Visualizations
- **`grammar.txt`**: A declarative text file describing the formal Context-Free Grammar (CFG) for the Markdown subset. It is designed around **right-recursive chaining** to prevent trees from rendering too flat or wide.
- **`ast_visualizer.py`**: A utility that serializes the AST into a specific JSON layout optimized for D3.js visualization. It formats the data for a horizontal tree layout.
- **`cst_visualizer.py`**: Generates JSON for the **Concrete Syntax Tree**. It maps the generated AST explicitly against the rules in `grammar.txt`, generating strict top-down, right-recursive, binary-like derivation paths.

### Frontend Web UI
- **`templates/index.html`**: The main frontend view. Provides the HTML skeleton for the editor, output panels, and D3 visualization containers. It handles tab switching and triggers AJAX calls to `app.py`.
- **`templates/template.html`**: A baseline HTML template shell into which compiled HTML is injected when generating standalone output documents.
- **`static/style.css`**: The design system for the application. Implements a modern, dark-themed, glassmorphic UI with vibrant accents, responsive layout, and interactive micro-animations to create a premium developer tool aesthetic.

### Other Folders
- **`markdowns/`**: Directory meant to hold source Markdown (`.md`) files for testing and context (this file itself lives here).
- **`outputs/`**: Target directory where the compiler may save generated compiled files (`.html` or `.json`).
- **`docs/`**: Project documentation or additional generated data.

## Tips for Working on This Codebase
- **Testing Logic**: To test compiler logic independently of the web UI, you can use `compiler.py` directly on files in the `markdowns/` folder.
- **Modifying Grammar**: If adding new markdown syntax (e.g., tables or custom admonitions), you must:
   1. Add the token in `lex_token.py` and logic in `lexer.py`.
   2. Add the formal rule to `grammar.txt`.
   3. Update `parser.py` to create the AST nodes.
   4. Update `cst_visualizer.py` to recognize the new logic.
   5. Update `html_renderer.py` to render the new HTML tags.
- **Frontend Sync**: The frontend heavily relies on exact JSON shapes for its visualizers and analysis tables. Ensure any changes to `cst_visualizer.py` or `semantic_analyzer.py` output are mirrored in frontend JavaScript expectations.
