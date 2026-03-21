import re

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

# Miscellaneous regexes that cannot be easily combined because they are used differently
reHeadingID = re.compile(r'\{#([^}]+)\}\s*$')
reLineEnding = re.compile(r'\r\n|\n|\r')

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
