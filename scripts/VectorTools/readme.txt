1. vector_functions.py
Description : Ce script contient différents fonctions qui sont communes à tous les autres
scripts de traitement de données, par exemple, ouvrir un fichier, copier des entités, faire la
copie d'un shapefile, etc ... De la même manière, on peut faire tourner différentes traitements avec des différentes options. -v : Vérifier la validité des geometries -e : Vérifier s'il y a des géometries "vides" -i : Vérifier si les géometries d'un même fichier s'intersectent entre elles
Usage : python /vector_functions.py file.shp -v
2. AddFieldArea.py
Description : Permet d'ajouter une nouvelle colone que calcule la surface en pixels de chaque entité.
Usage : python /AddFieldArea.py <file.shp> <fieldID> <size one pixel in m2>
3. AddFieldID.py
Description : Permet d'ajouter une nouvelle colone "ID" à chaque entité.
Usage : python /AddFieldID.py <file.shp>
4. BufferOgr.py
Description : Permet de faire un buffer négatif ou positif.
Usage : python /BufferOgr.py <file.shp> <filebuffer.shp> <buffer_distance>
5. ChangeNameField.py
Description : Permet de changer le nom d'une colonne dans un shapefile.
Usage : python /ChangeNameField.py <file.shp> <fieldin> <fieldout>
6. CountFeature.py
Description : Retourne le nombre d'entités dans un shapefile.
Usage : python /CountFeature.py <file.shp>
7. CountNbPolByAtt.py
Description : Retourne le nombre d'entités par classe d'un shapefile.
Usage : python /CountNbPolByAtt.py <file.shp> <attribute_field>
1
8. DeleteDuplicateGeometries.py
Description : Supprime les geometries en double dans un shapefile et créé un nouveau fichier.
Usage : python /DeleteDuplicateGeometries.py <file.shp>
9. DeleteField.py
Description : Permet d'éliminer une colonne dans un shapefile.
Usage : python /DeleteField.py <file.shp> <attribute_field>
10. FileByClass.py
Description : Créé un fichier de polygones indépendant par classe
Usage : python /FileByClass.py <file.shp> <attribute_field> <output_path>
11. InvertSelection.py
12. KeepCommonFeature.py
Description : Compare deux shapefiles et créé un nouveau avec les entités qui sont communes et qui ont le même valeur pour une colonne designée.
Usage : python /KeepCommonFeature.py <file1.shp> <file2.shp> <field_shp1> <field_shp2>
13. ListValuesField.py
Usage : python /ListValuesField.py <file1.shp>
14. MergeFiles.py
Description : Permet la fusion de différents shapefiles.
Usage : python /MergeFiles.py <mergedfilename> <output_path> <list of files >
15. MultiPolyToPoly.py
Description : Convertie les entités multi-polygone en polygone.
Usage : python /MultiPolyToPoly.py <filein.shp> <fileout.shp>
16. PolyToMultiPoly.py
Description : Convertie les entités polygone en multi-polygone.
Usage : python /
17. Pol_in_Pixels.py
Description : Retourne l'équivalence de la surface de polygones en pixels.
Usage : python /Pol_in_Pixels.py <file.shp> <size of pixel>
18. RandomSelectionPolygons.py
Description : Permet de faire des tirages aléatoires d'un shapefile et créé des fichiers pour l'apprentissage et la validation d'après un pourcentage donné. Ce pourcentage d'éntrée correspond à l'apprentissage et le pourcentage restant sera mis dans le fichier validation.
(Si 40% = 40% pour le fichier apprentissage et 60% pour le fichier validation)
Usage : python /RandomSelectionPolygons.py <file.shp> <attribute_field> <nb_draws>
<percentage> <output path>
19. SelectBySize.py
Description : Permet de faire une séléction basée sur une requete sur la taille de polygones.
Usage : python /SelectBySize.py <file.shp> <Area> <1>
20. SelecNbPol.py
Description : Permet de faire des tirages aléatoires d'un shapefile pour l'apprentissage et la validation en nombre de polygones.
Usage : python /SelecNbPol.py <file.shp> <attribute_field> <outpath> <nb_polygons>
21. SelecByPerc.py
Description : Permet de faire un séléction aléatoire de l'ensemble de polygones 
Usage : python /SelecByPerc.py <file.shp> <attribute_field> <percentage> <outpath>
22. ToDataModelSudFrance.py
Description : Permet de convertir un shapefile dans le modèle de données utilisé dans le cadre de CES-OSO.
Usage : python /ToDataModelSudFrance.py <outfilename> <EPSGCode> <infile.shp>
23. ToDataModel.py
Description : Permet de convertir un shapefile dans le modèle de données utilisé dans le cadre de S2-Agri.
Usage : python /ToDataModel.py <outfilename> <EPSGCode> <infile.shp>

24. DifferenceQGIS.py
Description : Permet de calculer la dfférence géometrique entre deux shapefiles.
Usage : python /DfferenceQGIS.py <file1.shp> <file2.shp> <outfile.shp>
25. IntersectionQGIS.py
Description : Permet de calculer l'intersection entre deux shapefiles.
Usage : python /IntersectionQGIS.py <file1.shp> <file2.shp> <outfile.shp>



