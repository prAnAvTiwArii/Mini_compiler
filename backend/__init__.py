"""
backend package — re-exports all compiler pipeline components plus visualizers.
app.py should import from here exclusively.
"""
import sys
import os

_COMPILER_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'compiler')
if _COMPILER_DIR not in sys.path:
    sys.path.insert(0, _COMPILER_DIR)

from lexer import Lexer
from parser import Parser
from semantic_analyzer import SemanticAnalyzer
from html_renderer import HtmlRenderer
from node import Node
from lex_token import Token

from .ast_visualizer import ASTVisualizer
from .cst_visualizer import CSTVisualizer
from .analytics import AnalyticsGenerator

__all__ = [
    'Lexer',
    'Parser',
    'SemanticAnalyzer',
    'HtmlRenderer',
    'Node',
    'Token',
    'ASTVisualizer',
    'CSTVisualizer',
    'AnalyticsGenerator',
]
