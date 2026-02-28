from xml.etree.ElementTree import Element

import pytest

from pytmx.element import TiledElement
from pytmx.properties import parse_properties


class DummyElement(TiledElement):
    def __init__(self, allow_duplicate_names=False):
        super().__init__(allow_duplicate_names=allow_duplicate_names)

    def parse_xml(self, node):
        self._set_properties(node)
        return self


class CustomClass(TiledElement):
    def __init__(self):
        super().__init__()
        self.properties["foo"] = "bar"

    def parse_xml(self, node):
        self._set_properties(node)
        return self


@pytest.fixture
def element():
    return DummyElement()


def test_initial_state(element):
    assert element._allow_duplicate_names is False
    assert element.properties == {}


def test_cast_and_set_attributes(element):
    items = [("width", "32"), ("height", "64"), ("visible", "1")]
    element._cast_and_set_attributes_from_node_items(items)
    assert element.width == 32.0
    assert element.height == 64.0
    assert element.visible is True


def test_invalid_property_name_detection(element):
    element.name = "TestElement"
    items = [("name", "conflict")]
    assert element._contains_invalid_property_name(items)


def test_valid_property_name_with_duplicates_allowed():
    el = DummyElement(allow_duplicate_names=True)
    items = [("name", "conflict")]
    assert el._contains_invalid_property_name(items) is False


def test_set_properties_with_valid_data(element):
    xml = Element("element", attrib={"width": "128", "height": "256"})
    props = Element("properties")
    prop = Element("property", attrib={"name": "custom", "value": "hello"})
    props.append(prop)
    xml.append(props)

    element._set_properties(xml)
    assert element.width == 128.0
    assert element.height == 256.0
    assert element.properties["custom"] == "hello"


def test_set_properties_with_conflict_raises(element):
    xml = Element("element", attrib={"name": "conflict"})
    props = Element("properties")
    prop = Element("property", attrib={"name": "name", "value": "oops"})
    props.append(prop)
    xml.append(props)

    with pytest.raises(ValueError):
        element._set_properties(xml)


def test_getattr_existing_property(element):
    element.properties["foo"] = "bar"
    assert element.foo == "bar"


def test_getattr_missing_property_with_name(element):
    element.properties["name"] = "TestElement"
    with pytest.raises(AttributeError) as exc:
        _ = element.missing
    assert "TestElement" in str(exc.value)


def test_getattr_missing_property_without_name(element):
    with pytest.raises(AttributeError) as exc:
        _ = element.missing
    assert "Element has no property" in str(exc.value)


def test_repr_with_id(element):
    element.id = 42
    element.name = "MyElement"
    assert repr(element) == '<DummyElement[42]: "MyElement">'


def test_repr_without_id(element):
    element.name = "MyElement"
    assert repr(element) == '<DummyElement: "MyElement">'


def test_from_xml_string():
    xml = """
    <element width="100" height="200">
        <properties>
            <property name="custom" value="value" />
        </properties>
    </element>
    """
    obj = DummyElement.from_xml_string(xml)
    assert obj.width == 100.0
    assert obj.height == 200.0
    assert obj.properties["custom"] == "value"


def test_property_type_casting():
    xml = Element("element")
    props = Element("properties")
    prop = Element(
        "property", attrib={"name": "visible", "type": "bool", "value": "true"}
    )
    props.append(prop)
    xml.append(props)

    props_dict = parse_properties(xml)
    assert props_dict["visible"] is True


def test_nested_class_property(monkeypatch):
    monkeypatch.setattr("pytmx.properties.deepcopy", lambda x: x)

    customs = {"MyClass": CustomClass()}
    xml = Element("element")
    props = Element("properties")

    class_prop = Element(
        "property",
        attrib={"name": "nested", "type": "class", "propertytype": "MyClass"},
    )
    subprop = Element("property", attrib={"name": "foo", "value": "bar"})
    class_prop.append(subprop)

    props.append(class_prop)
    xml.append(props)

    props_dict = parse_properties(xml, customs)
    assert props_dict["nested"].foo == "bar"


def test_property_fallback_to_text():
    xml = Element("element")
    props = Element("properties")
    prop = Element("property", attrib={"name": "fallback"})
    prop.text = "fallback_value"
    props.append(prop)
    xml.append(props)

    props_dict = parse_properties(xml)
    assert props_dict["fallback"] == "fallback_value"


def test_property_type_not_found_logs_info():
    xml = Element("element")
    props = Element("properties")
    prop = Element(
        "property", attrib={"name": "unknown", "type": "mystery", "value": "42"}
    )
    props.append(prop)
    xml.append(props)

    props_dict = parse_properties(xml)
    assert props_dict["unknown"] == "42"


def test_parse_xml_sets_properties(element):
    xml = Element("element", attrib={"width": "100", "height": "200"})
    props = Element("properties")
    prop = Element("property", attrib={"name": "custom", "value": "hello"})
    props.append(prop)
    xml.append(props)

    result = element.parse_xml(xml)
    assert result.width == 100.0
    assert result.height == 200.0
    assert result.properties["custom"] == "hello"


def test_repr_output(element):
    element.id = 1
    element.name = "TestDummy"
    assert repr(element) == '<DummyElement[1]: "TestDummy">'


def test_property_access(element):
    element.properties["foo"] = "bar"
    assert element.foo == "bar"


def test_missing_property_raises(element):
    with pytest.raises(AttributeError):
        _ = element.nonexistent


def test_contains_invalid_property_name(element):
    element.name = "dummy"
    items = [("name", "conflict")]
    assert element._contains_invalid_property_name(items)
