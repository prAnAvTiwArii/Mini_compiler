# Marky: Grammar Specification

The Marky compiler maps Markdown text to HTML using a structured, predictable context-free grammar. The parsing process is split into two distinct phases to avoid complex regex overlaps: Block Parsing and Inline Parsing.

---

## 1. Document Structure (Block Level)

The document is parsed top-down into a sequence of block elements. Fenced elements (like code blocks, math, and mermaid) act as opaque containers during this phase.

```ebnf
Document        ::= Block*

Block           ::= Paragraph 
                  | Heading 
                  | ThematicBreak 
                  | Blockquote 
                  | List 
                  | CodeBlock 
                  | MathBlock 
                  | MermaidBlock 
                  | DetailsBlock
                  | FootnoteDef 
                  | DefList 
                  | Table 
                  | HtmlBlock
                  | BlankLine

Paragraph       ::= Inline+
Heading         ::= ATX_HEADING Inline+

ThematicBreak   ::= THEMATIC_BREAK

Blockquote      ::= BLOCKQUOTE Block*

List            ::= ListItem+
ListItem        ::= LIST_MARKER Block*

CodeBlock       ::= CODE_FENCE RAW_CONTENT* CODE_FENCE_END
MathBlock       ::= MATH_FENCE RAW_CONTENT* MATH_FENCE_END
MermaidBlock    ::= MERMAID_FENCE RAW_CONTENT* MERMAID_CLOSE
DetailsBlock    ::= DETAILS_FENCE Inline* DETAILS_CLOSE

FootnoteDef     ::= FOOTNOTE_DEF Block*
DefList         ::= DEF_TERM DEF_DESC+
DEF_TERM        ::= Inline+
DEF_DESC        ::= DEF_LIST_MARKER Block*

Table           ::= TableHeader TableBody?
TableHeader     ::= TABLE_ROW TABLE_SEP
TableBody       ::= TABLE_ROW+
TABLE_ROW       ::= Inline+ (cells separated by '|')

HtmlBlock       ::= HTML_BLOCK RAW_CONTENT*
BlankLine       ::= BLANK
```

### Block Parsing Rules & Edge Cases
1. **Fenced Blocks**: When a fence opens (e.g. ````python`), all subsequent lines are swallowed unconditionally as `RAW_CONTENT` until the specific closing fence token is matched. Nested blocks are entirely ignored.
2. **Lists**: Lists map recursively. A `List` is a container of `ListItem`s, which can themselves contain `Paragraph`s, `List`s, or any other `Block`.
3. **Tables**: Tables strictly require a `TableHeader` consisting of a `TABLE_ROW` followed immediately by a `TABLE_SEP` (the `|---|` divider line). Subsequent `TABLE_ROW`s form the `TableBody`.

---

## 2. Text Formatting (Inline Level)

Once the block structure is established (the Abstract Syntax Tree is built), block elements designated as containing `string_content` (such as Paragraphs, Headings, and Details Blocks) are passed to the `InlineParser`. 

The `InlineParser` breaks the raw inner string into a flat sequence of inline tokens, which are converted to child nodes of the parent block.

```ebnf
Inline          ::= Text
                  | Image
                  | Video
                  | Audio
                  | Link
                  | Strong
                  | Emphasis
                  | Highlight
                  | Underline
                  | Strikethrough
                  | Subscript
                  | Superscript
                  | MathInline
                  | CodeInline
                  | FootnoteRef
                  | Emoji
                  | TaskCheckbox
                  | HardBreak
                  | SoftBreak
                  | HtmlInline

Image           ::= '![' Text ']' '(' URL ')'
Video           ::= '@[' Text ']' '(' URL ')'
Audio           ::= '&[' Text ']' '(' URL ')'
Link            ::= '[' Text ']' '(' URL ')'

Strong          ::= '**' Inline+ '**' | '__' Inline+ '__'
Emphasis        ::= '*' Inline+ '*' | '_' Inline+ '_'
Highlight       ::= '==' Inline+ '=='
Underline       ::= '++' Inline+ '++'
Strikethrough   ::= '~~' Inline+ '~~'
Subscript       ::= '~' Inline+ '~'
Superscript     ::= '^' Inline+ '^'

MathInline      ::= '$' RAW_CONTENT '$'
CodeInline      ::= '`' RAW_CONTENT '`'
FootnoteRef     ::= '[^' Text ']'
Emoji           ::= ':' Text ':'
TaskCheckbox    ::= '[ ]' | '[x]' | '[X]'

HtmlInline      ::= '<' RAW_CONTENT '>'
```

### Inline Parsing Rules
1. **Nesting**: Inline elements can be safely nested due to iterative recursive token building. A Strong node can wrap an Emphasis node: `**bold with *italic* inside**`.
2. **Passthrough HTML**: Any raw HTML tags encountered inline (like `<b>`, `<i>`, `<var>`) are parsed as `HtmlInline` and passed directly as text to the final renderer, allowing usage of standard HTML without Markdown syntax conflicts.
3. **Escaping**: Characters prefixed by `\` (e.g., `\*`) bypass inline tokenization entirely.
