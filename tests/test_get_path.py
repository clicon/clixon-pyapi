from clixon.element import Element
from clixon.helpers import get_path
from clixon.parser import parse_string

xmlstr = """
<devices xmlns="http://clicon.org/controller"><device><name>juniper1</name><enabled>true</enabled><conn-type>NETCONF_SSH</conn-type><user>admin</user><addr>172.40.0.3</addr><config><configuration xmlns="http://yang.juniper.net/junos/conf/root"><version>20220909.043510_builder.r1282894</version><system><root-authentication><encrypted-password>$6$lB5c6$Zeud8c6IhCTE6hnZxXBl3ZMZTC2hOx9pxxYUWTHKW1oC32SATWLMH2EXarxWS5k685qMggUfFur1lq.o4p4cg1</encrypted-password></root-authentication><login><user><name>admin</name><uid>2000</uid><class>super-user</class><authentication><ssh-rsa><name>ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDF7BB+hkfqtLiwSvPNte72vQSzeF/KRtAEQywJtqrBAiRJBalZ30EyTMwXydPROHI5VBcm6hN28N89HtEBmKcrg8kU7qVLmmrBOJKYWI1aAWTgfwrPbnSOuo4sRu/jUClSHryOidEtUoh+SJ30X1yvm+S2rP0TM8W5URk0KqLvr4c/m1ejePhpg4BElicFwG6ogZYRWPAJZcygXkGil6N2SMJqFuPYC+IWnyh1l9t3C1wg3j1ldcbvagKSp1sH8zywPCfvly14qIHn814Y1ojgI+z27/TG2Y+svfQaRs6uLbCxy98+BMo2OqFQ1qSkzS5CyEis5tdZR3WW917aaEOJvxs5VVIXXb5RuB925z/rM/DwlSXKzefAzpj0hsrY365Gcm0mt/YfRv0hVAa0dOJloYnZwy7ZxcQKaEpDarPLlXhcb13oEGVFj0iQjAgdXpECk40MFXe//EAJyf4sChOoZyd6MNBlSTTOSLyM4vorEnmzFl1WeJze5bERFOsHjUM=</name></ssh-rsa></authentication></user></login><services><ssh/><netconf><ssh/><rfc-compliant/></netconf></services></system><interfaces><interface><name>lo0</name><unit><name>0</name><family><inet><address><name>1.1.1.1/32</name></address></inet></family></unit></interface></interfaces><policy-options><policy-statement><name>test-in</name><then><accept/></then></policy-statement><policy-statement><name>test-out</name><then><accept/></then></policy-statement></policy-options><routing-options><autonomous-system><as-number>1653</as-number></autonomous-system></routing-options><protocols><bgp><group><name>test</name><type>external</type><local-address>172.40.0.3</local-address><import>test-in</import><export>test-out</export><local-as><as-number>1111</as-number></local-as></group></bgp></protocols></configuration></config></device><device><name>juniper2</name><enabled>true</enabled><conn-type>NETCONF_SSH</conn-type><user>admin</user><addr>172.40.0.5</addr><config><configuration xmlns="http://yang.juniper.net/junos/conf/root"><version>20230909.043510_builder.r1282894</version><system><root-authentication><encrypted-password>$6$lB5c6$Zeud8c6IhCTE6hnZxXBl3ZMZTC2hOx9pxxYUWTHKW1oC32SATWLMH2EXarxWS5k685qMggUfFur1lq.o4p4cg1</encrypted-password></root-authentication><login><user><name>admin</name><uid>2000</uid><class>super-user</class><authentication><ssh-rsa><name>ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDF7BB+hkfqtLiwSvPNte72vQSzeF/KRtAEQywJtqrBAiRJBalZ30EyTMwXydPROHI5VBcm6hN28N89HtEBmKcrg8kU7qVLmmrBOJKYWI1aAWTgfwrPbnSOuo4sRu/jUClSHryOidEtUoh+SJ30X1yvm+S2rP0TM8W5URk0KqLvr4c/m1ejePhpg4BElicFwG6ogZYRWPAJZcygXkGil6N2SMJqFuPYC+IWnyh1l9t3C1wg3j1ldcbvagKSp1sH8zywPCfvly14qIHn814Y1ojgI+z27/TG2Y+svfQaRs6uLbCxy98+BMo2OqFQ1qSkzS5CyEis5tdZR3WW917aaEOJvxs5VVIXXb5RuB925z/rM/DwlSXKzefAzpj0hsrY365Gcm0mt/YfRv0hVAa0dOJloYnZwy7ZxcQKaEpDarPLlXhcb13oEGVFj0iQjAgdXpECk40MFXe//EAJyf4sChOoZyd6MNBlSTTOSLyM4vorEnmzFl1WeJze5bERFOsHjUM=</name></ssh-rsa></authentication></user></login><services><ssh/><netconf><ssh/><rfc-compliant/></netconf></services></system><interfaces><interface><name>lo0</name><unit><name>0</name><family><inet><address><name>2.2.2.2/32</name></address></inet></family></unit></interface></interfaces><policy-options><policy-statement><name>test-in</name><then><accept/></then></policy-statement><policy-statement><name>test-out</name><then><accept/></then></policy-statement></policy-options><routing-options><autonomous-system><as-number>1653</as-number></autonomous-system></routing-options><protocols><bgp><group><name>test</name><type>external</type><local-address>172.40.0.5</local-address><import>test-in</import><export>test-out</export><local-as><as-number>2222</as-number></local-as></group></bgp></protocols></configuration></config></device></devices>
"""

xmlstr2 = """
<devices-foo xmlns="http://clicon.org/controller"><device><device-name>juniper1</device-name><enabled>true</enabled><conn-type>NETCONF_SSH</conn-type><user>admin</user><addr>172.40.0.3</addr><config><configuration xmlns="http://yang.juniper.net/junos/conf/root"><version>20220909.043510_builder.r1282894</version><system><root-authentication><encrypted-password>$6$lB5c6$Zeud8c6IhCTE6hnZxXBl3ZMZTC2hOx9pxxYUWTHKW1oC32SATWLMH2EXarxWS5k685qMggUfFur1lq.o4p4cg1</encrypted-password></root-authentication><login><user><name>admin</name><uid>2000</uid><class>super-user</class><authentication><ssh-rsa><name>ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDF7BB+hkfqtLiwSvPNte72vQSzeF/KRtAEQywJtqrBAiRJBalZ30EyTMwXydPROHI5VBcm6hN28N89HtEBmKcrg8kU7qVLmmrBOJKYWI1aAWTgfwrPbnSOuo4sRu/jUClSHryOidEtUoh+SJ30X1yvm+S2rP0TM8W5URk0KqLvr4c/m1ejePhpg4BElicFwG6ogZYRWPAJZcygXkGil6N2SMJqFuPYC+IWnyh1l9t3C1wg3j1ldcbvagKSp1sH8zywPCfvly14qIHn814Y1ojgI+z27/TG2Y+svfQaRs6uLbCxy98+BMo2OqFQ1qSkzS5CyEis5tdZR3WW917aaEOJvxs5VVIXXb5RuB925z/rM/DwlSXKzefAzpj0hsrY365Gcm0mt/YfRv0hVAa0dOJloYnZwy7ZxcQKaEpDarPLlXhcb13oEGVFj0iQjAgdXpECk40MFXe//EAJyf4sChOoZyd6MNBlSTTOSLyM4vorEnmzFl1WeJze5bERFOsHjUM=</name></ssh-rsa></authentication></user></login><services><ssh/><netconf><ssh/><rfc-compliant/></netconf></services></system><interfaces><interface><name>lo0</name><unit><name>0</name><family><inet><address><name>1.1.1.1/32</name></address></inet></family></unit></interface></interfaces><policy-options><policy-statement><name>test-in</name><then><accept/></then></policy-statement><policy-statement><name>test-out</name><then><accept/></then></policy-statement></policy-options><routing-options><autonomous-system><as-number>1653</as-number></autonomous-system></routing-options><protocols><bgp><group><name>test</name><type>external</type><local-address>172.40.0.3</local-address><import>test-in</import><export>test-out</export><local-as><as-number>1111</as-number></local-as></group></bgp></protocols></configuration></config></device><device><device-name>juniper2</device-name><enabled>true</enabled><conn-type>NETCONF_SSH</conn-type><user>admin</user><addr>172.40.0.5</addr><config><configuration xmlns="http://yang.juniper.net/junos/conf/root"><version>20230909.043510_builder.r1282894</version><system><root-authentication><encrypted-password>$6$lB5c6$Zeud8c6IhCTE6hnZxXBl3ZMZTC2hOx9pxxYUWTHKW1oC32SATWLMH2EXarxWS5k685qMggUfFur1lq.o4p4cg1</encrypted-password></root-authentication><login><user><name>admin</name><uid>2000</uid><class>super-user</class><authentication><ssh-rsa><name>ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDF7BB+hkfqtLiwSvPNte72vQSzeF/KRtAEQywJtqrBAiRJBalZ30EyTMwXydPROHI5VBcm6hN28N89HtEBmKcrg8kU7qVLmmrBOJKYWI1aAWTgfwrPbnSOuo4sRu/jUClSHryOidEtUoh+SJ30X1yvm+S2rP0TM8W5URk0KqLvr4c/m1ejePhpg4BElicFwG6ogZYRWPAJZcygXkGil6N2SMJqFuPYC+IWnyh1l9t3C1wg3j1ldcbvagKSp1sH8zywPCfvly14qIHn814Y1ojgI+z27/TG2Y+svfQaRs6uLbCxy98+BMo2OqFQ1qSkzS5CyEis5tdZR3WW917aaEOJvxs5VVIXXb5RuB925z/rM/DwlSXKzefAzpj0hsrY365Gcm0mt/YfRv0hVAa0dOJloYnZwy7ZxcQKaEpDarPLlXhcb13oEGVFj0iQjAgdXpECk40MFXe//EAJyf4sChOoZyd6MNBlSTTOSLyM4vorEnmzFl1WeJze5bERFOsHjUM=</name></ssh-rsa></authentication></user></login><services><ssh/><netconf><ssh/><rfc-compliant/></netconf></services></system><interfaces><interface><name>lo0</name><unit><name>0</name><family><inet><address><name>2.2.2.2/32</name></address></inet></family></unit></interface></interfaces><policy-options><policy-statement><name>test-in</name><then><accept/></then></policy-statement><policy-statement><name>test-out</name><then><accept/></then></policy-statement></policy-options><routing-options><autonomous-system><as-number>1653</as-number></autonomous-system></routing-options><protocols><bgp><group><name>test</name><type>external</type><local-address>172.40.0.5</local-address><import>test-in</import><export>test-out</export><local-as><as-number>2222</as-number></local-as></group></bgp></protocols></configuration></config></device></devices-foo>
"""

xmlstr3 = """
<devices_foo xmlns="http://clicon.org/controller"><device><device_name>juniper1</device_name><enabled>true</enabled><conn-type>NETCONF_SSH</conn-type><user>admin</user><addr>172.40.0.3</addr><config><configuration xmlns="http://yang.juniper.net/junos/conf/root"><version>20220909.043510_builder.r1282894</version><system><root-authentication><encrypted-password>$6$lB5c6$Zeud8c6IhCTE6hnZxXBl3ZMZTC2hOx9pxxYUWTHKW1oC32SATWLMH2EXarxWS5k685qMggUfFur1lq.o4p4cg1</encrypted-password></root-authentication><login><user><name>admin</name><uid>2000</uid><class>super-user</class><authentication><ssh-rsa><name>ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDF7BB+hkfqtLiwSvPNte72vQSzeF/KRtAEQywJtqrBAiRJBalZ30EyTMwXydPROHI5VBcm6hN28N89HtEBmKcrg8kU7qVLmmrBOJKYWI1aAWTgfwrPbnSOuo4sRu/jUClSHryOidEtUoh+SJ30X1yvm+S2rP0TM8W5URk0KqLvr4c/m1ejePhpg4BElicFwG6ogZYRWPAJZcygXkGil6N2SMJqFuPYC+IWnyh1l9t3C1wg3j1ldcbvagKSp1sH8zywPCfvly14qIHn814Y1ojgI+z27/TG2Y+svfQaRs6uLbCxy98+BMo2OqFQ1qSkzS5CyEis5tdZR3WW917aaEOJvxs5VVIXXb5RuB925z/rM/DwlSXKzefAzpj0hsrY365Gcm0mt/YfRv0hVAa0dOJloYnZwy7ZxcQKaEpDarPLlXhcb13oEGVFj0iQjAgdXpECk40MFXe//EAJyf4sChOoZyd6MNBlSTTOSLyM4vorEnmzFl1WeJze5bERFOsHjUM=</name></ssh-rsa></authentication></user></login><services><ssh/><netconf><ssh/><rfc-compliant/></netconf></services></system><interfaces><interface><name>lo0</name><unit><name>0</name><family><inet><address><name>1.1.1.1/32</name></address></inet></family></unit></interface></interfaces><policy-options><policy-statement><name>test-in</name><then><accept/></then></policy-statement><policy-statement><name>test-out</name><then><accept/></then></policy-statement></policy-options><routing-options><autonomous-system><as-number>1653</as-number></autonomous-system></routing-options><protocols><bgp><group><name>test</name><type>external</type><local-address>172.40.0.3</local-address><import>test-in</import><export>test-out</export><local-as><as-number>1111</as-number></local-as></group></bgp></protocols></configuration></config></device><device><device_name>juniper2</device_name><enabled>true</enabled><conn-type>NETCONF_SSH</conn-type><user>admin</user><addr>172.40.0.5</addr><config><configuration xmlns="http://yang.juniper.net/junos/conf/root"><version>20230909.043510_builder.r1282894</version><system><root-authentication><encrypted-password>$6$lB5c6$Zeud8c6IhCTE6hnZxXBl3ZMZTC2hOx9pxxYUWTHKW1oC32SATWLMH2EXarxWS5k685qMggUfFur1lq.o4p4cg1</encrypted-password></root-authentication><login><user><name>admin</name><uid>2000</uid><class>super-user</class><authentication><ssh-rsa><name>ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDF7BB+hkfqtLiwSvPNte72vQSzeF/KRtAEQywJtqrBAiRJBalZ30EyTMwXydPROHI5VBcm6hN28N89HtEBmKcrg8kU7qVLmmrBOJKYWI1aAWTgfwrPbnSOuo4sRu/jUClSHryOidEtUoh+SJ30X1yvm+S2rP0TM8W5URk0KqLvr4c/m1ejePhpg4BElicFwG6ogZYRWPAJZcygXkGil6N2SMJqFuPYC+IWnyh1l9t3C1wg3j1ldcbvagKSp1sH8zywPCfvly14qIHn814Y1ojgI+z27/TG2Y+svfQaRs6uLbCxy98+BMo2OqFQ1qSkzS5CyEis5tdZR3WW917aaEOJvxs5VVIXXb5RuB925z/rM/DwlSXKzefAzpj0hsrY365Gcm0mt/YfRv0hVAa0dOJloYnZwy7ZxcQKaEpDarPLlXhcb13oEGVFj0iQjAgdXpECk40MFXe//EAJyf4sChOoZyd6MNBlSTTOSLyM4vorEnmzFl1WeJze5bERFOsHjUM=</name></ssh-rsa></authentication></user></login><services><ssh/><netconf><ssh/><rfc-compliant/></netconf></services></system><interfaces><interface><name>lo0</name><unit><name>0</name><family><inet><address><name>2.2.2.2/32</name></address></inet></family></unit></interface></interfaces><policy-options><policy-statement><name>test-in</name><then><accept/></then></policy-statement><policy-statement><name>test-out</name><then><accept/></then></policy-statement></policy-options><routing-options><autonomous-system><as-number>1653</as-number></autonomous-system></routing-options><protocols><bgp><group><name>test</name><type>external</type><local-address>172.40.0.5</local-address><import>test-in</import><export>test-out</export><local-as><as-number>2222</as-number></local-as></group></bgp></protocols></configuration></config></device></devices_foo>
"""


def test1():
    """
    Test get_path function using an index in the path.
    """

    root = parse_string(xmlstr)

    e = get_path(root, "/devices/device[0]/config/configuration/version")

    assert type(e) is Element
    teststr = str(e)

    assert teststr == "20220909.043510_builder.r1282894"


def test2():
    """
    Test get_path function using a name in the path.
    """

    root = parse_string(xmlstr)

    e = get_path(root, "/devices/device[name='juniper1']/config/configuration/version")

    assert type(e) is Element
    teststr = str(e)

    assert teststr == "20220909.043510_builder.r1282894"


def test3():
    """
    Test get_path function using another name in the path.
    """

    root = parse_string(xmlstr)

    e = get_path(root, "/devices/device[name='juniper2']/config/configuration/version")

    teststr = str(e)

    assert type(e) is Element
    assert teststr == "20230909.043510_builder.r1282894"


def test4():
    """
    Test get_path function using a name in the path that does not exist.
    """

    root = parse_string(xmlstr)

    e = get_path(root, "/devices/device[name='juniperX']/config/configuration/version")

    assert e is None


def test5():
    """
    Test get_path function using a string with mixed types in it.
    """

    root = parse_string(xmlstr)

    e = get_path(
        root,
        "/devices/device[name='juniper1']/config/configuration/interfaces/interface[name='lo0']/unit[name='0']/family/inet/address/name",
    )

    teststr = str(e)

    assert type(e) is Element
    assert teststr == "1.1.1.1/32"


def test6():
    """
    Test get_path and get the UID for the user test which does not exist.
    """

    root = parse_string(xmlstr)

    e = get_path(
        root,
        "/devices/device[name='juniper1']/config/configuration/system/login/user[name='test']/uid",
    )

    assert e is None


def test7():
    """
    Test get_path function and get the UID for the user admin.
    """

    root = parse_string(xmlstr)

    e = get_path(
        root,
        "/devices/device[name='juniper1']/config/configuration/system/login/user[name='admin']/uid",
    )

    assert str(e) == "2000"


def test8():
    """
    Test get_path function and get the UID for the user admin using an index.
    """

    root = parse_string(xmlstr)

    e = get_path(
        root,
        "/devices/device[name='juniper1']/config/configuration/system/login/user[0]/uid",
    )

    assert str(e) == "2000"


def test9():
    """
    Test get_path function and get the UID using and index for a user that does not exist.
    """

    root = parse_string(xmlstr)

    e = get_path(
        root,
        "/devices/device[name='juniper1']/config/configuration/system/login/user[1]/uid",
    )

    assert e is None


def test10():
    """
    Test get_path function and get the UID using and index for a user that does not exist.
    """

    root = parse_string(xmlstr)

    e = get_path(
        root,
        "/devices/device[name='juniper1']/config/configuration/system/login/user[666]/uid",
    )

    assert e is None


def test11():
    """
    Test get_path function and get the UID using indexes.
    """

    root = parse_string(xmlstr)

    e = get_path(
        root, "/devices/device[0]/config/configuration/system/login/user[0]/uid"
    )

    assert str(e) == "2000"


def test12():
    """
    Test get_path function and get the whole device configuration.
    """

    root = parse_string(xmlstr)

    e = get_path(root, "/devices/device[0]/config/configuration")

    config_xml = """<version>20220909.043510_builder.r1282894</version><system><root-authentication><encrypted-password>$6$lB5c6$Zeud8c6IhCTE6hnZxXBl3ZMZTC2hOx9pxxYUWTHKW1oC32SATWLMH2EXarxWS5k685qMggUfFur1lq.o4p4cg1</encrypted-password></root-authentication><login><user><name>admin</name><uid>2000</uid><class>super-user</class><authentication><ssh-rsa><name>ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQDF7BB+hkfqtLiwSvPNte72vQSzeF/KRtAEQywJtqrBAiRJBalZ30EyTMwXydPROHI5VBcm6hN28N89HtEBmKcrg8kU7qVLmmrBOJKYWI1aAWTgfwrPbnSOuo4sRu/jUClSHryOidEtUoh+SJ30X1yvm+S2rP0TM8W5URk0KqLvr4c/m1ejePhpg4BElicFwG6ogZYRWPAJZcygXkGil6N2SMJqFuPYC+IWnyh1l9t3C1wg3j1ldcbvagKSp1sH8zywPCfvly14qIHn814Y1ojgI+z27/TG2Y+svfQaRs6uLbCxy98+BMo2OqFQ1qSkzS5CyEis5tdZR3WW917aaEOJvxs5VVIXXb5RuB925z/rM/DwlSXKzefAzpj0hsrY365Gcm0mt/YfRv0hVAa0dOJloYnZwy7ZxcQKaEpDarPLlXhcb13oEGVFj0iQjAgdXpECk40MFXe//EAJyf4sChOoZyd6MNBlSTTOSLyM4vorEnmzFl1WeJze5bERFOsHjUM=</name></ssh-rsa></authentication></user></login><services><ssh/><netconf><ssh/><rfc-compliant/></netconf></services></system><interfaces><interface><name>lo0</name><unit><name>0</name><family><inet><address><name>1.1.1.1/32</name></address></inet></family></unit></interface></interfaces><policy-options><policy-statement><name>test-in</name><then><accept/></then></policy-statement><policy-statement><name>test-out</name><then><accept/></then></policy-statement></policy-options><routing-options><autonomous-system><as-number>1653</as-number></autonomous-system></routing-options><protocols><bgp><group><name>test</name><type>external</type><local-address>172.40.0.3</local-address><import>test-in</import><export>test-out</export><local-as><as-number>1111</as-number></local-as></group></bgp></protocols>"""

    assert e.dumps() == config_xml


def tes13():
    """
    Test get_path function with valid an invalid paths.
    """

    root = parse_string(xmlstr2)

    e = get_path(
        root,
        "/devices-foo/device[device-name='juniper1']/config/configuration/system/login/user[name='admin']/uid",
    )

    assert str(e) == "2000"

    root = parse_string(xmlstr3)

    e = get_path(
        root,
        "/devices_foo/device[device_name='juniper1']/config/configuration/system/login/user[name='admin']/uid",
    )

    assert str(e) == "2000"


def test14():
    """
    Test that get_path replaces " with ' in the path.
    """

    root = parse_string(xmlstr)
    e = get_path(
        root,
        '/devices/device[name="juniper1"]/config/configuration/system/login/user[name="admin"]/uid',
    )

    assert str(e) == "2000"
