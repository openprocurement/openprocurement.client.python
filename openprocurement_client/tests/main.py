import unittest

from openprocurement_client.tests import tests, tests_sync, tests_api_base_client


def suite():
    suite = unittest.TestSuite()
    suite.addTest(tests.suite())
    suite.addTest(tests_sync.suite())
    suite.addTest(tests_api_base_client.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
