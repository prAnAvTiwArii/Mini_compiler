import re
from node import Node
import html
import urllib.parse
from regex_rules import *

class InlineParser:
    def __init__(self):
        self.subject = ""
        self.pos = 0
        self.refmap = {}

    def parse(self, block_node):
        self.subject = block_node.string_content.strip()
        self.pos = 0
        self.parse_inlines(block_node)
        block_node.string_content = ""

    def peek(self):
        if self.pos < len(self.subject):
            return self.subject[self.pos]
        return ''

    def match(self, pattern):
        m = pattern.match(self.subject, self.pos)
        if m:
            self.pos = m.end()
            return m.group(0)
        return None

    def parse_inlines(self, block):
        for m in inline_token_pattern.finditer(self.subject):
            token = m.group(0)
            if not token: continue

            if token.startswith('![') and '](' in token and token.endswith(')'):
                node = Node('image')
                label, rest = token[2:].split('](', 1)
                dest = rest[:-1]
                node.destination = dest
                node.title = label # Using literal title mapping for alt
                text_child = Node('text')
                text_child.literal = label
                node.append_child(text_child)
                block.append_child(node)
                
            elif token.startswith('[') and '](' in token and token.endswith(')'):
                node = Node('link')
                label, rest = token[1:].split('](', 1)
                dest = rest[:-1]
                node.destination = dest
                text_child = Node('text')
                text_child.literal = label
                node.append_child(text_child)
                block.append_child(node)
                
            elif (token.startswith('**') and token.endswith('**')) or (token.startswith('__') and token.endswith('__')):
                node = Node('strong')
                text_child = Node('text')
                text_child.literal = token[2:-2]
                node.append_child(text_child)
                block.append_child(node)
                
            elif (token.startswith('*') and token.endswith('*')) or (token.startswith('_') and token.endswith('_')):
                node = Node('emph')
                text_child = Node('text')
                text_child.literal = token[1:-1]
                node.append_child(text_child)
                block.append_child(node)
                
            elif token.startswith('==') and token.endswith('=='):
                node = Node('mark')
                text_child = Node('text')
                text_child.literal = token[2:-2]
                node.append_child(text_child)
                block.append_child(node)
                
            elif token.startswith('++') and token.endswith('++'):
                node = Node('u')
                text_child = Node('text')
                text_child.literal = token[2:-2]
                node.append_child(text_child)
                block.append_child(node)
                
            elif token.startswith('~~') and token.endswith('~~'):
                node = Node('del')
                text_child = Node('text')
                text_child.literal = token[2:-2]
                node.append_child(text_child)
                block.append_child(node)
                
            elif token.startswith('~') and token.endswith('~'):
                node = Node('sub')
                text_child = Node('text')
                text_child.literal = token[1:-1]
                node.append_child(text_child)
                block.append_child(node)
                
            elif token.startswith('^') and token.endswith('^'):
                node = Node('sup')
                text_child = Node('text')
                text_child.literal = token[1:-1]
                node.append_child(text_child)
                block.append_child(node)
                
            elif token.startswith('$') and token.endswith('$'):
                node = Node('math_inline')
                node.literal = token[1:-1]
                block.append_child(node)
                
            elif token.startswith('[^') and token.endswith(']'):
                node = Node('footnote_ref')
                node.label = token[2:-1]
                block.append_child(node)
                
            elif token.startswith(':') and token.endswith(':'):
                node = Node('emoji')
                node.literal = token
                block.append_child(node)
                
            elif token in ('[ ]', '[x]', '[X]'):
                node = Node('task_checkbox')
                node.checked = token.lower() == '[x]'
                block.append_child(node)
                
            elif token.startswith('`') and token.endswith('`'):
                node = Node('code')
                # Strip backticks
                strip_len = len(token) - len(token.lstrip('`'))
                node.literal = token[strip_len:-strip_len].strip()
                block.append_child(node)
                
            elif token.startswith('<') and token.endswith('>') and not token.startswith('</') and '@' in token and ' ' not in token:
                # Email autolink
                dest = token[1:-1]
                node = Node('link')
                node.destination = 'mailto:' + dest
                text_child = Node('text')
                text_child.literal = dest
                node.append_child(text_child)
                block.append_child(node)
                
            elif token.startswith('<') and token.endswith('>') and ':' in token and not token.startswith('</') and ' ' not in token:
                # URI autolink
                dest = token[1:-1]
                node = Node('link')
                node.destination = urllib.parse.quote(dest, safe=":/?#[]@!$&'()*+,;=")
                text_child = Node('text')
                text_child.literal = dest
                node.append_child(text_child)
                block.append_child(node)
                
            elif token.startswith('<') and token.endswith('>'):
                node = Node('html_inline')
                node.literal = token
                block.append_child(node)
                
            elif token.startswith('&') and token.endswith(';'):
                node = Node('text')
                node.literal = html.unescape(token)
                block.append_child(node)
                
            elif token == '  \n':
                node = Node('hardbreak')
                block.append_child(node)
                
            elif token.startswith('\\') and len(token) == 2:
                # Escaped character
                node = Node('text')
                node.literal = token[1]
                block.append_child(node)
                
            elif token == '\n':
                node = Node('softbreak')
                block.append_child(node)
                
            else:
                # Regular text
                node = Node('text')
                node.literal = token
                block.append_child(node)

class Parser:
    def __init__(self):
        self.inline_parser = InlineParser()
        self.doc = Node('document')
        self.tip = self.doc
        self.current_line = ""
        self.line_number = 0
        self.offset = 0
        self.indent = 0
        self.blank = False
        
    def parse(self, text):
        self.doc = Node('document')
        self.tip = self.doc
        
        lines = reLineEnding.split(text)
        if text and text[-1] == '\n':
            lines.pop()
            
        for line in lines:
            self.line_number += 1
            self.incorporate_line(line)
            
        # Close all open blocks
        while self.tip:
            self.tip.is_open = False
            self.tip = self.tip.parent
            
        # Phase 2: Inline Parsing
        self.process_inlines(self.doc)
        return self.doc

    def incorporate_line(self, line):
        self.current_line = line
        stripped_line = line.lstrip()
        self.indent = len(line) - len(stripped_line)
        self.blank = len(stripped_line) == 0
        
        # Test block rules with a single combined regex using named groups
        block_match = block_token_pattern.match(stripped_line)
        block_group = block_match.lastgroup if block_match else None
        
        # 0. Check for open Raw Blocks Continuation (HTML / Code / Math / Mermaid)
        if self.tip and getattr(self.tip, 'is_open', False):
            if self.tip.type in ('code_block', 'math_block', 'mermaid_block'):
                # Check for closing fence
                if self.tip.type == 'code_block' and getattr(self.tip, 'is_fenced', False):
                    if block_group == 'code_fence' and block_match.group('code_fence')[0] == self.tip.fence_char and len(block_match.group('code_fence')) >= self.tip.fence_length:
                        self.tip.is_open = False
                        self.tip = self.tip.parent
                        return
                elif self.tip.type == 'math_block' and block_group == 'math_fence':
                    self.tip.is_open = False
                    self.tip = self.tip.parent
                    return
                elif self.tip.type == 'mermaid_block' and block_group == 'mermaid_close':
                    self.tip.is_open = False
                    self.tip = self.tip.parent
                    return
                
                # If not closing, it's content
                self.tip.string_content += line + '\n'
                return
                
            elif self.tip.type == 'html_block':
                if self.blank:
                    self.tip.is_open = False
                    self.tip = self.tip.parent
                else:
                    self.tip.literal += '\n' + line
                return

        # 1. Blockquote
        if stripped_line.startswith('>'):
            if not self.tip or self.tip.type != 'block_quote' or not getattr(self.tip, 'is_open', False):
                bq = Node('block_quote')
                self.doc.append_child(bq)
                self.tip = bq
            
            p = Node('paragraph')
            # Remove > and optional leading space
            content = stripped_line[1:]
            if content.startswith(' '): content = content[1:]
            p.string_content = content
            self.tip.append_child(p)
            self.tip = p
            return

        # 2. ATX Heading
        if block_group == 'atx_heading':
            heading = Node('heading')
            heading.level = len(block_match.group('atx_heading').strip())
            # strip trailing hashes
            raw_content = stripped_line[heading.level:].strip().rstrip('#').strip()
            
            # Check for Heading ID {#custom-id}
            id_match = reHeadingID.search(raw_content)
            if id_match:
                heading.custom_id = id_match.group(1)
                raw_content = raw_content[:id_match.start()].strip()
                
            heading.string_content = raw_content
            self.doc.append_child(heading)
            self._close_tip_if_paragraph()
            return

        # 2a. Footnote Definitions
        if block_group == 'footnote_def':
            fn = Node('footnote_def')
            # Extract the actual groups matched within the footnote_def named group
            # We have to re-evaluate the capturing groups since lastgroup only gives the name
            fn_match = re.match(r'^\[\^([^\]]+)\]:[ \t]*(.*)', stripped_line)
            if fn_match:
                fn.label = fn_match.group(1)
                content = fn_match.group(2)
            else:
                fn.label = "unknown"
                content = ""
            self.doc.append_child(fn)
            self._close_tip_if_paragraph()
            self.tip = fn
            
            if content:
                p = Node('paragraph')
                p.string_content = content
                fn.append_child(p)
                self.tip = p
            return

        # 2b. Definition Lists
        if block_group == 'def_list_marker':
            def_match = re.match(r'^:[ \t]+(.*)', stripped_line)
            # If the previous block was a paragraph, we construct a definition list
            if self.tip and self.tip.type == 'paragraph':
                # Convert the paragraph into a definition list term
                term_content = self.tip.string_content
                self.tip.is_open = False
                
                # Check if it's already part of a definition list
                if self.tip.parent and self.tip.parent.type == 'def_list':
                    dl = self.tip.parent
                else:
                    dl = Node('def_list')
                    # Replace paragraph with def_list in the tree
                    self.tip.insert_after(dl)
                    dl.append_child(self.tip) # Keep paragraph as the first child of dl (the term)
                    self.tip.type = 'def_term' # repurpose it
                
                # Add the new definition item
                di = Node('def_item')
                dl.append_child(di)
                
                # Add the content of the definition
                dp = Node('paragraph')
                dp.string_content = def_match.group(1)
                di.append_child(dp)
                self.tip = dp
                return
            elif self.tip and self.tip.type in ('def_item', 'def_term'):
                # Continued definition list
                dl = self.tip.parent if self.tip.type == 'def_item' else self.tip.parent
                di = Node('def_item')
                dl.append_child(di)
                dp = Node('paragraph')
                dp.string_content = def_match.group(1)
                di.append_child(dp)
                self.tip = dp
                return

        # 3. Thematic Break
        if block_group == 'thematic_break':
            tbreak = Node('thematic_break')
            self.doc.append_child(tbreak)
            self._close_tip_if_paragraph()
            return

        # Attempt to open new fences
        if block_group == 'code_fence':
            cb = Node('code_block')
            cb.is_fenced = True
            cb.fence_char = block_match.group('code_fence')[0]
            cb.fence_length = len(block_match.group('code_fence'))
            cb.info = stripped_line[cb.fence_length:].strip()
            
            # Devops specification: ```mermaid is a mermaid block
            if cb.info.lower() == 'mermaid':
                cb.type = 'mermaid_block'
                
            cb.string_content = ""
            self.doc.append_child(cb)
            self._close_tip_if_paragraph()
            self.tip = cb
            return
            
        if block_group == 'math_fence':
            mb = Node('math_block')
            mb.string_content = ""
            self.doc.append_child(mb)
            self._close_tip_if_paragraph()
            self.tip = mb
            return
            
        if block_group == 'mermaid_fence':
            mm = Node('mermaid_block')
            mm.string_content = ""
            self.doc.append_child(mm)
            self._close_tip_if_paragraph()
            self.tip = mm
            return

        # 5. Lists (Bullet and Ordered)
        is_list_item = False
        list_type = None
        list_start = None
        content = ""
        
        if block_group == 'bullet_list':
            is_list_item = True
            list_type = 'bullet'
            content = stripped_line[len(block_match.group('bullet_list')):]
        elif block_group == 'ordered_list':
            is_list_item = True
            list_type = 'ordered'
            list_start = int(re.search(r'\d+', block_match.group('ordered_list')).group()) # The number group
            content = stripped_line[len(block_match.group('ordered_list')):]
            
        if is_list_item:
            self._close_tip_if_paragraph()
            
            # Find the nearest open list and check its indentation
            current = self.tip
            target_list = None
            
            while current:
                if current.type == 'list' and getattr(current, 'is_open', False):
                    list_indent = getattr(current, 'indent', 0)
                    if self.indent < list_indent:
                        current.is_open = False
                    elif self.indent >= list_indent:
                        target_list = current
                        break
                current = current.parent
                
            if target_list is not None:
                target_indent = getattr(target_list, 'indent', 0)
                if self.indent > target_indent and target_list.last_child and target_list.last_child.type == 'item':
                    # Nesting: create a new list inside the last item
                    lst = Node('list')
                    lst.list_type = list_type
                    lst.list_start = list_start
                    lst.is_open = True
                    lst.indent = self.indent
                    target_list.last_child.append_child(lst)
                    self.tip = lst
                else:
                    # Same level list
                    if target_list.list_type == list_type:
                        self.tip = target_list
                    else:
                        target_list.is_open = False
                        lst = Node('list')
                        lst.list_type = list_type
                        lst.list_start = list_start
                        lst.is_open = True
                        lst.indent = self.indent
                        if target_list.parent:
                            target_list.parent.append_child(lst)
                        else:
                            self.doc.append_child(lst)
                        self.tip = lst
            else:
                # No open list found, create a new one
                lst = Node('list')
                lst.list_type = list_type
                lst.list_start = list_start
                lst.is_open = True
                lst.indent = self.indent
                
                # Append to tip if tip can hold a list
                if self.tip and getattr(self.tip, 'is_open', False) and self.tip.type in ('document', 'block_quote', 'item'):
                    self.tip.append_child(lst)
                elif self.tip and self.tip.parent:
                    self.tip.parent.append_child(lst)
                else:
                    self.doc.append_child(lst)
                self.tip = lst
                
            item = Node('item')
            self.tip.append_child(item)
            
            p = Node('paragraph')
            p.string_content = content
            item.append_child(p)
            self.tip = p
            return

        # 6. Simple Tables
        if stripped_line.startswith('|') and stripped_line.endswith('|'):
            if not self.tip or self.tip.type != 'table' or not getattr(self.tip, 'is_open', False):
                self._close_tip_if_paragraph()
                table = Node('table')
                table.is_open = True
                self.doc.append_child(table)
                self.tip = table
                
            if re.match(r'^\|[ \t-:|]+\|[ \t]*$', stripped_line):
                self.tip.headers_done = True
                return
                
            row = Node('table_row')
            self.tip.append_child(row)
            
            cells = [c.strip() for c in stripped_line.strip('|').split('|')]
            for cell_content in cells:
                is_header = not getattr(self.tip, 'headers_done', False)
                cell = Node('table_header' if is_header else 'table_cell')
                row.append_child(cell)
                cell.string_content = cell_content
            return

        # 7. HTML Blocks
        html_match = None
        for pattern in reHtmlBlockOpen:
            if pattern.match(stripped_line):
                html_match = True
                break
        
        if html_match:
            hb = Node('html_block')
            hb.literal = line
            hb.is_open = True
            self.doc.append_child(hb)
            self._close_tip_if_paragraph()
            self.tip = hb
            return

        # 7. Blank lines
        if self.blank:
            if self.tip and getattr(self.tip, 'is_open', False):
                self.tip.is_open = False
            return
            
        # 8. Paragraphs and Paragraph Continuation
        if self.tip and self.tip.type == 'paragraph' and self.tip.is_open:
            self.tip.string_content += '\n' + stripped_line
        else:
            p = Node('paragraph')
            p.string_content = stripped_line
            if self.tip and self.tip.type in ('block_quote', 'item') and getattr(self.tip, 'is_open', False):
                self.tip.append_child(p)
            else:
                self.doc.append_child(p)
            self.tip = p

    def _close_tip_if_paragraph(self):
        if self.tip and self.tip.type == 'paragraph':
            self.tip.is_open = False
            self.tip = self.tip.parent

    def process_inlines(self, doc):
        """Passes flat string_content in AST nodes to Phase 2 tokenization."""
        walker = doc.walker()
        for node, entering in walker:
            if entering and node.type in ('paragraph', 'heading', 'table_cell', 'table_header', 'def_term') and getattr(node, 'string_content', None):
                self.inline_parser.parse(node)
                
            # Formatting Code block literal
            elif entering and node.type in ('code_block', 'math_block', 'mermaid_block'):
                node.literal = node.string_content
                node.string_content = ""
