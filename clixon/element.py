import re
import json
from typing import Optional

import xmltodict


class Element(object):
    def __init__(self, name: str, attributes: Optional[dict] = {},
                 cdata: Optional[str] = "", data: Optional[str] = "") -> None:
        """
        Create a new element.
        """

        self.attributes = attributes
        self._children = []
        self._is_root = False

        if data != "":
            self.cdata = data
        else:
            self.cdata = cdata

        self._origname = name

        if name:
            name = name.replace("-", "_")
            name = name.replace(".", "_")
            name = name.replace(":", "_")

        self._name = name
        self._parent = None

        self.clixon_element = False
        self.clixon_operation = ""
        self.clixon_path = ""

        self.last_container = ""
        self.last_list = ""
        self.yin_structure = {}

    def is_root(self, boolean: bool) -> None:
        """
        Set the element as root.
        """

        self._is_root = boolean

    def origname(self) -> str:
        """
        Return the original name of the element.
        """

        if self._origname == "":
            return self._name
        return self._origname

    def create(
            self, name: str, attributes: Optional[dict] = {},
            cdata: Optional[str] = "",
            data: Optional[str] = "",
            element: Optional[object] = None,
            clixon: Optional[bool] = False,
            operation: Optional[str] = "create"
    ) -> None:
        """
        Create a new element.
        """

        if not element:
            element = Element(name, attributes)

            if data != "":
                element.cdata = data
            else:
                element.cdata = cdata

        if clixon:
            element.clixon_element = True
            element.clixon_operation = operation

        element._parent = self

        self._children.append(element)

    def rename(self, name: str, origname: str) -> None:
        """
        Rename the element.
        """

        self._name = name
        self._origname = origname

    def get_name(self) -> str:
        """
        Return the name of the element.
        """

        return self._name

    def add(self, element: object) -> None:
        """
        Add an element to the children of the element.
        """

        self._children.append(element)

    def delete(self, name: str) -> None:
        """
        Delete an element from the children of the element.
        """

        index = 0

        if name == "*":
            self._children = []
            return

        for child in self._children:
            if child._origname == name:
                del self._children[index]
            index += 1

    def set_attributes(self, attributes: dict) -> None:
        """
        Set the attributes of the element.
        """

        self.attributes = attributes

    def update_attributes(self, attributes: dict) -> None:
        """
        Update the attributes of the element.
        """

        old_attributes = self.get_attributes()
        new_attributes = attributes | old_attributes

        self.set_attributes(new_attributes)

    def get_attributes(self, key: Optional[str] = None) -> Optional[dict]:
        """
        Return the attributes of the element.
        """

        if key:
            return self.attributes.get(key)
        return self.attributes

    def get_elements(self, name: Optional[str] = "",
                     data: Optional[str] = "") -> list:
        """
        Return the children of the element.
        """

        name = name.replace("-", "_")

        if name:
            elements = [e for e in self._children if e._name == name]
        else:
            elements = self._children

        if data:
            return [e for e in elements if e.get_data() == data]

        return elements

    def get_attributes_str(self) -> str:
        """
        Return the attributes of the element as a string.
        """

        attr_string = ""
        if self.attributes and self.attributes != {}:
            for key in self.attributes.keys():
                value = self.attributes[key]
                attr_string += f" {key}=\"{value}\""
        return attr_string

    def set_data(self, data: str) -> None:
        """
        Set the data of the element.
        """

        self.cdata = data

    def get_data(self) -> str:
        """
        Return the data of the element.
        """

        return self.cdata

    def set_creator(self, element: bool, operation: str) -> None:
        """
        Set the creator of the element.
        """

        self.clixon_element = element
        self.clixon_operation = operation

    def get_creator(self) -> tuple:
        """
        Return the creator of the element.
        """

        return self.clixon_element, self.clixon_operation

    def get_parent(self) -> object:
        """
        Return the parent of the element.
        """

        return self._parent

    def dump_creators(self) -> list():
        xmlstr = self.__dump_creators().split("\n")
        creators = []
        pattern = r" \*(.*?)\* "

        for creator in xmlstr:
            if "clixon:operation" not in creator:
                continue

            creator = re.sub(pattern, "", creator)

            creators.append(creator)

        return creators

    def __dump_creators(self) -> None:
        """
        Dump the creators of the element.
        """

        xmlstr = ""
        children = False

        childs = self.get_elements()
        children = len(childs)
        child_str = ""

        for child in childs:
            name = child.origname()
            data = child.get_data()
            childs = child.get_elements()
            clixon = child.clixon_element
            operation = child.clixon_operation

            if not childs:
                if data != "":
                    child_str += f"[{name}={data}]"
            else:
                child_str += "/" + name

            if clixon:
                child_str += f" *clixon:operation={operation}* "
                break

            child_str += child.__dump_creators()

        xmlstr += child_str

        if children:
            xmlstr += "\n"

        return xmlstr

    def dumps(self, clixon: Optional[bool] = False) -> str:
        """
        Return the XML string of the element and its children.
        """

        xmlstr = ""
        attr_string = ""

        for child in self.get_elements():
            name = child.origname()
            cdata = child.cdata

            attr_string = ""
            attr_string = child.get_attributes_str()

            has_creator, operation = child.get_creator()

            if clixon and has_creator:
                attr_string += f" clixon:operation=\"{operation}\""

            if child.get_elements() != [] or child.cdata != "":
                xmlstr += f"<{name}{attr_string}>"
            else:
                xmlstr += f"<{name}{attr_string}/>"

            if cdata != "":
                xmlstr += cdata

            xmlstr += child.dumps(clixon)

            if child.get_elements() != [] or child.cdata != "":
                xmlstr += f"</{name}>"

        return xmlstr

    def dumpj(self) -> str:
        """
        Return the JSON string of the element and its children.
        """

        data_dict = xmltodict.parse(self.dumps())
        json_data = json.dumps(data_dict)

        return json_data

    def __getitem__(self, key: str) -> Optional[dict]:
        """
        Return the attributes of the element.
        """

        return self.get_attributes(key=key)

    def __getattr__(self, key: str) -> Optional[dict]:
        """
        Return the attributes of the element.
        """

        matching_children = [x for x in self._children if x._name == key]
        if matching_children:
            if len(matching_children) == 1:
                self.__dict__[key] = matching_children[0]
                return matching_children[0]
            else:
                self.__dict__[key] = matching_children
                return matching_children
        else:
            raise AttributeError(
                "'%s' has no attribute '%s'" % (self._name, key))

    def __hasattribute__(self, name: str) -> bool:
        """
        Return True if the element has the attribute.
        """

        if name in self.__dict__:
            return True
        return any(x._name == name for x in self._children)

    def __iter__(self) -> object:
        yield self

    def __str__(self) -> str:
        return self.cdata.strip()

    def __repr__(self) -> str:
        return self.cdata.strip()

    def __bool__(self) -> bool:
        return self._is_root or self._name is not None

    __nonzero__ = __bool__

    def __eq__(self, val) -> bool:
        return self.cdata == val

    def __dir__(self) -> list:
        childrennames = [x._name for x in self._children]
        return childrennames

    def __len__(self) -> int:
        return len(self._children)

    def __contains__(self, key: str) -> bool:
        return key in dir(self)

    def path(self) -> str:
        tree = self.__backwards()
        tree = reversed(list(tree))
        confstr = ""

        for node in tree:
            confstr += "/"
            data = node.get_data()
            name = node.get_name()

            potential_key = node.get_elements("name")
            if potential_key:
                key_name = potential_key[0].get_data()
                if key_name:
                    data = key_name

            if data:
                confstr += f"{name}=[{data}]"
            else:
                confstr += f"{name}"

        return confstr

    def __backwards(self):
        """
        Iterate the whole three backwards using the parent attribute.
        """
        while self._parent:
            yield self
            self = self._parent
        yield self

    def dumpy(self) -> str:
        """
            Return the XML string of the element and its children.
        """
        output = ""

        for child in self.get_elements():
            name = child.origname()
            attr_dict = child.get_attributes()
            if name == "container":
                self.last_container = attr_dict["name"]
                for item in child.get_elements():
                    item_name = item.get_name()
                    if item_name != "list":
                        continue
                    item_attr = item.get_attributes()
                    item_name = item_attr["name"]

                    for subitem in item.get_elements():
                        sub_name = subitem.get_name()
                        if sub_name != "key":
                            continue
                        sub_attr = subitem.get_attributes()
                        sub_name = sub_attr["value"]

                        output += f"container \"{self.last_container}\" is a list of \"{item_name}\" with key \"{sub_name}\"\n"

            output += child.dumpy()

        return output
