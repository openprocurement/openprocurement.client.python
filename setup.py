from setuptools import find_packages, setup
import os

version = '2.0b4'

tests_require = {
    'test': 'bottle'
}
setup(
    name='openprocurement_client',
    version=version,
    description="",
    long_description="{0}".format(
        open("README.rst").read()
    ),

    # Get more strings from
    # http://pypi.python.org/pypi?:action=list_classifiers
    classifiers=[
        "Programming Language :: Python",
    ],
    keywords='',

    author='',
    author_email='',
    url='https://github.com/openprocurement/openprocurement.client.python',
    license='Apache Software License 2.0',

    packages=find_packages(exclude=['ez_setup']),
    include_package_data=True,
    zip_safe=False,

    install_requires=[
        'gevent',
        'iso8601',
        'munch',
        'retrying',
        'simplejson',
        'requests',
        'python-magic'
        # -*- Extra requirements: -*-
    ],
    tests_require=tests_require,
    extras_require = tests_require,
    entry_points="""
    # -*- Entry points: -*-
    """,
    test_suite="openprocurement_client.tests"
)
