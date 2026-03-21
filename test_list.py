import sys
sys.path.append('.')
from parser import Parser
from html_renderer import HtmlRenderer
import json

md = """## Common Modifications

### Add a new block type:
1. Add pattern to `block_token_pattern` in `regex_rules.py`
2. Add condition in `Parser.incorporate_line()`
"""

p = Parser()
ast = p.parse(md)
h = HtmlRenderer()
html = h.render_json_ir(ast.to_dict())
print("HTML:")
print(html)
print("AST:")
print(json.dumps(ast.to_dict(), indent=2))
