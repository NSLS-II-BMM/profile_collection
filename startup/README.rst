This is the IPython startup directory

``.py`` and ``.ipy`` files in this directory will be run *prior* to any code or files specified
via the exec_lines or exec_files configurables whenever you load this profile.

Files will be run in lexicographical order, so you can control the execution order of files
with a prefix, e.g.::

    00-first.py
    50-middle.py
    99-last.ipy

That said, there is only one such file in use at BMM,
``00-populate-namespace.py``.  This file has one line:

.. sourcecode:: python

		from BMM.user_ns import *


All subsequent python code is imported in the order specified in
``BMM/user_ns/__init__.py``.

Folders
=======

``BMM/``
  All of BMM's bsui code

``ML/``
  Files and data related to BMM's machine learning routines

``dossier/``
  Files used to create BMM dossiers

``telemetry/``
  Files and data related to BMM's telemetry routines

``tmpl/``
  Template files used to generate dossier and other content

``xlsx/``
  Automation spreadsheet templates in .xlsx format


Files
=====

#. ``.yaml`` files are used to configure the bluesky queueserver

#. ``rois.json``: ROI configuration for the Xspress3



