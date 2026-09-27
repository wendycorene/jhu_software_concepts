Building and publishing documentation
======================================

Local build
-----------

From ``module_4``::

   python -m sphinx -b html -W --keep-going docs docs/_build/html

Open ``docs/_build/html/index.html`` in a browser. ``-W`` makes documentation
warnings fail the build. The generated HTML is included under ``module_4``
for the assignment. Rebuild it after changing documentation or API signatures.

The API reference uses Sphinx autodoc to import the actual application modules:
https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html

Read the Docs
-------------

The repository-root ``.readthedocs.yaml`` specifies the Python environment,
requirements file, and ``module_4/docs/conf.py`` configuration path.

1. Commit and push the documentation and configuration.
2. Sign in to Read the Docs and connect the GitHub repository.
3. Import the project and start a build for the intended branch.
4. Open the published documentation after the build succeeds.
5. Add its actual public URL to ``module_4/README.md`` and submit that URL.

Publication is not complete until the hosted build and public URL have been
verified. The assignment asks for a public repository for this step; repository
visibility must be reviewed separately in GitHub settings.

Configuration reference:
https://docs.readthedocs.com/platform/stable/config-file/v2.html
