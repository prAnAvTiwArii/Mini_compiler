from regex_rules import *

class Lexer:

    def tokenize(self, text: str) -> list:
        lines = re_line_ending.split(text)
        if text and text[-1] == '\n':
            lines.pop()

        tokens: list[Token] = []

        in_fence = False         
        fence_block_type = None  
        fence_char = None      
        fence_length = 0

        for line in lines:
            stripped = line.lstrip()
            indent   = len(line) - len(stripped)
            blank    = len(stripped) == 0

            block_match = block_token_pattern.match(stripped)
            bg = block_match.lastgroup if block_match else None

            # inside a fenced block
            if in_fence:
                if fence_block_type == 'code_block':
                    if bg == 'code_fence' and block_match.group('code_fence')[0] == fence_char \
                            and len(block_match.group('code_fence')) >= fence_length:
                        tokens.append(Token(CODE_FENCE_END, stripped, indent=indent))
                        in_fence = False
                        continue

                elif fence_block_type == 'math_block':
                    if bg == 'math_fence':
                        tokens.append(Token(MATH_FENCE_END, stripped, indent=indent))
                        in_fence = False
                        continue

                elif fence_block_type == 'mermaid_block':
                    if bg == 'mermaid_close':
                        tokens.append(Token(MERMAID_CLOSE, stripped, indent=indent))
                        in_fence = False
                        continue

                tokens.append(Token(RAW_CONTENT, line, indent=indent))
                continue

            # blank line 
            if blank:
                tokens.append(Token(BLANK, line, indent=indent))
                continue

            # blockquote 
            if stripped.startswith('>'):
                content = stripped[1:]
                if content.startswith(' '):
                    content = content[1:]
                tokens.append(Token(BLOCKQUOTE, stripped,
                                    meta={'content': content}, indent=indent))
                continue

            # ATX heading 
            if bg == 'atx_heading':
                level      = len(block_match.group('atx_heading').strip())
                raw_content = stripped[level:].strip().rstrip('#').strip()
                id_match   = re_heading_id.search(raw_content)
                custom_id  = None
                if id_match:
                    custom_id   = id_match.group(1)
                    raw_content = raw_content[:id_match.start()].strip()
                tokens.append(Token(ATX_HEADING, stripped,
                                    meta={'level': level, 'content': raw_content,
                                          'custom_id': custom_id},
                                    indent=indent))
                continue

            # thematic break
            if bg == 'thematic_break':
                tokens.append(Token(THEMATIC_BREAK, stripped, indent=indent))
                continue

            # footnote definition 
            if bg == 'footnote_def':
                m = re_footnote.match(stripped)
                label, content = (m.group(1), m.group(2)) if m else ("unknown", "")
                tokens.append(Token(FOOTNOTE_DEF, stripped,
                                    meta={'label': label, 'content': content},
                                    indent=indent))
                continue

            # definition list marker 
            if bg == 'def_list_marker':
                m = re_deflist.match(stripped)
                content = m.group(1) if m else ""
                tokens.append(Token(DEF_LIST_MARKER, stripped,
                                    meta={'content': content}, indent=indent))
                continue

            # fenced code block: opening 
            if bg == 'code_fence':
                fc   = block_match.group('code_fence')[0]
                fl   = len(block_match.group('code_fence'))
                info = stripped[fl:].strip()
                btype = 'mermaid_block' if info.lower() == 'mermaid' else 'code_block'
                in_fence       = True
                fence_block_type = btype
                fence_char     = fc
                fence_length   = fl
                tokens.append(Token(CODE_FENCE, stripped,
                                    meta={'fence_char': fc, 'fence_length': fl,
                                          'info': info, 'block_type': btype},
                                    indent=indent))
                continue

            # math fence: opening 
            if bg == 'math_fence':
                in_fence       = True
                fence_block_type = 'math_block'
                tokens.append(Token(MATH_FENCE, stripped, indent=indent))
                continue

            # mermaid fence (:::mermaid) 
            if bg == 'mermaid_fence':
                in_fence       = True
                fence_block_type = 'mermaid_block'
                fence_char     = None
                tokens.append(Token(MERMAID_FENCE, stripped, indent=indent))
                continue

            # bullet list item
            if bg == 'bullet_list':
                marker  = block_match.group('bullet_list')
                content = stripped[len(marker):]
                tokens.append(Token(BULLET_LIST, stripped,
                                    meta={'list_type': 'bullet', 'content': content},
                                    indent=indent))
                continue

            # ordered list item 
            if bg == 'ordered_list':
                marker     = block_match.group('ordered_list')
                start_num  = int(re_ol_num.search(marker).group())
                content    = stripped[len(marker):]
                tokens.append(Token(ORDERED_LIST, stripped,
                                    meta={'list_type': 'ordered',
                                          'list_start': start_num,
                                          'content': content},
                                    indent=indent))
                continue

            # table separator / table row 
            if stripped.startswith('|') and stripped.endswith('|'):
                if re_table_sep.match(stripped):
                    tokens.append(Token(TABLE_SEP, stripped, indent=indent))
                else:
                    cells = [c.strip() for c in stripped.strip('|').split('|')]
                    tokens.append(Token(TABLE_ROW, stripped,
                                        meta={'cells': cells}, indent=indent))
                continue

            # raw HTML block
            for pattern in reHtmlBlockOpen:
                if pattern.match(stripped):
                    tokens.append(Token(HTML_BLOCK, line, indent=indent))
                    break
            else:
                # plain paragraph line
                tokens.append(Token(PARAGRAPH, stripped, indent=indent))

        return tokens

    def tokenize_inline(self, text: str) -> list:

        tokens: list[Token] = []

        for m in inline_token_pattern.finditer(text):
            raw = m.group(0)
            if not raw:
                continue

            tok_type = self._classify_inline(raw)
            meta     = self._inline_meta(raw, tok_type)
            tokens.append(Token(tok_type, raw, meta=meta))

        return tokens

    @staticmethod
    def _classify_inline(token: str) -> str:
        if token.startswith('![') and '](' in token and token.endswith(')'):
            return IL_IMAGE
        if token.startswith('[') and '](' in token and token.endswith(')'):
            return IL_LINK
        if (token.startswith('**') and token.endswith('**')) or \
           (token.startswith('__') and token.endswith('__')):
            return IL_STRONG
        if (token.startswith('*') and token.endswith('*')) or \
           (token.startswith('_') and token.endswith('_')):
            return IL_EMPH
        if token.startswith('==') and token.endswith('=='):
            return IL_MARK
        if token.startswith('++') and token.endswith('++'):
            return IL_UNDERLINE
        if token.startswith('~~') and token.endswith('~~'):
            return IL_DEL
        if token.startswith('~') and token.endswith('~'):
            return IL_SUB
        if token.startswith('^') and token.endswith('^'):
            return IL_SUP
        if token.startswith('`') and token.endswith('`'):
            return IL_CODE
        if token.startswith('$') and token.endswith('$'):
            return IL_MATH
        if token.startswith('[^') and token.endswith(']'):
            return IL_FOOTNOTE_REF
        if token.startswith(':') and token.endswith(':'):
            return IL_EMOJI
        if token in {'[ ]', '[x]', '[X]'}:
            return IL_TASK
        if token.startswith('<') and token.endswith('>'):
            inner = token[1:-1]
            if not token.startswith('</') and '@' in inner and ' ' not in inner:
                return IL_EMAIL_LINK
            if not token.startswith('</') and ':' in inner and ' ' not in inner:
                return IL_URI_LINK
            return IL_HTML
        if token.startswith('&') and token.endswith(';'):
            return IL_ENTITY
        if token == '  \n':
            return IL_HARDBREAK
        if token == '\n':
            return IL_SOFTBREAK
        if token.startswith('\\') and len(token) == 2:
            return IL_ESCAPED
        return IL_TEXT

    @staticmethod
    def _inline_meta(token: str, type_: str) -> dict:
        if type_ == IL_IMAGE:
            label, rest = token[2:].split('](', 1)
            return {'label': label, 'dest': rest[:-1]}
        if type_ == IL_LINK:
            label, rest = token[1:].split('](', 1)
            return {'label': label, 'dest': rest[:-1]}
        if type_ in (IL_STRONG, IL_MARK, IL_UNDERLINE, IL_DEL):
            return {'text': token[2:-2]}
        if type_ in (IL_EMPH, IL_SUB, IL_SUP, IL_MATH):
            return {'text': token[1:-1]}
        if type_ == IL_CODE:
            strip_len = len(token) - len(token.lstrip('`'))
            return {'text': token[strip_len:-strip_len].strip()}
        if type_ == IL_FOOTNOTE_REF:
            return {'label': token[2:-1]}
        if type_ in (IL_EMAIL_LINK, IL_URI_LINK):
            return {'dest': token[1:-1]}
        if type_ == IL_TASK:
            return {'checked': token.lower() == '[x]'}
        if type_ == IL_ESCAPED:
            return {'char': token[1]}
        return {}
