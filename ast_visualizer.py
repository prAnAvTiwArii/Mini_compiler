"""
AST Visualizer Module — Generates D3.js-compatible tree data from the AST.
Used by the web UI to render an interactive, animated AST tree visualization.
Supports collapsible nodes: block-level nodes with inline children start
collapsed, showing the raw token text. Click to expand/collapse.
"""

# Color palette for different node types
NODE_COLORS = {
    'document':       '#6366f1',   # Indigo
    'heading':        '#f59e0b',   # Amber
    'paragraph':      '#10b981',   # Emerald
    'text':           '#94a3b8',   # Slate
    'strong':         '#ef4444',   # Red
    'emph':           '#f97316',   # Orange
    'code':           '#06b6d4',   # Cyan
    'code_block':     '#0891b2',   # Dark Cyan
    'link':           '#3b82f6',   # Blue
    'image':          '#8b5cf6',   # Violet
    'list':           '#22c55e',   # Green
    'item':           '#4ade80',   # Light Green
    'block_quote':    '#a855f7',   # Purple
    'thematic_break': '#64748b',   # Gray
    'table':          '#14b8a6',   # Teal
    'table_row':      '#2dd4bf',   # Light Teal
    'table_header':   '#0d9488',   # Dark Teal
    'table_cell':     '#5eead4',   # Pale Teal
    'html_block':     '#e11d48',   # Rose
    'html_inline':    '#fb7185',   # Pink
    'softbreak':      '#cbd5e1',   # Light gray
    'hardbreak':      '#9ca3af',   # Medium gray
    'mark':           '#eab308',   # Yellow
    'del':            '#dc2626',   # Dark Red
    'sub':            '#7c3aed',   # Deep Purple
    'sup':            '#6d28d9',   # Deeper Purple
    'u':              '#2563eb',   # Royal Blue
    'math_inline':    '#d946ef',   # Fuchsia
    'math_block':     '#c026d3',   # Dark Fuchsia
    'mermaid_block':  '#059669',   # Emerald dark
    'emoji':          '#fbbf24',   # Amber light
    'footnote_ref':   '#f472b6',   # Pink
    'footnote_def':   '#ec4899',   # Pink
    'def_list':       '#84cc16',   # Lime
    'def_term':       '#a3e635',   # Light Lime
    'def_item':       '#65a30d',   # Dark Lime
    'task_checkbox':  '#0ea5e9',   # Sky
}

DEFAULT_COLOR = '#64748b'

# Node types whose inline children should be collapsible
COLLAPSIBLE_TYPES = {'heading', 'paragraph', 'table_cell', 'table_header', 'def_term'}


class ASTVisualizer:
    """
    Converts an AST Node tree into a D3.js-compatible hierarchical
    JSON structure for interactive tree visualization.
    Marks block-level nodes with inline children as collapsible.
    """

    def __init__(self):
        self._id_counter = 0

    def to_vis_tree(self, node):
        """
        Convert the AST into a D3-friendly hierarchical dict.
        Each node has: id, name, color, attributes, children, build_order.
        Collapsible nodes also have: collapsible, raw_content, _children.
        """
        self._id_counter = 0
        return self._convert_node(node)

    def _convert_node(self, node):
        self._id_counter += 1
        node_id = self._id_counter

        # Build display label
        label = node.type
        attributes = {}

        if node.type == 'heading':
            level = getattr(node, 'level', None)
            if level:
                label = f"H{level}"
                attributes['level'] = level

        if node.type == 'text' and node.literal:
            preview = node.literal[:30]
            if len(node.literal) > 30:
                preview += '…'
            label = f'"{preview}"'
            attributes['literal'] = node.literal

        if node.literal and node.type != 'text':
            preview = node.literal[:25]
            if len(node.literal) > 25:
                preview += '…'
            attributes['literal'] = preview

        if getattr(node, 'destination', None):
            attributes['destination'] = node.destination

        if getattr(node, 'info', None):
            attributes['info'] = node.info

        if getattr(node, 'level', None) and node.type != 'heading':
            attributes['level'] = node.level

        if getattr(node, 'list_type', None):
            attributes['list_type'] = getattr(node, 'list_type')

        if getattr(node, 'label', None):
            attributes['label'] = getattr(node, 'label')

        if getattr(node, 'checked', None) is not None:
            attributes['checked'] = getattr(node, 'checked')

        # Build children
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
            "build_order": node_id,
            "attributes": attributes
        }

        # Mark collapsible nodes: block-level nodes that had inline parsing
        raw_content = getattr(node, 'raw_content', None)
        if node.type in COLLAPSIBLE_TYPES and raw_content and children:
            result["collapsible"] = True
            result["raw_content"] = raw_content
            # Children go into _children (collapsed by default)
            result["_children"] = children
            # No visible children initially
        elif children:
            result["children"] = children

        return result
