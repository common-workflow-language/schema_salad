#!/usr/bin/env python3

import os
import sys

from setuptools import find_packages, setup

SETUP_DIR = os.path.dirname(__file__)
README = os.path.join(SETUP_DIR, "README.rst")

needs_pytest = {"pytest", "test", "ptr"}.intersection(sys.argv)
pytest_runner: list[str] = ["pytest < 10", "pytest-runner"] if needs_pytest else []

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
        "src/schema_salad/__init__.py",
        "src/schema_salad/__main__.py",
        "src/schema_salad/codegen_base.py",
        "src/schema_salad/codegen.py",
        "src/schema_salad/cpp_codegen.py",
        "src/schema_salad/dlang_codegen.py",
        "src/schema_salad/dotnet_codegen.py",
        # "src/schema_salad/exceptions.py", # leads to memory leaks
        # "src/schema_salad/fetcher.py",  # to allow subclassing {Default,}Fetcher
        "src/schema_salad/java_codegen.py",
        "src/schema_salad/jsonld_context.py",
        "src/schema_salad/main.py",
        "src/schema_salad/makedoc.py",
        "src/schema_salad/python_codegen.py",
        "src/schema_salad/ref_resolver.py",
        "src/schema_salad/schema.py",
        "src/schema_salad/sourceline.py",
        "src/schema_salad/typescript_codegen.py",
        "src/schema_salad/utils.py",
        "src/schema_salad/validate.py",
        "src/schema_salad/avro/__init__.py",
        "src/schema_salad/avro/schema.py",
        # "src/schema_salad/tests/util.py",
        # "src/schema_salad/tests/test_print_oneline.py",
        # "src/schema_salad/tests/test_python_codegen.py",
        # "src/schema_salad/tests/test_java_codegen.py",
        # "src/schema_salad/tests/__init__.py",
        # "src/schema_salad/tests/test_cli_args.py",
        # "src/schema_salad/tests/test_fetch.py",
        # "src/schema_salad/tests/matcher.py",
        # "src/schema_salad/tests/test_cg.py",
        # "src/schema_salad/tests/test_examples.py",
        # "src/schema_salad/tests/test_errors.py",
        # "src/schema_salad/tests/test_real_cwl.py",
        # "src/schema_salad/tests/test_ref_resolver.py",
        # "src/schema_salad/tests/test_fp.py",
    ]

    from mypyc.build import mypycify

    opt_level = os.getenv("MYPYC_OPT_LEVEL", "3")
    ext_modules = mypycify(mypyc_targets, opt_level=opt_level, debug_level="0", verbose=True)
else:
    ext_modules = []

install_requires = [
    "requests >= 1.0",
    "ruamel.yaml >= 0.17.6, < 0.20",
    "rdflib >= 4.2.2, < 8.0.0",
    "mistune>=3,<3.3",
    "CacheControl[filecache] >= 0.13.1, < 0.15",
    "mypy_extensions",
    "rich-argparse",
]

extras_require = {
    "docs": [
        "sphinx >= 2.2",
        "sphinx-rtd-theme >= 1",
        "pytest < 10",
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
    python_requires=">=3.10,<3.15",
    use_scm_version=True,
    setup_requires=pytest_runner + ["setuptools_scm>=8.0.4,<11"],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
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
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Typing :: Typed",
    ],
)
