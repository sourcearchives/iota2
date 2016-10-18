# =========================================================================
# Program:   iota2
# Language:  C++
#
# Copyright (c) CESBIO. All rights reserved.
#
# See LICENSE for details.
#
# This software is distributed WITHOUT ANY WARRANTY; without even
# the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the above copyright notices for more information.
#
# =========================================================================

OTB_CREATE_APPLICATION(
  NAME iota2FeatureExtraction
  SOURCES iota2FeatureExtraction.cxx
  LINK_LIBRARIES  ${OTBCommon_LIBRARIES} ${OTBITK_LIBRARIES} ${OTBApplicationEngine_LIBRARIES}   )

OTB_CREATE_APPLICATION(
  NAME iota2GapFillingFeatureExtraction
  SOURCES iota2GapFillingFeatureExtraction.cxx
  LINK_LIBRARIES  ${OTBCommon_LIBRARIES} ${OTBITK_LIBRARIES} ${OTBApplicationEngine_LIBRARIES} ${OTBTemporalGapFilling_LIBRARIES} ${OTBBoost_LIBRARIES} ${GSL_LIBRARIES}  )
