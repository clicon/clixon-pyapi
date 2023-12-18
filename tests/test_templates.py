from clixon.parser import (
    parse_template, parse_template_config,
    parse_template_file,
    parse_string
)


def test1():
    """
    Test template parsing from string using {{variale}}.
    """

    xml = """
<term>
    <name>{{NAME}}</name>
    <from>
        <family>inet</family>
        <community>{{COMMUNITY}}</community>
        <prefix-list-filter>
            <list_name>{{LIST_NAME}}</list_name>
            <longer/>
        </prefix-list-filter>
    </from>
    <then>
        <community>
            <delete/>
            <community-name>{{COMMUNITY_NAME}}</community-name>
        </community>
        <next-hop>
            <discard/>
        </next-hop>
        <accept/>
    </then>
</term>
"""
    result = """<term><name>my_name</name><from><family>inet</family><community>community</community><prefix-list-filter><list_name>my_list</list_name><longer/></prefix-list-filter></from><then><community><delete/><community-name>my_community</community-name></community><next-hop><discard/></next-hop><accept/></then></term>"""

    root = parse_template(xml, COMMUNITY_NAME="my_community",
                          COMMUNITY="community",
                          LIST_NAME="my_list",
                          NAME="my_name")

    assert (root.dumps() == result)


def test2():
    """
    Test template parsing from string using ${variale}.
    """

    xml = """
<term>
    <name>${NAME}</name>
    <from>
        <family>inet</family>
        <community>${COMMUNITY}</community>
        <prefix-list-filter>
            <list_name>${LIST_NAME}</list_name>
            <longer/>
        </prefix-list-filter>
    </from>
    <then>
        <community>
            <delete/>
            <community-name>${COMMUNITY_NAME}</community-name>
        </community>
        <next-hop>
            <discard/>
        </next-hop>
        <accept/>
    </then>
</term>
"""
    result = """<term><name>my_name</name><from><family>inet</family><community>community</community><prefix-list-filter><list_name>my_list</list_name><longer/></prefix-list-filter></from><then><community><delete/><community-name>my_community</community-name></community><next-hop><discard/></next-hop><accept/></then></term>"""

    root = parse_template(xml,
                          COMMUNITY_NAME="my_community",
                          COMMUNITY="community",
                          LIST_NAME="my_list",
                          NAME="my_name")

    assert (root.dumps() == result)


def test3():
    """
    Test template parsing from file using mixed variable types.
    """

    xml = """
<term>
    <name>${NAME}</name>
    <from>
        <family>inet</family>
        <community>${COMMUNITY}</community>
        <prefix-list-filter>
            <list_name>${LIST_NAME}</list_name>
            <longer/>
        </prefix-list-filter>
    </from>
    <then>
        <community>
            <delete/>
            <community-name>{{COMMUNITY_NAME}}</community-name>
        </community>
        <next-hop>
            <discard/>
        </next-hop>
        <accept/>
    </then>
</term>
"""
    result = """<term><name>my_name</name><from><family>inet</family><community>community</community><prefix-list-filter><list_name>my_list</list_name><longer/></prefix-list-filter></from><then><community><delete/><community-name>my_community</community-name></community><next-hop><discard/></next-hop><accept/></then></term>"""

    with open("/tmp/test_template.xml", "w") as f:
        f.write(xml)

    root = parse_template_file("/tmp/test_template.xml", format="clixon",
                               COMMUNITY_NAME="my_community",
                               COMMUNITY="community",
                               LIST_NAME="my_list",
                               NAME="my_name")

    assert (root.dumps() == result)


def test4():
    """
    Test template parsing from configuration root using mixed variable types.
    """

    xml = """
<devices xmlns="http://clicon.org/controller">
   <template>
      <name>customer-in</name>
      <config>
         <configuration xmlns="http://yang.juniper.net/junos/conf/root">
            <policy-options xmlns="http://yang.juniper.net/junos/conf/policy-options">
               <policy-statement>
                  <name>test</name>
                  <term>
                     <name>blackhole-v4</name>
                     <from>
                        <family>inet</family>
                        <community>{{BLACKHOLE}}</community>
                        <prefix-list-filter>
                           <list_name>${PREFIX_LIST}</list_name>
                           <choice-ident>longer</choice-ident>
                           <choice-value/>
                        </prefix-list-filter>
                     </from>
                     <then>
                        <community>
                           <choice-ident>delete</choice-ident>
                           <choice-value/>
                           <community-name>${CORE-COMMUNITY}</community-name>
                        </community>
                        <next-hop>
                           <discard/>
                        </next-hop>
                        <accept/>
                     </then>
                  </term>
               </policy-statement>
            </policy-options>
         </configuration>
      </config>
   </template>
</devices>"""

    root = parse_string(xml)

    template_root = parse_template_config(root, "customer-in",
                                          BLACKHOLE="blackhole",
                                          PREFIX_LIST="my_list",
                                          CORE_COMMUNITY="my_community")

    result = """<policy-options xmlns="http://yang.juniper.net/junos/conf/policy-options"><policy-statement><name>test</name><term><name>blackhole-v4</name><from><family>inet</family><community>blackhole</community><prefix-list-filter><list_name>my_list</list_name><choice-ident>longer</choice-ident><choice-value/></prefix-list-filter></from><then><community><choice-ident>delete</choice-ident><choice-value/><community-name>my_community</community-name></community><next-hop><discard/></next-hop><accept/></then></term></policy-statement></policy-options>"""

    assert (template_root.dumps() == result)
