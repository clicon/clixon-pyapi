import json
from typing import Optional, Generator

import xmltodict


class Element(object):
    def __init__(
        self,
        name: Optional[str] = "root",
        attributes: Optional[dict] = {},
        cdata: Optional[str] = "",
        data: Optional[str] = "",
        parent: Optional[object] = None,
    ) -> None:
        """
        Create a new element.

        :param name: The name of the element.
        :type name: str
        :param attributes: The attributes of the element.
        :type attributes: dict
        :param cdata: The cdata of the element.
        :type cdata: str
        :param data: The data of the element.
        :type data: str
        :return: None
        :rtype: None

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

        if parent:
            self._parent = parent

    def is_root(self, boolean: bool) -> None:
        """
        Set the element as root.

        :param boolean: True or False.
        :type boolean: bool
        :return: None
        :rtype: None

        """

        self._is_root = boolean

    def origname(self) -> str:
        """
        Return the original name of the element.

        :return: The original name of the element.
        :rtype: str

        """

        if self._origname == "":
            return self._name
        return self._origname

    def create(
        self,
        name: str,
        attributes: Optional[dict] = {},
        cdata: Optional[str] = "",
        data: Optional[str] = "",
        element: Optional[object] = None,
    ) -> None:
        """
        Create a new element.

        :param name: The name of the element.
        :type name: str
        :param attributes: The attributes of the element.
        :type attributes: dict
        :param cdata: The cdata of the element.
        :type cdata: str
        :param data: The data of the element.
        :type data: str
        :param element: The element to create.
        :type element: object
        :return: None
        :rtype: None

        """

        if not element:
            element = Element(name, attributes, parent=self)

            if data != "":
                element.cdata = data
            else:
                element.cdata = cdata

        self._children.append(element)

        return element

    def rename(self, name: str, origname: str) -> None:
        """
        Rename the element.

        :param name: The new name of the element.
        :type name: str
        :param origname: The original name of the element.
        :type origname: str
        :return: None
        :rtype: None

        """

        self._name = name
        self._origname = origname

    def get_name(self) -> str:
        """
        Return the name of the element.

        :return: The name of the element.
        :rtype: str
        """

        return self._name

    def add(self, element: object) -> None:
        """
        Add an element to the children of the element.

        :param element: The element to add.
        :type element: object
        :return: None
        :rtype: None

        """

        self._children.append(element)

    def delete(
        self,
        name: Optional[str] = "",
        element: Optional[object] = None,
    ) -> None:
        """
        Delete an element from the children of the element.

        :param name: The name of the element to delete.
        :type name: str
        :return: None
        :rtype: None

        """

        if not name and not element:
            self._parent.delete(element=self)

        if element:
            index = 0
            for child in self._children:
                if child == element:
                    del self._children[index]
                    index += 1

        if name == "*":
            self._children = []
            return
        elif name != "" and name != "*":
            index = 0
            for child in self._children:
                if child._origname == name:
                    del self._children[index]
                index += 1

    def replace(self, name: str, element: object) -> None:
        """
        Replace an element in the children of the element.

        :param name: The name of the element to replace.
        :type name: str
        :param element: The element to replace.
        :type element: object
        :return: None
        :rtype: None

        """

        self.delete(name)
        self.add(element)

    def set_attributes(self, attributes: dict) -> None:
        """
        Set the attributes of the element.

        :param attributes: The attributes of the element.
        :type attributes: dict
        :return: None
        :rtype: None

        """

        self.attributes = attributes

    def update_attributes(self, attributes: dict) -> None:
        """
        Update the attributes of the element.

        :param attributes: The attributes of the element.
        :type attributes: dict
        :return: None
        :rtype: None

        """

        old_attributes = self.get_attributes()
        new_attributes = attributes | old_attributes

        self.set_attributes(new_attributes)

    def get_attributes(self, key: Optional[str] = None) -> Optional[dict]:
        """
        Return the attributes of the element.

        :param key: The key of the attribute to return.
        :type key: str
        :return: The attributes of the element.
        :rtype: dict

        """

        if key:
            return self.attributes.get(key)
        return self.attributes

    def get_elements(self, name: Optional[str] = "", data: Optional[str] = "") -> list:
        """
        Return the children of the element.

        :param name: The name of the element to return.
        :type name: str
        :param data: The data of the element to return.
        :type data: str
        :return: The children of the element.
        :rtype: list

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

        :return: The attributes of the element as a string.
        :rtype: str

        """

        attr_string = ""
        if self.attributes and self.attributes != {}:
            for key in self.attributes.keys():
                value = self.attributes[key]
                attr_string += f' {key}="{value}"'
        return attr_string

    def set_data(self, data: str) -> None:
        """
        Set the data of the element.

        :param data: The data of the element.
        :type data: str
        :return: None

        """

        self.cdata = data

    def get_data(self) -> str:
        """

        Return the data of the element.

        :return: The data of the element.
        :rtype: str

        """

        return self.cdata

    def dumps(self) -> str:
        """

        Return the XML string of the element and its children.

        :return: The XML string of the element and its children.
        :rtype: str

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

        :return: The JSON string of the element and its children.
        :rtype: str

        """

        data_dict = xmltodict.parse(self.dumps())
        json_data = json.dumps(data_dict)

        return json_data

    def parent(self) -> object:
        """
        Return the parent of the element.

        :return: The parent of the element.
        :rtype: object

        """

        return self._parent

    def parents(self) -> Generator:
        """
        Return the parents of the element.

        :return: The parents of the element.
        :rtype: Generator

        """

        parent = self._parent
        while parent:
            yield parent
            parent = parent._parent

    def __getitem__(self, key: str) -> Optional[dict]:
        """
        Return the attributes of the element.

        :param key: The key of the attribute to return.
        :type key: str
        :return: The attributes of the element.
        :rtype: dict

        """

        return self.get_attributes(key=key)

    def __getattr__(self, key: str) -> Optional[dict]:
        """
        Return the attributes of the element.

        :param key: The key of the attribute to return.
        :type key: str
        :return: The attributes of the element.
        :rtype: dict

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
            raise AttributeError("'%s' has no attribute '%s'" % (self._name, key))

    def __hasattribute__(self, name: str) -> bool:
        """
        Return True if the element has the attribute.

        :param name: The name of the attribute.
        :type name: str
        :return: True if the element has the attribute.
        :rtype: bool
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
