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


def test_list_property_basic():
    """Test basic list property parsing."""
    xml = Element("element")
    props = Element("properties")

    list_prop = Element("property", attrib={"name": "test_list", "type": "list"})

    # Add various typed items
    item1 = Element("item", attrib={"type": "string", "value": "hello"})
    item2 = Element("item", attrib={"type": "int", "value": "42"})
    item3 = Element("item", attrib={"type": "float", "value": "3.14"})
    item4 = Element("item", attrib={"type": "bool", "value": "true"})
    item5 = Element("item", attrib={"type": "color", "value": "#ff0000"})

    list_prop.extend([item1, item2, item3, item4, item5])
    props.append(list_prop)
    xml.append(props)

    props_dict = parse_properties(xml)
    result = props_dict["test_list"]

    assert isinstance(result, list)
    assert len(result) == 5
    assert result[0] == "hello"
    assert result[1] == 42
    assert result[2] == 3.14
    assert result[3] is True
    assert result[4] == "#ff0000"


def test_list_property_with_nested_list():
    """Test list property containing nested lists."""
    xml = Element("element")
    props = Element("properties")

    list_prop = Element("property", attrib={"name": "nested_list", "type": "list"})

    # Add some regular items
    item1 = Element("item", attrib={"type": "string", "value": "outer"})

    # Add a nested list
    nested_list = Element("item", attrib={"type": "list"})
    nested_item1 = Element("item", attrib={"type": "int", "value": "1"})
    nested_item2 = Element("item", attrib={"type": "int", "value": "2"})
    nested_list.extend([nested_item1, nested_item2])

    # Add another regular item
    item3 = Element("item", attrib={"type": "string", "value": "end"})

    list_prop.extend([item1, nested_list, item3])
    props.append(list_prop)
    xml.append(props)

    props_dict = parse_properties(xml)
    result = props_dict["nested_list"]

    assert isinstance(result, list)
    assert len(result) == 3
    assert result[0] == "outer"
    assert isinstance(result[1], list)
    assert result[1] == [1, 2]
    assert result[2] == "end"


def test_list_property_deep_nesting():
    """Test list property with arbitrarily deep nesting."""
    xml = Element("element")
    props = Element("properties")

    # Create a deeply nested structure: [[[[1]]]]
    outer_list = Element("property", attrib={"name": "deep_list", "type": "list"})

    level1 = Element("item", attrib={"type": "list"})
    level2 = Element("item", attrib={"type": "list"})
    level3 = Element("item", attrib={"type": "list"})
    innermost = Element("item", attrib={"type": "int", "value": "42"})

    level3.append(innermost)
    level2.append(level3)
    level1.append(level2)
    outer_list.append(level1)

    props.append(outer_list)
    xml.append(props)

    props_dict = parse_properties(xml)
    result = props_dict["deep_list"]

    # Should be: [[[[42]]]]
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], list)
    assert len(result[0]) == 1
    assert isinstance(result[0][0], list)
    assert len(result[0][0]) == 1
    assert isinstance(result[0][0][0], list)
    assert len(result[0][0][0]) == 1
    assert result[0][0][0][0] == 42


def test_list_property_mixed_types():
    """Test list property with mixed types including objects."""
    xml = Element("element")
    props = Element("properties")

    list_prop = Element("property", attrib={"name": "mixed_list", "type": "list"})

    # Test all supported types
    items = [
        Element("item", attrib={"type": "bool", "value": "false"}),
        Element("item", attrib={"type": "color", "value": "#00ff00"}),
        Element("item", attrib={"type": "file", "value": "test.png"}),
        Element("item", attrib={"type": "float", "value": "2.71"}),
        Element("item", attrib={"type": "int", "value": "123"}),
        Element("item", attrib={"type": "object", "value": "456"}),
        Element("item", attrib={"type": "string", "value": "test"}),
        Element("item", attrib={"type": "enum", "value": "option1"}),
    ]

    list_prop.extend(items)
    props.append(list_prop)
    xml.append(props)

    props_dict = parse_properties(xml)
    result = props_dict["mixed_list"]

    assert isinstance(result, list)
    assert len(result) == 8
    assert result[0] is False
    assert result[1] == "#00ff00"
    assert result[2] == "test.png"
    assert result[3] == 2.71
    assert result[4] == 123
    assert result[5] == 456
    assert result[6] == "test"
    assert result[7] == "option1"


def test_list_property_empty():
    """Test empty list property."""
    xml = Element("element")
    props = Element("properties")

    list_prop = Element("property", attrib={"name": "empty_list", "type": "list"})
    # No items added

    props.append(list_prop)
    xml.append(props)

    props_dict = parse_properties(xml)
    result = props_dict["empty_list"]

    assert isinstance(result, list)
    assert len(result) == 0


def test_list_property_default_types():
    """Test list items without explicit type attributes."""
    xml = Element("element")
    props = Element("properties")

    list_prop = Element("property", attrib={"name": "default_list", "type": "list"})

    # Items without type should default to string
    item1 = Element("item", attrib={"value": "string1"})
    item2 = Element("item")  # No value attribute, should use text
    item2.text = "string2"

    list_prop.extend([item1, item2])
    props.append(list_prop)
    xml.append(props)

    props_dict = parse_properties(xml)
    result = props_dict["default_list"]

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0] == "string1"
    assert result[1] == "string2"


def test_object_property_type():
    """Test object property type parsing."""
    xml = Element("element")
    props = Element("properties")

    obj_prop = Element(
        "property", attrib={"name": "test_object", "type": "object", "value": "789"}
    )
    props.append(obj_prop)
    xml.append(props)

    props_dict = parse_properties(xml)
    result = props_dict["test_object"]

    assert isinstance(result, int)
    assert result == 789
