import unittest
from unittest.mock import patch
from xml.etree.ElementTree import Element

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


class TestTiledElement(unittest.TestCase):

    def setUp(self):
        self.element = DummyElement()

    def test_initial_state(self):
        self.assertFalse(self.element._allow_duplicate_names)
        self.assertEqual(self.element.properties, {})

    def test_cast_and_set_attributes(self):
        items = [("width", "32"), ("height", "64"), ("visible", "1")]
        self.element._cast_and_set_attributes_from_node_items(items)
        self.assertEqual(self.element.width, 32.0)
        self.assertEqual(self.element.height, 64.0)
        self.assertTrue(self.element.visible)

    def test_invalid_property_name_detection(self):
        self.element.name = "TestElement"
        items = [("name", "conflict")]
        self.assertTrue(self.element._contains_invalid_property_name(items))

    def test_valid_property_name_with_duplicates_allowed(self):
        self.element.allow_duplicate_names = True
        items = [("name", "conflict")]
        self.assertFalse(self.element._contains_invalid_property_name(items))

    def test_set_properties_with_valid_data(self):
        xml = Element("element", attrib={"width": "128", "height": "256"})
        props = Element("properties")
        prop = Element("property", attrib={"name": "custom", "value": "hello"})
        props.append(prop)
        xml.append(props)

        self.element._set_properties(xml)
        self.assertEqual(self.element.width, 128.0)
        self.assertEqual(self.element.height, 256.0)
        self.assertEqual(self.element.properties["custom"], "hello")

    def test_set_properties_with_conflict_raises(self):
        xml = Element("element", attrib={"name": "conflict"})
        props = Element("properties")
        prop = Element("property", attrib={"name": "name", "value": "oops"})
        props.append(prop)
        xml.append(props)

        with self.assertRaises(ValueError):
            self.element._set_properties(xml)

    def test_getattr_existing_property(self):
        self.element.properties["foo"] = "bar"
        self.assertEqual(self.element.foo, "bar")

    def test_getattr_missing_property_with_name(self):
        self.element.properties["name"] = "TestElement"
        with self.assertRaises(AttributeError) as cm:
            _ = self.element.missing
        self.assertIn("TestElement", str(cm.exception))

    def test_getattr_missing_property_without_name(self):
        with self.assertRaises(AttributeError) as cm:
            _ = self.element.missing
        self.assertIn("Element has no property", str(cm.exception))

    def test_repr_with_id(self):
        self.element.id = 42
        self.element.name = "MyElement"
        self.assertEqual(repr(self.element), '<DummyElement[42]: "MyElement">')

    def test_repr_without_id(self):
        self.element.name = "MyElement"
        self.assertEqual(repr(self.element), '<DummyElement: "MyElement">')

    def test_from_xml_string(self):
        xml = """
        <element width="100" height="200">
            <properties>
                <property name="custom" value="value" />
            </properties>
        </element>
        """
        obj = DummyElement.from_xml_string(xml)
        self.assertEqual(obj.width, 100.0)
        self.assertEqual(obj.height, 200.0)
        self.assertEqual(obj.properties["custom"], "value")

    def test_property_type_casting(self):
        xml = Element("element")
        props = Element("properties")
        prop = Element(
            "property", attrib={"name": "visible", "type": "bool", "value": "true"}
        )
        props.append(prop)
        xml.append(props)

        props_dict = parse_properties(xml)
        self.assertTrue(props_dict["visible"])

    @patch("pytmx.properties.deepcopy", lambda x: x)
    def test_nested_class_property(self):
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
        self.assertEqual(props_dict["nested"].foo, "bar")

    def test_property_fallback_to_text(self):
        xml = Element("element")
        props = Element("properties")
        prop = Element("property", attrib={"name": "fallback"})
        prop.text = "fallback_value"
        props.append(prop)
        xml.append(props)

        props_dict = parse_properties(xml)
        self.assertEqual(props_dict["fallback"], "fallback_value")

    def test_property_type_not_found_logs_info(self):
        xml = Element("element")
        props = Element("properties")
        prop = Element(
            "property", attrib={"name": "unknown", "type": "mystery", "value": "42"}
        )
        props.append(prop)
        xml.append(props)

        props_dict = parse_properties(xml)
        self.assertEqual(props_dict["unknown"], "42")

    def test_parse_xml_sets_properties(self):
        xml = Element("element", attrib={"width": "100", "height": "200"})
        props = Element("properties")
        prop = Element("property", attrib={"name": "custom", "value": "hello"})
        props.append(prop)
        xml.append(props)

        result = self.element.parse_xml(xml)
        self.assertEqual(result.width, 100.0)
        self.assertEqual(result.height, 200.0)
        self.assertEqual(result.properties["custom"], "hello")

    def test_repr_output(self):
        self.element.id = 1
        self.element.name = "TestDummy"
        self.assertEqual(repr(self.element), '<DummyElement[1]: "TestDummy">')

    def test_property_access(self):
        self.element.properties["foo"] = "bar"
        self.assertEqual(self.element.foo, "bar")

    def test_missing_property_raises(self):
        with self.assertRaises(AttributeError):
            _ = self.element.nonexistent

    def test_contains_invalid_property_name(self):
        self.element.name = "dummy"
        items = [("name", "conflict")]
        self.assertTrue(self.element._contains_invalid_property_name(items))
