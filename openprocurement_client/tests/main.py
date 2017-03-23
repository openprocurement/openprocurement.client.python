import unittest

from openprocurement_client.tests import tests, tests_sync


def suite():
    suite = unittest.TestSuite()
    suite.addTest(tests.suite())
    suite.addTest(tests_sync.suite())
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
