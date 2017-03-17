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
  iota2ConnectGapFex.cxx
  extractSortedIndicesTest.cxx
  functor.cxx)

add_executable(iota2FeatureExtractionTests ${${otb-module}Tests})
target_link_libraries(iota2FeatureExtractionTests ${${otb-module}-Test_LIBRARIES})
otb_module_target_label(iota2FeatureExtractionTests)

add_executable(extractSortedIndicesTest ${${otb-module}Tests})
target_link_libraries(extractSortedIndicesTest ${${otb-module}-Test_LIBRARIES})
otb_module_target_label(extractSortedIndicesTest)

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

otb_add_test(NAME functorTest
  COMMAND extractSortedIndicesTest functor 0)

otb_test_application(NAME testNominal
	APP extractSortedIndices 
	OPTIONS
	-in ${IOTA2_SOURCE_DIR}/data/Stack_3dates_tlse_sample_blue.tif
	-out ${TEMP}/nomTest_test.tif
	-mask ${IOTA2_SOURCE_DIR}/data/Stack_3dates_tlse_MASK_sample.tif
	-id ${IOTA2_SOURCE_DIR}/data/Stack_3dates_010203Janv2016.txt
	VALID   --compare-image ${EPSILON_6}
	${IOTA2_SOURCE_DIR}/data/nomTest.tif
	${TEMP}/nomTest_test.tif)

otb_test_application(NAME wrongMaskNumberOfDates
	APP extractSortedIndices 
	OPTIONS
	-in ${IOTA2_SOURCE_DIR}/data/Stack_3dates_tlse_sample_blue.tif
	-out ${TEMP}/nomTest_wrongMNOD_test.tif
	-mask ${IOTA2_SOURCE_DIR}/data/Stack_2dates_tlse_MASK_sample.tif
	-id ${IOTA2_SOURCE_DIR}/data/Stack_3dates_010203Janv2016.txt
	VALID   --compare-image ${EPSILON_6}
	${IOTA2_SOURCE_DIR}/data/nomTest_wrongMNOD.tif
  	${TEMP}/nomTest_wrongMNOD_test.tif)

otb_test_application(NAME wrongNumberOfDates
	APP extractSortedIndices 
	OPTIONS
	-in ${IOTA2_SOURCE_DIR}/data/Stack_3dates_tlse_sample_blue.tif
	-out ${TEMP}/data/nomTest_wrongNOD_test.tif
	-mask ${IOTA2_SOURCE_DIR}/data/Stack_3dates_tlse_MASK_sample.tif
	-id ${IOTA2_SOURCE_DIR}/data/Stack_3dates_0102Janv2016.txt
	VALID   --compare-image ${EPSILON_6}
	${IOTA2_SOURCE_DIR}/data/nomTest_wrongNOD.tif
  	${TEMP}/nomTest_wrongNOD_test.tif)

set_tests_properties(wrongMaskNumberOfDates PROPERTIES WILL_FAIL TRUE)
set_tests_properties(wrongNumberOfDates PROPERTIES WILL_FAIL TRUE)

