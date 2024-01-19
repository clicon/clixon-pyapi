import pytest
from clixon.element import Element
from clixon.helpers import (
    set_creator_attributes, get_value,
    get_path,
    get_service_instance,
    get_service_instances,
    get_devices,
    get_device,
    get_devices_configuration,
    get_properties,
    get_devices_from_group,
    is_juniper,
    get_junos_interface_address
)
from clixon.parser import parse_string


def test_set_creator_attributes():
    """
    Test that set_creator_attributes works as expected.
    """

    root = Element("root")
    root.create("test")
    root.test.create("bar")

    set_creator_attributes(root.test, "test", instance_name="keff")

    xmlstr = """<test cl:creator="test[service-name='keff']" nc:operation="create" xmlns:cl="http://clicon.org/lib"><bar/></test>"""

    assert root.dumps() == xmlstr

    set_creator_attributes(root.test, "test", "keff", "create")

    xmlstr = """<test cl:creator="test[service-name='keff']" nc:operation="create" xmlns:cl="http://clicon.org/lib"><bar/></test>"""

    assert root.dumps() == xmlstr


def test_set_creator_attributes_update():
    """
    Test that set_creator_attributes works and existing attributes are kept.
    """

    root = Element("root")
    root.create("test", attributes={"test": "foo"})
    root.test.create("bar")

    set_creator_attributes(root.test, "test", "keff", "create")

    xmlstr = """<test cl:creator="test[service-name='keff']" nc:operation="create" xmlns:cl="http://clicon.org/lib" test="foo"><bar/></test>"""

    assert root.dumps() == xmlstr


def test_get_value():
    """
    Test that get_value works as expected.
    """

    xmlstr_1 = """<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0"><data><table xmlns="urn:example:clixon"><parameter><name>name1</name><value>value1</value></parameter><parameter><name>name2</name><value>value2</value></parameter><parameter><name>name3</name><value>value3</value></parameter></table></data></rpc-reply>"""

    root = parse_string(xmlstr_1)

    value1_path = get_path(
        root, "/rpc-reply/data/table/parameter[name='name1']")

    value1 = get_value(value1_path, "value")

    assert value1 == "value1"

    value1 = get_value(value1_path, "valueX", default="value1")

    assert value1 == "value1"

    with pytest.raises(Exception):
        get_value(value1_path, "valueX", required=True)


def test_get_service_instance():
    """
    Test that get_service_instance works as expected.
    """

    xmlstr = """
<services xmlns="http://clicon.org/controller">
   <as-path-filter xmlns="http://nordu.net/ns/clixon/as-path-filter">
      <service-name>as-test1</service-name>
      <filter-name>as-test1</filter-name>
      <manual-as-numbers>1111</manual-as-numbers>
      <as-macro>AS-KTH</as-macro>
      <irr-sources>irr.ntt.org</irr-sources>
      <devices>crpd1</devices>
   </as-path-filter>
   <as-path-filter xmlns="http://nordu.net/ns/clixon/as-path-filter">
      <service-name>as-test2</service-name>
      <filter-name>as-test2</filter-name>
      <manual-as-numbers>1111</manual-as-numbers>
      <as-macro>AS-KTH</as-macro>
      <irr-sources>irr.ntt.org</irr-sources>
      <devices>crpd1</devices>
   </as-path-filter>
</services>
    """

    root = parse_string(xmlstr)

    instance = get_service_instance(
        root, "as-path-filter", instance="as-test1")

    assert instance.service_name == "as-test1"
    assert instance.filter_name == "as-test1"

    instance = get_service_instance(
        root, "as-path-filter", instance="as-test2")

    assert instance.service_name == "as-test2"
    assert instance.filter_name == "as-test2"


def test_get_service_instances():
    """
    Test that get_service_instances works as expected.
    """

    xmlstr = """
<services xmlns="http://clicon.org/controller">
   <as-path-filter xmlns="http://nordu.net/ns/clixon/as-path-filter">
      <service-name>as-test1</service-name>
      <filter-name>as-test1</filter-name>
      <manual-as-numbers>1111</manual-as-numbers>
      <as-macro>AS-KTH</as-macro>
      <irr-sources>irr.ntt.org</irr-sources>
      <devices>crpd1</devices>
   </as-path-filter>
   <as-path-filter xmlns="http://nordu.net/ns/clixon/as-path-filter">
      <service-name>as-test2</service-name>
      <filter-name>as-test2</filter-name>
      <manual-as-numbers>1111</manual-as-numbers>
      <as-macro>AS-KTH</as-macro>
      <irr-sources>irr.ntt.org</irr-sources>
      <devices>crpd1</devices>
   </as-path-filter>
</services>
    """

    root = parse_string(xmlstr)

    for instance in get_service_instances(root, "as-path-filter"):
        assert instance.service_name in ["as-test1", "as-test2"]
        assert instance.filter_name in ["as-test1", "as-test2"]


def test_get_devices():
    """
    Test that get_devices works as expected.
    """

    xmlstr = """
<devices xmlns="http://clicon.org/controller">
   <device-profile>
      <name>junos</name>
      <user>admin</user>
      <conn-type>NETCONF_SSH</conn-type>
   </device-profile>
   <device>
      <name>crpd1</name>
      <device-profile>junos</device-profile>
      <addr>172.40.0.2</addr>
      <config>
        <blah1/>
      </config>
    </device>
   <device>
      <name>crpd2</name>
      <device-profile>junos</device-profile>
      <addr>172.40.0.3</addr>
      <config>
        <blah1/>
      </config>
    </device>
</devices>
"""

    root = parse_string(xmlstr)

    for device in get_devices(root):
        assert device.name in ["crpd1", "crpd2"]
        assert device.addr in ["172.40.0.2", "172.40.0.3"]


def test_get_device():
    """
    Test that get_device works as expected.
    """

    xmlstr = """
<devices xmlns="http://clicon.org/controller">
   <device-profile>
      <name>junos</name>
      <user>admin</user>
      <conn-type>NETCONF_SSH</conn-type>
   </device-profile>
   <device>
      <name>crpd1</name>
      <device-profile>junos</device-profile>
      <addr>172.40.0.2</addr>
      <config>
        <blah1/>
      </config>
    </device>
   <device>
      <name>crpd2</name>
      <device-profile>junos</device-profile>
      <addr>172.40.0.3</addr>
      <config>
        <blah1/>
      </config>
    </device>
</devices>"""

    root = parse_string(xmlstr)

    device = get_device(root, "crpd1")

    assert device.name == "crpd1"
    assert device.addr == "172.40.0.2"

    device = get_device(root, "crpd2")

    assert device.name == "crpd2"
    assert device.addr == "172.40.0.3"


def test_get_devices_configuration():
    """
    Test that get_devices_configuration works as expected.
    """

    xmlstr = """
<devices xmlns="http://clicon.org/controller">
   <device-profile>
      <name>junos</name>
      <user>admin</user>
      <conn-type>NETCONF_SSH</conn-type>
   </device-profile>
   <device>
      <name>crpd1</name>
      <device-profile>junos</device-profile>
      <addr>172.40.0.2</addr>
      <config>
        <blah1/>
      </config>
    </device>
   <device>
      <name>crpd2</name>
      <device-profile>junos</device-profile>
      <addr>172.40.0.3</addr>
      <config>
        <blah2/>
      </config>
    </device>
</devices>"""

    root = parse_string(xmlstr)

    config = get_devices_configuration(root, "crpd1")

    assert config.dumps() == "<blah1/>"

    config = get_devices_configuration(root, "crpd2")

    assert config.dumps() == "<blah2/>"


def test_get_properties():
    """
    Test that get_properties works as expected.
    """

    xmlstr = """
<services xmlns="http://clicon.org/controller">
   <properties>
      <bgp-customer xmlns="http://nordu.net/ns/ncs/bgp">
         <bgp-core-community>4444</bgp-core-community>
         <bgp-blackhole-community>3333</bgp-blackhole-community>
         <bgp-upstream-blackhole-community>5555</bgp-upstream-blackhole-community>
         <bgp-group>test</bgp-group>
         <bgp-group-ipv6>test6</bgp-group-ipv6>
         <irr-database>rr.ntt.net</irr-database>
         <irr-sources>RIPE</irr-sources>
         <prefix-list-delta-limit>100</prefix-list-delta-limit>
         <prefix-list-delta-limit-v6>200</prefix-list-delta-limit-v6>
      </bgp-customer>
   </properties>
</services>"""

    root = parse_string(xmlstr)

    properties = get_properties(root, "bgp-customer")

    assert properties["bgp_core_community"] == "4444"
    assert properties["bgp_blackhole_community"] == "3333"
    assert properties["bgp_upstream_blackhole_community"] == "5555"
    assert properties["bgp_group"] == "test"
    assert properties["bgp_group_ipv6"] == "test6"
    assert properties["irr_database"] == "rr.ntt.net"
    assert properties["irr_sources"] == "RIPE"
    assert properties["prefix_list_delta_limit"] == "100"
    assert properties["prefix_list_delta_limit_v6"] == "200"


def test_get_devices_from_group():
    """
    Test that get_devices_from_group works as expected.
    """

    xmlstr = """
   <devices xmlns="http://clicon.org/controller">
      <device-group>
         <name>ALL</name>
         <device-name>crpd1</device-name>
         <device-name>crpd2</device-name>
      </device-group>
    </devices>
"""

    root = parse_string(xmlstr)

    devices = get_devices_from_group(root, "ALL")

    assert devices == ["crpd1", "crpd2"]


def test_is_juniper():
    """
    Test that is_juniper works as expected.
    """

    xmlstr = """<device><config><configuration xmlns="http://yang.juniper.net/junos/conf/root"><version>22.4R2-S2.4-EVO</version></configuration></config></device>"""

    root = parse_string(xmlstr)

    assert is_juniper(root.device) is True


def test_get_junos_interface_address():
    """
    Test that get_junos_interface_address works as expected.
    """

    xmlstr = """
<devices xmlns="http://clicon.org/controller"><device><name>juniper1</name><enabled>true</enabled><conn-type>NETCONF_SSH</conn-type><user>admin</user><addr>172.40.0.3</addr><config><configuration xmlns="http://yang.juniper.net/junos/conf/root"><version>20220909.043510_builder.r1282894</version><system><root-authentication><encrypted-password>$6$lB5c6$Zeud8c6IhCTE6hnZxXBl3ZMZTC2hOx9pxxYUWTHKW1oC32SATWLMH2EXarxWS5k685qMggUfFur1lq.o4p4cg1</encrypted-password></root-authentication><login><user><name>admin</name><uid>2000</uid><class>super-user</class><authentication><ssh-rsa><name>ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDF7BB+hkfqtLiwSvPNte72vQSzeF/KRtAEQywJtqrBAiRJBalZ30EyTMwXydPROHI5VBcm6hN28N89HtEBmKcrg8kU7qVLmmrBOJKYWI1aAWTgfwrPbnSOuo4sRu/jUClSHryOidEtUoh+SJ30X1yvm+S2rP0TM8W5URk0KqLvr4c/m1ejePhpg4BElicFwG6ogZYRWPAJZcygXkGil6N2SMJqFuPYC+IWnyh1l9t3C1wg3j1ldcbvagKSp1sH8zywPCfvly14qIHn814Y1ojgI+z27/TG2Y+svfQaRs6uLbCxy98+BMo2OqFQ1qSkzS5CyEis5tdZR3WW917aaEOJvxs5VVIXXb5RuB925z/rM/DwlSXKzefAzpj0hsrY365Gcm0mt/YfRv0hVAa0dOJloYnZwy7ZxcQKaEpDarPLlXhcb13oEGVFj0iQjAgdXpECk40MFXe//EAJyf4sChOoZyd6MNBlSTTOSLyM4vorEnmzFl1WeJze5bERFOsHjUM=</name></ssh-rsa></authentication></user></login><services><ssh/><netconf><ssh/><rfc-compliant/></netconf></services></system><interfaces><interface><name>lo0</name><unit><name>0</name><family><inet><address><name>1.1.1.1/32</name><primary/></address><address><name>1.1.1.2/32</name></address></inet><inet6><address><name>dead:beef::1/64</name><primary/></address><address><name>dead:beef::2/64</name></address></inet6></family></unit></interface></interfaces><policy-options><policy-statement><name>test-in</name><then><accept/></then></policy-statement><policy-statement><name>test-out</name><then><accept/></then></policy-statement></policy-options><routing-options><autonomous-system><as-number>1653</as-number></autonomous-system></routing-options><protocols><bgp><group><name>test</name><type>external</type><local-address>172.40.0.3</local-address><import>test-in</import><export>test-out</export><local-as><as-number>1111</as-number></local-as></group></bgp></protocols></configuration></config></device><device><name>juniper2</name><enabled>true</enabled><conn-type>NETCONF_SSH</conn-type><user>admin</user><addr>172.40.0.5</addr><config><configuration xmlns="http://yang.juniper.net/junos/conf/root"><version>20230909.043510_builder.r1282894</version><system><root-authentication><encrypted-password>$6$lB5c6$Zeud8c6IhCTE6hnZxXBl3ZMZTC2hOx9pxxYUWTHKW1oC32SATWLMH2EXarxWS5k685qMggUfFur1lq.o4p4cg1</encrypted-password></root-authentication><login><user><name>admin</name><uid>2000</uid><class>super-user</class><authentication><ssh-rsa><name>ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDF7BB+hkfqtLiwSvPNte72vQSzeF/KRtAEQywJtqrBAiRJBalZ30EyTMwXydPROHI5VBcm6hN28N89HtEBmKcrg8kU7qVLmmrBOJKYWI1aAWTgfwrPbnSOuo4sRu/jUClSHryOidEtUoh+SJ30X1yvm+S2rP0TM8W5URk0KqLvr4c/m1ejePhpg4BElicFwG6ogZYRWPAJZcygXkGil6N2SMJqFuPYC+IWnyh1l9t3C1wg3j1ldcbvagKSp1sH8zywPCfvly14qIHn814Y1ojgI+z27/TG2Y+svfQaRs6uLbCxy98+BMo2OqFQ1qSkzS5CyEis5tdZR3WW917aaEOJvxs5VVIXXb5RuB925z/rM/DwlSXKzefAzpj0hsrY365Gcm0mt/YfRv0hVAa0dOJloYnZwy7ZxcQKaEpDarPLlXhcb13oEGVFj0iQjAgdXpECk40MFXe//EAJyf4sChOoZyd6MNBlSTTOSLyM4vorEnmzFl1WeJze5bERFOsHjUM=</name></ssh-rsa></authentication></user></login><services><ssh/><netconf><ssh/><rfc-compliant/></netconf></services></system><interfaces><interface><name>lo0</name><unit><name>0</name><family><inet><address><name>2.2.2.2/32</name></address><address><name>2.2.2.3/32</name></address></inet><inet6><address><name>dead:beef::10/64</name></address><address><name>dead:beef::20/64</name></address></inet6></family></unit></interface></interfaces><policy-options><policy-statement><name>test-in</name><then><accept/></then></policy-statement><policy-statement><name>test-out</name><then><accept/></then></policy-statement></policy-options><routing-options><autonomous-system><as-number>1653</as-number></autonomous-system></routing-options><protocols><bgp><group><name>test</name><type>external</type><local-address>172.40.0.5</local-address><import>test-in</import><export>test-out</export><local-as><as-number>2222</as-number></local-as></group></bgp></protocols></configuration></config></device></devices>
    """

    root = parse_string(xmlstr)

    addresses = get_junos_interface_address(
        root, "juniper1", "lo0", "0", primary=True)

    assert (len(addresses) == 1)
    assert (addresses == ["1.1.1.1/32"])

    addresses = get_junos_interface_address(
        root, "juniper1", "lo0", "0", primary=False)

    assert (len(addresses) == 2)
    assert (addresses == ["1.1.1.1/32", "1.1.1.2/32"])

    addresses = get_junos_interface_address(
        root, "juniper2", "lo0", "0", primary=True)

    assert (len(addresses) == 0)
    assert (addresses == [])

    addresses = get_junos_interface_address(
        root, "juniper2", "lo0", "0", primary=False)

    assert (len(addresses) == 2)
    assert (addresses == ["2.2.2.2/32", "2.2.2.3/32"])

    addresses = get_junos_interface_address(
        root, "juniper1", "lo0", "0", family="inet6", primary=True)

    assert (len(addresses) == 1)
    assert (addresses == ["dead:beef::1/64"])

    addresses = get_junos_interface_address(
        root, "juniper1", "lo0", "0", family="inet6", primary=False)

    assert (len(addresses) == 2)
    assert (addresses == ["dead:beef::1/64", "dead:beef::2/64"])
