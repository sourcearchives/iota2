#/bin/bash

module load python/2.7.5
module remove xerces/2.7
module load xerces/2.8
module load gdal/1.11.0-py2.7

pkg="otb_superbuild"
version="5.0.0"
name=$pkg-$version
install_dir=$DATACI/modules/repository/$pkg/$name-install/

export ITK_AUTOLOAD_PATH=""
export PATH=$install_dir/bin:$PATH
export LD_LIBRARY_PATH=$install_dir/lib:$install_dir/lib/otb/python:${LD_LIBRARY_PATH}
