# Marky: Token & Regex Specification

The `lex_token.py` file defines the standard expressions to extract lexical items natively from Markdown arrays. By keeping complex Regex strictly inside the Lexer stage, the AST logic avoids catastrophic backtracking issues.

## 1. Block Level Regex (`block_token_pattern`)

The Block tokenizer runs line-by-line using a master regex with named capture groups.

| Token Group | Regex Pattern | Description |
| :--- | :--- | :--- |
| **thematic_break** | `^(?:\*[ \t]*){3,}$...` | Matches `---`, `***`, or `___` establishing horizontal rules (`<hr>`). |
| **bullet_list** | `^\s*[*+-]\s+` | Unordered list. Uses `indent` tracking for nesting depth. |
| **ordered_list** | `^\s*(\d{1,9})[.)]\s+` | Ordered list prefix. Captures the numeric prefix for `<ol>`. |
| **atx_heading** | `^#{1,6}(?:[ \t]+\|$)` | Matches 1 to 6 hash marks. Extracts level natively via length. |
| **code_fence** | ``^`{3,}(?!.*`)\|~{3,}`` | Opens a Code Block container. |
| **math_fence** | `^\$\$[ \t]*$` | Opens a LaTeX Block container. |
| **mermaid_fence** | `^:::[ \t]+mermaid[ \t]*$` | Opens a Mermaid diagram container. |
| **details_fence** | `^:::[ \t]*details(?:[ \t]+(.*))?[ \t]*$`| Captures `:::details Title` where Title maps to the `<summary>` property. |
| **mermaid_close** | `^:::[ \t]*$` | General `:::` fenced closer for diagram/details blocks. |
| **footnote_def** | `^\[\^([^\]]+)\]:[ \t]*(.*)` | Captures label and subsequent text. |
| **def_list_marker**| `^:[ \t]+(.*)` | Captures terms mapping to `<dd>`. |

### Boundary Tracking
Fenced closures for pure code (` ``` `) utilize dynamic exact matching within `lexer.py` rather than static Regex to guarantee accurate boundaries, resolving typical markdown trailing character bugs.

---

## 2. Inline Level Regex (`inline_token_pattern`)

Applied recursively on node `string_content`. Matches dictate token replacement parameters.

| Syntax | Token Name | Regex Pattern | Meta Keys Extracted |
| :--- | :--- | :--- | :--- |
| `&[a](b)` | **IL_AUDIO** | `(&\[.*?\]\(.*?\))` | `label` (a), `dest` (b) |
| `@[a](b)` | **IL_VIDEO** | `(@\[.*?\]\(.*?\))` | `label`, `dest` |
| `![a](b)` | **IL_IMAGE** | `(!\[.*?\]\(.*?\))` | `label`, `dest` |
| `[a](b)` | **IL_LINK** | `(\[.*?\]\(.*?\))` | `label`, `dest` |
| `**x**` | **IL_STRONG**| `(\*\*.*?\*\*\|__.*?__)` | `text` (x) |
| `*x*` | **IL_EMPH** | `(\*.*?\*\|_.*?_)` | `text` (x) |
| `==x==` | **IL_MARK** | `(==.*?==)` | `text` (x) |
| `++x++` | **IL_UNDERLINE** | `(\+\+.*?\+\+)` | `text` (x) |
| `~~x~~` | **IL_DEL** | `(~~.*?~~)` | `text` (x) |
| `~x~` | **IL_SUB** | `(~.*?~)` | `text` (x) |
| `^x^` | **IL_SUP** | `(\^.*?\^)` | `text` (x) |
| `` `x` `` | **IL_CODE** | ``(`+.*?`+)`` | `text` (x) |
| `$x$` | **IL_MATH** | `(\$.*?\$)` | `text` (x) |

### HTML & Edge Inlines
- **IL_HTML**: `(<[A-Za-z/].*?>)` safely captures native HTML tags passing through markdown compilation to the browser renderer directly.
- **IL_HARDBREAK**: Captures trailing double-spaces before newlines (`  \n`) for `<br>` elements.
- **IL_TEXT**: Extracts residual non-matched characters (`([^!\[\]*_`<&\\n\\=+\~^$: ]+)`) safely ensuring extreme iteration speeds over large strings.
