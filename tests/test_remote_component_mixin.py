import unittest
from webhunt.core import RemoteComponentMixin, get_uuid


class ComponentSyncMixinTest(unittest.TestCase):
    def setUp(self):
        self.rcm = RemoteComponentMixin()
        self.rcm.init_database("Test", "root", "12345678")

    def test_select_component_with(self):
        info = self.rcm.select_component_with("Nginx")
        if info:
            print("select 'Nginx'", info)
            self.assertEqual(info["c_name"], "Nginx")

    def test_insert_component(self):
        info = {
            "c_id": get_uuid(),
            "c_name": "Nginx",
            "c_first": "n",
            "c_type": "Cms",
            "matches": '{"text": "test"}',
        }
        self.rcm.insert_component(**info)

    def test_update_component_with(self):
        info = {
            "c_type": "others",
            "matches": '{"text": "test1"}'
        }
        self.rcm.update_component_with("Nginx", **info)

    def test_get_count(self):
        count = self.rcm.get_count()
        self.assertTrue(count >= 0)
        print('get_count', count)

    def test_select_components(self):
        for components in self.rcm.select_components():
            print(components)
            break

    def tearDown(self):
        self.rcm.cnx_close()


if __name__ == "__main__":
    unittest.main()
