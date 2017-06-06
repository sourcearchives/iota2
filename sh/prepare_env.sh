#!/bin/bash                                        
export IOTA2DIR=/data/OSO/iota2
export prefix_dir=/data/OSO/OTB
export PYTHONPATH=$PYTHONPATH:$IOTA2DIR/../python/lib//python2.7/site-packages/
export PYTHONPATH=$PYTHONPATH:$IOTA2DIR/data/test_scripts
#----------------------------------------
install_dir=$prefix_dir/OTB/SuperBuild-5.10
export ITK_AUTOLOAD_PATH=""
export PATH=$install_dir/bin:$PATH
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}
export OTB_APPLICATION_PATH=$install_dir/lib/otb/applications/
export PYTHONPATH=$install_dir/lib/otb/python:$install_dir/lib/python2.7/site-packages/:$PYTHONPATH
export GDAL_DATA=$install_dir/share/gdal
export GEOTIFF_CSV=$install_dir/share/epsg_csv 
#----------------------------------------

