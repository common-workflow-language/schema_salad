#!/usr/bin/env python3

import os
import sys
from typing import List

from setuptools import setup

SETUP_DIR = os.path.dirname(__file__)
README = os.path.join(SETUP_DIR, "README.rst")

needs_pytest = {"pytest", "test", "ptr"}.intersection(sys.argv)
pytest_runner: List[str] = ["pytest < 9", "pytest-runner"] if needs_pytest else []

USE_MYPYC = False
# To compile with mypyc, a mypyc checkout must be present on the PYTHONPATH
if len(sys.argv) > 1 and sys.argv[1] == "--use-mypyc":
    sys.argv.pop(1)
    USE_MYPYC = True
if os.getenv("SCHEMA_SALAD_USE_MYPYC", None) == "1":
    USE_MYPYC = True

if USE_MYPYC and any(
    item in sys.argv
    for item in [
        "build",
        "bdist_wheel",
        "build_ext",
        "install",
        "install-lib",
        "bdist",
        "bdist_dumb",
        "bdist_rpm",
        "develop",
        "bdist_egg",
        "editable_wheel",
        "test",
    ]
):
    mypyc_targets = [
        "schema_salad/__init__.py",
        "schema_salad/__main__.py",
        "schema_salad/codegen.py",
        "schema_salad/codegen_base.py",
        "schema_salad/cpp_codegen.py",
        "schema_salad/dlang_codegen.py",
        "schema_salad/dotnet_codegen.py",
        # "schema_salad/exceptions.py", # leads to memory leaks
        "schema_salad/java_codegen.py",
        "schema_salad/jsonld_context.py",
        "schema_salad/main.py",
        "schema_salad/makedoc.py",
        "schema_salad/python_codegen.py",
        "schema_salad/ref_resolver.py",
        # "schema_salad/fetcher.py",  # to allow subclassing {Default,}Fetcher
        "schema_salad/schema.py",
        "schema_salad/sourceline.py",
        "schema_salad/typescript_codegen.py",
        "schema_salad/utils.py",
        "schema_salad/validate.py",
        "schema_salad/avro/__init__.py",
        "schema_salad/avro/schema.py",
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
    ext_modules = mypycify(mypyc_targets, opt_level=opt_level, debug_level="0", verbose=True)
else:
    ext_modules = []

install_requires = [
    "requests >= 1.0",
    "ruamel.yaml >= 0.17.6, < 0.19",
    "rdflib >= 4.2.2, < 8.0.0",
    "mistune>=3,<3.1",
    "CacheControl[filecache] >= 0.13.1, < 0.15",
    "mypy_extensions",
    "importlib_resources>=1.4;python_version<'3.9'",
]

extras_require = {
    "docs": [
        "sphinx >= 2.2",
        "sphinx-rtd-theme >= 1",
        "pytest < 9",
        "sphinx-autoapi",
        "sphinx-autodoc-typehints",
        "sphinxcontrib-autoprogram",
    ],
    "pycodegen": ["black"],
}

setup(
    name="schema-salad",
    description="Schema Annotations for Linked Avro Data (SALAD)",
    long_description=open(README).read(),
    long_description_content_type="text/x-rst",
    author="Common workflow language working group",
    author_email="common-workflow-language@googlegroups.com",
    url="https://schema-salad.readthedocs.io/",
    download_url="https://github.com/common-workflow-language/schema_salad/releases",
    ext_modules=ext_modules,
    license="Apache 2.0",
    python_requires=">=3.8,<3.14",
    use_scm_version=True,
    setup_requires=pytest_runner + ["setuptools_scm>=8.0.4,<9"],
    packages=["schema_salad", "schema_salad.tests", "schema_salad.avro"],
    package_data={
        "schema_salad": [
            "metaschema/*",
            "py.typed",
            "dotnet/*",
            "dotnet/*/*",
            "dotnet/*/*/*",
            "java/*",
            "java/*/*",
            "typescript/*",
            "typescript/*/*",
            "typescript/*/*/*",
            "typescript/.*",
        ],
        "schema_salad.tests": [
            "*.json",
            "*.yml",
            "cpp_tests/*",
            "docimp/*",
            "*.owl",
            "*.cwl",
            "*.txt",
            "foreign/*.cwl",
            "test_real_cwl/*",
            "test_real_cwl/*/*",
            "test_schema/*",
        ],
    },
    install_requires=install_requires,
    extras_require=extras_require,
    test_suite="tests",
    tests_require=["pytest<9"],
    entry_points={
        "console_scripts": [
            "schema-salad-tool=schema_salad.main:main",
            "schema-salad-doc=schema_salad.makedoc:main",
        ]
    },
    zip_safe=True,
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: POSIX",
        "Operating System :: MacOS :: MacOS X",
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Typing :: Typed",
    ],
)
