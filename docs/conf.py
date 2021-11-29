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
import subprocess
import os
import sys
sys.path.insert(0, os.path.abspath('..'))
sys.path.append(os.path.abspath('_ext'))

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

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
              'sphinx.ext.inheritance_diagram',
              'sphinxarg.ext',
              'xref',
              'sphinx_rtd_theme',
              'sphinxcontrib.napoleon',
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
copyright = '2021, John Harwell'
author = 'John Harwell'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
# version = '0.3.0.0'
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
    exclude_patterns.extend(['man'])
elif 'man' in sys.argv:
    exclude_patterns.extend(['api',
                             'src/projects'
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
    ('py:class', 'argparse'),
    ('py:class', 'implements.Interface'),
    ('py:class', 'xml.etree.ElementTree'),
    ('py:class', 'multiprocessing.context.BaseContext.Queue')
]
autoapi_modules = {
    'sierra.core.cmdline': {'output': 'api/core'},
    'sierra.core.generators': {'output': 'api/core/generators'},
    'sierra.core.pipeline': {'output': 'api/core/pipeline'},
    'sierra.core.variables': {'output': 'api/core/variables'},
    'sierra.core.graphs': {'output': 'api/core/graphs'},
    'sierra.core.xml': {'output': 'api/core'},
    'sierra.core.utils': {'output': 'api/core'},
    'sierra.core.experiment_spec': {'output': 'api/core'},
    'sierra.core.vector': {'output': 'api/core'},
    'sierra.core.models.interface': {'output': 'api/core/models'},
    'sierra.core.models.graphs': {'output': 'api/core/models'},
    'sierra.plugins.hpc': {'output': 'api/plugins/hpc'},
    'sierra.plugins.storage': {'output': 'api/plugins/storage'},
    'sierra.plugins.platform.argos': {'output': 'api/plugins/platform/argos'}
}

autoapi_ignore = ['*flycheck*']
xref_links = {
    "Harwell2021a": ("Improved Swarm Engineering: Aligning Intuition and Analysis",
                     "https://arxiv.org/pdf/2012.04144.pdf"),
    "Harwell2021b": ("Characterizing The Limits of Linear Modeling of Non-Linear Swarm Behaviors",
                     "https://arxiv.org/abs/2110.12307"),
    "Harwell2020": ("Demystifying Emergent Intelligence and Its Effect on Performance in Large Swarms",
                    "http://ifaamas.org/Proceedings/aamas2020/pdfs/p474.pdf"),
    "Harwell2019": ("Swarm Engineering Through Quantitative Measurement in a 10,000 Robot Swarm",
                    "https://www.ijcai.org/Proceedings/2019/0048.pdf"),
    "White2019": ("Socially Inspired Communication in Swarm Robotics",
                  "https://arxiv.org/abs/1906.01108"),
    "Chen2019": ("Maximizing Energy Efficiency in Swarm Robotics",
                 "https://arxiv.org/abs/1906.01957"),
    "Hecker2015": ("Hecker2015",
                   "https://www.cs.unm.edu/~wjust/CS523/S2018/Readings/Hecker_Beyond_Pheromones_Swarm_Intelligence.pdf"),
    "Rosenfeld2006": ("Rosenfeld2006",
                      "http://users.umiacs.umd.edu/~sarit/data/articles/rosenfeldetalbook06.pdf"),
    "SIERRA_GITHUB": ("https://github.com:swarm-robotics/sierra.git", "https://github.com:swarm-robotics/sierra.git"),
    "FORDYCA": ("FORDYCA", "https://swarm-robotics-fordyca.readthedocs.io"),
    "PRISM": ("PRISM", "https://swarm-robotics-prism.readthedocs.io"),
    "LIBRA": ("LIBRA", "https://swarm-robotics-libra.readthedocs.io"),
    "2021-ijcai-demo": ("2021 IJCAI Robot Exhibition",
                        "https://www-users.cse.umn.edu/~harwe006/showcase/ijcai-2021-robot-exhibition"),
}

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

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

html_context = {
    'css_files': [
        '_static/theme_overrides.css',  # override wide tables in RTD theme
    ],
}

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
    (master_doc, 'Sierra.tex', 'Sierra Documentation',
     'John Harwell', 'manual'),
]


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
autosectionlabel_prefix_document = True
man_pages = [
    ('man/sierra-cli', 'sierra-cli',
     'The SIERRA Command Line Interface', [author], 1),
    ('man/sierra-rendering', 'sierra-rendering',
     'SIERRA Rendering', [author], 7),
    ('man/sierra', 'sierra',
     'reSearch pIpEline Reusable Robotics Automation (SIERRA)', [author], 7)
]

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
intersphinx_mapping = {'python3': ('https://docs.python.org/3', None),
                       'numpy': ('https://numpy.org/doc/stable/', None),
                       'scipy': ('https://docs.scipy.org/doc/scipy/reference', None),
                       'matplotlib': ('https://matplotlib.org', None),
                       'sphinx': ('https://www.sphinx-doc.org/en/stable/', None),
                       'pandas': ('https://pandas.pydata.org/docs/', None),
                       'implements': ('https://implements.readthedocs.io/en/latest/', None)
                       }

# This is the expected signature of the handler for this event, cf doc


def autodoc_skip_member_handler(app, what, name, obj, skip, options):
    # Basic approach; you might want a regex instead
    return 'flycheck' in name

# Automatically called by sphinx at startup


def setup(app):
    # Connect the autodoc-skip-member event from apidoc to the callback
    app.connect('autodoc-skip-member', autodoc_skip_member_handler)
