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

import sys, os, argparse
import subprocess
import OSO_functions as osof

def checkTile(depts, grid, voisins, out, nbcore, finalout, jobname, field):
    """
    Status analysis of tile production.
    
    in : 
        depts : departments shapefile
        grid : grid from generated grid
        
    """
    # shapefiles
    grid_shape = osof.shape_open(grid,0)
    dept_shape = osof.shape_open(depts,0)
    grid_layer = grid_shape.GetLayer()
    dept_layer = dept_shape.GetLayer()    

    list_files_tiles = []

    nb_grid = grid_layer.GetFeatureCount()

    # check status
    #listerrorgeom = getGeomError(out)
    #cptblock = 0
    for feature1 in dept_layer:
        deptready = True
        geom1 = feature1.GetGeometryRef()
        ndept = int(feature1.GetField("CODE_DEPT"))
        #if ndept in listerrorgeom and ndept != 14:
        if ndept not in [50]:
           #not os.path.exists(out + '/stats/' + 'departement_' + str(ndept) + '.shp'):
            grid_layer.ResetReading()
        
            """
            try:
            #print 'Création de %s'(out + '/dept_' + str(ndept))
            os.mkdir(out + '/dept_' + str(ndept))
            except:
            continue
            """
            jobPath = out + '/dept_' + str(ndept) + "/%s%s.pbs"%(jobname, ndept)
            #if not int(feature1.GetField("CODE_DEPT")) in listshapesuccess or \
                #not int(feature1.GetField("CODE_DEPT")) in liststatssuccess:
            #if int(feature1.GetField("CODE_DEPT")) != 83:
            #if not os.path.exists(out + '/dept_' + str(ndept) + '/' + 'departement_' + str(ndept) + '.shp'):
            for feature2 in grid_layer:
                if deptready:
                    geom2 = feature2.GetGeometryRef()
                    if geom2.Intersects(geom1):
                        tile = int(feature2.GetField("FID"))
                        if not os.path.isfile(voisins + "/" + str(tile) + "/outfiles/tile_%s.shp"%(tile)) :
                            grid_layer.GetFeature(nb_grid - 1)
                            deptready = False
                        else:
                            list_files_tiles.append(voisins + "/" + str(tile) + "/outfiles/tile_%s.shp"%(tile))
                            deptready = True

                jobPathBool = True
            if not deptready:
                print 'Certains vecteurs de tuiles ne sont pas disponibles pour la fusion départementale'
            else:
                '''
                if not int(feature1.GetField("CODE_DEPT")) in listshapesuccess:
                    if not int(feature1.GetField("CODE_DEPT"))  in liststatssuccess:
                        jobPath = generateJob(jobPath, list_files_tiles, ndept, depts, out, nbcore)
                    else:
                        jobPath = generateJobPartielStats(jobPath, list_files_tiles, ndept, depts, out, nbcore)
                else:
                    if not int(feature1.GetField("CODE_DEPT")) in liststatssuccess:
                        jobPath = generateJobPartiel(jobPath, list_files_tiles, ndept, depts, out, nbcore)
                    else:
                        jobPathBool = False
                        
                if jobPathBool:
                    cptblock += 1
                    if cptblock%20 != 0:
		        print 'qsub %s'%(jobPath)
                        subprocess.check_output('qsub %s'%(jobPath), shell=True)
                    else:
                        print 'qsub -W block=true %s'%(jobPath)
                        subprocess.check_output('qsub -W block=true %s'%(jobPath), shell=True)

                print ndept
                cptblock += 1
                '''
                jobPath = generateJobCorse(jobPath, list_files_tiles, ndept, depts, out, nbcore, finalout, jobname, field)
                '''
                if cptblock%20 != 0:
                    print 'qsub %s'%(jobPath)
                    subprocess.check_output('qsub %s'%(jobPath), shell=True)
                else:
                    print 'qsub -W block=true %s'%(jobPath)
                    subprocess.check_output('qsub -W block=true %s'%(jobPath), shell=True)
                
                jobPath = generateJobDuplicate(jobPath, ndept, out)
                '''
                print ndept                
                subprocess.check_output('qsub %s'%(jobPath), shell=True)
                
            list_files_tiles = []
            

def getStatus(path):
    command="grep -r --include 'shapeDept_error_*' reached %s/"%(path)
    result_size = subprocess.check_output(command, shell=True)
    tabresult = result_size.rstrip().split('\n')
    listinit = range(1, 96, 1)
    listinit.remove(20)
    listsize = list(set([int(x.split('_')[1].split('/')[0]) for x in tabresult]))
    listshapesuccess = [x for x in listinit if x not in listsize]

    command = "find %s/dept_*/ -name stats.csv"%(path)
    result_stats = subprocess.check_output(command, shell=True)
    tabresult = result_stats.rstrip().split('\n')
    liststatssuccess = [int(x.split('_')[1].split('/')[0]) for x in tabresult]
    return listshapesuccess, liststatssuccess

def getGeomError(path):
    command="grep -lr %s/dept_*/statsdept_error_* -e 'Area of size = 0.0'"%(path)
    result_size = subprocess.check_output(command, shell=True)
    tabresult = result_size.rstrip().split('\n')
    listgeomerror = [int(x.split('_')[1].split('/')[0]) for x in tabresult]
    return listgeomerror

def generateJobDuplicate(jobPath, ndept, out):
    outputlog = out + '/' + 'dept_' + str(ndept) + '/' + 'DeleteDup_out' + str(ndept)
    errorlog = out + '/' + 'dept_' + str(ndept) + '/' + 'DeleteDup_err' + str(ndept)

    if int(ndept) < 10:
        ndeptcond = '0' + str(ndept)
    else:
        ndeptcond = str(ndept)
    
    jobFile = open(jobPath,"w")
    jobFile.write('#!/bin/bash\n\
#PBS -N DeleteDup%s\n\
#PBS -l select=1:ncpus=1:mem=20000mb\n\
#PBS -l walltime=4:00:00\n\
#PBS -o %s\n\
#PBS -e %s\n\
\n\
module load python/2.7.12\n\
\n\
source /work/OT/theia/oso/OTB/otb_superbuild/otb_superbuild-5.10.1-Release-install/config_otb.sh\n\
export PYTHONPATH=${PYTHONPATH}:/home/qt/thierionv/vector_tools\n\
cd /home/qt/thierionv/vector_tools/\n\
\n\
deptNumber=%s\n\
python DeleteDuplicateGeometries.py -s /work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/vecteurs/stats/departement_"$deptNumber".shp\n\
'%(ndept, outputlog, errorlog, ndept))
    jobFile.close()

    return jobPath

def generateJobShape(jobPath, list_files_tiles, ndept, depts, out, nbcore):

    outputlog = out + '/' + 'dept_' + str(ndept) + '/' + 'shapeDept_output_' + str(ndept)
    errorlog = out + '/' + 'dept_' + str(ndept) + '/' + 'shapeDept_error_' + str(ndept)
    vectorclassif = out + '/' + 'dept_' + str(ndept) + '/' + 'departement_' + str(ndept) + '.shp'

    if int(ndept) < 10:
        ndeptcond = '0' + str(ndept)
    else:
        ndeptcond = str(ndept)
    
    jobFile = open(jobPath,"w")
    jobFile.write('#!/bin/bash\n\
#PBS -N shapeDept%s\n\
#PBS -l select=1:ncpus=%s:mem=60000mb\n\
#PBS -l walltime=15:00:00\n\
#PBS -o %s\n\
#PBS -e %s\n\
\n\
module load python/2.7.12\n\
\n\
source /work/OT/theia/oso/OTB/otb_superbuild/otb_superbuild-5.10.1-Release-install/config_otb.sh\n\
export PYTHONPATH=${PYTHONPATH}:/home/qt/thierionv/vector_tools\n\
PYPATH=/home/qt/thierionv/simplification/post-processing-oso/script_oso/\n\
cd $PYPATH\n\
\n\
cmd="python mergeTileShapes.py -wd $TMPDIR -extract %s -ndept %s -out %s -listTiles %s -grass /work/OT/theia/oso/OTB/GRASS/grass7.2.1svn-x86_64-pc-linux-gnu-13_03_2017"\n\
echo $cmd\n\
eval $cmd\n\
'%(ndept, nbcore, outputlog, errorlog, depts, ndept, out, " ".join(list_files_tiles)))
    jobFile.close()

    return jobPath

def generateJob(jobPath, list_files_tiles, ndept, depts, out, nbcore, finalout, jobname, field):

    outputlog = out + '/' + 'dept_' + str(ndept) + '/' + '%s_output_'%(jobname) + str(ndept)
    errorlog = out + '/' + 'dept_' + str(ndept) + '/' + '%s_error_'%(jobname) + str(ndept)
    vectorclassif = out + '/' + 'dept_' + str(ndept) + '/' + 'dept' + str(ndept) + '.shp'

    if int(ndept) < 10:
        ndeptcond = '0' + str(ndept)
    else:
        ndeptcond = str(ndept)
    
    jobFile = open(jobPath,"w")
    jobFile.write('#!/bin/bash\n\
#PBS -N %s%s\n\
#PBS -l select=1:ncpus=%s:mem=60000mb\n\
#PBS -l walltime=100:00:00\n\
#PBS -o %s\n\
#PBS -e %s\n\
\n\
module load python/2.7.12\n\
\n\
source /work/OT/theia/oso/OTB/otb_superbuild/otb_superbuild-5.10.1-Release-install/config_otb.sh\n\
export PYTHONPATH=${PYTHONPATH}:/home/qt/thierionv/vector_tools\n\
PYPATH=/home/qt/thierionv/simplification/post-processing-oso/script_oso/\n\
IOTAPATH=/home/qt/thierionv/chaineIOTA/scripts/common/\n\
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=%s\n\
cd $PYPATH\n\
\n\
cmd="python mergeTileShapes.py -wd $TMPDIR -extract %s -ndept %s -out %s -listTiles %s -grass /work/OT/theia/oso/OTB/GRASS/grass7.2.1svn-x86_64-pc-linux-gnu-13_03_2017"\n\
echo $cmd\n\
eval $cmd\n\
\n\
cp /work/OT/theia/oso/classifications/France_S2_AllFeatures_CropMix2/final/Classif_Seed_0.tif $TMPDIR\n\
cp /work/OT/theia/oso/classifications/France_S2_AllFeatures_CropMix2/final/Confidence_Seed_0.tif $TMPDIR\n\
cp /work/OT/theia/oso/classifications/France_S2_AllFeatures_CropMix2/final/PixelsValidity.tif $TMPDIR\n\
deptNumber=%s\n\
outpath=%s\n\
vectordept=%s\n\
deptNumberStr=%s\n\
nbcore=%s\n\
finaloutpath=%s\n\
\n\
mkdir -p "$outpath"/dept_"$deptNumber"/splits\n\
\n\
python extractAndSplit.py -workingDirectory $TMPDIR -Y 5 -X 5 -out.name Classif_dept_"$deptNumber" -out.directory "$outpath"/dept_"$deptNumber"/splits -dataFieldValue $deptNumberStr -field CODE_DEPT -in.vector $vectordept -in.raster $TMPDIR/Classif_Seed_0.tif -threads $nbcore\n\
python extractAndSplit.py -workingDirectory $TMPDIR -Y 5 -X 5 -out.name Confidence_dept_"$deptNumber" -out.directory "$outpath"/dept_"$deptNumber"/splits -dataFieldValue $deptNumberStr -field CODE_DEPT -in.vector $vectordept -in.raster $TMPDIR/Confidence_Seed_0.tif -threads $nbcore\n\
python extractAndSplit.py -workingDirectory $TMPDIR -Y 5 -X 5 -out.name PixelsValidity_dept_"$deptNumber" -out.directory "$outpath"/dept_"$deptNumber"/splits -dataFieldValue $deptNumberStr -field CODE_DEPT -in.vector $vectordept -in.raster $TMPDIR/PixelsValidity.tif -threads $nbcore\n\
\n\
job="$outpath"/dept_"$deptNumber"/splits/job.pbs\n\
splitFolder="$outpath"/dept_"$deptNumber"/splits\n\
python generateJobsZonalStats.py -output $job -nbJobs 25 -deptNumber %s -vectorPath %s -splitTileFolder $splitFolder -threads $nbcore -field %s\n\
qsub -W block=true $job\n\
bash mergeSubTilesDept.sh $outpath $deptNumber $IOTAPATH\n\
cd $PYPATH\n\
python stats_extract.py -wd $TMPDIR -in "$outpath"/dept_"$deptNumber"/sample_extract.sqlite -out "$outpath" -ndept $deptNumber\n\
python ogr_extract.py -wd $TMPDIR -vecteur "$outpath"/dept_"$deptNumber"/dept"$deptNumber".shp -stats "$outpath"/dept_"$deptNumber"/stats.csv -out $finaloutpath -ndept $deptNumber\n\
'%(jobname, ndept, nbcore, outputlog, errorlog, nbcore, depts, ndept, out, " ".join(list_files_tiles), ndept, out, depts, ndeptcond, nbcore, finalout, ndept, vectorclassif, field))
    jobFile.close()

    return jobPath

def generateJobCorse(jobPath, list_files_tiles, ndept, depts, out, nbcore, finalout, jobname, field):

    outputlog = out + '/' + 'dept_' + str(ndept) + '/' + '%s_output_'%(jobname) + str(ndept)
    errorlog = out + '/' + 'dept_' + str(ndept) + '/' + '%s_error_'%(jobname) + str(ndept)
    vectorclassif = out + '/' + 'dept_' + str(ndept) + '/' + 'dept' + str(ndept) + '.shp'

    if int(ndept) < 10:
        ndeptcond = '0' + str(ndept)
    else:
        ndeptcond = str(ndept)
    
    jobFile = open(jobPath,"w")
    jobFile.write('#!/bin/bash\n\
#PBS -N %s%s\n\
#PBS -l select=1:ncpus=%s:mem=60000mb\n\
#PBS -l walltime=50:00:00\n\
#PBS -o %s\n\
#PBS -e %s\n\
\n\
module load python/2.7.12\n\
\n\
source /work/OT/theia/oso/OTB/otb_superbuild/otb_superbuild-5.10.1-Release-install/config_otb.sh\n\
export PYTHONPATH=${PYTHONPATH}:/home/qt/thierionv/vector_tools\n\
PYPATH=/home/qt/thierionv/simplification/post-processing-oso/script_oso/\n\
IOTAPATH=/home/qt/thierionv/chaineIOTA/scripts/common/\n\
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=%s\n\
cd $PYPATH\n\
\n\
cmd="python mergeTileShapes.py -wd $TMPDIR -extract %s -ndept %s -out %s -listTiles %s -grass /work/OT/theia/oso/OTB/GRASS/grass7.2.1svn-x86_64-pc-linux-gnu-13_03_2017"\n\
echo $cmd\n\
eval $cmd\n\
\n\
cp /work/OT/theia/oso/vecteurCorse/final/Classif_Seed_0.tif $TMPDIR\n\
cp /work/OT/theia/oso/vecteurCorse/final/Confidence_Seed_0.tif $TMPDIR\n\
cp /work/OT/theia/oso/vecteurCorse/final/PixelsValidity.tif $TMPDIR\n\
deptNumber=%s\n\
outpath=%s\n\
vectordept=%s\n\
deptNumberStr=%s\n\
nbcore=%s\n\
finaloutpath=%s\n\
\n\
mkdir -p "$outpath"/dept_"$deptNumber"/splits\n\
\n\
python extractAndSplit.py -workingDirectory $TMPDIR -Y 5 -X 5 -out.name Classif_dept_"$deptNumber" -out.directory "$outpath"/dept_"$deptNumber"/splits -dataFieldValue $deptNumberStr -field CODE_DEPT -in.vector $vectordept -in.raster $TMPDIR/Classif_Seed_0.tif -threads $nbcore\n\
python extractAndSplit.py -workingDirectory $TMPDIR -Y 5 -X 5 -out.name Confidence_dept_"$deptNumber" -out.directory "$outpath"/dept_"$deptNumber"/splits -dataFieldValue $deptNumberStr -field CODE_DEPT -in.vector $vectordept -in.raster $TMPDIR/Confidence_Seed_0.tif -threads $nbcore\n\
python extractAndSplit.py -workingDirectory $TMPDIR -Y 5 -X 5 -out.name PixelsValidity_dept_"$deptNumber" -out.directory "$outpath"/dept_"$deptNumber"/splits -dataFieldValue $deptNumberStr -field CODE_DEPT -in.vector $vectordept -in.raster $TMPDIR/PixelsValidity.tif -threads $nbcore\n\
\n\
job="$outpath"/dept_"$deptNumber"/splits/job.pbs\n\
splitFolder="$outpath"/dept_"$deptNumber"/splits\n\
python generateJobsZonalStats.py -output $job -nbJobs 25 -deptNumber %s -vectorPath %s -splitTileFolder $splitFolder -threads $nbcore -field %s\n\
qsub -W block=true $job\n\
bash mergeSubTilesDept.sh $outpath $deptNumber $IOTAPATH\n\
cd $PYPATH\n\
python stats_extract.py -wd $TMPDIR -in "$outpath"/dept_"$deptNumber"/sample_extract.sqlite -out "$outpath" -ndept $deptNumber\n\
python sqlite_join.py -wd $TMPDIR -shape "$outpath"/dept_"$deptNumber"/dept"$deptNumber".shp -stats "$outpath"/dept_"$deptNumber"/stats.csv -outshape departement_"$deptNumber".shp -ndept $deptNumber -out $outpath\n\
'%(jobname, ndept, nbcore, outputlog, errorlog, nbcore, depts, ndept, out, " ".join(list_files_tiles), ndept, out, depts, ndeptcond, nbcore, finalout, ndept, vectorclassif, field))
    jobFile.close()

    return jobPath

def generateJobPartiel(jobPath, list_files_tiles, ndept, depts, out, nbcore):

    outputlog = out + '/' + 'dept_' + str(ndept) + '/' + 'shapeDept_output_' + str(ndept)
    errorlog = out + '/' + 'dept_' + str(ndept) + '/' + 'shapeDept_error_' + str(ndept)
    vectorclassif = out + '/' + 'dept_' + str(ndept) + '/' + 'departement_' + str(ndept) + '.shp'

    if int(ndept) < 10:
        ndeptcond = '0' + str(ndept)
    else:
        ndeptcond = str(ndept)
    
    jobFile = open(jobPath,"w")
    jobFile.write('#!/bin/bash\n\
#PBS -N shapeDept%s\n\
#PBS -l select=1:ncpus=%s:mem=60000mb\n\
#PBS -l walltime=200:00:00\n\
#PBS -o %s\n\
#PBS -e %s\n\
\n\
module load python/2.7.12\n\
\n\
source /work/OT/theia/oso/OTB/otb_superbuild/otb_superbuild-5.10.1-Release-install/config_otb.sh\n\
export PYTHONPATH=${PYTHONPATH}:/home/qt/thierionv/vector_tools\n\
PYPATH=/home/qt/thierionv/simplification/post-processing-oso/script_oso/\n\
IOTAPATH=/home/qt/thierionv/chaineIOTA/scripts/common/\n\
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=%s\n\
cd $PYPATH\n\
cp /work/OT/theia/oso/classifications/France_S2_AllFeatures_CropMix2/final/Classif_Seed_0.tif $TMPDIR\n\
cp /work/OT/theia/oso/classifications/France_S2_AllFeatures_CropMix2/final/Confidence_Seed_0.tif $TMPDIR\n\
cp /work/OT/theia/oso/classifications/France_S2_AllFeatures_CropMix2/final/PixelsValidity.tif $TMPDIR\n\
deptNumber=%s\n\
outpath=%s\n\
vectordept=%s\n\
deptNumberStr=%s\n\
nbcore=%s\n\
\n\
mkdir -p "$outpath"/dept_"$deptNumber"/splits\n\
\n\
python extractAndSplit.py -workingDirectory $TMPDIR -Y 5 -X 5 -out.name Classif_dept_"$deptNumber" -out.directory "$outpath"/dept_"$deptNumber"/splits -dataFieldValue $deptNumberStr -field CODE_DEPT -in.vector $vectordept -in.raster $TMPDIR/Classif_Seed_0.tif -threads $nbcore\n\
python extractAndSplit.py -workingDirectory $TMPDIR -Y 5 -X 5 -out.name Confidence_dept_"$deptNumber" -out.directory "$outpath"/dept_"$deptNumber"/splits -dataFieldValue $deptNumberStr -field CODE_DEPT -in.vector $vectordept -in.raster $TMPDIR/Confidence_Seed_0.tif -threads $nbcore\n\
python extractAndSplit.py -workingDirectory $TMPDIR -Y 5 -X 5 -out.name PixelsValidity_dept_"$deptNumber" -out.directory "$outpath"/dept_"$deptNumber"/splits -dataFieldValue $deptNumberStr -field CODE_DEPT -in.vector $vectordept -in.raster $TMPDIR/PixelsValidity.tif -threads $nbcore\n\
\n\
job="$outpath"/dept_"$deptNumber"/splits/job.pbs\n\
splitFolder="$outpath"/dept_"$deptNumber"/splits\n\
python generateJobsZonalStats.py -output $job -nbJobs 25 -deptNumber %s -vectorPath %s -splitTileFolder $splitFolder\n\
qsub -W block=true $job\n\
bash mergeSubTilesDept.sh $outpath $deptNumber $IOTAPATH\n\
cd $PYPATH\n\
python stats_extract.py -wd $TMPDIR -in "$outpath"/dept_"$deptNumber"/sample_extract.sqlite -out "$outpath" -ndept $deptNumber\n\
python ogr_extract.py -wd $TMPDIR -vecteur "$outpath"/dept_"$deptNumber"/departement_"$deptNumber".shp -stats "$outpath"/dept_"$deptNumber"/stats.csv -out $outpath -ndept $deptNumber\n\
jobcorrect=job_correct_"$deptNumber".pbs\n\
python genCorrectStats.py -output $jobcorrect -deptNumber $deptNumber -core $nbcore\n\
qsub $jobcorrect\n\
'%(ndept, nbcore, outputlog, errorlog, nbcore, ndept, out, depts, ndeptcond, nbcore,ndept, vectorclassif))
    jobFile.close()

    return jobPath

def generateJobPartielStats(jobPath, list_files_tiles, ndept, depts, out, nbcore):

    outputlog = out + '/' + 'dept_' + str(ndept) + '/' + 'shapeDept_output_' + str(ndept)
    errorlog = out + '/' + 'dept_' + str(ndept) + '/' + 'shapeDept_error_' + str(ndept)
    vectorclassif = out + '/' + 'dept_' + str(ndept) + '/' + 'departement_' + str(ndept) + '.shp'

    if int(ndept) < 10:
        ndeptcond = '0' + str(ndept)
    else:
        ndeptcond = str(ndept)
    
    jobFile = open(jobPath,"w")
    jobFile.write('#!/bin/bash\n\
#PBS -N shapeDept%s\n\
#PBS -l select=1:ncpus=%s:mem=60000mb\n\
#PBS -l walltime=200:00:00\n\
#PBS -o %s\n\
#PBS -e %s\n\
\n\
module load python/2.7.12\n\
\n\
source /work/OT/theia/oso/OTB/otb_superbuild/otb_superbuild-5.10.1-Release-install/config_otb.sh\n\
export PYTHONPATH=${PYTHONPATH}:/home/qt/thierionv/vector_tools\n\
PYPATH=/home/qt/thierionv/simplification/post-processing-oso/script_oso/\n\
IOTAPATH=/home/qt/thierionv/chaineIOTA/scripts/common/\n\
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=%s\n\
cd $PYPATH\n\
\n\
cmd="python mergeTileShapes.py -wd $TMPDIR -extract %s -ndept %s -out %s -listTiles %s"\n\
echo $cmd\n\
eval $cmd\n\
\n\
deptNumber=%s\n\
outpath=%s\n\
vectordept=%s\n\
deptNumberStr=%s\n\
nbcore=%s\n\
python ogr_extract.py -wd $TMPDIR -vecteur "$outpath"/dept_"$deptNumber"/departement_"$deptNumber".shp -stats "$outpath"/dept_"$deptNumber"/stats.csv -out $outpath -ndept $deptNumber\n\
jobcorrect=job_correct_"$deptNumber".pbs\n\
python genCorrectStats.py -output $jobcorrect -deptNumber $deptNumber -core $nbcore\n\
qsub $jobcorrect\n\
'%(ndept, nbcore, outputlog, errorlog, nbcore, depts, ndept, out, " ".join(list_files_tiles), ndept, out, depts, ndeptcond, nbcore))
    jobFile.close()

    return jobPath


if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
 
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Check vector tiles availability"\
        " and prepare cluster jobs for merge tiles by department")
                                
        parser.add_argument("-grid", dest="grid", action="store", \
                                help="grid name", required = True)
                                
        parser.add_argument("-depts", dest="depts", action="store", \
                                help="departements shapefile", required = True)

        parser.add_argument("-voisins", dest="voisins", action="store", \
                                help="neighbors name directory", required = True)        
        
        parser.add_argument("-out", dest="out", action="store", \
                                help="out name directory", required = True)

        parser.add_argument("-nbcore", dest="core", action="store", \
                                help="CPU number to execute job", required = True)        

        parser.add_argument("-finalout", dest="finalout", action="store", \
                                help="final outpath directory", required = True)

        parser.add_argument("-jobname", dest="jobname", action="store", \
                                help="jobname prefix", required = True)
        
        parser.add_argument("-field", dest="field", action="store", \
                            help="Classe field name", default = "value",required = False)          
        
	args = parser.parse_args()
        
        checkTile(args.depts, args.grid, args.voisins, args.out, args.core, args.finalout, args.jobname, args.field)
