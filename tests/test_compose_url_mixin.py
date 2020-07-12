import unittest

from src.core import ComposeURLMixin


class ComposeURLMixinTest(unittest.TestCase):
    def setUp(self):
        self.c = ComposeURLMixin()
        self.c.target = "https://github.com/torvalds/linux"

    def test_compose_url(self):
        self.assertEqual(self.c.compose_url("/test"),
                         "https://github.com/test")
        self.assertEqual(self.c.compose_url("test"),
                         "https://github.com/torvalds/test")


if __name__ == "__main__":
    unittest.main()
