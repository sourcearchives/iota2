path="/home/donatien/4_Simplification/Donnees/classifsS2_simplif/nodataTest"
oso_main="/home/donatien/4_Simplification/git/script_oso/OSO_main.py"
list_tiles_process="/home/donatien/4_Simplification/git/script_oso/list_tiles_process.py"
job_tif="/home/donatien/4_Simplification/git/script_oso/job_tif_v2.py"
job_simplification="/home/donatien/4_Simplification/git/script_oso/job_simplification.py"
oso_extract="/home/donatien/4_Simplification/git/script_oso/OSO_extract.py"
zonal_stats_otb="/home/donatien/4_Simplification/git/script_oso/zonal_stats_otb.py"
stats_extract="/home/donatien/4_Simplification/git/script_oso/stats_extract.py"
ogr_extract="/home/donatien/4_Simplification/git/script_oso/sqlite_join.py"
grasslib="/usr/lib/grass72"

classification_brut=nodata.tif
validity=validity_rodez.tif 
confidence=confidence_rodez.tif 
output_directory=/home/donatien/4_Simplification/Donnees/classifsS2_simplif/nodataOut
douglas=10
hermite=10
nbcore=3
strippe=2
umc1=10
umc2=3
resample_size=20
nbprocess=4
xygrid=4
ngrid=10
departements=/home/donatien/4_Simplification/Donnees/classifsS2_simplif/strasbourg_refonte/FranceDepartements.shp
otb_version=5.10
doregul=True
ndept=12

python ${oso_main} -wd ${path} -in ${path}/${classification_brut} -nbcore ${nbcore} -strippe ${strippe} -umc1 ${umc1} -umc2 ${umc2} -log log.csv -tmp False -regul ${doregul} -nbprocess ${nbprocess} -grid ${xygrid} -cluster True -rssize ${resample_size} -out ${output_directory} -mer ${path}/masque_mer.shp -clump otb

#liste les tuiles à traiter
python ${list_tiles_process} -wd ${path} -in ${output_directory}/classif_clump_regularisee.tif -nbcore ${nbcore} -strippe ${strippe} -grid ${output_directory}/grille.shp -out ${output_directory}

#parallele
python ${job_tif} -wd ${path} -in ${output_directory}/classif_clump_regularisee.tif -nbcore ${nbcore} -strippe ${strippe} -grid ${output_directory}/grille.shp -ngrid ${ngrid} -out ${output_directory} -cluster

#parallele
python ${job_simplification} -wd ${path} -grass ${grasslib} -in ${output_directory}/${ngrid}/outfiles/tile_${ngrid}.tif -ngrid ${ngrid} -out ${output_directory} -douglas ${douglas} -hermite ${hermite} -angle True -resample False -tmp -cluster

#parallele
python ${oso_extract} -wd ${path} -grid ${output_directory}/grille.shp -extract ${departements} -out ${output_directory} -ndept ${ndept}

#parallele
python ${zonal_stats_otb} -wd ${path} -classif ${path}/${classification_brut} -vecteur ${output_directory}/dept_${ndept}/departement_${ndept}.shp -confid ${path}/${confidence} -validity ${path}/${validity} -nbcore ${nbcore} -strippe ${strippe} -otbversion ${otb_version} -out ${output_directory} -ndept ${ndept}

#parallele
python ${stats_extract} -wd ${path} -in ${output_directory}/dept_${ndept}/sample_extract.sqlite -out ${output_directory} -ndept ${ndept}

#parallele
python ${ogr_extract} -wd ${path} -vecteur ${output_directory}/dept_${ndept}/departement_${ndept}.shp -stats ${output_directory}/dept_${ndept}/stats.csv -out /home/donatien/4_Simplification/Donnees/classifsS2_simplif/output_directory/out/dept_64 -ndept ${ndept}

#stats confusion matrix
python ValidOTB.py -class /home/donatien/4_Simplification/Donnees/classifsS2_simplif/strasbourg_refonte/bayonne.tif -ref /home/donatien/4_Simplification/Donnees/classifsS2_simplif/output_directory/10/outfiles/tile_10.shp -reff value -cm confusion

#read_Conf
python Read_confMat.py -path.matrix /home/donatien/4_Simplification/Donnees/classifsS2_reechant/bayonne/OSORR20MSD10H10_Bayonne/confusionMatrixOSORR20MSD10H10Bayonne -path.classes /home/donatien/4_Simplification/git_oso/script_stats/classes -level niv1 -out /home/donatien/4_Simplification/Donnees/classifsS2_reechant/bayonne/OSORR20MSD10H10_Bayonne/confMat_OSORR20MSD10H10_Bayonne.png -v -title "OSORR20MSD10H10_Bayonne"


#recuperer les logs, classif_clump_regularisee.tif, le dossier out_extract, les dossiers tuiles (0 a n)

#slqitejoin
python /home/donatien/4_Simplification/git/script_oso/sqlite_join.py -wd ${path} -shape ${output_directory}/dept_${ndept}/departement_${ndept}.shp -stats ${output_directory}/dept_${ndept}/stats.csv -outshape departement_${ndept}.shp -ndept ${ndept} -out ${output_directory}

#parallel python pour chaine hors cluster jusqua simplifciation
python ${oso_main} -wd ${path} -in ${path}/${classification_brut} -nbcore ${nbcore} -strippe ${strippe} -umc1 ${umc1} -umc2 ${umc2} -log log.csv -regul ${doregul} -nbprocess ${nbprocess} -grid ${xygrid} -cluster False -rssize ${resample_size} -out ${output_directory} -mer ${path}/masque_mer.shp -nbprocess 3 -grass ${grasslib} -douglas ${douglas} -hermite ${hermite} -angle True -resample False -clump scikit

#genTileEntititesExtent
python /home/qt/thierionv/simplification/post-processing-oso/script_oso/genTileEntitiesExtent.py -wd /home/qt/thierionv/simplification/out/ -in /work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/classif_clump_regularisee.tif -grid /work/OT/theia/oso/classifications/Simplification/FranceEntiere/otb/grille.shp -out /home/qt/thierionv/simplification/out/results/ -env enveloppes_France.shp

