class CSTVisualizer:
    def __init__(self):
        self._id_counter = 0

    def to_cst_tree(self, ast_root):
        self._id_counter = 0
        return self._document(ast_root)

    def _next_id(self):
        self._id_counter += 1
        return self._id_counter

    def _nt(self, name, children=None, collapsed=False):
        node = {
            "id": self._next_id(),
            "name": name,
            "type": "non_terminal",
            "color": "#a855f7",
        }
        if children: node["children"] = children
        if collapsed: node["collapsed"] = True
        return node

    def _term(self, name, value=None):
        if value is not None:
            preview = str(value).strip()[:20].replace('\n', '↵')
            display = f"{name} «{preview}»" if preview else name
        else:
            display = name
        return {
            "id": self._next_id(),
            "name": display,
            "type": "terminal",
            "color": "#10b981",
            "children": [],
        }

    def _document(self, node):
        return self._nt("Document", [self._block_list_chain(node.first_child)])

    def _block_list_chain(self, child_node):
        blocks = []
        c = child_node
        while c:
            b = self._block(c)
            if b: blocks.append(b)
            c = c.next
        if not blocks: return self._nt("BlockList", [self._term("ε")])

        tail = self._nt("BlockList'", [self._term("ε")])
        for block in reversed(blocks[1:]):
            block_node = self._nt("Block", [block], collapsed=True)
            tail = self._nt("BlockList'", [block_node, tail])
        return self._nt("BlockList", [self._nt("Block", [blocks[0]], collapsed=True), tail])

    def _block_list_inline(self, child_node): return self._block_list_chain(child_node)

    def _block(self, node):
        t = node.type
        if t == 'heading': return self._nt(f"Heading H{getattr(node, 'level', '?')}", [self._term("HEADING_TOKEN"), self._inline_list_chain(node.first_child)])
        elif t == 'paragraph': return self._nt("Paragraph", [self._inline_list_chain(node.first_child)])
        elif t == 'block_quote': return self._nt("Blockquote", [self._term("BLOCKQUOTE_TOKEN"), self._block_list_inline(node.first_child)])
        elif t == 'code_block': return self._nt("CodeBlock", [self._term("CODE_FENCE"), self._nt("CodeBlock'", [self._content_chain("CodeContentList", "CODE_CONTENT", getattr(node, 'literal', None)), self._term("CODE_FENCE_CLOSE")])])
        elif t == 'list': return self._list_chain(node)
        elif t == 'table': return self._table_chain(node)
        elif t == 'html_block': return self._nt("HtmlBlock", [self._term("HTML_BLOCK", getattr(node, 'literal', ''))])
        else: return self._nt(t.title(), [self._term(t.upper())])

    def _content_chain(self, list_name, token_name, literal):
        if not literal or not literal.strip(): return self._nt(list_name, [self._term("ε")])
        return self._nt(list_name, [self._term(token_name, literal), self._nt(list_name, [self._term("ε")])])

    def _list_chain(self, list_node):
        items = []
        c = list_node.first_child
        while c:
            marker = "BULLET_LIST_ITEM" if getattr(list_node, 'list_type', '') == 'bullet' else "ORDERED_LIST_ITEM"
            items.append(self._nt("Item", [self._nt("ListMarker", [self._term(marker)]), self._block_list_inline(c.first_child)]))
            c = c.next
        if not items: return self._nt("List", [self._term("ε")])
        tail = self._nt("ListTail", [self._term("ε")])
        for item in reversed(items[1:]): tail = self._nt("ListTail", [item, tail])
        return self._nt("List", [items[0], tail])

    def _table_chain(self, table_node):
        rows = []
        c = table_node.first_child
        while c:
            rows.append(self._table_row(c))
            c = c.next
        if not rows: return self._nt("Table", [self._term("ε")])
        tail = self._nt("TableTail", [self._term("ε")])
        for row in reversed(rows[1:]): tail = self._nt("TableTail", [row, tail])
        return self._nt("Table", [rows[0], tail])

    def _table_row(self, row_node):
        cells = []
        cell = row_node.first_child
        while cell:
            cells.append(self._term("TABLE_CELL", getattr(cell, 'string_content', '') or getattr(cell, 'literal', '')))
            cell = cell.next
        if not cells: return self._nt("TableRow", [self._term("TABLE_SEPARATOR")])
        cell_tail = self._nt("CellList", [self._term("ε")])
        for cell_term in reversed(cells[1:]): cell_tail = self._nt("CellList", [cell_term, cell_tail])
        return self._nt("TableRow", [self._term("TABLE_ROW"), self._nt("CellList", [cells[0], cell_tail])])

    def _inline_list_chain(self, child_node):
        inlines = []
        c = child_node
        while c:
            inlines.append(self._inline(c))
            c = c.next
        if not inlines: return self._nt("InlineList", [self._term("ε")])
        tail = self._nt("InlineList'", [self._term("ε")])
        for inline_term in reversed(inlines[1:]): tail = self._nt("InlineList'", [self._nt("Inline", [inline_term]), tail])
        return self._nt("InlineList", [self._nt("Inline", [inlines[0]]), tail])

    _INLINE_MAP = {
        'text': 'TEXT', 'strong': 'STRONG', 'emph': 'EMPH', 'code': 'INLINE_CODE',
        'link': 'LINK', 'image': 'IMAGE', 'mark': 'HIGHLIGHT', 'del': 'STRIKETHROUGH',
        'sub': 'SUBSCRIPT', 'sup': 'SUPERSCRIPT', 'u': 'UNDERLINE', 'math_inline': 'INLINE_MATH',
        'softbreak': 'SOFT_BREAK', 'hardbreak': 'HARD_BREAK', 'html_inline': 'HTML_INLINE'
    }

    def _inline(self, node):
        t = node.type
        name = self._INLINE_MAP.get(t, t.upper())
        literal = getattr(node, 'literal', None) or getattr(node, 'label', None) or getattr(node, 'destination', None)
        return self._term(name, literal)
