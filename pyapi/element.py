import json

import xmltodict


class Element(object):
    def __init__(self, name, attributes, origname=""):
        self._name = name
        self._attributes = attributes
        self._children = []
        self._is_root = False
        self.cdata = ""
        self._origname = origname

    def is_root(self, boolean):
        self._is_root = boolean

    def get_name(self):
        return self._name

    def get_origname(self):
        if self._origname == "":
            return self._name

        return self._origname

    def add_element(self, name, attributes={}, origname="", cdata="",
                    element=None):
        if not element:
            element = Element(name, attributes, origname)
            element.set_cdata(cdata)

        self.add_child(element)

    def del_element(self, name):
        index = 0
        for child in self._children:
            if child._name == name:
                del self._children[index]
            index += 1

    def add_child(self, element):
        self._children.append(element)

    def add_cdata(self, cdata):
        self.cdata = self.cdata + cdata

    def set_cdata(self, cdata):
        self.cdata = cdata

    def get_attribute(self, key):
        return self._attributes.get(key)

    def set_attributes(self, attributes):
        self._attributes = attributes

    def add_attributes(self, attributes):
        if type(attributes) != dict:
            raise AttributeError("add_attribute argument should be dict")

        for key in attributes.keys():
            self._attributes[key] = attributes[key]

    def get_attributes(self):
        return self._attributes

    def get_elements(self, name=None):
        if name:
            return [e for e in self._children if e.name == name]
        else:
            return self._children

    def get_cdata(self):
        return self.cdata

    def get_attributes_str(self):
        attr_string = ""
        if self._attributes and self._attributes != {}:
            for key in self._attributes.keys():
                value = self._attributes[key]
                attr_string += f" {key}=\"{value}\""
        return attr_string

    def dumps(self):
        xmlstr = ""
        attr_string = ""

        for child in self.get_elements():
            name = child.get_origname()
            cdata = child.get_cdata().strip()
            attr_string = ""

            attr_string = child.get_attributes_str()

            if child.get_elements() != [] or child.get_cdata() != "":
                xmlstr += f"<{name}{attr_string}>"
            else:
                xmlstr += f"<{name}{attr_string}/>"

            if cdata != "":
                xmlstr += cdata

            xmlstr += child.dumps()

            if child.get_elements() != [] or child.get_cdata() != "":
                xmlstr += f"</{name}>"

        return xmlstr

    def dumpj(self):
        data_dict = xmltodict.parse(self.dumps())
        json_data = json.dumps(data_dict)

        return json_data

    def __getitem__(self, key):
        return self.get_attribute(key)

    def __getattr__(self, key):
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

    def __hasattribute__(self, name):
        if name in self.__dict__:
            return True
        return any(x._name == name for x in self._children)

    def __iter__(self):
        yield self

    def __str__(self):
        return self.get_cdata().strip()

    def __repr__(self):
        name = self.get_name()
        cdata = self.get_cdata().strip()
        attribs = self.get_attributes_str()
        outstr = f"name={name}"

        if cdata != "":
            outstr += f", cdata={cdata}"
        if attribs != "":
            outstr += f", attributes={attribs}"

        return outstr

    def __bool__(self):
        return self._is_root or self._name is not None

    __nonzero__ = __bool__

    def __eq__(self, val):
        return self.cdata == val

    def __dir__(self):
        childrennames = [x._name for x in self._children]
        return childrennames

    def __len__(self):
        return len(self._children)

    def __contains__(self, key):
        return key in dir(self)
