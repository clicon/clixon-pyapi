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
        self.cdata = cdata

        if data != "":
            self.cdata = data

        self._origname = name

        if name:
            name = name.replace("-", "_")
            name = name.replace(".", "_")
            name = name.replace(":", "_")

        self._name = name

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

    def create(self, name: str, attributes: Optional[dict] = {},
               cdata: Optional[str] = "",
               data: Optional[str] = "",
               element: Optional[object] = None) -> None:
        """
        Create a new element.
        """

        if not element:
            element = Element(name, attributes)

            if data != "":
                element.cdata = data
            else:
                element.cdata = cdata

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

    def get_attributes(self, key: Optional[str] = None) -> Optional[dict]:
        """
        Return the attributes of the element.
        """

        if key:
            return self.attributes.get(key)
        return self.attributes

    def get_elements(self, name: Optional[str] = "") -> list:
        """
        Return the children of the element.
        """

        name = name.replace("-", "_")

        if name:
            return [e for e in self._children if e._name == name]
        else:
            return self._children

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

    def dumps(self) -> str:
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

            if child.get_elements() != [] or child.cdata != "":
                xmlstr += f"<{name}{attr_string}>"
            else:
                xmlstr += f"<{name}{attr_string}/>"

            if cdata != "":
                xmlstr += cdata

            xmlstr += child.dumps()

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
        cdata = self.cdata.strip()

        return cdata

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
