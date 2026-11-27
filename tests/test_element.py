from clixon.element import Element
from clixon.parser import parse_string

xml = """
<xml>
    <apply-groups>ETH</apply-groups>
    <interface>
        <name>et-0/0/0</name>
        <description>to ptx-ac-2</description>
        <speed>400g</speed>
        <unit>
            <name>0</name>
            <family>
                <inet>
                    <address>
                        <name>1.2.3.4/31</name>
                    </address>
                </inet>
                <iso/>
                <inet6>
                    <filter>
                        <input>
                            <filter-name>sampling-input-v6</filter-name>
                        </input>
                    </filter>
                    <dad-disable/>
                </inet6>
                <mpls/>
            </family>
        </unit>
    </interface>
    <interface>
        <name>et-0/0/1</name>
        <flexible-vlan-tagging/>
        <encapsulation>flexible-ethernet-services</encapsulation>
        <unit>
            <name>101</name>
            <vlan-id>101</vlan-id>
            <family>
                <inet>
                    <rpf-check>
                        <fail-filter>rpf-AS8748</fail-filter>
                    </rpf-check>
                    <mtu>1500</mtu>
                    <filter>
                        <input>
                            <filter-name>cust-input-ip-v4</filter-name>
                        </input>
                    </filter>
                </inet>
            </family>
        </unit>
        <unit>
            <name>102</name>
            <vlan-id>102</vlan-id>
            <family>
                <inet>
                    <rpf-check>
                        <fail-filter>rpf-AS8748</fail-filter>
                    </rpf-check>
                    <mtu>1500</mtu>
                    <filter>
                        <input>
                            <filter-name>cust-input-ip-v4</filter-name>
                        </input>
                    </filter>
                </inet>
            </family>
        </unit>
        <unit>
            <name>103</name>
            <description>11111111 kaka, ZZZZZZ, EXT:CUST</description>
            <vlan-id>103</vlan-id>
            <family>
                <inet>
                    <rpf-check>
                        <fail-filter>rpf-AS8748</fail-filter>
                    </rpf-check>
                    <mtu>1500</mtu>
                    <filter>
                        <input>
                            <filter-name>cust-input-ip-v4</filter-name>
                        </input>
                    </filter>
                </inet>
            </family>
        </unit>
    </interface>
    <interface>
        <name>et-0/0/2</name>
        <flexible-vlan-tagging/>
        <encapsulation>flexible-ethernet-services</encapsulation>
        <unit>
            <name>10</name>
            <vlan-id>10</vlan-id>
            <family>
                <inet>
                    <rpf-check>
                        <fail-filter>rpf-AS8748</fail-filter>
                    </rpf-check>
                    <mtu>1500</mtu>
                    <filter>
                        <input>
                            <filter-name>cust-input-ip-v4</filter-name>
                        </input>
                    </filter>
                    <address>
                        <name>192.168.2.0/31</name>
                    </address>
                </inet>
            </family>
        </unit>
        <unit>
            <name>101</name>
            <encapsulation>vlan-ccc</encapsulation>
            <vlan-id>101</vlan-id>
            <family>
                <ccc>
                    <filter>
                        <input>cust-input-l2c</input>
                    </filter>
                </ccc>
            </family>
        </unit>
    </interface>
    <interface>
        <name>et-0/0/3</name>
        <flexible-vlan-tagging/>
        <encapsulation>flexible-ethernet-services</encapsulation>
        <unit>
            <name>1</name>
            <vlan-id>1</vlan-id>
            <family>
                <inet>
                    <rpf-check>
                        <fail-filter>rpf-AS41001</fail-filter>
                    </rpf-check>
                    <mtu>1600</mtu>
                    <filter>
                        <input>
                            <filter-name>cust-input-ip-v4</filter-name>
                        </input>
                    </filter>
                </inet>
                <inet6>
                    <rpf-check>
                        <fail-filter>rpf-AS41001-v6</fail-filter>
                    </rpf-check>
                    <mtu>1600</mtu>
                    <filter>
                        <input>
                            <filter-name>cust-input-ip-v6</filter-name>
                        </input>
                    </filter>
                    <dad-disable/>
                </inet6>
            </family>
        </unit>
        <unit>
            <name>2</name>
            <encapsulation>vlan-ccc</encapsulation>
            <vlan-id>2</vlan-id>
            <family>
                <ccc>
                    <filter>
                        <input>cust-input-l2c</input>
                    </filter>
                </ccc>
            </family>
        </unit>
        <unit>
            <name>3</name>
            <encapsulation>vlan-ccc</encapsulation>
            <vlan-id>3</vlan-id>
            <family>
                <ccc>
                    <filter>
                        <input>cust-input-l2c</input>
                    </filter>
                </ccc>
            </family>
        </unit>
    </interface>
    <interface>
        <name>et-0/0/4</name>
        <description>loopie</description>
    </interface>
    <interface>
        <name>et-0/0/6</name>
        <flexible-vlan-tagging/>
        <encapsulation>flexible-ethernet-services</encapsulation>
        <unit>
            <name>3000</name>
            <vlan-id>3000</vlan-id>
            <family>
                <inet>
                    <rpf-check/>
                    <no-neighbor-learn/>
                </inet>
                <inet6>
                    <rpf-check/>
                    <no-neighbor-learn/>
                    <policer>
                        <output>corero-mirror-policer</output>
                    </policer>
                </inet6>
            </family>
        </unit>
    </interface>
    <interface>
        <name>et-0/0/7</name>
        <flexible-vlan-tagging/>
        <mtu>9192</mtu>
        <encapsulation>flexible-ethernet-services</encapsulation>
    </interface>
    <interface>
        <name>et-0/0/8</name>
        <flexible-vlan-tagging/>
        <speed>10g</speed>
        <mtu>9192</mtu>
        <encapsulation>flexible-ethernet-services</encapsulation>
    </interface>
    <interface>
        <name>et-0/2/7</name>
        <vlan-tagging/>
        <speed>10g</speed>
        <unit>
            <name>10</name>
            <vlan-id>10</vlan-id>
            <family>
                <inet>
                    <address>
                        <name>1.2.3.4/31</name>
                    </address>
                </inet>
            </family>
        </unit>
        <unit>
            <name>20</name>
            <vlan-id>20</vlan-id>
            <family>
                <inet>
                    <address>
                        <name>1.2.3.4/31</name>
                    </address>
                </inet>
            </family>
        </unit>
    </interface>
    <interface>
        <name>lo0</name>
        <unit>
            <name>0</name>
            <family>
                <inet>
                    <filter>
                        <input>
                            <filter-name>re-protect-v4</filter-name>
                        </input>
                    </filter>
                    <address>
                        <name>1.2.3.4/32</name>
                        <primary/>
                    </address>
                    <address>
                        <name>1.2.3.4/32</name>
                    </address>
                    <address>
                        <name>127.0.0.1/32</name>
                    </address>
                </inet>
                <iso>
                    <address>
                        <name>00.00.00.00</name>
                    </address>
                </iso>
                <inet6>
                    <filter>
                        <input>
                            <filter-name>re-protect-v6</filter-name>
                        </input>
                    </filter>
                    <address>
                        <name>dead:beef::1/128</name>
                        <primary/>
                    </address>
                    <address>
                        <name>dead:beef::1/128</name>
                    </address>
                </inet6>
                <mpls/>
            </family>
        </unit>
    </interface>
    <interface>
        <name>re0:mgmt-0</name>
        <unit>
            <name>0</name>
            <family>
                <inet>
                    <address>
                        <name>1.2.3.4/27</name>
                    </address>
                </inet>
            </family>
        </unit>
    </interface>
</xml>
"""


def test_element_delete():
    """
    Test the deletion of an element from an XML element object.
    """

    root = parse_string(xml)

    # Delete the lo0 element
    for interface in root.xml.interface:
        if interface.name.get_data() == "lo0":
            interface.delete()

    # Check if lo0 is deleted
    assert not any(
        interface.name.get_data() == "lo0" for interface in root.xml.interface
    ), "lo0 element was not deleted"


def test_element_delete_argument():
    """
    Test the deletion of an element from an XML element object using the delete method with an argument.
    """

    root = parse_string(xml)

    for interface in root.xml.interface:
        if interface.name.get_data() == "lo0":
            root.xml.delete(element=interface)

    # Check if lo0 is deleted
    assert not any(
        interface.name.get_data() == "lo0" for interface in root.xml.interface
    ), "lo0 element was not deleted"


def test_element_replace():
    """
    Test the replacement of an element in an XML element object.
    """

    xmlstr = """<xml><a><name>This one should be replaced!</name></a><b><name>This one should still be there.</name></b></xml>"""
    newstr = """<c><name>I am the new one!</name></c>"""

    root = parse_string(xmlstr)
    new = parse_string(newstr)

    assert "<a>" in root.xml.dumps()
    assert "<b>" in root.xml.dumps()
    assert "<c>" not in root.xml.dumps()
    assert "This one should be replaced!" in root.xml.dumps()
    assert "This one should still be there." in root.xml.dumps()
    assert "I am the new one!" not in root.xml.dumps()

    root.xml.replace("a", new.c)

    assert "<a>" not in root.xml.dumps()
    assert "<b>" in root.xml.dumps()
    assert "<c>" in root.xml.dumps()
    assert "This one should be replaced!" not in root.xml.dumps()
    assert "This one should still be there." in root.xml.dumps()
    assert "I am the new one!" in root.xml.dumps()


def test_dumps_attributes_cdata_and_empty_elements():
    root = Element("root")
    a = root.create("a", attributes={"xmlns": "urn:x", "k": "v"})
    a.create("b", data="text")
    a.create("empty")
    root.create("c", data="only-cdata")

    assert root.dumps() == (
        '<a xmlns="urn:x" k="v"><b>text</b><empty/></a><c>only-cdata</c>'
    )


def test_dumps_uses_original_name():
    root = Element("root")
    child = root.create("my-name")

    assert child.get_name() == "my_name"
    assert root.dumps() == "<my-name/>"


def test_dumps_modified_comment_only_on_direct_children():
    root = Element("root")
    a = root.create("a")
    a.create("b", data="x")
    a._modified = True
    a.b._modified = True

    assert root.dumps(modified=True) == "<a><b>x</b></a> <!-- modified -->"
    assert root.dumps() == "<a><b>x</b></a>"


def test_dumps_does_not_share_state_between_calls():
    root = Element("root")
    root.create("a").create("b")

    assert root.dumps() == root.dumps() == "<a><b/></a>"
    assert root.a.dumps() == "<b/>"


# What the backend returns for get-config with depth 3: the device's leaves
# keep their values, but config is cut off and the module list entry has no key
DEPTH_3_REPLY = """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data><devices xmlns="http://clicon.org/controller"><device><name>r1</name><enabled>true</enabled><config></config><module></module></device></devices></data></rpc-reply>"""


def test_mark_truncated():
    """
    Test that empty elements are marked, and elements with text or children
    are not.
    """

    from clixon.element import mark_truncated

    root = parse_string(DEPTH_3_REPLY).rpc_reply.data
    mark_truncated(root)

    device = root.devices.device

    assert root.devices._truncated is False
    assert device._truncated is False
    assert device.name._truncated is False
    assert device.config._truncated is True
    assert device.module._truncated is True


def test_mark_truncated_any_level():
    """
    Test that empty elements are marked at every level, since the backend
    counts the depth from the node the xpath selects.
    """

    from clixon.element import mark_truncated

    root = parse_string(
        "<rpc-reply><data><a><b/><c><d/><e>1</e></c></a><f/></data></rpc-reply>"
    ).rpc_reply.data
    mark_truncated(root)

    assert root.a.b._truncated is True
    assert root.a.c.d._truncated is True
    assert root.f._truncated is True
    assert root.a._truncated is False
    assert root.a.c._truncated is False
    assert root.a.c.e._truncated is False
    assert root.dumps() == "<a><c><e>1</e></c></a>"


def test_dumps_skips_truncated():
    """
    Test that cut off elements are not serialized, so they are never written
    back, unless something has been added to them.
    """

    from clixon.element import mark_truncated

    root = parse_string(DEPTH_3_REPLY).rpc_reply.data
    mark_truncated(root)

    assert root.dumps() == (
        '<devices xmlns="http://clicon.org/controller"><device>'
        "<name>r1</name><enabled>true</enabled></device></devices>"
    )

    root.devices.device.config.create("system").create("hostname", data="r1")

    assert "<config><system><hostname>r1</hostname></system></config>" in root.dumps()


def test_dumps_writes_changed_truncated():
    """
    Test that a marked element is written back once it has text or has been
    changed, for example given new attributes.
    """

    from clixon.element import mark_truncated

    root = parse_string(DEPTH_3_REPLY).rpc_reply.data
    mark_truncated(root)

    root.devices.device.config.set_data("x")
    root.devices.device.module.update_attributes({"a": "1"})

    assert "<config>x</config>" in root.dumps()
    assert '<module a="1"/>' in root.dumps()


def test_prune_skips_truncated():
    """
    Test that a pruned edit-config does not send marked elements kept as
    leaves next to a change, so no list entry without keys is sent.
    """

    from clixon.element import mark_truncated

    root = parse_string(DEPTH_3_REPLY).rpc_reply.data
    mark_truncated(root)
    root.devices.device.enabled.set_data("false")

    assert root.devices.prune().dumps() == (
        "<device><name>r1</name><enabled>false</enabled></device>"
    )
