How to get IOTA² ?
==================

Licence
-------

:abbr:`IOTA² (Infrastructure pour l'Occupation des sols par Traitement Automatique Incorporant les Orfeo Toolbox Applications)`
is a free software under the GNU Affero General Public License v3.0. See `here <http://www.gnu.org/licenses/agpl.html>`_ 
for details.

How to install IOTA² ?
----------------------

IOTA² is only available on some Linux distributions : Ubuntu and CentOS.
In this section, steps to install IOTA² from scratch will be detailed.

Assuming installation will be done in the directory : ``MyInstall``

**Step 1 :** download IOTA²

.. code-block:: console

    cd MyInstall
    git clone -b develop https://framagit.org/inglada/iota2.git

Now you have the directory ``iota2`` in ``MyInstall`` which contains all IOTA² scripts.

**Step 2 :** get IOTA² light dependencies

if you are using Ubuntu :

.. code-block:: console

     sudo ./MyInstall/iota2/install/init_Ubuntu.sh
    
if you are using CentOS :

.. code-block:: console

     sudo ./MyInstall/iota2/install/init_CentOS.sh

**Step 3 :** get OTB

.. code-block:: console

     sudo ./MyInstall/iota2/install/generation.sh --all

Then OTB ant its dependencies will be downloaded (around 5Gb) and installed. If you only want to download or install OTB, you could use options ``--update`` or ``--compil`` instead of ``--all``.
This step could be long (several hours).

How to test installation
------------------------

IOTA² tests are implemented thanks to unittest which is a famous python's library dedicated to set-up test environment.
To check if most of IOTA² is well installed you should launch the commands below :

.. code-block:: console

    source /MyInstall/iota2/scripts/install/prepare_env.sh
    cd /MyInstall/iota2/scripts/Tests/UnitTests
    python -m unittest Iota2Tests

At the end, a short print resume if tests pass. If everything is ok you will get :

.. code-block:: console

    Ran 42 tests in 46.632s

    OK

In order to launch IOTA² to produce classifications you could follow one of these :doc:`examples. <IOTA2_Example>`

        
