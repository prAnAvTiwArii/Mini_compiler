# Grammar Reference

This document specifies the complete formal grammar of the Markdown dialect recognised by Mini_Compiler, describes the parser strategy, and provides a YACC/PLY-compatible grammar file that captures the block and inline production rules.

---

## Parser Type

Mini_Compiler uses a **hand-written, top-down, single-pass** parser. It is best described as an **incremental top-down parser with a "tip" cursor**.

Key properties:

- **Single pass over the token list.** The lexer produces the full token list first; the parser then processes tokens one at a time in order.
- **Tip pointer.** The parser maintains a `tip` pointer to the currently open deepest node. New tokens are incorporated either into `tip` or as new siblings/ancestors of `tip`.
- **No backtracking.** Every token classification is deterministic. There are no lookahead conflicts.
- **Context-sensitive list nesting.** List nesting is resolved at parse time by comparing the `indent` field of incoming list tokens against the `indent` stored on open list nodes.
- **Two-phase inline expansion.** Inline content is stored as raw `string_content` during block parsing. After all block tokens are consumed, a second pass calls `InlineParser` on every content-holding node.

---

## Block Grammar

The following BNF describes the block-level grammar. Terminal symbols correspond directly to `Token.type` constants.

```bnf
document        ::= block*

block           ::= heading
                  | paragraph
                  | thematic_break
                  | block_quote
                  | list
                  | code_block
                  | math_block
                  | mermaid_block
                  | details_block
                  | table
                  | footnote_def
                  | def_list
                  | html_block
                  | BLANK

heading         ::= ATX_HEADING

paragraph       ::= PARAGRAPH (PARAGRAPH)*

thematic_break  ::= THEMATIC_BREAK

block_quote     ::= BLOCKQUOTE (BLOCKQUOTE)*

list            ::= list_item+

list_item       ::= (BULLET_LIST | ORDERED_LIST) paragraph? list?

code_block      ::= CODE_FENCE RAW_CONTENT* CODE_FENCE_END

math_block      ::= MATH_FENCE RAW_CONTENT* MATH_FENCE_END

mermaid_block   ::= (MERMAID_FENCE | CODE_FENCE<info=mermaid>)
                    RAW_CONTENT*
                    (MERMAID_CLOSE | CODE_FENCE_END)

details_block   ::= DETAILS_FENCE RAW_CONTENT* MERMAID_CLOSE

table           ::= TABLE_ROW+ TABLE_SEP TABLE_ROW*

footnote_def    ::= FOOTNOTE_DEF paragraph?

def_list        ::= paragraph DEF_LIST_MARKER+

html_block      ::= HTML_BLOCK (non-BLANK token)* BLANK
```

---

## Inline Grammar

Inline content is stored in `node.string_content` during block parsing and then parsed by `InlineParser`. The inline grammar is:

```bnf
inline_content  ::= inline_token*

inline_token    ::= audio
                  | video
                  | image
                  | link
                  | strong
                  | emph
                  | mark
                  | underline
                  | strikethrough
                  | subscript
                  | superscript
                  | code_span
                  | math_inline
                  | footnote_ref
                  | emoji
                  | task_checkbox
                  | autolink_email
                  | autolink_uri
                  | html_inline
                  | html_entity
                  | hardbreak
                  | softbreak
                  | escaped_char
                  | text

audio           ::= IL_AUDIO                    /* &[caption](url) */
video           ::= IL_VIDEO                    /* @[caption](url) */
image           ::= IL_IMAGE                    /* ![alt](url)     */
link            ::= IL_LINK                     /* [label](url)    */
strong          ::= IL_STRONG                   /* **…** or __…__  */
emph            ::= IL_EMPH                     /* *…* or _…_      */
mark            ::= IL_MARK                     /* ==…==           */
underline       ::= IL_UNDERLINE                /* ++…++           */
strikethrough   ::= IL_DEL                      /* ~~…~~           */
subscript       ::= IL_SUB                      /* ~…~             */
superscript     ::= IL_SUP                      /* ^…^             */
code_span       ::= IL_CODE                     /* `…`             */
math_inline     ::= IL_MATH                     /* $…$             */
footnote_ref    ::= IL_FOOTNOTE_REF             /* [^label]        */
emoji           ::= IL_EMOJI                    /* :name:          */
task_checkbox   ::= IL_TASK                     /* [x] or [ ]      */
autolink_email  ::= IL_EMAIL_LINK               /* <user@host>     */
autolink_uri    ::= IL_URI_LINK                 /* <scheme:path>   */
html_inline     ::= IL_HTML                     /* <tag>           */
html_entity     ::= IL_ENTITY                   /* &name; &#n;     */
hardbreak       ::= IL_HARDBREAK                /* two spaces + \n */
softbreak       ::= IL_SOFTBREAK                /* bare \n         */
escaped_char    ::= IL_ESCAPED                  /* \char           */
text            ::= IL_TEXT                     /* plain text      */
```

---

## YACC / PLY Grammar File

The following is a PLY (Python Lex-Yacc) compatible grammar that captures the block-level structure. It can be used to build a parse table with `yacc.yacc()`. Note that the actual Mini_Compiler parser does not use YACC — this is provided as a formal specification.

```python
# Mini_Compiler block grammar for PLY
# tokens list must include all terminal symbols below

tokens = (
    'BLANK', 'PARAGRAPH', 'ATX_HEADING', 'THEMATIC_BREAK',
    'BLOCKQUOTE', 'BULLET_LIST', 'ORDERED_LIST',
    'CODE_FENCE', 'CODE_FENCE_END', 'MATH_FENCE', 'MATH_FENCE_END',
    'MERMAID_FENCE', 'MERMAID_CLOSE', 'DETAILS_FENCE',
    'FOOTNOTE_DEF', 'DEF_LIST_MARKER',
    'TABLE_ROW', 'TABLE_SEP',
    'HTML_BLOCK', 'RAW_CONTENT',
)

# ── Document ──────────────────────────────────────────────────────────────────

def p_document(p):
    '''document : block_list'''
    p[0] = ('document', p[1])

def p_block_list(p):
    '''block_list : block_list block
                  | block
                  | empty'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    elif p[1] is None:
        p[0] = []
    else:
        p[0] = [p[1]]

# ── Block ─────────────────────────────────────────────────────────────────────

def p_block(p):
    '''block : heading
             | paragraph
             | thematic_break
             | block_quote
             | list
             | code_block
             | math_block
             | mermaid_block
             | details_block
             | table
             | footnote_def
             | def_list
             | html_block
             | BLANK'''
    p[0] = p[1]

# ── Heading ───────────────────────────────────────────────────────────────────

def p_heading(p):
    '''heading : ATX_HEADING'''
    p[0] = ('heading', p[1])

# ── Paragraph ─────────────────────────────────────────────────────────────────

def p_paragraph(p):
    '''paragraph : para_lines'''
    p[0] = ('paragraph', p[1])

def p_para_lines(p):
    '''para_lines : para_lines PARAGRAPH
                  | PARAGRAPH'''
    if len(p) == 3:
        p[0] = p[1] + '\n' + p[2]
    else:
        p[0] = p[1]

# ── Thematic break ────────────────────────────────────────────────────────────

def p_thematic_break(p):
    '''thematic_break : THEMATIC_BREAK'''
    p[0] = ('thematic_break',)

# ── Blockquote ────────────────────────────────────────────────────────────────

def p_block_quote(p):
    '''block_quote : bq_lines'''
    p[0] = ('block_quote', p[1])

def p_bq_lines(p):
    '''bq_lines : bq_lines BLOCKQUOTE
                | BLOCKQUOTE'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

# ── Lists ─────────────────────────────────────────────────────────────────────

def p_list(p):
    '''list : list list_item
            | list_item'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_list_item_bullet(p):
    '''list_item : BULLET_LIST'''
    p[0] = ('item', p[1])

def p_list_item_ordered(p):
    '''list_item : ORDERED_LIST'''
    p[0] = ('item', p[1])

# ── Code block ────────────────────────────────────────────────────────────────

def p_code_block(p):
    '''code_block : CODE_FENCE raw_content CODE_FENCE_END'''
    p[0] = ('code_block', p[1], p[2])

def p_raw_content(p):
    '''raw_content : raw_content RAW_CONTENT
                   | empty'''
    if len(p) == 3:
        p[0] = p[1] + p[2]
    else:
        p[0] = ''

# ── Math block ────────────────────────────────────────────────────────────────

def p_math_block(p):
    '''math_block : MATH_FENCE raw_content MATH_FENCE_END'''
    p[0] = ('math_block', p[2])

# ── Mermaid block ─────────────────────────────────────────────────────────────

def p_mermaid_block_colon(p):
    '''mermaid_block : MERMAID_FENCE raw_content MERMAID_CLOSE'''
    p[0] = ('mermaid_block', p[2])

def p_mermaid_block_fence(p):
    '''mermaid_block : CODE_FENCE raw_content CODE_FENCE_END'''
    p[0] = ('mermaid_block', p[2])

# ── Details block ─────────────────────────────────────────────────────────────

def p_details_block(p):
    '''details_block : DETAILS_FENCE raw_content MERMAID_CLOSE'''
    p[0] = ('details', p[1], p[2])

# ── Table ─────────────────────────────────────────────────────────────────────

def p_table(p):
    '''table : header_rows TABLE_SEP body_rows'''
    p[0] = ('table', p[1], p[3])

def p_header_rows(p):
    '''header_rows : header_rows TABLE_ROW
                   | TABLE_ROW'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

def p_body_rows(p):
    '''body_rows : body_rows TABLE_ROW
                 | empty'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = []

# ── Footnote definition ───────────────────────────────────────────────────────

def p_footnote_def(p):
    '''footnote_def : FOOTNOTE_DEF'''
    p[0] = ('footnote_def', p[1])

# ── Definition list ───────────────────────────────────────────────────────────

def p_def_list(p):
    '''def_list : paragraph def_markers'''
    p[0] = ('def_list', p[1], p[2])

def p_def_markers(p):
    '''def_markers : def_markers DEF_LIST_MARKER
                   | DEF_LIST_MARKER'''
    if len(p) == 3:
        p[0] = p[1] + [p[2]]
    else:
        p[0] = [p[1]]

# ── HTML block ────────────────────────────────────────────────────────────────

def p_html_block(p):
    '''html_block : HTML_BLOCK html_continuation BLANK'''
    p[0] = ('html_block', p[1] + p[2])

def p_html_continuation(p):
    '''html_continuation : html_continuation PARAGRAPH
                         | html_continuation ATX_HEADING
                         | empty'''
    if len(p) == 3:
        p[0] = p[1] + '\n' + p[2]
    else:
        p[0] = ''

# ── Empty / epsilon ───────────────────────────────────────────────────────────

def p_empty(p):
    '''empty :'''
    p[0] = None

def p_error(p):
    raise SyntaxError(f"Unexpected token: {p}")
```

---

## Inline Grammar — YACC Representation

Inline tokens are not processed by YACC in Mini_Compiler (they are handled by `InlineParser`). The following is a formal representation for reference:

```python
inline_tokens = (
    'IL_AUDIO', 'IL_VIDEO', 'IL_IMAGE', 'IL_LINK',
    'IL_STRONG', 'IL_EMPH', 'IL_MARK', 'IL_UNDERLINE',
    'IL_DEL', 'IL_SUB', 'IL_SUP', 'IL_CODE', 'IL_MATH',
    'IL_FOOTNOTE_REF', 'IL_EMOJI', 'IL_TASK',
    'IL_EMAIL_LINK', 'IL_URI_LINK', 'IL_HTML', 'IL_ENTITY',
    'IL_HARDBREAK', 'IL_SOFTBREAK', 'IL_ESCAPED', 'IL_TEXT',
)

def p_inline_content(p):
    '''inline_content : inline_content inline_token
                      | inline_token
                      | empty'''

def p_inline_token(p):
    '''inline_token : IL_AUDIO
                    | IL_VIDEO
                    | IL_IMAGE
                    | IL_LINK
                    | IL_STRONG
                    | IL_EMPH
                    | IL_MARK
                    | IL_UNDERLINE
                    | IL_DEL
                    | IL_SUB
                    | IL_SUP
                    | IL_CODE
                    | IL_MATH
                    | IL_FOOTNOTE_REF
                    | IL_EMOJI
                    | IL_TASK
                    | IL_EMAIL_LINK
                    | IL_URI_LINK
                    | IL_HTML
                    | IL_ENTITY
                    | IL_HARDBREAK
                    | IL_SOFTBREAK
                    | IL_ESCAPED
                    | IL_TEXT'''
    p[0] = p[1]
```

---

## Operator Precedence and Ambiguity Notes

- **Media > Image > Link:** The lexer tests `&[` before `![` before `[`, so there is no ambiguity between audio, video, image, and link syntax.
- **Strong > Emph:** `**` is tested before `*`, so `**bold**` is never mis-parsed as two emphasis markers.
- **Del > Sub:** `~~` is tested before `~`, so `~~strike~~` is never mis-parsed as two subscript markers.
- **List nesting** is resolved at parse time by comparing `indent` values, not by grammar rules — it is a context-sensitive disambiguation.
- **Table vs Paragraph:** A line starting and ending with `|` is always a table row or separator; it is never a paragraph.
- **HTML block continuation:** An open `html_block` consumes all subsequent non-blank lines until a blank line closes it.
