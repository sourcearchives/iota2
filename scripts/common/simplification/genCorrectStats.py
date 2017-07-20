#!/usr/bin/python
#-*- coding: utf-8 -*-

# =========================================================================
#   Program:   iota2
#
#   Copyright (c) CESBIO. All rights reserved.
#
#   See LICENSE for details.
#
#   This software is distributed WITHOUT ANY WARRANTY; without even
#   the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the above copyright notices for more information.
#
# =========================================================================

import argparse,os

def genJob(jobPath, deptNumber, core):

    jobFile = open(jobPath,"w")
    jobFile.write('#!/bin/bash\n\
#PBS -N correctstats%s\n\
#PBS -l select=1:ncpus=%s:mem=20000mb:generation=g2016\n\
#PBS -l walltime=1:00:00\n\
#PBS -o /home/qt/thierionv/simplification/correctstats_out_%s.log\n\
#PBS -e /home/qt/thierionv/simplification/correctstats_err_%s.log\n\
\n\
module load python/2.7.12\n\
\n\
source /work/OT/theia/oso/OTB/otb_superbuild/otb_superbuild-5.10.1-Release-install/config_otb.sh\n\
PYPATH=/home/qt/thierionv/simplification/post-processing-oso/script_oso/\n\
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=%s\n\
export PYTHONPATH=${PYTHONPATH}:/home/qt/thierionv/vector_tools\n\
deptNumber=%s\n\
cd $PYPATH\n\
cp /work/OT/theia/oso/classifications/France_S2_AllFeatures_CropMix2/final/Classif_Seed_0.tif $TMPDIR\n\
cp /work/OT/theia/oso/classifications/France_S2_AllFeatures_CropMix2/final/Confidence_Seed_0.tif $TMPDIR\n\
cp /work/OT/theia/oso/classifications/France_S2_AllFeatures_CropMix2/final/PixelsValidity.tif $TMPDIR\n\
cp /work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/vecteurs/dept_"$deptNumber"/departement_"$deptNumber".* $TMPDIR\n\
mkdir -p $TMPDIR/dept_"$deptNumber"\n\
mkdir -p /work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/vecteurs/final/\n\
# creation polygones manquants\n\
python correct_vector.py -wd $TMPDIR -grass /work/OT/theia/oso/OTB/GRASS/grass7.2.1svn-x86_64-pc-linux-gnu-13_03_2017 -ndept $deptNumber -classif $TMPDIR/departement_"$deptNumber".shp -depts /work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/FranceDepartements.shp -out $TMPDIR/dept_"$deptNumber"/\n\
# Subset des raster + creation du mask\n\
python MaskFromVector.py -wd $TMPDIR -vector $TMPDIR/dept_"$deptNumber"/eaux_"$deptNumber".shp -threads 20 -pixFormat Byte -validity $TMPDIR/PixelsValidity.tif -classif $TMPDIR/Classif_Seed_0.tif -confid $TMPDIR/Confidence_Seed_0.tif -out $TMPDIR/dept_"$deptNumber"/ -mask mask_eau.tif\n\
# Extraction des samples\n\
python zonal_stats_otb_v3.py -wd $TMPDIR -classif $TMPDIR/Classif_Seed_0_subset.tif -vecteur $TMPDIR/dept_"$deptNumber"/eaux_"$deptNumber".shp -confid $TMPDIR/Confidence_Seed_0_subset.tif -validity $TMPDIR/PixelsValidity_subset.tif -nbcore 20 -strippe 2 -otbversion 5.9 -ndept $deptNumber -mask $TMPDIR/dept_"$deptNumber"/mask_eau.tif -out $TMPDIR/dept_"$deptNumber"/ -field cat\n\
# Statistiques zonales\n\
python stats_extract.py -wd $TMPDIR -in $TMPDIR/dept_"$deptNumber"/sample_extract.sqlite -out $TMPDIR/ -ndept $deptNumber -classif value_0 -id cat\n\
# Jointure\n\
python join_correctif.py -wd $TMPDIR -vecteur $TMPDIR/dept_"$deptNumber"/eaux_"$deptNumber".shp -stats $TMPDIR/dept_"$deptNumber"/stats.csv -out $TMPDIR -ndept $deptNumber\n\
# Union des vecteurs\n\
python /home/qt/thierionv/vector_tools/MergeFiles.py -list $TMPDIR/departement_"$deptNumber".shp $TMPDIR/dept_"$deptNumber"/eaux_"$deptNumber".shp -o $TMPDIR/dept"$deptNumber".shp\n\
cp -fur $TMPDIR/dept"$deptNumber".* /work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/vecteurs/final/\n\
rm -R $TMPDIR/*\n\
'%(deptNumber, core, deptNumber, deptNumber, core, deptNumber))
    jobFile.close()

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "This function creates the jobArray.pbs for DataAppVal")
    parser.add_argument("-output",help ="outputPath (mandatory)",dest = "output",required=True)
    parser.add_argument("-deptNumber",help ="Departement number",dest = "deptNumber",required=True)
    parser.add_argument("-core",dest = "core",help ="number of cpu",required=False,default='2')
    args = parser.parse_args()

    genJob(args.output,args.deptNumber, args.core)
