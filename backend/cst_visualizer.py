"""
CST Visualizer Module — Generates a vertical, LALR-style parse tree.

Uses right-recursive chaining patterns matching the restructured grammar:
  BlockList  → Block BlockList'
  BlockList' → Block BlockList' | ε
  InlineList → Inline InlineList'
  List       → Item ListTail
  Table      → TableRow TableTail
  etc.

This guarantees at most 2 children per non-terminal, producing a deep
vertical tree instead of a flat wide tree.

Based strictly on the grammar defined in grammar.txt.
"""


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
        """Non-terminal node — purple circle in D3."""
        node = {
            "id": self._next_id(),
            "name": name,
            "type": "non_terminal",
            "color": "#a855f7",
        }
        if children:
            node["children"] = children
        if collapsed:
            node["collapsed"] = True
        return node

    def _term(self, name, value=None):
        """Terminal token node — green circle (leaf) in D3."""
        if value is not None:
            preview = value.strip()[:20].replace('\n', '↵')
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

    # ── Top-level ────────────────────────────────────────────────────────────

    def _document(self, node):
        """Document → BlockList"""
        block_list = self._block_list_chain(node.first_child)
        return self._nt("Document", [block_list])

    # ── BlockList right-recursive chain ──────────────────────────────────────

    def _block_list_chain(self, child_node):
        """
        BlockList  → Block  BlockList'
        BlockList' → Block  BlockList' | ε
        Produces a right-leaning spine: each node has exactly 2 children.
        """
        # Collect block AST nodes
        blocks = []
        c = child_node
        while c:
            b = self._block(c)
            if b:
                blocks.append(b)
            c = c.next

        if not blocks:
            return self._nt("BlockList", [self._term("ε")])

        # Build the spine right-to-left so the first block is at top
        # Seed: innermost BlockList' = ε
        tail = self._nt("BlockList'", [self._term("ε")])

        # Walk blocks in reverse; each becomes a 2-child node
        for block in reversed(blocks[1:]):
            block_node = self._nt("Block", [block], collapsed=True)
            tail = self._nt("BlockList'", [block_node, tail])

        # Root BlockList uses the first block
        first = self._nt("Block", [blocks[0]], collapsed=True)
        return self._nt("BlockList", [first, tail])

    def _block_list_inline(self, child_node):
        """Small version used inside Blockquote / Items — same chain logic."""
        return self._block_list_chain(child_node)

    # ── Block-level rules ────────────────────────────────────────────────────

    def _block(self, node):
        t = node.type

        if t == 'heading':
            level = getattr(node, 'level', '?')
            return self._nt(f"Heading H{level}", [
                self._term("HEADING_TOKEN"),
                self._inline_list_chain(node.first_child),
            ])

        elif t == 'paragraph':
            return self._nt("Paragraph", [
                self._inline_list_chain(node.first_child),
            ])

        elif t == 'block_quote':
            return self._nt("Blockquote", [
                self._term("BLOCKQUOTE_TOKEN"),
                self._block_list_inline(node.first_child),
            ])

        elif t == 'code_block':
            content_chain = self._content_chain(
                "CodeContentList", "CODE_CONTENT",
                getattr(node, 'literal', None)
            )
            return self._nt("CodeBlock", [
                self._term("CODE_FENCE"),
                self._nt("CodeBlock'", [content_chain, self._term("CODE_FENCE_CLOSE")]),
            ])

        elif t == 'math_block':
            content_chain = self._content_chain(
                "MathContentList", "MATH_CONTENT",
                getattr(node, 'literal', None)
            )
            return self._nt("MathBlock", [
                self._term("MATH_FENCE"),
                self._nt("MathBlock'", [content_chain, self._term("MATH_FENCE_CLOSE")]),
            ])

        elif t == 'mermaid_block':
            content_chain = self._content_chain(
                "MermaidContentList", "MERMAID_CONTENT",
                getattr(node, 'literal', None)
            )
            return self._nt("MermaidBlock", [
                self._term("MERMAID_OPEN"),
                self._nt("MermaidBlock'", [content_chain, self._term("MERMAID_CLOSE")]),
            ])

        elif t == 'list':
            return self._list_chain(node)

        elif t == 'table':
            return self._table_chain(node)

        elif t == 'thematic_break':
            return self._nt("ThematicBreak", [self._term("THEMATIC_BREAK")])

        elif t == 'html_block':
            return self._nt("HtmlBlock", [
                self._term("HTML_BLOCK", getattr(node, 'literal', ''))
            ])

        elif t == 'footnote_def':
            return self._nt("FootnoteDef", [
                self._term("FOOTNOTE_DEF", getattr(node, 'label', '')),
                self._inline_list_chain(node.first_child),
            ])

        elif t == 'def_list':
            return self._def_list_chain(node)

        else:
            return self._nt(t.title(), [self._term(t.upper())])

    # ── Content chains (CODE_CONTENT, MATH_CONTENT, MERMAID_CONTENT) ─────────

    def _content_chain(self, list_name, token_name, literal):
        """
        XContentList → TOKEN XContentList | ε
        For fenced blocks with a single literal blob, treat it as one node.
        """
        if not literal or not literal.strip():
            return self._nt(list_name, [self._term("ε")])
        # Treat the whole literal as one content token for readability
        content_node = self._term(token_name, literal)
        epsilon = self._nt(list_name, [self._term("ε")])
        return self._nt(list_name, [content_node, epsilon])

    # ── List right-recursive chain ────────────────────────────────────────────

    def _list_chain(self, list_node):
        """
        List     → Item  ListTail
        ListTail → Item  ListTail | ε
        """
        items = []
        c = list_node.first_child
        while c:
            marker = "BULLET_LIST_ITEM" if getattr(list_node, 'list_type', '') == 'bullet' else "ORDERED_LIST_ITEM"
            items.append(self._nt("Item", [
                self._nt("ListMarker", [self._term(marker)]),
                self._block_list_inline(c.first_child),
            ]))
            c = c.next

        if not items:
            return self._nt("List", [self._term("ε")])

        # Build ListTail spine
        tail = self._nt("ListTail", [self._term("ε")])
        for item in reversed(items[1:]):
            tail = self._nt("ListTail", [item, tail])

        return self._nt("List", [items[0], tail])

    # ── Table right-recursive chain ───────────────────────────────────────────

    def _table_chain(self, table_node):
        """
        Table     → TableRow  TableTail
        TableTail → TableRow  TableTail | ε
        """
        rows = []
        c = table_node.first_child
        while c:
            rows.append(self._table_row(c))
            c = c.next

        if not rows:
            return self._nt("Table", [self._term("ε")])

        # Build TableTail spine
        tail = self._nt("TableTail", [self._term("ε")])
        for row in reversed(rows[1:]):
            tail = self._nt("TableTail", [row, tail])

        return self._nt("Table", [rows[0], tail])

    def _table_row(self, row_node):
        """
        TableRow → TABLE_ROW  CellList
                 | TABLE_SEPARATOR
        CellList → TABLE_CELL  CellList | ε
        """
        cells = []
        cell = row_node.first_child
        while cell:
            v = getattr(cell, 'string_content', '') or getattr(cell, 'literal', '')
            cells.append(self._term("TABLE_CELL", v))
            cell = cell.next

        if not cells:
            # Separator row
            return self._nt("TableRow", [self._term("TABLE_SEPARATOR")])

        # Build CellList chain
        cell_tail = self._nt("CellList", [self._term("ε")])
        for cell_term in reversed(cells[1:]):
            cell_tail = self._nt("CellList", [cell_term, cell_tail])

        cell_list = self._nt("CellList", [cells[0], cell_tail])
        return self._nt("TableRow", [self._term("TABLE_ROW"), cell_list])

    # ── DefList right-recursive chain ─────────────────────────────────────────

    def _def_list_chain(self, dl_node):
        """
        DefList     → DefTerm  DefItemList
        DefItemList → DefItem  DefItemList | ε
        """
        term_node = None
        items = []
        c = dl_node.first_child
        while c:
            if c.type == 'def_term':
                term_node = self._nt("DefTerm", [
                    self._nt("Paragraph", [self._inline_list_chain(c.first_child)])
                ])
            elif c.type == 'def_item':
                items.append(self._nt("DefItem", [
                    self._term("DEF_LIST_MARKER"),
                    self._inline_list_chain(c.first_child),
                ]))
            c = c.next

        if term_node is None:
            term_node = self._nt("DefTerm", [self._term("ε")])

        # Build DefItemList chain
        item_list = self._nt("DefItemList", [self._term("ε")])
        for item in reversed(items):
            item_list = self._nt("DefItemList", [item, item_list])

        return self._nt("DefList", [term_node, item_list])

    # ── InlineList right-recursive chain ──────────────────────────────────────

    def _inline_list_chain(self, child_node):
        """
        InlineList  → Inline  InlineList'
        InlineList' → Inline  InlineList' | ε
        Produces a right-leaning spine guaranteeing at most 2 children.
        """
        inlines = []
        c = child_node
        while c:
            inlines.append(self._inline(c))
            c = c.next

        if not inlines:
            return self._nt("InlineList", [self._term("ε")])

        # Seed: innermost InlineList' = ε
        tail = self._nt("InlineList'", [self._term("ε")])

        for inline_term in reversed(inlines[1:]):
            inline_node = self._nt("Inline", [inline_term])
            tail = self._nt("InlineList'", [inline_node, tail])

        first_inline = self._nt("Inline", [inlines[0]])
        return self._nt("InlineList", [first_inline, tail])

    # ── Inline terminal mapping ───────────────────────────────────────────────

    _INLINE_MAP = {
        'text': 'TEXT',
        'strong': 'STRONG',
        'emph': 'EMPH',
        'code': 'INLINE_CODE',
        'link': 'LINK',
        'image': 'IMAGE',
        'mark': 'HIGHLIGHT',
        'del': 'STRIKETHROUGH',
        'sub': 'SUBSCRIPT',
        'sup': 'SUPERSCRIPT',
        'u': 'UNDERLINE',
        'math_inline': 'INLINE_MATH',
        'footnote_ref': 'FOOTNOTE_REF',
        'task_checkbox': 'CHECKBOX',
        'emoji': 'EMOJI',
        'html_inline': 'HTML_INLINE',
        'softbreak': 'SOFT_BREAK',
        'hardbreak': 'HARD_BREAK',
    }

    def _inline(self, node):
        t = node.type
        name = self._INLINE_MAP.get(t, t.upper())
        literal = (
            getattr(node, 'literal', None)
            or getattr(node, 'label', None)
            or getattr(node, 'destination', None)
        )
        if t == 'task_checkbox':
            literal = '[x]' if getattr(node, 'checked', False) else '[ ]'
        return self._term(name, literal)
