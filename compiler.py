import json
import sys
import os
from parser import Parser
from html_renderer import HtmlRenderer

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 compiler.py <markdown_file>")
        sys.exit(1)
        
    md_file_path = sys.argv[1]
    
    if not os.path.exists(md_file_path):
        print(f"Error: File '{md_file_path}' not found.")
        sys.exit(1)
    
    base_name = os.path.basename(md_file_path)
    title, _ = os.path.splitext(base_name)
    output_html_path = title + ".html"
    output_json_path = title + ".json"
    
    print(f"Reading from {md_file_path}...")
    with open(md_file_path, 'r', encoding='utf-8') as f:
        markdown_input = f.read()

    print("Step 1: Parsing blocks and inlines...")
    parser = Parser()
    ast_root = parser.parse(markdown_input)
    
    print("Step 2: Generating JSON IR...")
    ir_data = ast_root.to_dict()
    
    print("Step 3: Generating HTML tags...")
    renderer = HtmlRenderer()
    body_html = renderer.render(ir_data)
    
    try:
        template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html")
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        print("Error: template.html not found.")
        sys.exit(1)

    final_html = template.replace("__TITLE__", title).replace("__BODY_HTML__", body_html)
    
    print(f"Writing output to {output_html_path}...")
    with open(output_html_path, 'w', encoding='utf-8') as f:
        f.write(final_html)
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(ir_data,f, indent=2)
    print(f"Compilation successful! Wrote to {output_html_path}")

if __name__ == "__main__":
    main()
