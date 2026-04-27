import os
import sys
import json
from flask import Flask, render_template, request, jsonify, Response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

_compiler_dir = os.path.join(BASE_DIR, 'compiler')
if _compiler_dir not in sys.path:
    sys.path.insert(0, _compiler_dir)

from backend import (
    Lexer,
    Parser,
    SemanticAnalyzer,
    ASTVisualizer,
    CSTVisualizer,
    AnalyticsGenerator,
    HtmlRenderer,
)

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'frontend', 'templates'),
    static_folder=os.path.join(BASE_DIR, 'frontend', 'static'),
)

app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.after_request
def _no_cache(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

_SAMPLE_MD_PATH = os.path.join(BASE_DIR, 'docs/test.md')
_FALLBACK_MD = "# Hello World\n\nWelcome to the **Markdown Compiler** visualizer.\n\n"

def _load_sample() -> str:
    try:
        with open(_SAMPLE_MD_PATH, encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return _FALLBACK_MD

def _run_pipeline(md_input: str) -> dict:
    lexer = Lexer()
    tokens = lexer.tokenize(md_input)
    token_list = []
    
    for t in tokens:
        t_type = getattr(t, "type", "")
        token_list.append({
            "type": t_type, 
            "value": getattr(t, "value", ""), 
            "line": getattr(t, "indent", 0)
        })
        
        text_content = ""
        if t_type == "PARAGRAPH":
            text_content = getattr(t, "value", "")
        elif t_type == "ATX_HEADING":
            text_content = getattr(t, "meta", {}).get("content", "")
        elif t_type == "TABLE_ROW":
            text_content = " ".join(getattr(t, "meta", {}).get("cells", []))
        elif t_type in ("BLOCKQUOTE", "ORDERED_LIST", "BULLET_LIST"):
            text_content = getattr(t, "meta", {}).get("content", "")
            
        if text_content:
            try:
                inlines = lexer.tokenize_inline(text_content)
                for it in inlines:
                    token_list.append({
                        "type": getattr(it, "type", ""),
                        "value": getattr(it, "value", ""),
                        "line": getattr(t, "indent", 0)
                    })
            except Exception:
                pass

    parser = Parser()
    ast_root = parser.parse(md_input)

    ast_vis = ASTVisualizer()
    vis_tree = ast_vis.to_vis_tree(ast_root)

    cst_vis = CSTVisualizer()
    cst_tree = cst_vis.to_cst_tree(ast_root)
    
    analytics = AnalyticsGenerator()
    analytics_stats = analytics.generate_stats(tokens, ast_root)

    ir_data = ast_root.to_dict()

    renderer = HtmlRenderer()
    body_html = renderer.render(ir_data)

    return {
        "lexer": {
            "token_count": len(token_list),
            "tokens": token_list,
        },
        "parser": {
            "vis_tree": vis_tree,
            "cst_tree": cst_tree,
        },
        "analytics": analytics_stats,
        "ir": ir_data,
        "codegen": {
            "html": body_html,
            "html_length": len(body_html),
        },
    }

@app.route('/')
def index():
    sample = _load_sample()
    return render_template('index.html', sample_markdown=sample)

@app.route('/compile', methods=['POST'])
def compile_endpoint():
    data = request.get_json(silent=True) or {}
    md_input = data.get('markdown', '')

    if not md_input.strip():
        return jsonify({"error": "Empty input"}), 400

    try:
        phases = _run_pipeline(md_input)
        return jsonify({"success": True, "phases": phases})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

@app.route('/upload', methods=['POST'])
def upload_endpoint():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.lower().endswith('.md'):
        return jsonify({"error": "Only .md files accepted"}), 400

    md_input = file.read().decode('utf-8')
    if not md_input.strip():
        return jsonify({"error": "Uploaded file is empty"}), 400

    try:
        phases = _run_pipeline(md_input)
        return jsonify({
            "success": True,
            "filename": file.filename,
            "markdown": md_input,
            "phases": phases,
        })
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500

@app.route('/download', methods=['POST'])
def download_endpoint():
    data = request.get_json(silent=True) or {}
    body_html = data.get('html', '')
    filename = data.get('filename', 'output').removesuffix('.md')

    template_path = os.path.join(BASE_DIR, 'frontend', 'templates', 'template.html')
    try:
        with open(template_path, encoding='utf-8') as f:
            template = f.read()
    except FileNotFoundError:
        template = '<!DOCTYPE html><html><head><title>__TITLE__</title></head><body>__BODY_HTML__</body></html>'

    full_html = template.replace('__TITLE__', filename).replace('__BODY_HTML__', body_html)

    return Response(
        full_html,
        mimetype='text/html',
        headers={'Content-Disposition': f'attachment; filename="{filename}.html"'},
    )

if __name__ == '__main__':
    bar = '═' * 52
    print(bar)
    print('  Markdown Compiler — Interactive Web UI (API)')
    print('  Open http://localhost:5001 in your browser')
    print(bar)
    app.run(debug=True, port=5001)
