"""
Semantic Analyzer Module — Phase 3: Semantic Analysis
Validates and enriches the AST after parsing.
"""


class SemanticAnalyzer:
    """
    Phase 3 — Semantic Analysis.
    
    Walks the AST to perform validation checks and enrich nodes
    with additional metadata. Produces a list of warnings/errors.
    """

    def __init__(self):
        self.warnings = []
        self.errors = []
        self.footnote_refs = set()
        self.footnote_defs = set()
        self.heading_levels = []

    def analyze(self, ast_root):
        """
        Perform semantic analysis on the AST.
        Returns a dict with 'warnings' and 'errors' lists.
        """
        self.warnings = []
        self.errors = []
        self.footnote_refs = set()
        self.footnote_defs = set()
        self.heading_levels = []
        self.symbol_table = []

        self._walk(ast_root)
        self._check_footnotes()
        self._check_heading_hierarchy()

        return {
            "warnings": self.warnings,
            "errors": self.errors,
            "stats": self._collect_stats(ast_root),
        }

    def _walk(self, node):
        """Recursively walk the AST collecting information."""
        if node.type == 'heading':
            level = getattr(node, 'level', 1) or 1
            self.heading_levels.append(level)

        elif node.type == 'footnote_ref':
            label = getattr(node, 'label', None)
            if label:
                self.footnote_refs.add(label)

        elif node.type == 'footnote_def':
            label = getattr(node, 'label', None)
            if label:
                self.footnote_defs.add(label)

        elif node.type == 'link':
            dest = getattr(node, 'destination', None)
            if dest and dest.startswith('javascript:'):
                self.warnings.append({
                    "type": "security",
                    "message": f"Potentially unsafe JavaScript link detected: {dest[:50]}",
                    "severity": "warning"
                })

        elif node.type == 'image':
            dest = getattr(node, 'destination', None)
            if not dest:
                self.warnings.append({
                    "type": "missing_src",
                    "message": "Image element with empty source URL",
                    "severity": "warning"
                })

        # Walk children
        child = node.first_child
        while child:
            self._walk(child)
            child = child.next

    def _check_footnotes(self):
        """Check that all footnote references have definitions and vice versa."""
        undefined = self.footnote_refs - self.footnote_defs
        unused = self.footnote_defs - self.footnote_refs

        for ref in undefined:
            self.errors.append({
                "type": "undefined_footnote",
                "message": f"Footnote reference [^{ref}] has no matching definition",
                "severity": "error"
            })

        for defn in unused:
            self.warnings.append({
                "type": "unused_footnote",
                "message": f"Footnote definition [^{defn}] is never referenced",
                "severity": "warning"
            })

    def _check_heading_hierarchy(self):
        """Check that heading levels don't skip (e.g. H1 → H3 without H2)."""
        if not self.heading_levels:
            return

        # Check for skipped levels
        for i in range(1, len(self.heading_levels)):
            prev = self.heading_levels[i - 1]
            curr = self.heading_levels[i]
            if curr > prev + 1:
                self.warnings.append({
                    "type": "heading_skip",
                    "message": f"Heading level jumped from H{prev} to H{curr} (skipped H{prev+1})",
                    "severity": "warning"
                })

        # Check if first heading is not H1
        if self.heading_levels[0] != 1:
            self.warnings.append({
                "type": "heading_start",
                "message": f"Document starts with H{self.heading_levels[0]} instead of H1",
                "severity": "info"
            })

    def _collect_stats(self, ast_root):
        """Collect document statistics by walking the AST."""
        stats = {
            "total_nodes": 0,
            "node_types": {},
            "heading_count": 0,
            "paragraph_count": 0,
            "link_count": 0,
            "image_count": 0,
            "code_block_count": 0,
            "list_count": 0,
            "table_count": 0
        }
        self._count_nodes(ast_root, stats)
        return stats

    def _count_nodes(self, node, stats):
        """Recursively count nodes by type."""
        stats["total_nodes"] += 1
        ntype = node.type
        stats["node_types"][ntype] = stats["node_types"].get(ntype, 0) + 1

        if ntype == 'heading':
            stats["heading_count"] += 1
        elif ntype == 'paragraph':
            stats["paragraph_count"] += 1
        elif ntype == 'link':
            stats["link_count"] += 1
        elif ntype == 'image':
            stats["image_count"] += 1
        elif ntype == 'code_block':
            stats["code_block_count"] += 1
        elif ntype == 'list':
            stats["list_count"] += 1
        elif ntype == 'table':
            stats["table_count"] += 1

        child = node.first_child
        while child:
            self._count_nodes(child, stats)
            child = child.next
