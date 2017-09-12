cmake_minimum_required(VERSION 3.0)

project(IOTA2)

set(CMAKE_MODULE_PATH ${IOTA2_SOURCE_DIR}/CMake ${CMAKE_MODULE_PATH})
message("-- Using iota2. Your OTB will be under the GNU GPL License.")

if(NOT OTB_SOURCE_DIR)
  find_package(OTB REQUIRED)
  list(APPEND CMAKE_MODULE_PATH ${OTB_CMAKE_DIR})
  include(OTBModuleExternal)
else()
  otb_module_impl()
endif()
