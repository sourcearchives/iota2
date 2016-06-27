project(IOTA2)

set(CMAKE_MODULE_PATH ${IOTA2_SOURCE_DIR}/CMake ${CMAKE_MODULE_PATH})
message("-- Using iota2. Your OTB will be under the GNU GPL License.")

#set(IOTA2_LIBRARIES ${otb-module})
otb_module_impl()
