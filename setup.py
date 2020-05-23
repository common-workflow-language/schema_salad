#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import setuptools.command.egg_info as egg_info_cmd
from setuptools import setup

SETUP_DIR = os.path.dirname(__file__)
README = os.path.join(SETUP_DIR, "README.rst")

try:
    import gittaggers

    tagger = gittaggers.EggInfoFromGit
except ImportError:
    tagger = egg_info_cmd.egg_info

needs_pytest = {"pytest", "test", "ptr"}.intersection(sys.argv)
pytest_runner = ["pytest < 5", "pytest-runner"] if needs_pytest else []

if os.path.exists("requirements.txt"):
    requirements = [
        r for r in open("requirements.txt").read().split("\n") if ";" not in r
    ]
else:
    # In tox, it will cover them anyway.
    requirements = []

USE_MYPYC = False
# To compile with mypyc, a mypyc checkout must be present on the PYTHONPATH
if len(sys.argv) > 1 and sys.argv[1] == "--use-mypyc":
    sys.argv.pop(1)
    USE_MYPYC = True
if os.getenv("SCHEMA_SALAD_USE_MYPYC", None) == "1":
    USE_MYPYC = True

if USE_MYPYC:
    mypyc_targets = [
        # "schema_salad/codegen_base.py",  # interpreted classes cannot inherit from compiled
        # "schema_salad/codegen.py",
        "schema_salad/exceptions.py",
        "schema_salad/__init__.py",
        # "schema_salad/java_codegen.py",  # due to use of __name__
        "schema_salad/jsonld_context.py",
        "schema_salad/__main__.py",
        "schema_salad/main.py",
        "schema_salad/makedoc.py",
        # "schema_salad/python_codegen.py",  # due to use of __name__
        "schema_salad/ref_resolver.py",
        "schema_salad/schema.py",
        "schema_salad/sourceline.py",
        "schema_salad/utils.py",
        "schema_salad/validate.py",
        "schema_salad/avro/__init__.py",
        "schema_salad/avro/schema.py",
        "schema_salad/tests/other_fetchers.py",
        # "schema_salad/tests/util.py",
        # "schema_salad/tests/test_print_oneline.py",
        # "schema_salad/tests/test_python_codegen.py",
        # "schema_salad/tests/test_java_codegen.py",
        # "schema_salad/tests/__init__.py",
        # "schema_salad/tests/test_cli_args.py",
        # "schema_salad/tests/test_fetch.py",
        # "schema_salad/tests/matcher.py",
        # "schema_salad/tests/test_cg.py",
        # "schema_salad/tests/test_examples.py",
        # "schema_salad/tests/test_errors.py",
        # "schema_salad/tests/test_real_cwl.py",
        # "schema_salad/tests/test_ref_resolver.py",
        # "schema_salad/tests/test_fp.py",
    ]

    from mypyc.build import mypycify

    opt_level = os.getenv("MYPYC_OPT_LEVEL", "3")
    ext_modules = mypycify(mypyc_targets, opt_level=opt_level)
else:
    ext_modules = []

install_requires = [
    "setuptools",
    "requests >= 1.0",
    "ruamel.yaml >= 0.12.4, <= 0.16.5",
    # once the minimum version for ruamel.yaml >= 0.15.99
    # then please update the mypy targets in the Makefile
    "rdflib >= 4.2.2, < 4.3.0",
    "rdflib-jsonld >= 0.3.0, < 0.6.0",
    "mistune >= 0.8.1, < 0.9",
    "CacheControl >= 0.11.7, < 0.12",
    "lockfile >= 0.9",
    "typing-extensions",
]

extras_require = {
    ':python_version<"3.5"': ["typing >= 3.7.4"],
    "docs": ["sphinx >= 2.2", "sphinx-rtd-theme", "pytest"],
}

setup(
    name="schema-salad",
    version="6.0",  # update the VERSION prefix in the Makefile as well 🙂
    description="Schema Annotations for Linked Avro Data (SALAD)",
    long_description=open(README).read(),
    long_description_content_type="text/x-rst",
    author="Common workflow language working group",
    author_email="common-workflow-language@googlegroups.com",
    url="https://github.com/common-workflow-language/schema_salad",
    download_url="https://github.com/common-workflow-language/schema_salad/releases",
    ext_modules=ext_modules,
    license="Apache 2.0",
    python_requires=">=3.5",
    setup_requires=[] + pytest_runner,
    packages=["schema_salad", "schema_salad.tests"],
    package_data={"schema_salad": ["metaschema/*", "py.typed"]},
    include_package_data=True,
    install_requires=install_requires,
    extras_require=extras_require,
    test_suite="tests",
    tests_require=["pytest<5"],
    entry_points={
        "console_scripts": [
            "schema-salad-tool=schema_salad.main:main",
            "schema-salad-doc=schema_salad.makedoc:main",
        ]
    },
    zip_safe=True,
    cmdclass={"egg_info": tagger},
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Typing :: Typed",
    ],
)
