import unittest

from src import echo


class EchoTest(unittest.TestCase):
    def test_echo(self):
        echo.succ("succ", "succ", "succ")
        echo.fail("fail", "fail", "fail")
        echo.warn("warn", "warn", "warn")
        echo.info("info", "info", "info")
        echo.blod("blod", "blod", "blod")
        echo.tips("tips", "tips", "tips")


if __name__ == "__main__":
    unittest.main()
