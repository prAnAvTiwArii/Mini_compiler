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
        
        # New deep metrics
        word_count = 0
        char_count = 0
        link_count = 0
        image_count = 0
        list_count = 0
        item_count = 0
        max_heading_level = 0
        code_block_count = 0
        inline_code_count = 0
        table_count = 0
        total_paragraphs = 0
        emphasis_count = 0

        def _walk(node, current_depth):
            depths.append(current_depth)
            node_counts[node.type] = node_counts.get(node.type, 0) + 1
            
            if node.type in block_types:
                nonlocal block_count
                block_count += 1
            else:
                nonlocal inline_count
                inline_count += 1
                
            # Compute specific metrics
            if node.type == 'text' and getattr(node, 'literal', None):
                nonlocal word_count, char_count
                txt = node.literal.strip()
                char_count += len(txt)
                if txt:
                    word_count += len(txt.split())
            elif node.type == 'link':
                nonlocal link_count
                link_count += 1
            elif node.type == 'image':
                nonlocal image_count
                image_count += 1
            elif node.type == 'list':
                nonlocal list_count
                list_count += 1
            elif node.type == 'item':
                nonlocal item_count
                item_count += 1
            elif node.type == 'heading':
                nonlocal max_heading_level
                level = getattr(node, 'level', 0)
                if level > max_heading_level:
                    max_heading_level = level
            elif node.type == 'code_block':
                nonlocal code_block_count
                code_block_count += 1
            elif node.type == 'code':
                nonlocal inline_code_count
                inline_code_count += 1
            elif node.type == 'table':
                nonlocal table_count
                table_count += 1
            elif node.type == 'paragraph':
                nonlocal total_paragraphs
                total_paragraphs += 1
            elif node.type in ('strong', 'emph'):
                nonlocal emphasis_count
                emphasis_count += 1

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
        
        avg_tokens_per_block = round(len(tokens) / block_count, 2) if block_count > 0 else 0

        return {
            "total_tokens": len(tokens),
            "tokens_breakdown": sorted_tokens,
            "total_nodes": sum(node_counts.values()) if node_counts else 0,
            "nodes_breakdown": sorted_nodes,
            "max_depth": max_depth,
            "avg_depth": round(avg_depth, 2),
            "block_nodes": block_count,
            "inline_nodes": inline_count,
            
            # New metrics mapped to frontend
            "advanced": {
                "word_count": word_count,
                "char_count": char_count,
                "link_count": link_count,
                "image_count": image_count,
                "list_count": list_count,
                "item_count": item_count,
                "max_heading_level": max_heading_level,
                "code_block_count": code_block_count,
                "inline_code_count": inline_code_count,
                "table_count": table_count,
                "total_paragraphs": total_paragraphs,
                "emphasis_count": emphasis_count,
                "avg_tokens_per_block": avg_tokens_per_block
            }
        }
