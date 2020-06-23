import os
import unittest
from typing import Generator

from webhunt.core import Component, ComponentGeneratorMixin, ComponentType


class ComponentTest(unittest.TestCase):
    def test_cls_make(self):
        component = Component.make(
            os.path.join(os.getcwd(), "components/plugins/cms/1Caitong.json"))
        self.assertIsNotNone(component)
        print("Component.make:", component)


class ComponentTypeTest(unittest.TestCase):
    def test_get_memeber_name(self):
        self.assertEqual(ComponentType.cms.name, "cms")
        self.assertEqual(ComponentType.others.name, "others")

    def test_all_components(self):
        all_components = ComponentType.all_kinds()
        print("All component type:", all_components)
        self.assertTrue(isinstance(all_components, list))
        self.assertIn("others", all_components)


class ComponentGeneratorMixinTest(unittest.TestCase):
    def test_iter_components(self):
        c = ComponentGeneratorMixin()
        c.directory = os.path.join(
            os.getcwd(), "components")
        components = c.iter_components()
        self.assertIsInstance(components, Generator)
        for component in components:
            self.assertIsInstance(component, Component)
            print(component)
            break


if __name__ == "__main__":
    unittest.main()
