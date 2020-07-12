import unittest
from typing import Dict

from src.core import RequestManagerMixin, fake_user_agent, plain2md5


class RequestManagerMixinTest(unittest.TestCase):
    def setUp(self):
        self.reqm = RequestManagerMixin()
        self.reqm.headers = {
            "user-agent": fake_user_agent()
        }
        self.reqm.allow_redirect = True
        self.reqm.timeout = 30

    def test_request(self):
        resp = self.reqm.request("https://www.baidu.com")
        self.assertIsInstance(resp, Dict)
        self.assertEqual(resp["url"], "https://www.baidu.com")
        self.assertIsInstance(resp["script"], list)
        self.assertIsInstance(resp["meta"], Dict)
        self.assertIsInstance(resp["raw_cookies"], str)
        self.assertIsInstance(resp["raw_headers"], str)

    def test_history(self):
        self.reqm.request("https://www.baidu.com")
        resp = self.reqm.request_manager_history[plain2md5(
            "https://www.baidu.com")]
        self.assertIsInstance(resp, Dict)


if __name__ == "__main__":
    unittest.main()
