Development recommendations
###########################

GIT 
***

IOTA² is manage thanks to `GIT <https://git-scm.com>`_ which allow us the development 
monitoring.

GIT-Flow
========

GIT could be use in different way, in IOTA² ``git-flow`` has been chosen to maintain the project (**without release branches**).
You could find more about it `here <https://jeffkreeftmeijer.com/git-flow/>`_.

To roughly sum-up the development of a new feature, the developer **must** :

   1. from develop, create a feature ``branch``
   2. ``commit`` often
   3. ``merge`` new features comming from the develop branch into the feature branch
   4. when the feature is ready, propose it thanks to a ``pull request`` in the develop branch.

Branch naming conventions
=========================

+-----------------------+-------------------+------------------------------------------+
| branch purpose        | naming convention | Example                                  |
+=======================+===================+==========================================+
| develop a new feature | feature-*         | feature-Classsifications_fusion          |
+-----------------------+-------------------+------------------------------------------+
| respond to an issue   | issue-*           | issue-#53_Improve_Classifications        |
+-----------------------+-------------------+------------------------------------------+
| solve a fix           | fix-*             | fix-#27_Bug                              |
+-----------------------+-------------------+------------------------------------------+

the ``#27`` in *fix-#27_Bug* could refer to an issue reported on `IOTA² GIT repository <https://framagit.org/inglada/iota2/issues>`_.

FRAMAGIT
********

IOTA² is hosted on a `FramaGit <https://framagit.org/inglada/iota2>`_ server.
Everybody could create an account for **free** to submit a pull request. To monitor the project, 
`issues <https://framagit.org/inglada/iota2/issues>`_ are mainly used. Developments often start by a 
reported issue describing a bug, a new interesting feature or an investigation idea.

Issues
======

If a developer want to contribute to IOTA² :

   1. If an issue does not exists about the new feature, create a dedicated one.
   2. Attribute to himself the issue.
   3. When the contribution is done, close the issue.

Theses simple rules will avoid duplicate work between developers.

.. Note::
    The Board view is very useful to see which features are in development, need to be done, or are in backlog.

.. figure:: ./Images/board_view.jpg
    :scale: 50 %
    :align: center
    :alt: Boad view
    
    Boad view


TESTS
*****

Unittest
========

IOTA² is mainly developed in python, and we chose the `Unittest <https://docs.python.org/2.7/library/unittest.html>`_ library
to implement our unit test framework. It is ``highly recommended`` to add tests to each new features.
Currently, unit tests are placed in the ``/iota2/scripts/Tests/UnitTests`` directory.

Baseline
========

A set of baseline are already present at ``/iota2/data/references``, please use them as references to your tests.
If new baseline must be created, add it in the directory  previously quoted.

.. Warning::
    Baselines must be as small as possible.
