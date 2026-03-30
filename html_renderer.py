class HtmlRenderer:
    def __init__(self):
        self.buffer = []
        
    def escape(self, text):
        text = str(text)
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        text = text.replace("'", "&#x27;")
        return text

    def _text_content(self, node: dict) -> str:
        """Recursively extract plain text from a node subtree (used for alt attributes)."""
        if node.get("literal") is not None:
            return str(node["literal"])
        return "".join(self._text_content(c) for c in node.get("children", []))
        
    def render(self, ir_dict):
        self.buffer = []
        self._render_node(ir_dict)
        return "".join(self.buffer)
        
    def _render_node(self, node, tight=False):
        node_type = node.get("type")
        
        if node_type == "document":
            for child in node.get("children", []):
                self._render_node(child)
                
        elif node_type == "heading":
            level = node.get("level", 1)
            custom_id = node.get("custom_id")
            id_attr = f' id="{self.escape(custom_id)}"' if custom_id else ""
            self.buffer.append(f"<h{level}{id_attr}>")
            for child in node.get("children", []):
                self._render_node(child)
            self.buffer.append(f"</h{level}>\n")
            
        elif node_type == "paragraph":
            if tight:
                for child in node.get("children", []):
                    self._render_node(child)
            else:
                self.buffer.append("<p>")
                for child in node.get("children", []):
                    self._render_node(child)
                self.buffer.append("</p>\n")
            
        elif node_type == "block_quote":
            self.buffer.append("<blockquote>\n")
            for child in node.get("children", []):
                self._render_node(child)
            self.buffer.append("</blockquote>\n")
            
        elif node_type == "text":
            self.buffer.append(self.escape(node.get("literal", "")))
            
        elif node_type == "strong":
            self.buffer.append("<strong>")
            for child in node.get("children", []):
                self._render_node(child)
            self.buffer.append("</strong>")
            
        elif node_type == "emph":
            self.buffer.append("<em>")
            for child in node.get("children", []):
                self._render_node(child)
            self.buffer.append("</em>")
            
        elif node_type == "code_block":
            info = node.get("info", "")
            class_attr = f' class="language-{self.escape(info)}"' if info else ""
            self.buffer.append(f"<pre><code{class_attr}>\n")
            self.buffer.append(self.escape(node.get("literal", "")))
            self.buffer.append("</code></pre>\n")
            
        elif node_type == "code":
            self.buffer.append("<code>")
            self.buffer.append(self.escape(node.get("literal", "")))
            self.buffer.append("</code>")
            
        elif node_type == "link":
            dest = self.escape(node.get("destination", ""))
            if dest.startswith("javascript:"):
                dest = ""
            self.buffer.append(f'<a href="{dest}">')
            for child in node.get("children", []):
                self._render_node(child)
            self.buffer.append("</a>")

        elif node_type == "image":
            dest = self.escape(node.get("destination", ""))
            alt  = self.escape(self._text_content(node))
            self.buffer.append(f'<img src="{dest}" alt="{alt}" />')

        elif node_type == "video":
            dest    = self.escape(node.get("destination", ""))
            caption = self.escape(node.get("title", ""))
            self.buffer.append(f'<video controls>\n')
            self.buffer.append(f'  <source src="{dest}" />\n')
            if caption:
                self.buffer.append(f'  {caption}\n')
            self.buffer.append('</video>\n')
            
        elif node_type == "list":
            tag = "ul" if node.get("list_type") == "bullet" else "ol"
            self.buffer.append(f"<{tag}>\n")
            for child in node.get("children", []):
                self._render_node(child)
            self.buffer.append(f"</{tag}>\n")
            
        elif node_type == "item":
            self.buffer.append("<li>")
            for child in node.get("children", []):
                self._render_node(child, tight=True)
            self.buffer.append("</li>\n")
            
        elif node_type == "mark":
            self.buffer.append("<mark>")
            for child in node.get("children", []):
                self._render_node(child)
            self.buffer.append("</mark>")
            
        elif node_type == "u":
            self.buffer.append("<u>")
            for child in node.get("children", []):
                self._render_node(child)
            self.buffer.append("</u>")
            
        elif node_type == "del":
            self.buffer.append("<del>")
            for child in node.get("children", []):
                self._render_node(child)
            self.buffer.append("</del>")
            
        elif node_type == "table":
            self.buffer.append("<table border=\"1\">\n")
            for child in node.get("children", []):
                self._render_node(child)
            self.buffer.append("</table>\n")
            
        elif node_type == "table_row":
            self.buffer.append("<tr>\n")
            for child in node.get("children", []):
                self._render_node(child)
            self.buffer.append("</tr>\n")
            
        elif node_type == "table_header":
            self.buffer.append("<th>")
            for child in node.get("children", []):
                self._render_node(child, tight=True)
            self.buffer.append("</th>\n")
            
        elif node_type == "table_cell":
            self.buffer.append("<td>")
            for child in node.get("children", []):
                self._render_node(child, tight=True)
            self.buffer.append("</td>\n")
            
        elif node_type == "math_block":
            self.buffer.append("<div class=\"math math-display\">\n")
            self.buffer.append(self.escape(node.get("literal", "")))
            self.buffer.append("</div>\n")
            
        elif node_type == "mermaid_block":
            self.buffer.append("<pre class=\"mermaid\">\n")
            self.buffer.append(node.get("literal", ""))
            self.buffer.append("</pre>\n")
            
        elif node_type == "footnote_def":
            label = self.escape(node.get("label", ""))
            self.buffer.append(f"<div class=\"footnote\" id=\"fn:{label}\">\n")
            
            children = node.get("children", [])
            if children and children[0].get("type") == "paragraph":
                self.buffer.append("<p>")
                self.buffer.append(f"<strong>[{label}]:</strong> ")
                for inline_child in children[0].get("children", []):
                    self._render_node(inline_child)
                self.buffer.append("</p>\n")
                for child in children[1:]:
                    self._render_node(child)
            else:
                self.buffer.append(f"<strong>[{label}]:</strong> ")
                for child in children:
                    self._render_node(child)
                    
            self.buffer.append("</div>\n")
            
        elif node_type == "def_list":
            self.buffer.append("<dl>\n")
            for child in node.get("children", []):
                self._render_node(child)
            self.buffer.append("</dl>\n")
            
        elif node_type == "def_term":
            self.buffer.append("<dt>")
            for child in node.get("children", []):
                self._render_node(child)
            self.buffer.append("</dt>\n")
            
        elif node_type == "def_item":
            self.buffer.append("<dd>")
            for child in node.get("children", []):
                self._render_node(child)
            self.buffer.append("</dd>\n")
            
        elif node_type == "sub":
            self.buffer.append("<sub>")
            for child in node.get("children", []):
                self._render_node(child)
            self.buffer.append("</sub>")
            
        elif node_type == "sup":
            self.buffer.append("<sup>")
            for child in node.get("children", []):
                self._render_node(child)
            self.buffer.append("</sup>")
            
        elif node_type == "math_inline":
            self.buffer.append("<span class=\"math math-inline\">")
            self.buffer.append(self.escape(node.get("literal", "")))
            self.buffer.append("</span>")
            
        elif node_type == "footnote_ref":
            label = self.escape(node.get("label", ""))
            self.buffer.append(f"<sup><a href=\"#fn:{label}\">^{label}</a></sup>")
            
        elif node_type == "emoji":
            self.buffer.append(self.escape(node.get("literal", "")))
            
        elif node_type == "task_checkbox":
            checked = " checked" if node.get("checked", False) else ""
            self.buffer.append(f"<input type=\"checkbox\" disabled{checked}>")
            
        elif node_type == "hardbreak":
            self.buffer.append("<br />\n")
            
        elif node_type == "softbreak":
            self.buffer.append("<br />\n")
            
        elif node_type == "html_block":
            self.buffer.append(node.get("literal", ""))
            
        elif node_type == "html_inline":
            self.buffer.append(node.get("literal", ""))
