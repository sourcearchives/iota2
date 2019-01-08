IOTA² use cases
###############

Assuming IOTA² is :doc:`fully operational <HowToGetIOTA2>` , this section will present some IOTA² use cases.
Users can re-produce the results presented here by using the downloadable `data-set <http://osr-cesbio.ups-tlse.fr/echangeswww/TheiaOSO/IOTA2_TEST_S2.tar.bz2>`_ .

First try with IOTA²? :ref:`first-contact`

You have two distinct regions to classify? :ref:`two-zones`


.. _first-contact:

IOTA² first contact
*******************

The purpose of this example is to provide to users a fully detailed step by step of how to run IOTA² on a simple data-set.
An area that covers a full Sentinel-2 tile will be classified using ground truth containing 13 different classes.

Get the data-set
================

Download the data-set `here <http://osr-cesbio.ups-tlse.fr/echangeswww/TheiaOSO/IOTA2_TEST_S2.tar.bz2>`_ (4Go).
This archive contains satellite imagery (two sentinel-2 dates) available on THEIA's `website <https://theia.cnes.fr/atdistrib/rocket/#/search?collection=SENTINEL2>`_ and other IOTA²'s inputs:

Archive contents:

.. code-block:: console

    ├── colorFile.txt
    ├── IOTA2_Example.cfg
    ├── IOTA2_Outputs
    │   └── Results
    │       └── #IOTA2's output (according to the configuration file)
    ├── nomenclature.txt
    ├── sensor_data
    │   ├── T31TCJ
    │   │   ├── SENTINEL2A_20180511-105804-037_L2A_T31TCJ_D_V1-7
    │   │   │   ├── MASKS
    │   │   │   │   └── *.tif
    │   │   │   └── *.tif
    │   │   └── SENTINEL2A_20180521-105702-711_L2A_T31TCJ_D_V1-7
    │   │       ├── MASKS
    │   │       │   └── *.tif
    │   │       └── *.tif
    │   └── T31TDJ
    │       └── #empty
    └── vector_data
        ├── EcoRegion.shp
        └── groundTruth.shp


``colorFile.txt`` : color table.

.. code-block:: console

    cat colorFile.txt
    ...
    10 255 85 0
    ...

Here the class **10** has the **RGB** color **255 85 0**.

``nomenclature.txt`` : label's name.

.. code-block:: console

    cat colorFile.txt
    ...
    prairie:211
    ...
    
.. Warning:: Each class must be represented in colorFile.txt and nomenclature.txt

``sensor_data`` : the directory which contains Sentinel-2 data. These data **must** be stored by tiles as in the archive.

``groundTruth.shp`` : the shapeFile containing geo-referenced and labelled polygons (no multi-polygons, no overlapping) used to train a classifier.

``EcoRegion.shp`` : shapeFile containing two geo-referenced polygons representing a spatial stratification (eco-climatic areas, for instance).

``IOTA2_Example.cfg`` : the file used to set IOTA²'s parameters such as inputs/outputs paths, classifier parameters etc.

Edit IOTA² configuration file
=============================

A configuration file is a simple text file containing sections and fields.

Example :

.. code-block:: python

    First_section:
    {
        First_section_field_1:"value"
        First_section_field_2:10
    }
    Second_section:
    {
        Second_section_field_1:"value"
        ...
        MyAwesome_field:10
    }


To be able to run the chain, you have to replace ``XXXX`` in ``IOTA2_Example.cfg`` by the path where you stored
the provided archive. Also replace the ``MyInstall`` by the path where IOTA² is installed.

.. Note:: ``IOTA2_Example.cfg`` is the minimal configuration file understandable by IOTA².

Run IOTA²
============

First, you have to set a list of environement variables to inform IOTA² "where OTB is".
The file ``prepare_env.sh`` will do it for you. Then use ``Iota2.py`` to launch the chain.

.. code-block:: console

    source /MyInstall/iota2/scripts/install/prepare_env.sh
    python /MyInstall/iota2/scripts/Iota2.py -config /absolutePath/to/IOTA2_Example.cfg

IOTA² is launched, it will print all processing steps needed to produce the maps and their validation:

.. code-block:: console

    Full processing include the following steps (checked steps will be run): 
    Group init:
         [x] Step 1: create directories
         [x] Step 2: generate common masks
         [x] Step 3: compute validity mask by tile
    Group sampling:
         [x] Step 4: generate envelopes
         [x] Step 5: generate region shapes
         [x] Step 6: Prepare samples
         [x] Step 7: merge samples by models
         [x] Step 8: generate samples statistics
         [x] Step 9: select samples
         [x] Step 10: generate samples
         [x] Step 11: merge samples
    Group dimred:
    Group learning:
         [x] Step 12: learning
    Group classification:
         [x] Step 13: generate classification commands
         [x] Step 14: generate classifications
    Group mosaic:
         [x] Step 15: classfication shaping
    Group validation:
         [x] Step 16: confusion matrix command generation
         [x] Step 17: generate confusion matrix
         [x] Step 18: confusion matrix fusion
         [x] Step 19: report generation

Afterwards, it will sequentially print the current step until the end of the processing is reached.

.. code-block:: console

    Running step 1: create directories (1 tasks)
    Running step 2: generate common masks (1 tasks)
    ...
    some prints
    ...
    Running step 3: compute validity mask by tile (1 tasks)
    ...

**Let's have a look at IOTA²'s outputs.**

You will find them in the directory specified in field ``outputPath`` into the configuration file.
IOTA² generates a lot of temporary data which helps users to analyse classification's results. 
For example, IOTA² keeps sample's label with associated features which feed the classification model. You can find these
data in the directory ``learningSamples``.

Final results are stored in the ``final`` directory. In it you can find ``Classif_Seed_0.tif`` as the final map.
Also, ``Classif_Seed_0_ColorIndexed.tif`` corresponds to the same image but colorized in order to be easily visualized.

A report is also available next to final classifications: ``RESULTS.txt``. It summarizes the classification quality.
It contains a verbose confusion matrix and metrics computed from it: Kappa coeffcient, OA (overall accuracy), Precision, Recall, F-score by class.

**Outputs rasters**

Your *Classif_Seed_0.tif* should look like this one:

.. figure:: ./Images/classif_Example.jpg
    :scale: 15 %
    :align: center
    :alt: classification map
    
    Classif_Seed_0.tif Example


This map contains labels from the shapeFile ``groundTruth.shp``. As you can see the classification's quality is rather low.
A possible explanation is the low number of dates used to produce it. A raster called ``PixelsValidity.tif`` gives the number of dates for which the pixel is clear (no cloud, cloud shadow, saturation)

.. figure:: ./Images/PixVal_Example.png
    :scale: 50 %
    :align: center
    :alt: validity map
    
    PixelsValidity.tif Example

As only two dates are used to produce the classification map, pixels are in the [0; 2] range. IOTA² also provides a confidence map: ``Confidence_Seed_0.tif`` which
allows to better understand the resulting classification. This map gives for each pixel a likelihood (from 0 to 100) of the result to be correct as estimated by the classifier itself. This is not a validation, just an estimate of the confidence in the decision of the classifier.

.. figure:: ./Images/confidence_example.jpg
    :scale: 63 %
    :align: center
    :alt: confidence map
    
    Confidence_Seed_0.tif Example

These three maps form IOTA²'s main outputs: they are the minimum outputs required to analyse and understand the results.

We analyzed and produced classifications thanks to IOTA². The main objective is to get the better land cover map as 
possible. There are many ways to achieve this purpose: researchers publish every day new methods.

The simplest method to get better results can consist in using a longer time series, improving the reference data for training, etc. 

Improve your classification
===========================

1. Download new dates from `THEIA <https://theia.cnes.fr/atdistrib/rocket/#/search?collection=SENTINEL2>`_.
These data are zipped. Unzip them next to the ones already present in the directory ``T31TCJ`` in ``sensor_data``.

.. Note:: To get less interpolated dates, you should pick-up dates near the ones already used : 2018-05-11 and 2018-05-21. **Every** date placed in ``sensor_data`` will be used.

2. Re-run IOTA²

.. code-block:: console

    source /MyInstall/iota2/scripts/install/prepare_env.sh
    python iota2/scripts/Iota2.py -config /absolutePath/to/IOTA2_Example.cfg

.. Warning::
    The previous run is stored in the directory ``Results``.
    In order **not to overwrite** this directory, **you must** change the field ``outputPath`` in ``IOTA2_Example.cfg``.
    Or create a new configuration file.

Expand your map
===============

IOTA² allows the use of many tiles to produce classifications. If you want to classify more than one tile, 
you have to create a new directory by tile. One is already created in ``sensor_data`` : ``T31TDJ`` which is empty.
As before, you can download dates and unzip them in the corresponding directory.

.. Warning::
    Do not forget to add the tile in the field ``listTile`` of the configuration file. 

    .. code-block:: python
    
        listTile:'T31TCJ T31UDP'

.. _two-zones:

Multi regions
*************

You can give to IOTA² a shapeFile describing different regions (spatial stratification). Each polygon contains 
a label referencing the region it belongs to. In the archive there is the file ``EcoRegion.shp`` containing two regions.

**What is it used for ?**

If the area to be classified is large, a given class may have different behaviours due to different climate conditions.
Train a different classifier for each eco-climatic area can improve the quality of the maps.
To classify the entire French metropolitan area, we used the following region distribution
(more details about the national product `here <http://www.mdpi.com/2072-4292/9/1/95>`_).

.. figure:: ./Images/regionFrance.jpg
    :scale: 50 %
    :align: center
    :alt: France regions shape
    
    France regions

How to set it in the configuration file ?
=========================================

As already explained, the region shapefile must contain a field to descriminate regions.
Let's have a look at the shape ``EcoRegion.shp``

.. figure:: ./Images/regions.jpg
    :scale: 50 %
    :align: center
    :alt: two regions shape
    
    Region shape Example

There are two regions, region "1" and "2" (field ``region``) which cover almost a full Sentinel-2 tile.
Two models will be produced: the first one will use training polygons of ``groundTruth.shp`` under the green region, while
the second model will use polygons under the red region.

.. Note:: Each model will classify **only** its own region.

.. Warning:: There must not be overlapping between polygons in the regions shapefile.

In order to use the region file add these fields to your configuration file :

.. code-block:: python
    
        chain:
        {
        ...
        regionPath:'/XXXX/IOTA2_TEST_S2/EcoRegion.shp'
        regionField:'region'
        ...
        }

Here is the example of configuration file :download:`configuration <./config/config_MultiRegions.cfg>`

IOTA²'s outputs with regions
============================

Every IOTA² run follows the same workflow but can generate different outputs.
In this particular run, IOTA² generated two models (in the ``model`` directory).
Each model is used to classify its region as show below:

+--------------------------------------------------+--------------------------------------------------+
| .. figure:: ./Images/classification_region1.jpg  | .. figure:: ./Images/classification_region2.jpg  |
|   :alt: classication region 1                    |   :alt: classication region 2                    |
|   :scale: 50 %                                   |   :scale: 50 %                                   |
|   :align: center                                 |   :align: center                                 |
|                                                  |                                                  |
|   classification of region 1                     |   classification of region 2                     |
+--------------------------------------------------+--------------------------------------------------+

Then these two rasters are merged and constitute the final classification.

.. figure:: ./Images/classification_region12.jpg
    :scale: 50 %
    :align: center
    :alt: two regions shape
    
    Classif_Seed_0.tif Multi regions Example

.. Note:: you can notice that the right-top corner is not classified. It's because this area does not belong to any region.


