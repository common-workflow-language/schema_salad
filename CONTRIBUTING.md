Style guide:
- Python 3.6+ compatible code
- PEP-484 type hints
- Prefer new style format strings https://pyformat.info/
- Use ``make format`` to format your code

In order to contribute to the development of ``schema-salad``, you need to install it from source (preferably in a virtual environment):
Here's a rough guide (improvements are welcome!)
- Install virtualenv via pip: ``pip install virtualenv``
- Clone the code repository locally: ``git clone https://github.com/common-workflow-language/schema_salad.git``
- Switch to schema_salad directory: ``cd schema_salad``
- Create a virtual Python environment: ``virtualenv env``
- To begin using the Python virtual environment, it needs to be activated: ``source env/bin/activate``
- To check if you have the Python virtual environment set up: ``which python`` and it should point to python executable in your virtual env
- Install schema-salad in the Python virtual environment: ``pip install .``
- Check the version which might be different from the version installed in general on any system: ``schema-salad-tool --version``
- After you've made the changes, you can the complete test suite via tox: ``tox``
	- If you want to run specific tests, say ``unit tests`` in Python 3.5, then: ``tox -e py35-unit``.
	- Look at ``tox.ini`` for all available tests and runtimes
- If tests are passing, you can simply commit and create a PR on ``schema_salad`` repo:
- After you're done working, you can deactivate the virtual environment: ``deactivate``
