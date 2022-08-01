import unittest
from rainbows.helpers import asyncify


class AsyncifyTest(unittest.IsolatedAsyncioTestCase):
    async def test_async_passthrough(self):
        async def test_func(name):
            return "my name " + name
        fn = asyncify(test_func)
        self.assertEqual(await fn("jeff"), "my name jeff")

    async def test_sync_passthrough(self):
        def test_func(name):
            return "my name " + name
        fn = asyncify(test_func)
        self.assertEqual(await fn("jeff"), "my name jeff")
