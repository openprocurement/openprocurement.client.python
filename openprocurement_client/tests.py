from collections import Iterable
from openprocurement_client import client
import unittest

API_KEY = 'e9c3ccb8e8124f26941d5f9639a4ebc3'


class ViewerTestCase(unittest.TestCase):
    """"""
    def setUp(self):
        self.client = client.Client('')

    def test_get_tenders(self):
        self.assertTrue(isinstance(self.client.get_tenders(), Iterable))


class UserTestCase(unittest.TestCase):
    def setUp(self):
        self.client = client.Client(API_KEY)

if __name__ == '__main__':
    unittest.main()
