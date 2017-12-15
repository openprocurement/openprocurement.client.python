from setuptools import find_packages, setup

version = '2.1.1+sale'

extras_require = {
    'test': [
        'bottle',
        'mock',
        'nose'
    ]
}
setup(
    name='openprocurement_client',
    version=version,
    description="",
    long_description="{0}\n".format(
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
        'python-magic',
        'bottle',
        'mock',
        'nose'
        # -*- Extra requirements: -*-
    ],
    extras_require=extras_require,
    entry_points="""
    # -*- Entry points: -*-
    """,
    test_suite="openprocurement_client.tests.main:suite"
)
