path="/home/donatien/4_Simplification/Donnees/classifsS2_simplif/strasbourg_refonte/"
scriptsimplif="/home/donatien/4_Simplification/git_oso/script_oso/OSO_main.py"
grasslib="/usr/lib/grass72"
scriptextract="/home/donatien/4_Simplification/git_oso/script_oso/OSO_extract.py"
classification=narbonne.tif
nbcore=4
strippe=2
umc1=10
umc2=3
resample_size=20
nbprocess=4
xygrid=4
cluster=False
ngrid=10
zone_extract="zone.shp"
otb_version=5.8
tmp=False
validity=validity_narbonne.tif
confidence=confidence_narbonne.tif
out_extract="normandie"
douglas=10
hermite=10
doregul=True


python ${scriptsimplif} -wd ${path} -in ${path}${classification} -nbcore ${nbcore} -strippe ${strippe} -umc1 ${umc1} -umc2 ${umc2} -log log.csv -tmp ${tmp} -regul ${doregul} -nbprocess ${nbprocess} -grid ${xygrid} -cluster ${cluster} -grass ${grasslib} -douglas ${douglas} -hermite ${hermite} -angle True -resample False -rssize ${resample_size}

python ${scriptextract} -wd ${path} -nbcore ${nbcore} -strippe ${strippe} -grid "grille.shp" -extract ${zone_extract} -out ${out_extract} -classif ${path}${classification} -valid ${path}${validity} -clsfier ${path}${confidence} -otbversion ${otb_version} -cluster ${cluster}


