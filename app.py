"""
Flask Web Application — Interactive Compiler Demo UI
Serves a web interface showing all 5 compiler phases with
interactive AST visualization using D3.js.
"""

import os
import json
from flask import Flask, render_template, request, jsonify, Response

from lexer import Lexer
from parser import Parser
from semantic_analyzer import SemanticAnalyzer
from ast_visualizer import ASTVisualizer
from cst_visualizer import CSTVisualizer
from html_renderer import HtmlRenderer

app = Flask(__name__)

# Load default sample markdown
SAMPLE_MD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "markdowns", "test.md")


def get_sample_markdown():
    try:
        with open(SAMPLE_MD_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "# Hello World\n\nThis is a **test** document.\n"


@app.route('/')
def index():
    sample = get_sample_markdown()
    return render_template('index.html', sample_markdown=sample)


@app.route('/compile', methods=['POST'])
def compile_endpoint():
    """Run all 5 phases and return results as JSON."""
    data = request.get_json()
    md_input = data.get('markdown', '')

    if not md_input.strip():
        return jsonify({"error": "Empty input"}), 400

    try:
        # Phase 1: Lexical Analysis
        lexer = Lexer()
        tokens = lexer.tokenize(md_input)
        token_list = [{"type": getattr(t, "type", ""), "value": getattr(t, "value", ""), "line": getattr(t, "indent", 0)} for t in tokens]

        # Phase 2: Parsing → AST
        parser = Parser()
        ast_root = parser.parse(md_input)

        # Phase 3: Semantic Analysis
        analyzer = SemanticAnalyzer()
        analysis = analyzer.analyze(ast_root)

        # Phase 4: IR Generation (JSON)
        ir_data = ast_root.to_dict()

        # AST Visualization data (for D3.js)
        visualizer = ASTVisualizer()
        vis_tree = visualizer.to_vis_tree(ast_root)

        # CST Visualization data
        cst_vis = CSTVisualizer()
        cst_tree = cst_vis.to_cst_tree(ast_root)

        # Phase 5: Code Generation (HTML)
        renderer = HtmlRenderer()
        body_html = renderer.render(ir_data)

        return jsonify({
            "success": True,
            "phases": {
                "lexer": {
                    "token_count": len(token_list),
                    "tokens": token_list
                },
                "parser": {
                    "vis_tree": vis_tree,
                    "cst_tree": cst_tree
                },
                "semantic": analysis,
                "ir": ir_data,
                "codegen": {
                    "html": body_html,
                    "html_length": len(body_html)
                }
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/parse-tree', methods=['POST'])
def parse_tree_endpoint():
    """Generates and returns the JSON CST based on grammar rules."""
    data = request.get_json()
    md_input = data.get('markdown', '')

    if not md_input.strip():
        return jsonify({"error": "Empty input"}), 400

    try:
        lexer = Lexer()
        tokens = lexer.tokenize(md_input)
        parser = Parser()
        ast_root = parser.parse(md_input)
        cst_vis = CSTVisualizer()
        cst_tree = cst_vis.to_cst_tree(ast_root)

        return jsonify({
            "success": True,
            "parse_tree": cst_tree
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/upload', methods=['POST'])
def upload_endpoint():
    """Accept a .md file upload, compile it, and return results."""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith('.md'):
        return jsonify({"error": "Only .md files are accepted"}), 400

    md_input = file.read().decode('utf-8')
    if not md_input.strip():
        return jsonify({"error": "Uploaded file is empty"}), 400

    try:
        lexer = Lexer()
        tokens = lexer.tokenize(md_input)
        token_list = [{"type": getattr(t, "type", ""), "value": getattr(t, "value", ""), "line": getattr(t, "indent", 0)} for t in tokens]

        parser = Parser()
        ast_root = parser.parse(md_input)

        analyzer = SemanticAnalyzer()
        analysis = analyzer.analyze(ast_root)

        ir_data = ast_root.to_dict()

        visualizer = ASTVisualizer()
        vis_tree = visualizer.to_vis_tree(ast_root)

        cst_vis = CSTVisualizer()
        cst_tree = cst_vis.to_cst_tree(ast_root)

        renderer = HtmlRenderer()
        body_html = renderer.render(ir_data)

        return jsonify({
            "success": True,
            "filename": file.filename,
            "markdown": md_input,
            "phases": {
                "lexer": {"token_count": len(token_list), "tokens": token_list},
                "parser": {"vis_tree": vis_tree, "cst_tree": cst_tree},
                "semantic": analysis,
                "ir": ir_data,
                "codegen": {"html": body_html, "html_length": len(body_html)}
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/download', methods=['POST'])
def download_endpoint():
    """Generate a full HTML file from body HTML and send as download."""
    import os as _os
    data = request.get_json()
    body_html = data.get('html', '')
    filename = data.get('filename', 'output')

    # Strip .md extension if present
    if filename.lower().endswith('.md'):
        filename = filename[:-3]

    try:
        template_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "templates", "template.html")
        with open(template_path, 'r', encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        template = '<!DOCTYPE html><html><head><title>__TITLE__</title></head><body>__BODY_HTML__</body></html>'

    full_html = template.replace('__TITLE__', filename).replace('__BODY_HTML__', body_html)

    return Response(
        full_html,
        mimetype='text/html',
        headers={'Content-Disposition': f'attachment; filename="{filename}.html"'}
    )


if __name__ == '__main__':
    print("═" * 50)
    print("  Markdown Compiler — Interactive Web UI")
    print("  Open http://localhost:5001 in your browser")
    print("═" * 50)
    app.run(debug=True, port=5001)
