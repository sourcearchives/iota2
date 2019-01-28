SAR and Optical post-classification fusion
##########################################

Purpose of the approach
***********************

Goal
====

The main goal of this feature is to allow IOTA² to perform a post-classification
fusion of SAR and optical data.

Issue
=====

This feature was proposed in issue `#67 <https://framagit.org/inglada/iota2/issues/67>`_ open on September 5, 2018.

Fields
******

An unique field has been added to the configuration file to enable the feature : ``dempster_shafer_SAR_Opt_fusion``

argTrain.dempster_shafer_SAR_Opt_fusion
=======================================

*Type*
    bool
*Default value*
    False
*Example*
    dempster_shafer_SAR_Opt_fusion : True

Fields compatibility 
====================

If ``dempster_shafer_SAR_Opt_fusion`` is ``True``, then ``S1Path`` must
be ``different from 'None'`` and an ``optical sensor has to be set``.
If this conditions are not met, a exception is thrown and the execution of IOTA² 
is aborted.

About steps
***********

Steps impacted
==============

1. vectorSampler
2. mergeSample
3. fusion
4. noData
5. mosaic

Steps created
=============

1. SAROptConfusionMatrix
    Step created in order to compute the confusion matrix using a set
    of validation samples, to evaluate SAR classifications and optical
    ones. These confusion matrices are computed by tile.

2. SAROptConfusionMatrixFusion
    Fusion of confusion matrices by tile in order to obtain a confusion by model

3. SAROptFusion
    Fusion of classifications comming from SAR and optical models.

Outputs
*******

Vectors
=======

Some vector data are created in order to compute confusion matrices and being
able to chose the label coming from SAR or optical models.

They are ``/dataAppVal/bymodels/TTTT_region_RRRR_seed_SSSS_samples_val.shp``
shapeFiles

 - TTTT : tile's name
 - RRRR : region's name
 - SSSS : seed number

CSV
===

| CSV representing confusion matrix are produced under names :
|    ``/dataAppVal/bymodels/TTTT_region_RRRR_seed_SSSS_samples_val.csv``
|    ``/dataAppVal/bymodels/TTTT_region_RRRR_seed_SSSS_samples_val_SAR.csv``
| Representing SAR and optical confusion matrix by tiles and by models.

| Also :
|    ``model_RRRR_seed_SSSS.csv``
|    ``model_RRRR_seed_SSSS_SAR.csv``
| Are the confusion matrices by model and by sensor and are produced next to the previous ones.

Rasters
=======

This functionality requires the production of two classifications by
region, one by model.

| Consequently, two raster are produced :
|    ``/classif/Classif_TTTT_model_RRRR_seed_SSSS.tif``
|    ``/classif/Classif_TTTT_model_RRRR_seed_SSSS_SAR.tif``

| As an equivalent for confidence map : 
|    ``/classif/TTTT_model_RRRR_confidence_seed_SSSS.tif``
|    ``/classif/TTTT_model_RRRR_confidence_seed_SSSS_SAR.tif``

| Fusions are done under names :
|    ``/classif/TTTT_model_RRRR_confidence_seed_SSSS_DS.tif`` to classification map
|    ``/classif/TTTT_model_RRRR_confidence_seed_SSSS_DS.tif`` to confidence map

Thanks to the fusion of classification results, we can produce a map which
allows users to know which label has been chosen by the fusion of classifications.

| This map which allow us to know who chose the final label is produced under the name 
| ``/final/TMP/DSchoice_TTTT_model_RRRR_seed_SSSS.tif``

It contains 4 possible values resumed in the following table :

    +-------+--------------+
    | value | Model chosen |
    +=======+==============+
    |   0   |     None     |
    +-------+--------------+
    |   1   | SAR + optical|
    +-------+--------------+
    |   2   |     SAR      |
    +-------+--------------+
    |   3   |   optical    |
    +-------+--------------+


Internal choices
****************

Fusion
======

The fusion of classifications is perfomed using the OTB's Application ``FusionOfClassifications``.
The Dempster-Shafer method is the one chosen to decide which label will be the
one in the final classification.

Confidence
==========

The FusionOfClassification OTB application does not provide a confidence map.
The confidence map corresponding to the fusion of classfications is generated thanks to 
the map of choices with the following rules:

    - SAR label has been chosen :
        SAR confidence is used
    - Optical label has been chosen :
        Optical confidence is used
    - SAR and optical models voted for the same label :
        the maximum confidence is used

Tests
*****

The unittest script called ``OpticalSARFusionTests.py`` has been created to test this
feature.

