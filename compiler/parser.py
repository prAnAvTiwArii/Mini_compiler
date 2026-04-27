import re
import html
import urllib.parse

from node import Node
from lexer import Lexer
from lex_token import *

class InlineParser:

    def __init__(self):
        self._lexer = Lexer()

    def parse(self, block_node: Node) -> None:
        text = (block_node.string_content or "").strip()
        if not text:
            return
        tokens = self._lexer.tokenize_inline(text)
        self._build_nodes(block_node, tokens)
        block_node.string_content = ""

    def _build_nodes(self, block: Node, tokens: list) -> None:  # list[Token]
        for tok in tokens:
            node = self._token_to_node(tok)
            if node is not None:
                block.append_child(node)

    def _token_to_node(self, tok: Token) -> Node | None:
        t, v, m = tok.type, tok.value, tok.meta

        if t == IL_AUDIO:
            node = Node('audio')
            node.destination = m['dest']
            node.title = m['label']
            return node

        if t == IL_VIDEO:
            node = Node('video')
            node.destination = m['dest']
            node.title = m['label']
            return node

        if t == IL_IMAGE:
            node = Node('image')
            node.destination = m['dest']
            node.title = m['label']
            inner = self._lexer.tokenize_inline(m['label'])
            self._build_nodes(node, inner)
            return node

        if t == IL_LINK:
            node = Node('link')
            node.destination = m['dest']
            inner = self._lexer.tokenize_inline(m['label'])
            self._build_nodes(node, inner)
            return node

        if t == IL_STRONG:
            node = Node('strong')
            inner = self._lexer.tokenize_inline(m['text'])
            self._build_nodes(node, inner)
            return node

        if t == IL_EMPH:
            node = Node('emph')
            inner = self._lexer.tokenize_inline(m['text'])
            self._build_nodes(node, inner)
            return node

        if t == IL_MARK:
            node = Node('mark')
            inner = self._lexer.tokenize_inline(m['text'])
            self._build_nodes(node, inner)
            return node

        if t == IL_UNDERLINE:
            node = Node('u')
            inner = self._lexer.tokenize_inline(m['text'])
            self._build_nodes(node, inner)
            return node

        if t == IL_DEL:
            node = Node('del')
            inner = self._lexer.tokenize_inline(m['text'])
            self._build_nodes(node, inner)
            return node

        if t == IL_SUB:
            node = Node('sub')
            inner = self._lexer.tokenize_inline(m['text'])
            self._build_nodes(node, inner)
            return node

        if t == IL_SUP:
            node = Node('sup')
            inner = self._lexer.tokenize_inline(m['text'])
            self._build_nodes(node, inner)
            return node

        if t == IL_MATH:
            node = Node('math_inline')
            node.literal = m['text']
            return node

        if t == IL_CODE:
            node = Node('code')
            node.literal = m['text']
            return node

        if t == IL_FOOTNOTE_REF:
            node = Node('footnote_ref')
            node.label = m['label']
            return node

        if t == IL_EMOJI:
            node = Node('emoji')
            node.literal = v
            return node

        if t == IL_TASK:
            node = Node('task_checkbox')
            node.checked = m['checked']
            return node

        if t == IL_EMAIL_LINK:
            node = Node('link')
            node.destination = 'mailto:' + m['dest']
            child = Node('text'); child.literal = m['dest']
            node.append_child(child)
            return node

        if t == IL_URI_LINK:
            node = Node('link')
            node.destination = urllib.parse.quote(m['dest'], safe=":/?#[]@!$&'()*+,;=")
            child = Node('text'); child.literal = m['dest']
            node.append_child(child)
            return node

        if t == IL_HTML:
            node = Node('html_inline')
            node.literal = v
            return node

        if t == IL_ENTITY:
            node = Node('text')
            node.literal = html.unescape(v)
            return node

        if t == IL_HARDBREAK:
            return Node('hardbreak')

        if t == IL_SOFTBREAK:
            return Node('softbreak')

        if t == IL_ESCAPED:
            node = Node('text')
            node.literal = m['char']
            return node

        # IL_TEXT
        node = Node('text')
        node.literal = v
        return node

class Parser:

    def __init__(self):
        self.inline_parser = InlineParser()
        self._lexer        = Lexer()
        self.doc           = Node('document')
        self.tip: Node | None = self.doc

    def parse(self, text: str) -> Node:
        self.doc = Node('document')
        self.tip = self.doc

        tokens = self._lexer.tokenize(text)
        for tok in tokens:
            self._incorporate_token(tok)

        while self.tip:
            self.tip.is_open = False
            self.tip = self.tip.parent

        self.process_inlines(self.doc)
        return self.doc

    def _incorporate_token(self, tok: Token) -> None:
        t  = tok.type
        m  = tok.meta
        indent = tok.indent

        # open raw-block continuation
        if t == RAW_CONTENT:
            if self.tip and self.tip.type in ('code_block', 'math_block', 'mermaid_block', 'details'):
                self.tip.string_content += tok.value + '\n'
            return

        # fence closers 
        if t in (CODE_FENCE_END, MATH_FENCE_END, MERMAID_CLOSE):
            if self.tip:
                self.tip.is_open = False
                self.tip = self.tip.parent
            return

        # HTML block continuation 
        if self.tip and self.tip.type == 'html_block' and getattr(self.tip, 'is_open', False):
            if t == BLANK:
                self.tip.is_open = False
                self.tip = self.tip.parent
            else:
                self.tip.literal += '\n' + tok.value
            return

        # blank line 
        if t == BLANK:
            if self.tip and getattr(self.tip, 'is_open', False):
                self.tip.is_open = False
            return

        # blockquote 
        if t == BLOCKQUOTE:
            if not self.tip or self.tip.type != 'block_quote' or not getattr(self.tip, 'is_open', False):
                bq = Node('block_quote')
                self.doc.append_child(bq)
                self.tip = bq
            p = Node('paragraph')
            p.string_content = m['content']
            self.tip.append_child(p)
            self.tip = p
            return

        # ATX heading 
        if t == ATX_HEADING:
            heading = Node('heading')
            heading.level = m['level']
            heading.string_content = m['content']
            if m.get('custom_id'):
                heading.custom_id = m['custom_id']
            self.doc.append_child(heading)
            self._close_tip_if_paragraph()
            heading.is_open = False
            self.tip = heading
            return

        # footnote definition 
        if t == FOOTNOTE_DEF:
            fn = Node('footnote_def')
            fn.label = m['label']
            self.doc.append_child(fn)
            self._close_tip_if_paragraph()
            self.tip = fn
            if m.get('content'):
                p = Node('paragraph')
                p.string_content = m['content']
                fn.append_child(p)
                self.tip = p
            return

        # definition list marker 
        if t == DEF_LIST_MARKER:
            content = m.get('content', '')
            if self.tip and self.tip.type == 'paragraph':
                self.tip.is_open = False
                if self.tip.parent and self.tip.parent.type == 'def_list':
                    dl = self.tip.parent
                else:
                    dl = Node('def_list')
                    self.tip.insert_after(dl)
                    dl.append_child(self.tip)
                    self.tip.type = 'def_term'
                di = Node('def_item')
                dl.append_child(di)
                dp = Node('paragraph')
                dp.string_content = content
                di.append_child(dp)
                self.tip = dp
            elif self.tip and self.tip.type in ('def_item', 'def_term'):
                dl = self.tip.parent
                di = Node('def_item')
                dl.append_child(di)
                dp = Node('paragraph')
                dp.string_content = content
                di.append_child(dp)
                self.tip = dp
            return

        # thematic break 
        if t == THEMATIC_BREAK:
            tbreak = Node('thematic_break')
            self.doc.append_child(tbreak)
            self._close_tip_if_paragraph()
            tbreak.is_open = False
            self.tip = tbreak
            return

        # fenced code block: opening 
        if t == CODE_FENCE:
            btype = m.get('block_type', 'code_block')
            cb = Node(btype)
            cb.is_fenced    = True
            cb.fence_char   = m['fence_char']
            cb.fence_length = m['fence_length']
            cb.info         = m.get('info', '')
            cb.string_content = ""
            self.doc.append_child(cb)
            self._close_tip_if_paragraph()
            self.tip = cb
            return

        # math fence: opening 
        if t == MATH_FENCE:
            mb = Node('math_block')
            mb.string_content = ""
            self.doc.append_child(mb)
            self._close_tip_if_paragraph()
            self.tip = mb
            return

        # mermaid fence 
        if t == MERMAID_FENCE:
            mm = Node('mermaid_block')
            mm.string_content = ""
            self.doc.append_child(mm)
            self._close_tip_if_paragraph()
            self.tip = mm
            return

        # details fence (:::details Title)
        if t == DETAILS_FENCE:
            det = Node('details')
            det.title = m.get('title', '')
            det.string_content = ""
            self.doc.append_child(det)
            self._close_tip_if_paragraph()
            self.tip = det
            return

        # bullet / ordered list item 
        if t in (BULLET_LIST, ORDERED_LIST):
            list_type  = m['list_type']
            list_start = m.get('list_start')
            content    = m.get('content', '')
            self._close_tip_if_paragraph()
            self._handle_list_item(indent, list_type, list_start, content)
            return

        # table separator 
        if t == TABLE_SEP:
            if self.tip and self.tip.type == 'table':
                self.tip.headers_done = True
            return

        # table row 
        if t == TABLE_ROW:
            if not self.tip or self.tip.type != 'table' or not getattr(self.tip, 'is_open', False):
                self._close_tip_if_paragraph()
                table = Node('table')
                table.is_open = True
                self.doc.append_child(table)
                self.tip = table
            row = Node('table_row')
            self.tip.append_child(row)
            for cell_content in m['cells']:
                is_header = not getattr(self.tip, 'headers_done', False)
                cell = Node('table_header' if is_header else 'table_cell')
                cell.string_content = cell_content
                row.append_child(cell)
            return

        # raw HTML block 
        if t == HTML_BLOCK:
            hb = Node('html_block')
            hb.literal  = tok.value
            hb.is_open  = True
            self.doc.append_child(hb)
            self._close_tip_if_paragraph()
            self.tip = hb
            return

        # Paragraph
        if t == PARAGRAPH:
            if self.tip and self.tip.type == 'paragraph' and self.tip.is_open:
                self.tip.string_content += '\n' + tok.value
            else:
                p = Node('paragraph')
                p.string_content = tok.value
                if self.tip and self.tip.type in ('block_quote', 'item') \
                        and getattr(self.tip, 'is_open', False):
                    self.tip.append_child(p)
                else:
                    self.doc.append_child(p)
                self.tip = p

    # list handling 
    def _handle_list_item(self, indent: int, list_type: str,
                          list_start: int | None, content: str) -> None:
        current     = self.tip
        target_list = None

        while current:
            if current.type == 'list' and getattr(current, 'is_open', False):
                list_indent = getattr(current, 'indent', 0)
                if indent < list_indent:
                    current.is_open = False
                else:
                    target_list = current
                    break
            current = current.parent

        if target_list is not None:
            target_indent = getattr(target_list, 'indent', 0)
            if indent > target_indent and target_list.last_child \
                    and target_list.last_child.type == 'item':
                # Nesting: new list inside last item
                lst = self._make_list(list_type, list_start, indent)
                target_list.last_child.append_child(lst)
                self.tip = lst
            elif target_list.list_type == list_type:
                self.tip = target_list
            else:
                target_list.is_open = False
                lst = self._make_list(list_type, list_start, indent)
                if target_list.parent:
                    target_list.parent.append_child(lst)
                else:
                    self.doc.append_child(lst)
                self.tip = lst
        else:
            lst = self._make_list(list_type, list_start, indent)
            if self.tip and getattr(self.tip, 'is_open', False) \
                    and self.tip.type in ('document', 'block_quote', 'item'):
                self.tip.append_child(lst)
            elif self.tip and self.tip.parent:
                self.tip.parent.append_child(lst)
            else:
                self.doc.append_child(lst)
            self.tip = lst

        item = Node('item')
        self.tip.append_child(item)
        p = Node('paragraph')
        p.string_content = content
        item.append_child(p)
        self.tip = p

    @staticmethod
    def _make_list(list_type: str, list_start: int | None, indent: int) -> Node:
        lst = Node('list')
        lst.list_type  = list_type
        lst.list_start = list_start
        lst.is_open    = True
        lst.indent     = indent
        return lst

    # paragraph
    def _close_tip_if_paragraph(self) -> None:
        if self.tip and self.tip.type == 'paragraph':
            self.tip.is_open = False
            self.tip = self.tip.parent

    def process_inlines(self, doc: Node) -> None:
        for node, entering in doc.walker():
            if entering and node.type in ('paragraph', 'heading', 'table_cell',
                                          'table_header', 'def_term', 'details') \
                    and getattr(node, 'string_content', None):
                self.inline_parser.parse(node)

            elif entering and node.type in ('code_block', 'math_block', 'mermaid_block'):
                node.literal = node.string_content
                node.string_content = ""
