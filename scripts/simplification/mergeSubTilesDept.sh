#!/bin/bash

# /work/OT/theia/oso/vecteurCorse/versionModelCorsePlusBatiConti/results_vTest
# /home/qt/thierionv/chaineIOTA/scripts/common

sampleDirectory=$1/dept_$2/splits
listSample=($(ls -d $sampleDirectory/sample_extract*))
var=""
for ((i=0; i<${#listSample[@]}; i++)); do
    var=\"${listSample[$i]}\"","$var
done
listOfSample=${var:0:${#var}-1}
echo $listOfSample

IOTAPATH=$3
cd $IOTAPATH
folderOut=$TMPDIR
nameOut_tmp=sample_extract_tmp
nameOut=sample_extract
cmd="python -c 'from Common import FileUtils;fileUtils.mergeSQLite_cmd(\""$nameOut_tmp"\",\""$folderOut"\",$listOfSample)'"
echo $cmd
eval $cmd

ogr2ogr -f SQLite -a_srs EPSG:2154 "$folderOut"/"$nameOut".sqlite "$folderOut"/"$nameOut_tmp".sqlite

cp "$folderOut"/"$nameOut".sqlite $1/dept_$2/
