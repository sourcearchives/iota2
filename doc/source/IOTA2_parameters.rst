IOTA² input parameters
######################

IOTA² is fully configurable by using one file given to IOTA² at launch.
This file is call the 'configuration file' in the whole documentation.
This section is dedicated to the description of each parameters in it.

IOTA² parameters are split in 4 familly group : chain, argTrain,
argClassification and GlobChain. First let's have a look at chain parameters.

chain available parameters
**************************

chain.outputPath
================
*Description*
    Absolute path to the test folder. It is recommended to have one folder by test
*Type*
    string
*Default value*
    ``mandatory``
*Example*
    outputPath : '/absolute/path/to/IOTA2_output/' 
*Notes*
    the targeted directory will be created by IOTA²

chain.remove_outputPath
=======================
*Description*
    if set to True, remove the directory targeted by the field 'outputPath'
*Type*
    bool
*Default value*
    ``mandatory``
*Example*
    remove_outputPath : True

chain.pyAppPath
===============
*Description*
    absolute path to the IOTA² python's script
*Type*
    string
*Default value*
    ``mandatory``
*Example*
    pyAppPath : '/absolute/path/to/iota2/scripts'

chain.nomenclaturePath
======================
*Description*
    absolute path to the nomenclature description
*Type*
    string
*Default value*
    ``mandatory``
*Example*
    nomenclaturePath : '/to/Nomenclature.csv'
*Notes*
    the nomenclature file is the way IOTA² establish the link between
    the verbose class name and it's label. The file content must respect
    the following syntax :
    
    .. code-block:: console
    
        my_crop_class:1
        my_urbain_class:2
        ...

chain.listTile
==============
*Description*
    list of tiles to consider
*Type*
    string
*Default value*
    ``mandatory``
*Example*
    listTile : 'D0003H0001 D0008H0004'
*Notes*
    tiles must be separated by one space character

chain.L8Path
============
*Description*
    absolute path to Landsat-8 images comming from THEIA
*Type*
    string
*Default value*
    'None'
*Example*
    L8Path : '/to/L8/Path/'
*Notes*
    see the note about tilled sensors data storage : :ref:`tilled data storage`

chain.L5Path
============
*Description*
    absolute path to Landsat-5 images comming from THEIA
*Type*
    string
*Default value*
    'None'
*Example*
    L5Path : '/to/L5/Path/'
*Notes*
    see the note : :ref:`tilled data storage`

chain.S2Path
============
*Description*
    absolute path to  Sentinel_2 images (THEIA format)
*Type*
    string
*Default value*
    'None'
*Example*
    S2Path : '/to/S2/path/'
*Notes*
    see the note about tilled sensors data storage : :ref:`tilled data storage`

chain.S2_S2C_Path
=================
*Description*
    absolute path to  Sentinel_2 images (Sen2Cor format)
*Type*
    string
*Default value*
    'None'
*Example*
    S2Path : '/to/S2/path/'
*Notes*
    see the note about tilled sensors data storage : :ref:`tilled data storage`

chain.S1Path
============
*Description*
    absolute path to the configuration file needed to configure the
    production of Sentinel-1 data
*Type*
    string
*Default value*
    'None'
*Example*
    S1Path:'/path/to/SAR_data.cfg'
*Notes*
    see the documentation about how to fill-up Sentinel-1 configuration file 
    (comming soon)

chain.userFeatPath
==================
*Description*
    absolute path to the user's features path (they must be stored by tiles)
*Type*
    string
*Default value*
    'None'
*Example*
    userFeatPath:'/../../MNT_L8Grid'
*Notes*
    see the note about tilled sensors data storage : :ref:`tilled data storage`
    
chain.groundTruth
=================

*Description*
    absolute path to ground truth 
*Type*
    string
*Default value*
    ``mandatory``
*Example*
    groundTruth : '/to/my/groundTruth.shp'
*Notes*
    the ground truth file must respect the following rules

    1. It must be a shapeFile (.shp)
    2. The file must contain an integer field to descriminate features which belong to the same class
    3. Geometries as to be ``POLYGON``
    4. No overlapping between polygons

chain.dataField
===============
*Description*
    field's name discriminating features which belong to the same class in
    ground truth
*Type*
    string
*Default value*
    ``mandatory``
*Example*
    dataField : 'My_integer_field' 
*Notes*
    that field must contain integer

chain.regionPath
================
*Description*
    absolute path to the shapeFile containing learning regions
*Type*
    string
*Default value*
    None
*Example*
    regionPath : '/to/my/region.shp'
*Notes*
    The use of this field enable IOTA² to generate one model by regions.
    The purpose of this fonctionality is highlight by the example : :ref:`two-zones`

    the regions file must respect the following rules

    1. It must be a shapeFile (.shp)
    2. The file must contain an string field to descriminate regions
    3. Geometries as to be ``POLYGON`` or ``MULTIPOLYGON``
    4. No overlapping between polygons

chain.regionField
=================
*Description*
    field that discriminates regions into the region shapeFile
*Type*
    string
*Default value*
    None
*Example*
    regionField : 'My_string_region'
*Notes*
    that field must contain string

chain.runs
==========
*Description*
    number of random sample for training and validation
*Type*
    int
*Default value*
    1
*Example*
    runs : 1
*Notes*
    must be an integer different from 0

chain.logFileLevel
==================
*Description*
    logging level, 5 levels are available : "CRITICAL"<"ERROR"<"WARNING"<"INFO"<"DEBUG"
*Type*
    string
*Default value*
    'INFO'
*Example*
    logFileLevel:"DEBUG"

chain.enableConsole
===================
*Description*
    enable console logging
*Type*
    bool
*Default value*
    False
*Example*
    enableConsole:False

chain.OTB_HOME
==============
*Description*
    absolute path to the OTB installation directory
*Type*
    string
*Default value*
    'None'
*Example*
    OTB_HOME : 'MyOTBInstall'
*Notes*
    only available if IOTA² is launch thanks to IOTA2Cluster.py

chain.colorTable
================
*Description*
    absolute path to the file wich link classes and their color
*Type*
    string
*Default value*
    ``mandatory``
*Example*
    colorTable:'/path/to/MyColorFile.txt'
*Notes*
    The color file is the way IOTA² establish the link between
    the class label and it's color (usefull for vizualisation). It must
    respect the following syntax :
    
    .. code-block:: console
    
        0 255 255 255
        10 255 85 0
        11 255 85 0
        ...

    here the class 0 receive the RGB code 255 255 255, the class 10 : 255 85 0 etc...

chain.mode_outside_RegionSplit
==============================
*Description*
    This parameter is available if regionPath and argClassification.classifMode
    is set to ``fusion``. It represent the maximum size covered by a region.
    If the regions is superior to this threshold, then N models are build
    by randomly selected feature inside the region.
*Type*
    float
*Default value*
    0.1
*Example*
    mode_outside_RegionSplit : 0.001
*Notes*
    the threshold is exprimed in km²

chain.ratio
===========
*Description*
    ratio between training and validation set
*Type*
    float
*Default value*
    0.5
*Example*
    ratio : 0.6
*Notes*
    must be a float between ]0;1[

chain.cloud_treshold
====================
*Description*
    To learn models, IOTA² will use **only**, polygons (or part of them)
    which are "see" at least 'cloud_treshold' times. A valid area is a
    zone which is not covered by clouds or cloud's shadows and which is 
    not saturated.
*Type*
    int
*Default value*
    1
*Example*
    cloud_threshold:1
*Notes*
    must be an integer >= 0

chain.spatialResolution
=======================
*Description*
    output pixel's spatial resolution
*Type*
    int
*Default value*
    ``mandatory``
*Example*
    spatialResolution:30

chain.firstStep
===============
*Description*
    parameter use to restart chain from a specific step
*Type*
    string
*Default value*
    'init'
*Example*
    firstStep:'init'
*Notes*
    Must be chosen into the list of available steps.

    Available choices are 'init', 'sampling', 'learning', 'classification',
    'mosaic' or 'validation'

chain.lastStep
==============
*Description*
    parameter use to stop chain at a specific step
*Type*
    string
*Default value*
    'validation'
*Example*
    firstStep:'learning'
*Notes*
    Must be chosen into the list of available steps.

    Available choices are 'init', 'sampling', 'learning', 'classification',
    'mosaic' or 'validation'

chain.merge_final_classifications
=================================
*Description*
    flag to set in order to compute a raster which is the fusion of final classifications (one by run)
*Type*
    bool
*Default value*
    False
*Example*
    merge_final_classifications:True
*Notes*
    the fusion of classifications is saved under the name : ``Classifications_fusion.tif``

chain.merge_final_classifications_ratio
=======================================
*Description*
    percentage of samples to use in order to evaluate the fusion raster
*Type*
    float
*Default value*
    0.1
*Example*
    merge_final_classifications_ratio:0.1
*Notes*
    IOTA² will extract, for each models, a percentage of samples before the
    learning/validation split.

    percentage must be between ``]0; 1[``

chain.merge_final_classifications_undecidedlabel
================================================
*Description*
    fusion of classifications can produce undecisions, this field is the
    label for undecisions un fusion rasters
*Type*
    int
*Default value*
    255
*Example*
    merge_final_classifications_undecidedlabel:255

chain.merge_final_classifications_method
========================================
*Description*
    fusion of classifications method
*Type*
    string
*Default value*
    'majorityvoting'
*Example*
    merge_final_classifications_method : 'dempstershafer'
*Notes*
    Their is two choice : 'majorityvoting' or 'dempstershafer'

chain.dempstershafer_mob
========================
*Description*
    If ``merge_final_classifications`` is set to ``True``, and
    ``merge_final_classifications_method`` is set to ``'dempstershafer'``,
    define the dempstershafer's mass of belief measurement
*Type*
    string
*Default value*
    'precision'
*Example*
    dempstershafer_mob : 'kappa'
*Notes*
    Available choice are : 'precision', 'recall' , 'accuracy' or 'kappa'

chain.keep_runs_results
=======================
*Description*
    If ``merge_final_classifications`` is set to ``True``, two final reports can
    be compute. One by seed classification and one evaluating the fusion
    of classifications. If this flag is set to ``False``, then the computation
    of seed results is abort. 
*Type*
    bool
*Default value*
    True
*Example*
    keep_runs_results:True

chain.remove_tmp_files
======================
*Description*
    IOTA² produce a lot of data before being able to compute final 
    classifications. This flag is use to remove all temporary directories
    (ie : containing models, classifications...) and to keep final results.
*Type*
    bool
*Default value*
    False
*Example*
    remove_tmp_files : True

chain.outputStatistics
======================
*Description*
    flag used to genererate additionnal statistics (confidence by learning / validation pixels)
*Type*
    bool
*Default value*
    False
*Example*
    outputStatistics:True
*Notes*
    outputs are addtionals PNG files under /final directory

chain.enableCrossValidation
===========================
*Description*
    flag used to enable cross validation mode
*Type*
    bool
*Default value*
    False
*Example*
    enableCrossValidation : True
*Notes*
    Folds number is given by the field 'runs'

chain.splitGroundTruth
======================
*Description*
    Flag used to allow IOTA² to split ground truth. if set to False then
    the chain will use all polygons to learn models and to validate it.
*Type*
    bool
*Default value*
    True
*Example*
    splitGroundTruth : False


.. _tilled data storage:

About tilled data storage
=========================

Sensors data must be stored by sensors / tile / dates as the following tree

    .. code-block:: console

        ├── Sentinel2_MAJA
        │   ├── T31TCJ
        │   │   ├── SENTINEL2A_20180511-105804-037_L2A_T31TCJ_D_V1-7
        │   │   │   ├── MASKS
        │   │   │   │   └── *.tif
        │   │   │   └── *.tif
        │   │   └── SENTINEL2A_20180521-105702-711_L2A_T31TCJ_D_V1-7
        │   │       ├── MASKS
        │   │       │   └── *.tif
        │   │       └── *.tif
        │   ├── ...
        │   └── T31TDK
        │       └── ...
        ├── Sentinel2_Sen2Cor
        │   ├── T31TCJ
        │   ├── ...
        │   └── T31TDK
        │       └── ...
        ├── LandSat8
        │   ├── D0005H0002
        │   ├── ...
        │   └── D0005H0008
        ├── ...

argTrain available parameters
*****************************

argTrain.dempster_shafer_SAR_Opt_fusion
=======================================
*Description*
    IOTA² can deal with optical data and SAR data to produce land cover map.
    This data can be mixed together to learn a single model, or one model
    by sensor can be generated. This flag is about to set-up the second
    fonctionality.
*Type*
    bool
*Default value*
    False
*Example*
    dempster_shafer_SAR_Opt_fusion : True
*Notes*
    IOTA² implement the dempster-shafer fusion rules to choice labels
    comming from SAR decision and Optical decision.
    A fully detailed about the feature functionality is available :doc:`here <SAR_Opt_postClassif_fusion>`

    