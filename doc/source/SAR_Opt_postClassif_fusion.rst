SAR and Optical post-classification fusion
##########################################

Feature purpose
***************

Goal
====

The main goal of this feature is to allow IOTA² to perform a post-classification
fusion of SAR and optical data.

Issue
=====

This feature is result of the issue `#67 <https://framagit.org/inglada/iota2/issues/67>`_ opened the September 5, 2018.

Fields
******

An unique field has been added to the configuration file to enable the feature

argTrain.dempster_shafer_SAR_Opt_fusion
=======================================

*Type*
    bool
*Default value*
    False
*Example*
    dempster_shafer_SAR_Opt_fusion : True

Incompatible fields 
===================

If ``dempster_shafer_SAR_Opt_fusion`` is ``True``, then ``S1Path`` must
be ``different from 'None'`` and an ``optical sensor has to be set``.

Outputs
*******

Vectors
=======

Rasters
=======

Steps impacted
**************

Key choices
***********

Fusion
======

The fusion of classification is done thanks to otb Application ``FusionOfClassifications``.
In order to , the Dempster-Shafer method is the one chosen to decide which
label will be the one in the final classification.

Confidence
==========