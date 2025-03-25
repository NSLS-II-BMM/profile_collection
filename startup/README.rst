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
`BMM/user_ns/__init__.py <BMM/user_ns/__init__.py>`_.


Beamline configuration
======================

The file `BMM_configuration.ini <BMM_configuration.ini>`__ contains
configuration parameters for the beamnline, including

+ flags controlling to specific detectors, instruments, optical
  cameras, and experiment types
+ network addresses of services (Kafka, Redis, Tiled, qs, NSLS2 API,
  etc)
+ Slack channel configuration

and more...

The files `BMM/user_ns/base.py <BMM/user_ns/base.py>`_ and
`consumer/tools.py <consumer/tools.py>`_ import the configparser
module and export ``profile_configuration`` for use throughout the
bsui/qs profile and the Kafka consumers.

Anytime you see a reference to ``profile_configuration`` in the code,
look to `BMM_configuration.ini <BMM_configuration.ini>`__ for the
corresponding parameter.


Folders
=======

``BMM/``
  All of BMM's bsui code

``consumer/``
  The code for the Kafka-based file manager and plot manager

``ML/``
  Files and data related to BMM's machine learning routines

``dossier/``
  Files used to create BMM dossiers

``telemetry/``
  Files and data related to BMM's telemetry routines

``tmpl/``
  Template files used to generate dossier and other static text content

``xlsx/``
  Automation spreadsheet templates in .xlsx format


Files
=====

#. ``*.yaml`` files are used to configure the bluesky queueserver

#. ``rois.json``: ROI configuration for the Xspress3

#. ``BMM_configuration.ini``: configure detectors, electrometers, cameras, experiments

