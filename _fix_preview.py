#!/usr/bin/env python3
"""Patch renderPreview to inline render.css instead of linking it."""

import os

filepath = os.path.join(os.path.dirname(__file__), 'frontend', 'templates', 'index.html')

with open(filepath, 'r') as f:
    content = f.read()

# The old function start
old_start = 'function renderPreview(htmlStr) {'
new_start = """// Cache for render.css content
let _renderCSSCache = null;
async function _fetchRenderCSS() {
  if (_renderCSSCache !== null) return _renderCSSCache;
  try {
    const resp = await fetch('/static/render.css');
    _renderCSSCache = await resp.text();
  } catch (e) {
    console.error('Failed to load render.css:', e);
    _renderCSSCache = '';
  }
  return _renderCSSCache;
}

async function renderPreview(htmlStr) {"""

# Replace the function declaration
content = content.replace(old_start, new_start, 1)

# Replace the <base> + <link render.css> approach with inlined <style>
old_head = """    <base href="/">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
    <link rel="stylesheet" href="/static/render.css">"""

new_head = """    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
    <style>${renderCSS}</style>"""

content = content.replace(old_head, new_head, 1)

# Add the renderCSS fetch before the previewHTML template
old_preview_start = """  const previewHTML = `<!DOCTYPE html><html><head>"""
new_preview_start = """  const renderCSS = await _fetchRenderCSS();

  const previewHTML = `<!DOCTYPE html><html><head>"""

content = content.replace(old_preview_start, new_preview_start, 1)

with open(filepath, 'w') as f:
    f.write(content)

print("SUCCESS: Patched renderPreview to inline render.css")
