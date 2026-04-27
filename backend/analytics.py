"""
Analytics Module — Generates JSON stats with deeper metrics.
"""

class AnalyticsGenerator:
    def generate_stats(self, tokens, ast_root):
        token_counts = {}
        for t in tokens:
            t_type = getattr(t, 'type', 'UNKNOWN')
            token_counts[t_type] = token_counts.get(t_type, 0) + 1
            
        node_counts = {}
        depths = []
        block_types = {'document', 'heading', 'paragraph', 'block_quote', 'list', 'item', 'code_block', 'math_block', 'mermaid_block', 'table', 'table_row', 'thematic_break', 'html_block'}
        
        block_count = 0
        inline_count = 0

        def _walk(node, current_depth):
            depths.append(current_depth)
            node_counts[node.type] = node_counts.get(node.type, 0) + 1
            
            if node.type in block_types:
                nonlocal block_count
                block_count += 1
            else:
                nonlocal inline_count
                inline_count += 1

            child = node.first_child
            while child:
                _walk(child, current_depth + 1)
                child = child.next
                
        if ast_root:
            _walk(ast_root, 1)

        sorted_tokens = sorted([{"name": k, "value": v} for k, v in token_counts.items()], key=lambda x: x["value"], reverse=True)
        sorted_nodes = sorted([{"name": k, "value": v} for k, v in node_counts.items()], key=lambda x: x["value"], reverse=True)
            
        max_depth = max(depths) if depths else 0
        avg_depth = sum(depths) / len(depths) if depths else 0

        return {
            "total_tokens": len(tokens),
            "tokens_breakdown": sorted_tokens,
            "total_nodes": sum(node_counts.values()) if node_counts else 0,
            "nodes_breakdown": sorted_nodes,
            "max_depth": max_depth,
            "avg_depth": round(avg_depth, 2),
            "block_nodes": block_count,
            "inline_nodes": inline_count
        }
