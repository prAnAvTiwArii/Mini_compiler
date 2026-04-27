"""
AST Visualizer Module — Generates D3.js-compatible tree data from the AST.
"""

NODE_COLORS = {
    'document':       '#6366f1',
    'heading':        '#f59e0b',
    'paragraph':      '#10b981',
    'text':           '#94a3b8',
    'strong':         '#ef4444',
    'emph':           '#f97316',
    'code':           '#06b6d4',
    'code_block':     '#0891b2',
    'link':           '#3b82f6',
    'image':          '#8b5cf6',
    'list':           '#22c55e',
    'item':           '#4ade80',
    'block_quote':    '#a855f7',
    'thematic_break': '#64748b',
    'table':          '#14b8a6',
    'table_row':      '#2dd4bf',
    'table_header':   '#0d9488',
    'table_cell':     '#5eead4',
    'html_block':     '#e11d48',
    'html_inline':    '#fb7185',
    'softbreak':      '#cbd5e1',
    'hardbreak':      '#9ca3af',
    'task_checkbox':  '#0ea5e9',
}

DEFAULT_COLOR = '#64748b'
COLLAPSIBLE_TYPES = {'heading', 'paragraph', 'table_cell', 'table_header', 'def_term'}

class ASTVisualizer:
    def __init__(self):
        self._id_counter = 0

    def to_vis_tree(self, node):
        self._id_counter = 0
        return self._convert_node(node)

    def _convert_node(self, node):
        self._id_counter += 1
        node_id = self._id_counter

        label = node.type
        attributes = {}

        if node.type == 'heading':
            level = getattr(node, 'level', None)
            if level:
                label = f"H{level}"
                attributes['level'] = level

        if node.type == 'text' and node.literal:
            preview = node.literal[:30]
            if len(node.literal) > 30: preview += '…'
            label = f'"{preview}"'
            attributes['literal'] = node.literal

        if node.literal and node.type != 'text':
            preview = node.literal[:25]
            if len(node.literal) > 25: preview += '…'
            attributes['literal'] = preview

        if getattr(node, 'destination', None): attributes['destination'] = node.destination
        if getattr(node, 'info', None): attributes['info'] = node.info
        if getattr(node, 'list_type', None): attributes['list_type'] = getattr(node, 'list_type')
        if getattr(node, 'checked', None) is not None: attributes['checked'] = getattr(node, 'checked')

        children = []
        child = node.first_child
        while child:
            children.append(self._convert_node(child))
            child = child.next

        color = NODE_COLORS.get(node.type, DEFAULT_COLOR)

        result = {
            "id": node_id,
            "name": label,
            "type": node.type,
            "color": color,
            "attributes": attributes
        }

        raw_content = getattr(node, 'raw_content', None)
        if node.type in COLLAPSIBLE_TYPES and raw_content and children:
            result["collapsible"] = True
            result["raw_content"] = raw_content
            result["_children"] = children
        elif children:
            result["children"] = children

        return result
