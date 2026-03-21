import sys
sys.path.append('.')
from parser import Parser

def test():
    md = """* A
* B
  * C
    1. D
    2. E
  * F
* G"""
    p = Parser()
    ast = p.parse(md)
    print(ast.to_json())

if __name__ == "__main__":
    test()
