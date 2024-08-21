#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Sierra documentation build configuration file, created by
# sphinx-quickstart on Sat Oct 12 17:39:54 2019.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
import builtins
import pathlib

builtins.__sphinx_build__ = True

sys.path.insert(0, str(pathlib.Path('..').resolve()))
sys.path.append(str(pathlib.Path('_ext').resolve()))

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
needs_sphinx = '4.4.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.doctest',
              'sphinx.ext.intersphinx',
              'sphinx.ext.todo',
              'sphinx.ext.coverage',
              'sphinx.ext.mathjax',
              'sphinx.ext.ifconfig',
              'sphinx.ext.viewcode',
              'sphinx.ext.graphviz',
              'sphinx_tabs.tabs',
              'sphinx.ext.inheritance_diagram',
              'sphinxarg.ext',
              'xref',
              'sphinx_last_updated_by_git',
              'sphinx_rtd_theme',
              'sphinx.ext.napoleon',
              'autoapi.sphinx',
              'sphinx.ext.autosummary']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
source_suffix = ['.rst', '.md']
# source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'SIERRA'
copyright = '2022, John Harwell'
author = 'John Harwell'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
ver_ns = {}
ver_path = pathlib.Path('..') / 'sierra' / 'version.py'
with open(ver_path) as ver_file:
    exec(ver_file.read(), ver_ns)

# The short X.Y version.
version = ver_ns['__version__']
# The full version, including alpha/beta/rc tags.
# release = '0.3.0.0'

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'flycheck']

if 'html' in sys.argv:
    builtins.__sphinx_build_html__ = True
    exclude_patterns.extend(['man'])
elif 'man' in sys.argv:
    builtins.__sphinx_build_man__ = True
    exclude_patterns.extend(['api',
                             'src/tutorials',
                             'src/api.rst',
                             'src/contributing.rst',
                             'src/quickstart.rst',
                             'src/faq.rst',
                             'src/usage/index.rst'])

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

autosummary_generate = True

nitpicky = True
math_number_all = True
math_eqref_format = 'Eq. {number}'

nitpick_ignore = [
    ('py:class', 'pandas.core.frame.DataFrame'),
    ('py:class', 'pandas.core.groupby.generic.DataFrameGroupBy'),
    ('py:class', 'argparse'),
    ('py:class', 'module'),
    ('py:class', 'implements.Interface'),
    ('py:class', 'xml.etree.ElementTree'),
    ('py:class', 'multiprocessing.context.BaseContext.JoinableQueue'),
    ('py:class', 'multiprocessing.context.BaseContext.Queue')
]
autoapi_options = {
    'special-members': False,
    'show-inheritance-diagram': True
}
autoapi_modules = {
    'sierra.core': {'output': 'api'},
    'sierra.plugins': {'output': 'api'}
}

autoapi_ignore = ['*flycheck*']
xref_links = {
    "Harwell2021a-metrics": ("Improved Swarm Engineering: Aligning Intuition and Analysis",
                             "https://arxiv.org/pdf/2012.04144.pdf"),
    "Harwell2022b-ode": ("Characterizing The Limits of Linear Modeling of Non-Linear Swarm Behaviors",
                         "https://arxiv.org/abs/2110.12307"),
    "Harwell2020a-demystify": ("Demystifying Emergent Intelligence and Its Effect on Performance in Large Swarms",
                               "https://ifaamas.org/Proceedings/aamas2020/pdfs/p474.pdf"),
    "Harwell2019a-metrics": ("Swarm Engineering Through Quantitative Measurement in a 10,000 Robot Swarm",
                             "https://www.ijcai.org/Proceedings/2019/0048.pdf"),
    "White2019-social": ("Socially Inspired Communication in Swarm Robotics",
                         "https://arxiv.org/abs/1906.01108"),
    "Chen2019-battery": ("Maximizing Energy Efficiency in Swarm Robotics",
                         "https://arxiv.org/abs/1906.01957"),
    "Hecker2015": ("Hecker2015",
                   "https://www.cs.unm.edu/~wjust/CS523/S2018/Readings/Hecker_Beyond_Pheromones_Swarm_Intelligence.pdf"),
    "Rosenfeld2006": ("Rosenfeld2006",
                      "http://users.umiacs.umd.edu/~sarit/data/articles/rosenfeldetalbook06.pdf"),
    "SIERRA_GITHUB": ("https://github.com/jharwell/sierra.git",
                      "https://github.com/jharwell/sierra.git"),
    "SIERRA_ROSBRIDGE": ("https://github.com/jharwell/sierra_rosbridge.git",
                         "https://github.com/jharwell/sierra_rosbridge.git"),
    "SIERRA_SAMPLE_PROJECT": ("https://github.com/jharwell/sierra-sample-project.git",
                              "https://github.com/jharwell/sierra-sample-project.git"),
    "SIERRA_DOCS": ("https://sierra.readthedocs.io/en/master",
                    "https://sierra.readthedocs.io/en/master"),
    "FORDYCA": ("FORDYCA", "https://swarm-robotics-fordyca.readthedocs.io"),
    "PRISM": ("PRISM", "https://swarm-robotics-prism.readthedocs.io"),
    "2022-aamas-demo": ("2022 AAMAS Demo",
                        "https://www-users.cse.umn.edu/~harwe006/showcase/aamas-2022-demo")

}

sphinx_tabs_disable_tab_closing = True
# sphinx_tabs_disable_css_loading = True # True=tabs render more as buttons -_-

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    'globaltoc_maxdepth': 2,
    'collapse_navigation': False
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

html_last_updated_fmt = "%b %d, %Y"

# Custom sidebar templates, must be a dictionary that maps document names
# to template names.
#
# This is required for the alabaster theme
# refs: http://alabaster.readthedocs.io/en/latest/installation.html#sidebars
html_sidebars = {
    '**': [
        'relations.html',  # needs 'show_related': True theme option to display
        'searchbox.html',
    ]
}

# html_context = {
#     'css_files': [
#         '_static/theme_overrides.css',  # override wide tables in RTD theme
#     ],
# }

# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'Sierradoc'


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
    'maxlistdepth': '50'
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'SIERRA.tex', 'Sierra Documentation',
     'John Harwell', 'manual'),
]


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
autosectionlabel_prefix_document = True
man_pages = [
    ('man/sierra-cli', 'sierra-cli',
     'The SIERRA Command Line Interface (CLI).', [author], 1),
    ('man/sierra-usage', 'sierra-usage',
     'How to use SIERRA. This covers all non-command line interface aspects.',
     [author],
     7),
    ('man/sierra-platforms', 'sierra-platforms',
     'The platforms SIERRA supports, and platform-specific Batch Criteria.',
     [author],
     7),
    ('man/sierra-exec-envs', 'sierra-exec-envs',
     'The execution environments SIERRA supports.',
     [author],
     7),
    ('man/sierra-examples', 'sierra-examples',
     ('Examples of SIERRA usage. These examples all assume that you have '
      'successfully set up SIERRA with a project of your choice.'),
     [author],
     7),
    ('man/sierra-glossary', 'sierra-glossary',
     ('Glossary of SIERRA terminology.'),
     [author],
     7),
    ('man/sierra', 'sierra',
     'reSearch pIpEline for Reproducability, Reusability, and Automation.',
     [author],
     7)

]
man_show_urls = True
# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'Sierra', 'Sierra Documentation',
     author, 'Sierra', 'One line description of project.',
     'Miscellaneous'),
]


# Example configuration for intersphinx: refer to the Python standard library.
intersphinx_mapping = {
    'python3': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'scipy': ('https://docs.scipy.org/doc/scipy/reference', None),
    'matplotlib': ('https://matplotlib.org', None),
    'sphinx': ('https://www.sphinx-doc.org/en/stable/', None),
    'pandas': ('https://pandas.pydata.org/pandas-docs/dev', None),
    'implements': ('https://implements.readthedocs.io/en/latest/', None),
    'libra': ('https://jharwell.github.io/libra', None)
}

# This is the expected signature of the handler for this event, cf doc


def autodoc_skip_member_handler(app, what, name, obj, skip, options):
    # Basic approach; you might want a regex instead
    return 'flycheck' in name

# Automatically called by sphinx at startup


def setup(app):
    # Connect the autodoc-skip-member event from apidoc to the callback
    app.connect('autodoc-skip-member', autodoc_skip_member_handler)
