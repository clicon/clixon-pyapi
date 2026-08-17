import pytest

from clixon import yang

MODULE = """
module test-service {
    yang-version 1.1;
    namespace "http://clicon.org/test-service";
    prefix ts;

    import clixon-controller { prefix ctrl; }
    import ietf-inet-types { prefix inet; }

    revision 2024-01-01 {
        description "Second revision";
    }
    revision 2023-01-01 {
        description "Initial revision";
    }

    // A line comment.
    typedef percent {
        type uint8 {
            range "0 .. 100";
        }
    }

    /* A block comment
       spanning lines. */
    grouping endpoint {
        leaf address {
            type inet:ip-address;
            description "Address of the " +
                        "endpoint";
        }
        leaf port {
            type uint16;
            default 22;
        }
    }

    augment "/ctrl:services" {
        list test-service {
            key service-name;
            description "A test service";
            leaf service-name {
                type string;
                mandatory true;
            }
            leaf enabled {
                type boolean;
                default "true";
            }
            leaf load {
                type percent;
            }
            leaf mode {
                type enumeration {
                    enum fast;
                    enum slow;
                }
            }
            leaf-list tag {
                type string;
            }
            container limits {
                leaf max {
                    type int32;
                }
            }
            list peer {
                key name;
                leaf name {
                    type string;
                }
                uses endpoint;
            }
            choice protocol {
                case ssh {
                    leaf ssh-key {
                        type string;
                    }
                }
                case telnet {
                    leaf telnet-port {
                        type uint16;
                    }
                }
            }
            uses ctrl:created-by-service;
        }
    }
}
"""

CONTROLLER = """
module clixon-controller {
    namespace "http://clicon.org/controller";
    prefix ctrl;

    import clixon-autocli { prefix autocli; }

    grouping created-by-service {
        container created {
            autocli:hide-show;
            leaf-list path {
                type string;
            }
        }
    }
    container services {
        description "Placeholder for services.";
    }
}
"""

INET = """
module ietf-inet-types {
    namespace "urn:ietf:params:xml:ns:yang:ietf-inet-types";
    prefix inet;

    typedef ip-address {
        type string;
    }
}
"""

MODULES = {
    "clixon-controller": CONTROLLER,
    "ietf-inet-types": INET,
    "test-service": MODULE,
}


def loader(name):
    """
    Loader returning the modules of the test.
    """

    return MODULES[name]


def context():
    """
    Return a context with the test service module added.
    """

    ctx = yang.Context(loader=loader)

    return ctx, ctx.add(MODULE)


def service():
    """
    Return the schema node of the test service.
    """

    ctx, module = context()
    nodes = yang.service_nodes(ctx, module)

    return nodes[0]


def test_parse_module():
    """
    Test that a module is parsed.
    """

    statement = yang.parse(MODULE)

    assert statement.keyword == "module"
    assert statement.argument == "test-service"
    assert statement.arg("namespace") == "http://clicon.org/test-service"
    assert len(statement.findall("revision")) == 2


def test_parse_errors():
    """
    Test that invalid modules are rejected.
    """

    with pytest.raises(yang.YangError):
        yang.parse("")

    with pytest.raises(yang.YangError):
        yang.parse("container foo { leaf bar { type string; } }")

    with pytest.raises(yang.YangError):
        yang.parse("module foo { leaf bar { type string; }")

    with pytest.raises(yang.YangError):
        yang.parse('module foo { leaf bar { description "unterminated; } }')


def test_module_metadata():
    """
    Test that the metadata of a module is read.
    """

    _, module = context()

    assert module.name == "test-service"
    assert module.prefix == "ts"
    assert module.namespace == "http://clicon.org/test-service"
    assert module.revision == "2024-01-01"
    assert module.imports["ctrl"] == "clixon-controller"
    assert "endpoint" in module.groupings
    assert "percent" in module.typedefs


def test_comments_and_concatenation():
    """
    Test that comments are dropped and that strings are concatenated.
    """

    node = service().child("peer").child("address")

    assert node.description == "Address of the endpoint"


def test_is_service_module():
    """
    Test that service modules are recognized.
    """

    assert yang.is_service_module(MODULE) is True
    assert yang.is_service_module(CONTROLLER) is False
    assert yang.is_service_module(INET) is False


def test_service_nodes():
    """
    Test that the service list of an augment is found.
    """

    ctx, module = context()
    nodes = yang.service_nodes(ctx, module)

    assert len(nodes) == 1
    assert nodes[0].kind == "list"
    assert nodes[0].name == "test-service"
    assert nodes[0].keys == ["service-name"]
    assert nodes[0].description == "A test service"


def test_service_nodes_without_controller():
    """
    Test that the augment is found by module name when the controller module
    can not be loaded.
    """

    ctx = yang.Context(loader=lambda name: None)
    module = ctx.add(MODULE)

    assert len(yang.service_nodes(ctx, module)) == 1


def test_leaf_types():
    """
    Test that the types of the leafs are resolved.
    """

    node = service()

    assert node.child("service-name").type == "string"
    assert node.child("service-name").mandatory is True
    assert node.child("enabled").type == "boolean"
    assert node.child("enabled").default == "true"
    assert node.child("mode").type == "enumeration"
    assert node.child("mode").enums == ["fast", "slow"]
    assert node.child("tag").kind == "leaf-list"


def test_typedef_resolution():
    """
    Test that typedefs are resolved, both local and imported ones.
    """

    node = service()

    assert node.child("load").type == "uint8"
    assert node.child("peer").child("address").type == "string"


def test_containers_and_lists():
    """
    Test that containers and lists are built.
    """

    node = service()

    assert node.child("limits").kind == "container"
    assert node.child("limits").child("max").type == "int32"
    assert node.child("peer").kind == "list"
    assert node.child("peer").keys == ["name"]


def test_uses_expansion():
    """
    Test that groupings are expanded, also from imported modules.
    """

    node = service()

    assert node.child("peer").child("port").type == "uint16"
    assert node.child("peer").child("port").default == "22"
    assert node.child("created").kind == "container"
    assert node.child("created").child("path").kind == "leaf-list"


def test_hidden_extension():
    """
    Test that nodes hidden by an extension are marked.
    """

    node = service()

    assert node.child("created").hidden is True
    assert node.child("limits").hidden is False


def test_choice_flattening():
    """
    Test that the cases of a choice become optional siblings.
    """

    node = service()

    assert node.child("ssh-key").type == "string"
    assert node.child("ssh-key").mandatory is False
    assert node.child("telnet-port").type == "uint16"


def test_unknown_type():
    """
    Test that an unknown type falls back to string.
    """

    ctx = yang.Context()
    module = ctx.add(
        """
        module foo {
            namespace "http://clicon.org/foo";
            prefix foo;
            leaf bar {
                type nosuch:type;
            }
        }
        """
    )

    node = yang.build_children(ctx, module, module.statement)[0]

    assert node.type == "string"


def test_recursive_grouping():
    """
    Test that a recursive grouping does not recurse forever.
    """

    ctx = yang.Context()
    module = ctx.add(
        """
        module foo {
            namespace "http://clicon.org/foo";
            prefix foo;
            grouping loop {
                container inner {
                    uses loop;
                }
            }
            uses loop;
        }
        """
    )

    nodes = yang.build_children(ctx, module, module.statement)

    assert nodes[0].name == "inner"
    assert nodes[0].children == []


def test_escapes_and_dedent():
    """
    Test that escapes are expanded and multi line strings dedented.
    """

    module = yang.parse(
        "module foo {\n"
        '    namespace "http://clicon.org/foo";\n'
        "    prefix foo;\n"
        "    leaf bar {\n"
        "        type string;\n"
        '        description "first\n'
        '                     second\\nthird \\"quoted\\" \\\\ \\t";\n'
        "        reference 'a raw \\n string';\n"
        "    }\n"
        "}\n"
    )

    leaf = module.find("leaf")

    assert leaf.arg("description") == 'first\nsecond\nthird "quoted" \\ \t'
    assert leaf.arg("reference") == "a raw \\n string"


def test_statement_helpers():
    """
    Test the helpers of a statement.
    """

    module = yang.parse(MODULE)

    assert module.find("revision", "2023-01-01") is not None
    assert module.find("revision", "1999-01-01") is None
    assert module.find("nosuch") is None
    assert module.arg("nosuch", "default") == "default"
    assert module.arg("prefix") == "ts"
    assert repr(module).startswith("<Statement module test-service>")
    assert repr(yang.Module(module)).startswith("<Module test-service@")


def test_context_add_and_module():
    """
    Test that a context caches the modules it is given and loads.
    """

    ctx = yang.Context(loader=loader)
    module = ctx.add(MODULE)

    assert ctx.module("test-service") is module
    assert ctx.module("clixon-controller").name == "clixon-controller"


def test_context_without_loader():
    """
    Test that a context without a loader has only what it is given.
    """

    ctx = yang.Context()

    assert ctx.module("clixon-controller") is None


def test_context_loader_failure():
    """
    Test that a module which can not be loaded is not an error.
    """

    def broken(name):
        raise RuntimeError("no such module")

    ctx = yang.Context(loader=broken)

    assert ctx.module("clixon-controller") is None
    assert ctx.module("clixon-controller") is None


def test_context_empty_module():
    """
    Test that a loader returning nothing is not an error.
    """

    ctx = yang.Context(loader=lambda name: "")

    assert ctx.module("clixon-controller") is None


def test_context_unparsable_module():
    """
    Test that a module which does not parse is not an error.
    """

    ctx = yang.Context(loader=lambda name: "this is not yang")

    assert ctx.module("clixon-controller") is None


def test_imported():
    """
    Test that a prefix is resolved to its module.
    """

    ctx, module = context()

    assert ctx.imported(module, "ts") is module
    assert ctx.imported(module, None) is module
    assert ctx.imported(module, "ctrl").name == "clixon-controller"
    assert ctx.imported(module, "nosuch") is None


def test_node_helpers():
    """
    Test the helpers of a schema node.
    """

    node = service()

    assert repr(node) == "<Node list test-service>"
    assert node.child("nosuch") is None


def test_type_of_imported_module():
    """
    Test that a type of a module which can not be loaded is a string.
    """

    ctx = yang.Context(loader=lambda name: None)
    module = ctx.add(MODULE)
    node = yang.service_nodes(ctx, module)[0]

    assert node.child("peer").child("address").type == "string"


def test_type_without_typedef():
    """
    Test that a type an imported module does not have is a string.
    """

    ctx = yang.Context(loader=loader)
    module = ctx.add(
        """
        module foo {
            namespace "http://clicon.org/foo";
            prefix foo;
            import ietf-inet-types { prefix inet; }
            leaf bar {
                type inet:nosuch;
            }
        }
        """
    )

    assert yang.build_children(ctx, module, module.statement)[0].type == "string"


def test_uses_unknown_grouping():
    """
    Test that a grouping which is not there is skipped.
    """

    ctx = yang.Context()
    module = ctx.add(
        """
        module foo {
            namespace "http://clicon.org/foo";
            prefix foo;
            uses nosuch;
            uses nosuch:grouping;
        }
        """
    )

    assert yang.build_children(ctx, module, module.statement) == []


def test_augment_of_another_target():
    """
    Test that an augment of something else than the services is ignored.
    """

    ctx = yang.Context(loader=loader)
    module = ctx.add(
        """
        module foo {
            namespace "http://clicon.org/foo";
            prefix foo;
            import clixon-controller { prefix ctrl; }
            augment "/ctrl:devices" {
                list bar {
                    key name;
                    leaf name { type string; }
                }
            }
        }
        """
    )

    assert yang.service_nodes(ctx, module) == []


def test_augment_of_a_container():
    """
    Test that an augment which is not a list is not a service.
    """

    ctx = yang.Context(loader=loader)
    module = ctx.add(
        """
        module foo {
            namespace "http://clicon.org/foo";
            prefix foo;
            import clixon-controller { prefix ctrl; }
            augment "/ctrl:services" {
                container bar {
                    leaf name { type string; }
                }
            }
        }
        """
    )

    assert yang.service_nodes(ctx, module) == []


def test_config_false():
    """
    Test that state nodes are marked as such.
    """

    ctx = yang.Context()
    module = ctx.add(
        """
        module foo {
            namespace "http://clicon.org/foo";
            prefix foo;
            container state {
                config false;
                leaf uptime { type uint32; config false; }
            }
        }
        """
    )

    node = yang.build_children(ctx, module, module.statement)[0]

    assert node.config is False
    assert node.child("uptime").config is False


def test_tokenize_errors():
    """
    Test that unterminated comments and strings are errors.
    """

    with pytest.raises(yang.YangError):
        yang.tokenize("module foo { /* unterminated")

    with pytest.raises(yang.YangError):
        yang.tokenize("module foo { description 'unterminated")


def test_tokenize_comments():
    """
    Test that comments are dropped wherever they are.
    """

    tokens = yang.tokenize("module /* here */ foo { // and here\n    prefix f; }")

    assert tokens == [
        ("str", "module"),
        ("str", "foo"),
        ("sym", "{"),
        ("str", "prefix"),
        ("str", "f"),
        ("sym", ";"),
        ("sym", "}"),
    ]
