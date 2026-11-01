# Coding agents
For copyright and licensing reasons we can't accept any contributions made with
Claude or other LLM based coding agents. You can use whatever tools you want for
code exploration, but we can only accept human written code for the CWL project.

# Style guide
- Python 3.10+ compatible code
- PEP-484 type hints
- Prefer new style format strings https://pyformat.info/
- Use ``make format`` to format your code

It is suggested that you run `git config blame.ignoreRevsFile .git-blame-ignore-revs`
to filter out mass-formatting commits from `git blame`.

# Installing from source

- Clone the code repository locally: `git clone https://github.com/common-workflow-language/schema_salad.git`
- Switch to repository directory:`cd schema_salad`
- Create a virtual environment: `python3 -m venv env`
- To begin using the virtual environment, it needs to be activated: `source env/bin/activate`
- To check if you have the virtual environment set up: `which python` and it should point to python executable in your virtual env
- Install the project in editable mode along with the development dependencies: `make dev`
- After you've made the changes, you can the complete test suite via tox: ``tox``
	- If you want to run specific tests, say ``unit tests`` in Python 3.13, then: ``tox run -e py313-unit``.
	- Look at ``tox -l`` for all available tests and runtimes
- If tests are passing, you can create a PR on the GitHub repository.
- After you're done working you can deactivate the virtual environment: ``deactivate``
