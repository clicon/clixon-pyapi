import xml.etree.ElementTree as ET

XMLNS = "{urn:ietf:params:xml:ns:netconf:base:1.0}"
CONFIGNS = "http://clicon.org/config"


def clicon_sock(filename=None):
    """
    Find the configuration option CLICON_SOCK from a configuration file.
    """
    tree = ET.parse(filename)
    root = tree.getroot()

    sockpath = root.find("{CONFIG_NS}CLICON_SOCK")

    if sockpath:
        return sockpath.text

    return None


def build_rpc(username=None, messageid=42):
    """
    Build the basic structure of a RPC call, this will only set
    the namespace and message ID, the rest must be extended later.
    """
    root = ET.Element("rpc")
    root.set("xmlns", "urn:ietf:params:xml:ns:netconf:base:1.0")
    root.set("message-id", str(messageid))

    # In some cases we want to set a username
    if username:
        root.set("username", username)

    return root


def ping():
    """
    Build a ping RPC call, extend the RPC base with
    <ping xmlns="http://clicon.org/lib"/>
    """

    root = build_rpc()
    ping = ET.SubElement(root, "ping")
    ping.set("xmlns", "http://clicon.org/lib")

    return ET.tostring(root)


def show_configuration(store="candidate"):
    """
    get-conf, extend the RPC root with
    <get-config>
      <source>
        <candidate/>
      </source><nc:filter nc:type="xpath" nc:select="/"/>
    </get-config>
    """

    root = build_rpc(username="khn")
    get_config = ET.SubElement(root, "get-config")
    source = ET.SubElement(get_config, "source")
    ET.SubElement(source, store)

    return ET.tostring(root)


def error_check(data):
    """
    Figure out if we got an error sent back to us.
    """
    root = ET.fromstring(data)

    if not root.findall(f"{XMLNS}rpc-error"):
        return None

    error_tag = root.findall(f"{XMLNS}error-tag")

    print(type(error_tag))

    if error_tag:
        print(error_tag)

    return True


def set(xpath, value):
    pass
