from clixon.helpers import path_to_xpath


def test_path_to_xpath_simple():
    """
    Test path_to_xpath with a simple path.
    """
    assert path_to_xpath("devices/device") == "/devices/device"


def test_path_to_xpath_with_leading_slash():
    """
    Test path_to_xpath with a path that already has a leading slash.
    """
    assert path_to_xpath("/devices/device") == "/devices/device"


def test_path_to_xpath_with_index():
    """
    Test path_to_xpath with numeric index (0-based to 1-based conversion).
    """
    assert path_to_xpath("devices/device[0]") == "/devices/device[1]"
    assert path_to_xpath("devices/device[1]") == "/devices/device[2]"
    assert path_to_xpath("devices/device[0]/config") == "/devices/device[1]/config"


def test_path_to_xpath_with_name_filter():
    """
    Test path_to_xpath with name filter.
    """
    assert path_to_xpath("devices/device[name='r1']") == "/devices/device[name='r1']"
    assert (
        path_to_xpath("devices/device[name='r1']/config")
        == "/devices/device[name='r1']/config"
    )


def test_path_to_xpath_with_double_quotes():
    """
    Test path_to_xpath with double quotes (should be converted to single quotes).
    """
    assert path_to_xpath('devices/device[name="r1"]') == "/devices/device[name='r1']"


def test_path_to_xpath_complex():
    """
    Test path_to_xpath with complex paths.
    """
    assert (
        path_to_xpath("devices/device[name='juniper1']/config/configuration/version")
        == "/devices/device[name='juniper1']/config/configuration/version"
    )
    assert (
        path_to_xpath(
            "devices/device[name='juniper1']/config/configuration/interfaces/interface[name='lo0']/unit[0]"
        )
        == "/devices/device[name='juniper1']/config/configuration/interfaces/interface[name='lo0']/unit[1]"
    )


def test_path_to_xpath_empty():
    """
    Test path_to_xpath with empty path.
    """
    assert path_to_xpath("") == "/"
    assert path_to_xpath(None) == "/"


def test_path_to_xpath_multiple_filters():
    """
    Test path_to_xpath with multiple filters in the path.
    """
    assert (
        path_to_xpath("services/bgp-peer[name='bgp-test']")
        == "/services/bgp-peer[name='bgp-test']"
    )
