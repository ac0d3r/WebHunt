import random
import threading
import time
import unittest

from webhunt import utils


class Demo:
    _test = "123"
    _task = []
    _result = []

    @utils.cached_property
    def test(self):
        return self._test*2

    @utils.synchronized_property
    def task(self):
        return self._task

    @utils.synchronized_property
    def result(self):
        return self._result


class UtilsTest(unittest.TestCase):
    def test_cached_property(self):
        d = Demo()
        self.assertEqual(d.test, "123123")
        self.assertEqual(d.__dict__["test"], "123123")

    def test_synchronized_property(self):
        d = Demo()
        self.assertEqual(d.task, [])
        self.assertEqual(d.result, [])

        def test1(pre):
            nonlocal d
            for i in range(5):
                time.sleep(random.random())
                d.task.append(pre+str(i))

        def test2(pre):
            nonlocal d
            for i in range(5):
                d.result.append(pre+str(i))

        t1 = threading.Thread(target=test1, args=("1",))
        t2 = threading.Thread(target=test1, args=("2",))
        t3 = threading.Thread(target=test2, args=("result",))
        t1.start()
        t2.start()
        t3.start()

        t1.join()
        t2.join()
        t3.join()
        print(d.task, d.result)

    def test_get_pinyin_first_letter(self):
        self.assertEqual("n", utils.get_pinyin_first_letter("你好"))
        self.assertEqual("a", utils.get_pinyin_first_letter("assert"))
        self.assertEqual("n", utils.get_pinyin_first_letter("Nginx"))


if __name__ == "__main__":
    unittest.main()
