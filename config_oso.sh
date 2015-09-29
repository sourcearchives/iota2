#/bin/bash

module load python/2.7.5
module remove xerces/2.7
module load xerces/2.8
module load gdal/1.11.0-py2.7

export ITK_AUTOLOAD_PATH=""
export OTB_HOME=/data/qtis/inglada/modules/repository/otb_superbuild/otb_superbuild-5.0.0-install
export PATH=${OTB_HOME}/bin:$PATH
export LD_LIBRARY_PATH=${OTB_HOME}/lib:${OTB_HOME}/lib/otb/python:$LD_LIBRARY_PATH
export PYTHONPATH=${OTB_HOME}/lib/otb/python:${PYTHONPATH}
