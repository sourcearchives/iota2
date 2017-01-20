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
otb_module_test()

set(${otb-module}Tests
  iota2FeatureExtractionTests.cxx
  iota2FeatureExtractionFunctor.cxx
  iota2ConnectGapFex.cxx)

add_executable(iota2FeatureExtractionTests ${${otb-module}Tests})
target_link_libraries(iota2FeatureExtractionTests ${${otb-module}-Test_LIBRARIES})
otb_module_target_label(iota2FeatureExtractionTests)

otb_add_test(NAME iota2FexFunctor
  COMMAND iota2FeatureExtractionTests fexFunctor 1)

otb_add_test(NAME iota2FexFunctorNoCopy
  COMMAND iota2FeatureExtractionTests fexFunctor 0)

otb_test_application(NAME iota2FexApp
  APP  iota2FeatureExtraction
  OPTIONS 
  -in ${IOTA2_SOURCE_DIR}/data/D0005H0004_GAP.tif
  -comp 7
  -red 4
  -nir 5
  -swir 6
  -indfact 1.0
  -out ${TEMP}/iotaFex.tif
  -copyinput true
  VALID   --compare-image ${EPSILON_6}
  ${IOTA2_SOURCE_DIR}/data/AllFeat_D0005H0004.tif
  ${TEMP}/iotaFex.tif)

otb_test_application(NAME iota2FexAppNoCopy
  APP  iota2FeatureExtraction
  OPTIONS 
  -in ${IOTA2_SOURCE_DIR}/data/D0005H0004_GAP.tif
  -comp 7
  -red 4
  -nir 5
  -swir 6
  -indfact 1.0
  -out ${TEMP}/iotaFexNoCopy.tif
  -copyinput false
  VALID   --compare-image ${EPSILON_6}
  ${IOTA2_SOURCE_DIR}/data/OnlyIndices.tif
  ${TEMP}/iotaFexNoCopy.tif)

otb_test_application(NAME iota2FexAppWrongNumbComp
  APP  iota2FeatureExtraction
  OPTIONS 
  -in ${IOTA2_SOURCE_DIR}/data/D0005H0004_GAP.tif
  -comp 6
  -red 4
  -nir 5
  -swir 6
  -indfact 1.0
  -out ${TEMP}/iotaFexWrongNumbComp.tif)

set_tests_properties(iota2FexAppWrongNumbComp PROPERTIES WILL_FAIL TRUE)

otb_add_test(NAME iota2ConnectGapFex
  COMMAND iota2FeatureExtractionTests connectGapFex
  ${CMAKE_BINARY_DIR}/lib/otb/applications
  ${IOTA2_SOURCE_DIR}/data/D0005H0004_GAP.tif
  ${TEMP}/iota2ConnectGapFex.tif
  )
