path="/home/donatien/4_Simplification/Donnees/classifsS2_simplif/strasbourg_refonte/"
oso_main="/home/donatien/4_Simplification/git_oso/script_oso/OSO_main.py"
job_tif="/home/donatien/4_Simplification/git_oso/script_oso/job_tif.py"
job_simplification="/home/donatien/4_Simplification/git_oso/script_oso/job_simplification.py"
oso_extract="/home/donatien/4_Simplification/git_oso/script_oso/OSO_extract.py"
zonal_stats_otb="/home/donatien/4_Simplification/git_oso/script_oso/zonal_stats_otb.py"
stats_extract="/home/donatien/4_Simplification/git_oso/script_oso/stats_extract.py"
ogr_extract="/home/donatien/4_Simplification/git_oso/script_oso/ogr_extract.py"
grasslib="/usr/lib/grass72"

classification_brut=narbonne.tif
validity=validity_narbonne.tif
confidence=confidence_narbonne.tif
out_extract="normandie"
douglas=10
hermite=10
nbcore=3
strippe=2
umc1=10
umc2=3
resample_size=20
nbprocess=4
xygrid=4
cluster=True
ngrid=10
zone_extract="zone.shp"
otb_version=5.8
tmp=False
doregul=True

python ${oso_main} -wd ${path} -in ${path}${classification_brut} -nbcore ${nbcore} -strippe ${strippe} -umc1 ${umc1} -umc2 ${umc2} -log log.csv -tmp ${tmp} -regul ${doregul} -nbprocess ${nbprocess} -grid ${xygrid} -cluster ${cluster} -rssize ${resample_size}

#parallele
python ${job_tif} -wd ${path} -in ${path}classif_clump_regularisee.tif -nbcore ${nbcore} -strippe ${strippe} -grid grille.shp -ngrid ${ngrid} -out "outfiles" -tmp ${tmp} -cluster ${cluster}

#parallele
python ${job_simplification} -wd ${path} -grass ${grasslib} -in ${path}${ngrid}/outfiles/tile_${ngrid}.tif -ngrid ${ngrid} -out "outfiles" -douglas ${douglas} -hermite ${hermite} -angle True -resample False -tmp ${tmp} -cluster ${cluster}

#parallele
python ${zonal_stats_otb} -wd ${path}${ngrid}/outfiles/ -classif ${path}${classification_brut} -vecteur tile_${ngrid}.shp -confid ${path}${confidence} -validity ${path}${validity} -nbcore ${nbcore} -strippe ${strippe} -field "value" -otbversion ${otb_version} -tmp ${tmp} -independant True -ngrid ${ngrid}

#parallele
python ${stats_extract} -wd ${path}${ngrid}/outfiles/ -in ${path}${ngrid}/outfiles/sample_extract.sqlite -tmp ${tmp} -independant True -ngrid ${ngrid}

#parallele
python ${ogr_extract} -wd ${path}${ngrid}/outfiles/ -in tile_${ngrid}.shp -tmp ${tmp} -independant True

#parallele
python ${oso_extract} -wd ${path} -nbcore ${nbcore} -strippe ${strippe} -grid "grille.shp" -extract ${zone_extract} -out ${out_extract} -classif ${path}${classification_brut} -valid ${path}${validity} -clsfier ${path}${confidence} -otbversion ${otb_version} -cluster ${cluster} -independant True

#recuperer les logs, classif_clump_regularisee.tif, le dossier out_extract, les dossiers tuiles (0 a n)
