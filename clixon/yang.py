"""
Minimal YANG parser.

The parser covers the subset of YANG used by controller service modules:
container, list, leaf, leaf-list, choice, grouping/uses, typedef and
augment. It is not a validating YANG compiler, it is just enough to render
REST endpoints and OpenAPI schemas from the YANG the backend serves over
get-schema.
"""

import re

from typing import Callable, Optional

from clixon.args import get_logger

logger = get_logger()

CONTROLLER_NS_URI = "http://clicon.org/controller"
CONTROLLER_MODULE = "clixon-controller"

# YANG built in types, RFC 7950 section 4.2.4.
BUILTIN_TYPES = [
    "binary",
    "bits",
    "boolean",
    "decimal64",
    "empty",
    "enumeration",
    "identityref",
    "instance-identifier",
    "int8",
    "int16",
    "int32",
    "int64",
    "leafref",
    "string",
    "uint8",
    "uint16",
    "uint32",
    "uint64",
    "union",
]

DATA_NODES = ["container", "list", "leaf", "leaf-list"]

# Extensions marking a node as hidden, they are kept out of the request
# bodies of the generated REST API in the same way as the autocli hides them.
HIDE_EXTENSIONS = ["hide", "hide-show"]

# Statements that may contain data nodes.
CONTAINING_NODES = DATA_NODES + ["augment", "grouping", "choice", "case", "uses"]

__escapes = {
    "n": "\n",
    "t": "\t",
    '"': '"',
    "\\": "\\",
}


class YangError(Exception):
    """
    Raised when a YANG module can not be parsed.
    """

    pass


class Statement:
    """
    A single YANG statement, "keyword [argument] { substatements }".
    """

    def __init__(
        self,
        keyword: str,
        argument: Optional[str] = None,
        parent: Optional[object] = None,
    ) -> None:
        """
        Create a statement.

        :param keyword: Statement keyword, may be prefixed
        :type keyword: str
        :param argument: Statement argument
        :type argument: str
        :param parent: Parent statement
        :type parent: Statement
        :return: None
        :rtype: None

        """

        if ":" in keyword:
            self.prefix, self.keyword = keyword.split(":", 1)
        else:
            self.prefix = None
            self.keyword = keyword

        self.argument = argument
        self.parent = parent
        self.substatements = []

    def __repr__(self) -> str:
        return f"<Statement {self.keyword} {self.argument}>"

    def findall(self, keyword: str) -> list:
        """
        Return all substatements matching a keyword.

        :param keyword: Statement keyword
        :type keyword: str
        :return: List of statements
        :rtype: list

        """

        return [s for s in self.substatements if s.keyword == keyword]

    def find(self, keyword: str, argument: Optional[str] = None) -> Optional[object]:
        """
        Return the first substatement matching a keyword and, optionally, an
        argument.

        :param keyword: Statement keyword
        :type keyword: str
        :param argument: Statement argument
        :type argument: str
        :return: Statement or None
        :rtype: Statement

        """

        for statement in self.substatements:
            if statement.keyword != keyword:
                continue
            if argument is not None and statement.argument != argument:
                continue

            return statement

        return None

    def arg(self, keyword: str, default: Optional[str] = None) -> Optional[str]:
        """
        Return the argument of the first substatement matching a keyword.

        :param keyword: Statement keyword
        :type keyword: str
        :param default: Value returned if the statement is missing
        :type default: str
        :return: Statement argument
        :rtype: str

        """

        statement = self.find(keyword)

        if statement is None or statement.argument is None:
            return default

        return statement.argument


def __unescape(string: str) -> str:
    """
    Expand the escape sequences of a double quoted YANG string.

    :param string: Quoted string without the quotes
    :type string: str
    :return: Unescaped string
    :rtype: str

    """

    if "\\" not in string:
        return string

    out = ""
    idx = 0

    while idx < len(string):
        char = string[idx]

        if char == "\\" and idx + 1 < len(string):
            out += __escapes.get(string[idx + 1], "\\" + string[idx + 1])
            idx += 2
            continue

        out += char
        idx += 1

    return out


def __dedent(string: str, column: int) -> str:
    """
    Strip the leading whitespace of a multi line YANG string, RFC 7950
    section 6.1.3.

    :param string: String to strip
    :type string: str
    :param column: Column of the opening quote
    :type column: int
    :return: Stripped string
    :rtype: str

    """

    if "\n" not in string:
        return string

    lines = string.split("\n")
    out = [lines[0]]

    for line in lines[1:]:
        idx = 0

        while idx < len(line) and idx < column and line[idx] in " \t":
            idx += 1

        out.append(line[idx:])

    return "\n".join(out)


def tokenize(text: str) -> list:
    """
    Split a YANG module into tokens. Comments are dropped, quoted strings and
    string concatenations are resolved.

    :param text: YANG module
    :type text: str
    :return: List of tokens, ("str", value) or ("sym", value)
    :rtype: list

    """

    tokens = []
    idx = 0
    length = len(text)
    line_start = 0

    while idx < length:
        char = text[idx]

        if char == "\n":
            line_start = idx + 1
            idx += 1
            continue

        if char in " \t\r":
            idx += 1
            continue

        if text.startswith("//", idx):
            end = text.find("\n", idx)
            idx = length if end == -1 else end
            continue

        if text.startswith("/*", idx):
            end = text.find("*/", idx + 2)

            if end == -1:
                raise YangError("Unterminated comment")

            idx = end + 2
            continue

        if char in "{};":
            tokens.append(("sym", char))
            idx += 1
            continue

        if char in "\"'":
            end = text.find(char, idx + 1)

            while char == '"' and end != -1 and text[end - 1] == "\\":
                end = text.find(char, end + 1)

            if end == -1:
                raise YangError("Unterminated string")

            value = text[idx + 1 : end]

            if char == '"':
                value = __unescape(__dedent(value, idx - line_start + 1))

            tokens.append(("str", value))
            idx = end + 1
            continue

        end = idx

        while end < length and text[end] not in " \t\r\n{};":
            if text.startswith("//", end) or text.startswith("/*", end):
                break
            end += 1

        tokens.append(("str", text[idx:end]))
        idx = end

    return tokens


def parse(text: str) -> Statement:
    """
    Parse a YANG module and return the module statement.

    :param text: YANG module
    :type text: str
    :return: Module statement
    :rtype: Statement

    """

    tokens = tokenize(text)
    idx = 0

    def __parse_statement(parent: Optional[Statement]) -> tuple:
        """
        Parse a single statement, return the statement and the next index.
        """

        nonlocal idx

        kind, keyword = tokens[idx]

        if kind != "str":
            raise YangError(f"Expected a keyword, got '{keyword}'")

        idx += 1
        argument = None

        if idx < len(tokens) and tokens[idx][0] == "str":
            argument = tokens[idx][1]
            idx += 1

            # String concatenation, "foo" + "bar".
            while (
                idx + 1 < len(tokens)
                and tokens[idx] == ("str", "+")
                and tokens[idx + 1][0] == "str"
            ):
                argument += tokens[idx + 1][1]
                idx += 2

        statement = Statement(keyword, argument, parent=parent)

        if idx >= len(tokens):
            raise YangError(f"Unterminated statement '{keyword}'")

        kind, symbol = tokens[idx]

        if symbol == ";":
            idx += 1
            return statement

        if symbol != "{":
            raise YangError(f"Expected ';' or '{{' after '{keyword}'")

        idx += 1

        while idx < len(tokens) and tokens[idx] != ("sym", "}"):
            statement.substatements.append(__parse_statement(statement))

        if idx >= len(tokens):
            raise YangError(f"Unterminated statement '{keyword}'")

        idx += 1

        return statement

    if not tokens:
        raise YangError("Empty YANG module")

    module = __parse_statement(None)

    if module.keyword not in ["module", "submodule"]:
        raise YangError(f"Expected a module, got '{module.keyword}'")

    return module


class Module:
    """
    A parsed YANG module.
    """

    def __init__(self, statement: Statement) -> None:
        """
        Create a module from a parsed module statement.

        :param statement: Module statement
        :type statement: Statement
        :return: None
        :rtype: None

        """

        self.statement = statement
        self.name = statement.argument
        self.namespace = statement.arg("namespace")
        self.prefix = statement.arg("prefix")
        self.description = statement.arg("description")

        revisions = [r.argument for r in statement.findall("revision") if r.argument]
        self.revision = max(revisions) if revisions else None

        self.imports = {}

        for statement_import in statement.findall("import"):
            prefix = statement_import.arg("prefix")

            if prefix:
                self.imports[prefix] = statement_import.argument

        self.groupings = {
            g.argument: g for g in statement.findall("grouping") if g.argument
        }
        self.typedefs = {
            t.argument: t for t in statement.findall("typedef") if t.argument
        }

    def __repr__(self) -> str:
        return f"<Module {self.name}@{self.revision}>"


class Context:
    """
    A set of YANG modules. Imported modules are loaded on demand, which is
    needed to resolve groupings and typedefs from other modules.
    """

    def __init__(self, loader: Optional[Callable] = None) -> None:
        """
        Create a context.

        :param loader: Function returning the YANG text of a module name
        :type loader: Callable
        :return: None
        :rtype: None

        """

        self.__loader = loader
        self.__modules = {}

    def add(self, text: str) -> Module:
        """
        Parse a YANG module and add it to the context.

        :param text: YANG module
        :type text: str
        :return: Module
        :rtype: Module

        """

        module = Module(parse(text))
        self.__modules[module.name] = module

        return module

    def module(self, name: str) -> Optional[Module]:
        """
        Return a module by name, loading it if needed.

        :param name: Module name
        :type name: str
        :return: Module or None if it can not be loaded
        :rtype: Module

        """

        if name in self.__modules:
            return self.__modules[name]

        if self.__loader is None:
            return None

        try:
            text = self.__loader(name)
        except Exception as e:
            logger.debug(f"Could not load YANG module {name}: {e}")
            self.__modules[name] = None

            return None

        if not text:
            self.__modules[name] = None

            return None

        try:
            return self.add(text)
        except YangError as e:
            logger.warning(f"Could not parse YANG module {name}: {e}")
            self.__modules[name] = None

            return None

    def imported(self, module: Module, prefix: str) -> Optional[Module]:
        """
        Return the module a prefix refers to, as seen from a module.

        :param module: Module the prefix is used in
        :type module: Module
        :param prefix: Prefix
        :type prefix: str
        :return: Module or None
        :rtype: Module

        """

        if prefix is None or prefix == module.prefix:
            return module

        name = module.imports.get(prefix)

        if name is None:
            return None

        return self.module(name)


class Node:
    """
    A data node of a YANG schema tree.
    """

    def __init__(
        self,
        kind: str,
        name: str,
        module: Optional[Module] = None,
    ) -> None:
        """
        Create a schema node.

        :param kind: Node kind, container, list, leaf or leaf-list
        :type kind: str
        :param name: Node name
        :type name: str
        :param module: Module the node is defined in
        :type module: Module
        :return: None
        :rtype: None

        """

        self.kind = kind
        self.name = name
        self.module = module
        self.description = None
        self.type = None
        self.enums = []
        self.default = None
        self.units = None
        self.mandatory = False
        self.config = True
        self.hidden = False
        self.keys = []
        self.children = []

    def __repr__(self) -> str:
        return f"<Node {self.kind} {self.name}>"

    def child(self, name: str) -> Optional[object]:
        """
        Return a child node by name.

        :param name: Child name
        :type name: str
        :return: Node or None
        :rtype: Node

        """

        for child in self.children:
            if child.name == name:
                return child

        return None


def resolve_type(context: Context, module: Module, statement: Statement) -> dict:
    """
    Resolve a type statement down to a built in YANG type.

    :param context: Context
    :type context: Context
    :param module: Module the type is used in
    :type module: Module
    :param statement: Type statement
    :type statement: Statement
    :return: Dict with name, enums and range
    :rtype: dict

    """

    name = statement.argument or "string"
    prefix = None

    if ":" in name:
        prefix, name = name.split(":", 1)

    if prefix:
        imported = context.imported(module, prefix)

        if imported is None:
            logger.debug(f"Unknown prefix {prefix} in module {module.name}")

            return {"name": "string", "enums": [], "range": None}

        if imported is not module:
            typedef = imported.typedefs.get(name)

            if typedef is not None:
                return resolve_type(context, imported, typedef.find("type"))

            return {"name": "string", "enums": [], "range": None}

    if name not in BUILTIN_TYPES:
        typedef = module.typedefs.get(name)

        if typedef is None:
            logger.debug(f"Unknown type {name} in module {module.name}")

            return {"name": "string", "enums": [], "range": None}

        resolved = resolve_type(context, module, typedef.find("type"))

        if resolved.get("range") is None:
            resolved["range"] = typedef.find("type").arg("range")

        return resolved

    enums = []

    if name == "enumeration":
        enums = [e.argument for e in statement.findall("enum") if e.argument]

    return {"name": name, "enums": enums, "range": statement.arg("range")}


def __is_hidden(statement: Statement) -> bool:
    """
    Return True if a statement carries an extension hiding it, such as
    autocli:hide-show.
    """

    for substatement in statement.substatements:
        if substatement.prefix and substatement.keyword in HIDE_EXTENSIONS:
            return True

    return False


def __node_from_leaf(
    context: Context, module: Module, statement: Statement, kind: str
) -> Node:
    """
    Create a leaf or leaf-list node.
    """

    node = Node(kind, statement.argument, module=module)
    node.description = statement.arg("description")
    node.default = statement.arg("default")
    node.units = statement.arg("units")
    node.mandatory = statement.arg("mandatory") == "true"
    node.config = statement.arg("config", "true") != "false"
    node.hidden = __is_hidden(statement)

    type_statement = statement.find("type")

    if type_statement is not None:
        resolved = resolve_type(context, module, type_statement)
        node.type = resolved["name"]
        node.enums = resolved["enums"]

    return node


def build_children(
    context: Context,
    module: Module,
    statement: Statement,
    seen: Optional[list] = None,
) -> list:
    """
    Build the schema nodes of the data node substatements of a statement.

    Groupings are expanded, choices are flattened into their case nodes.

    :param context: Context
    :type context: Context
    :param module: Module the statement belongs to
    :type module: Module
    :param statement: Statement to walk
    :type statement: Statement
    :param seen: Groupings currently being expanded, used to stop recursion
    :type seen: list
    :return: List of nodes
    :rtype: list

    """

    if seen is None:
        seen = []

    nodes = []

    for substatement in statement.substatements:
        keyword = substatement.keyword

        if keyword not in CONTAINING_NODES:
            continue

        if keyword in ["leaf", "leaf-list"]:
            nodes.append(__node_from_leaf(context, module, substatement, keyword))
        elif keyword in ["container", "list"]:
            node = Node(keyword, substatement.argument, module=module)
            node.description = substatement.arg("description")
            node.config = substatement.arg("config", "true") != "false"
            node.hidden = __is_hidden(substatement)

            if keyword == "list":
                keys = substatement.arg("key", "")
                node.keys = keys.split()

            node.children = build_children(context, module, substatement, seen)
            nodes.append(node)
        elif keyword in ["choice", "case"]:
            # Flatten, the cases become optional siblings.
            nodes.extend(build_children(context, module, substatement, seen))
        elif keyword == "uses":
            nodes.extend(__expand_uses(context, module, substatement, seen))

    return nodes


def __expand_uses(
    context: Context, module: Module, statement: Statement, seen: list
) -> list:
    """
    Expand a uses statement into the nodes of its grouping.
    """

    name = statement.argument
    prefix = None

    if ":" in name:
        prefix, name = name.split(":", 1)

    grouping_module = context.imported(module, prefix) if prefix else module

    if grouping_module is None:
        logger.debug(f"Unknown prefix {prefix} in module {module.name}")

        return []

    grouping = grouping_module.groupings.get(name)

    if grouping is None:
        logger.debug(f"Unknown grouping {name} in module {grouping_module.name}")

        return []

    key = f"{grouping_module.name}:{name}"

    if key in seen:
        logger.warning(f"Recursive grouping {key}")

        return []

    return build_children(context, grouping_module, grouping, seen + [key])


def is_service_module(text: str) -> bool:
    """
    Return True if a YANG module looks like a controller service module, ie
    if it augments the services container.

    Used to avoid parsing every module the backend serves.

    :param text: YANG module
    :type text: str
    :return: True if the module augments /ctrl:services
    :rtype: bool

    """

    return re.search(r"""augment\s+["']?/[\w.-]+:services["']?""", text) is not None


def __is_services_target(context: Context, module: Module, target: str) -> bool:
    """
    Return True if an augment target is the controller services container.
    """

    if target is None:
        return False

    match = re.match(r"^/([\w.-]+):services$", target.strip())

    if not match:
        return False

    prefix = match.group(1)
    name = module.imports.get(prefix)

    if name == CONTROLLER_MODULE:
        return True

    imported = context.imported(module, prefix)

    return imported is not None and imported.namespace == CONTROLLER_NS_URI


def service_nodes(context: Context, module: Module) -> list:
    """
    Return the service list nodes a module augments /ctrl:services with.

    A controller service is a list directly under the services container, see
    the description of the services container in clixon-controller.yang.

    :param context: Context
    :type context: Context
    :param module: Module
    :type module: Module
    :return: List of nodes
    :rtype: list

    """

    nodes = []

    for augment in module.statement.findall("augment"):
        if not __is_services_target(context, module, augment.argument):
            continue

        for node in build_children(context, module, augment):
            if node.kind != "list":
                logger.warning(
                    f"Ignoring {node.kind} {node.name} in {module.name}, "
                    "services must be augmented with lists"
                )
                continue

            nodes.append(node)

    return nodes
