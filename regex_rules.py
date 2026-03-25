import re

class Token:
    __slots__ = ("type", "value", "meta", "indent")

    def __init__(self, type_: str, value: str, meta: dict | None = None, indent: int = 0):
        self.type   = type_ 
        self.value  = value   
        self.meta   = meta or {}
        self.indent = indent 

    def __repr__(self):
        return f"Token({self.type!r}, {self.value!r}, meta={self.meta})"


# Block token type constants

BLANK          = "BLANK"
PARAGRAPH      = "PARAGRAPH"
ATX_HEADING    = "ATX_HEADING"
THEMATIC_BREAK = "THEMATIC_BREAK"
BLOCKQUOTE     = "BLOCKQUOTE"
BULLET_LIST    = "BULLET_LIST"
ORDERED_LIST   = "ORDERED_LIST"
CODE_FENCE     = "CODE_FENCE"
CODE_FENCE_END = "CODE_FENCE_END"
MATH_FENCE     = "MATH_FENCE"
MATH_FENCE_END = "MATH_FENCE_END"
MERMAID_FENCE  = "MERMAID_FENCE"
MERMAID_CLOSE  = "MERMAID_CLOSE"
FOOTNOTE_DEF   = "FOOTNOTE_DEF"
DEF_LIST_MARKER= "DEF_LIST_MARKER"
TABLE_ROW      = "TABLE_ROW"
TABLE_SEP      = "TABLE_SEP"
HTML_BLOCK     = "HTML_BLOCK"
RAW_CONTENT    = "RAW_CONTENT"  

# Inline token type constants

IL_IMAGE        = "IL_IMAGE"
IL_LINK         = "IL_LINK"
IL_STRONG       = "IL_STRONG"
IL_EMPH         = "IL_EMPH"
IL_MARK         = "IL_MARK"
IL_UNDERLINE    = "IL_UNDERLINE"
IL_DEL          = "IL_DEL"
IL_SUB          = "IL_SUB"
IL_SUP          = "IL_SUP"
IL_CODE         = "IL_CODE"
IL_MATH         = "IL_MATH"
IL_FOOTNOTE_REF = "IL_FOOTNOTE_REF"
IL_EMOJI        = "IL_EMOJI"
IL_TASK         = "IL_TASK"
IL_HTML         = "IL_HTML"
IL_EMAIL_LINK   = "IL_EMAIL_LINK"
IL_URI_LINK     = "IL_URI_LINK"
IL_ENTITY       = "IL_ENTITY"
IL_HARDBREAK    = "IL_HARDBREAK"
IL_SOFTBREAK    = "IL_SOFTBREAK"
IL_ESCAPED      = "IL_ESCAPED"
IL_TEXT         = "IL_TEXT"


reHtmlBlockOpen = [
    re.compile(r'^<(?:script|pre|textarea|style)(?:\s|>|$)', re.IGNORECASE),
    re.compile(r'^<!--'),
    re.compile(r'^<\?'),
    re.compile(r'^<![A-Za-z]'),
    re.compile(r'^<!\[CDATA\['),
    re.compile(r'^</?(?:address|article|aside|base|basefont|blockquote|body|caption|center|col|colgroup|dd|details|dialog|dir|div|dl|dt|fieldset|figcaption|figure|footer|form|frame|frameset|h[123456]|head|header|hr|html|iframe|legend|li|link|main|menu|menuitem|nav|noframes|ol|optgroup|option|p|param|section|search|summary|table|tbody|td|tfoot|th|thead|title|tr|track|ul)(?:\s|/?>|$)', re.IGNORECASE),
    re.compile(r'^(?:<[A-Za-z][A-Za-z0-9-]*|</[A-Za-z][A-Za-z0-9-]*\s*>)\s*$', re.IGNORECASE)
]

block_token_pattern = re.compile(
    r'(?P<thematic_break>^(?:\*[ \t]*){3,}$|^(?:_[ \t]*){3,}$|^(?:-[ \t]*){3,}$)|'
    r'(?P<bullet_list>^\s*[*+-]\s+)|'
    r'(?P<ordered_list>^\s*(\d{1,9})[.)]\s+)|'
    r'(?P<atx_heading>^#{1,6}(?:[ \t]+|$))|'
    r'(?P<code_fence>^`{3,}(?!.*`)|^~{3,})|'
    r'(?P<math_fence>^\$\$[ \t]*$)|'
    r'(?P<mermaid_fence>^:::[ \t]+mermaid[ \t]*$)|'
    r'(?P<mermaid_close>^:::[ \t]*$)|'
    r'(?P<footnote_def>^\[\^([^\]]+)\]:[ \t]*(.*))|'
    r'(?P<def_list_marker>^:[ \t]+(.*))'
)

re_heading_id = re.compile(r'\{#([^}]+)\}\s*$')
re_line_ending = re.compile(r'\r\n|\n|\r')
re_table_sep = re.compile(r'^\|[ \t\-:|]+\|[ \t]*$')
re_footnote  = re.compile(r'^\[\^([^\]]+)\]:[ \t]*(.*)')
re_deflist   = re.compile(r'^:[ \t]+(.*)')
re_ol_num    = re.compile(r'\d+')

inline_token_pattern = re.compile(
    r'(!\[.*?\]\(.*?\))|'        # Image: ![alt](url)
    r'(\[.*?\]\(.*?\))|'         # Link: [label](url)
    r'(\*\*.*?\*\*|__.*?__)|'    # Strong: **text** or __text__
    r'(\*.*?\*|_.*?_)|'          # Emph: *text* or _text_
    r'(==.*?==)|'                # Highlight: ==text==
    r'(\+\+.*?\+\+)|'            # Underline: ++text++
    r'(~~.*?~~)|'                # Strikethrough: ~~text~~
    r'(~.*?~)|'                  # Subscript: ~text~
    r'(\^.*?\^)|'                # Superscript: ^text^
    r'(`+.*?`+)|'                # Code blocks inline
    r'(\$.*?\$)|'                # Inline Math: $equation$
    r'(\[\^[^\]]+\])|'           # Footnote Ref: [^label]
    r'(:[a-zA-Z0-9_\-]+:)|'      # Emoji Shortcode: :emoji:
    r'^(\[[ xX]\]|\[ \])|'       # Task list checkboxes at start: [x] or [ ]
    r'(<[A-Za-z/].*?>)|'         # HTML inline tags
    r'(<[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*>)|' # Email Autolink
    r'(<[a-zA-Z][a-zA-Z0-9+.-]{1,31}:[^<>\s]*>)|' # URL Autolink
    r'(&[#a-zA-Z0-9]+;)|'        # HTML Entity
    r'(  \n)|'                   # Hard line break
    r'(\\.)|'                    # Escaped char
    r'(\n)|'                     # Newlines
    r'([^!\[\]*_`<&\n\\=+\~^$: ]+)|' # Plain Text
    r'([!\[\]*_`<&\n\\=+\~^$: ])'    # Single special char fallback
)

CODE_INDENT = 4
