set(DOCUMENTATION "OTB Applications for iota2")

# otb_module_requires_cxx11 does not exist anymore in otb>=6.0
if(COMMAND otb_module_requires_cxx11)
  otb_module_requires_cxx11()
endif()

# OTB_module() defines the module dependencies in GapFilling
# GapFilling depends on OTBCommon and OTBApplicationEngine
# The testing module in GapFilling depends on OTBTestKernel
# and OTBCommandLine

# define the dependencies of the include module and the tests
otb_module(IOTA2
  DEPENDS
  OTBITK
  OTBCommon
  OTBApplicationEngine
  OTBBoost
  OTBTemporalGapFilling
  OTBConversion
  TEST_DEPENDS
    OTBTestKernel
    OTBCommandLine
  DESCRIPTION
    "${DOCUMENTATION}"
)
