import json

class Node:
    def __init__(self, node_type, sourcepos=None):
        self.type = node_type
        self.parent = None
        self.first_child = None
        self.last_child = None
        self.prev = None
        self.next = None
        self.sourcepos = sourcepos
        self.string_content = ""
        self.literal = None
        self.destination = None
        self.title = None
        self.info = None
        self.level = None
        self.is_open = True

    def append_child(self, child):
        child.unlink()
        child.parent = self
        if self.last_child:
            self.last_child.next = child
            child.prev = self.last_child
            self.last_child = child
        else:
            self.first_child = child
            self.last_child = child

    def unlink(self):
        if self.prev:
            self.prev.next = self.next
        elif self.parent:
            self.parent.first_child = self.next

        if self.next:
            self.next.prev = self.prev
        elif self.parent:
            self.parent.last_child = self.prev

        self.parent = None
        self.next = None
        self.prev = None

    def insert_after(self, sibling):
        sibling.unlink()
        sibling.next = self.next
        if sibling.next:
            sibling.next.prev = sibling
        sibling.prev = self
        self.next = sibling
        sibling.parent = self.parent
        if not sibling.next and sibling.parent:
            sibling.parent.last_child = sibling

    def walker(self):
        current = self
        entering = True
        while current:
            yield current, entering
            if entering and current.first_child:
                current = current.first_child
                entering = True
            elif current == self:
                break
            elif not current.next:
                current = current.parent
                entering = False
            else:
                current = current.next
                entering = True

    def to_dict(self):
        d = {"type": self.type}

        if self.literal is not None:
            d["literal"] = self.literal
        if self.level is not None:
            d["level"] = self.level
        if self.destination is not None:
            d["destination"] = self.destination
        if self.info is not None:
            d["info"] = self.info
        if self.title is not None:
            d["title"] = self.title

        if hasattr(self, 'custom_id') and self.custom_id is not None:
            d["custom_id"] = self.custom_id
        if hasattr(self, 'label') and self.label is not None:
            d["label"] = self.label
        if hasattr(self, 'checked') and self.checked is not None:
            d["checked"] = self.checked
        if hasattr(self, 'list_type') and self.list_type is not None:
            d["list_type"] = self.list_type

        children = []
        child = self.first_child
        while child:
            children.append(child.to_dict())
            child = child.next

        if children:
            d["children"] = children

        return d

