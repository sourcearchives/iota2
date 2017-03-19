
Scripts généraux
---

__vector_functions.py__

	Description: Ce script contient différents fonctions qui sont communes à tous les autres. Scripts de traitement de données, par exemple, ouvrir un fichier, copier des entités, faire la copie d'un shapefile, etc ... Il permet aussi de valider la géométrie d'un fichier shapefile : -v : Vérifier la validité des geometries -e : Vérifier s'il y a des géometries vides -i : Vérifier si les géometries d'un même fichier s'intersectent entre elles

	Usage : vector_functions.py <file.shp> -v

__AddField.py__

	Description: Ce script permet d'ajouter un nouveau champ d'un fichier shapefile et de remplir chaque enregistrement avec une valeur

	Usage : AddField.py <file.shp> <fieldName> <value>

__AddFieldArea.py__

	Description: Permet d'ajouter une nouvelle colone que calcule la surface en pixels de chaque entité.

	Usage : AddFieldArea.py <file.shp> <fieldID> <size one pixel in m2>

__AddFieldID.py__

	Description: Permet d'ajouter une nouvelle colone ID à chaque entité.

	Usage : AddFieldID.py <file.shp>

__AreaPolyinPoly.py__

	Description: Pour chaque entité dun fichier, calcule la surface intersecté par les entités d'un deuxième fichier. 

	Usage : AreaPolyinPoly.py <file1.shp> <file2.shp>

__BufferOgr.py__

	Description: Permet de faire un buffer négatif ou positif d'un fichier shapefile existant et de recopier les attributs du fichier en entrée 

	Usage : BufferOgr.py <file.shp> <filebuffer.shp> <buffer_distance>

__ChangeNameField.py__

	Description : Permet de changer le nom d'une colonne dans un shapefile.

	Usage : ChangeNameField.py <file.shp> <fieldin> <fieldout>

__CountFeature.py__

	Description: Retourne le nombre d'entités dans un shapefile.

	Usage : CountFeature.py <file.shp>

__CountNbPolByAtt.py__

	Description: Retourne le nombre d'entités par classe d'un shapefile.

	Usage : CountNbPolByAtt.py <file.shp> <attribute_field>

__CountPolyinPoly.py__

	Description: Permet de compter le nombre d'entités d'un fichier intersectant les entités d'un autre fichier et créé une nouvelle colonne 'Count' avec le résultat.

	Usage : CountPolyinPoly.shp <shpfile1> <shpfile2>

__csv_to_shp.py__

	Description: Converti un fichier CSV en fichier de formes

	Usage : csv_to_shp.py <file.shp> <attribute_field>


__DeleteDuplicateGeometries.py__

	Description: Supprime les geometries en double dans un shapefile et créé un nouveau fichier.

	Usage : DeleteDuplicateGeometries.py <file.shp>

__DeleteField.py__

	Description: Permet d'éliminer une colonne dans un shapefile.

	Usage : DeleteField.py <file.shp> <attribute_field>

__FileByClass.py__

	Description: Créé un fichier de polygones indépendant par classe

	Usage : FileByClass.py <file.shp> <attribute_field> <output_path>

__KeepCommonFeature.py__

	Description: Compare deux shapefiles et créé un nouveau avec les entités qui sont communes et qui ont le même valeur pour une colonne designée.

	Usage : KeepCommonFeature.py <file1.shp> <file2.shp> <field_shp1> <field_shp2>

__ListValuesField.py__

	Usage : ListValuesField.py <file1.shp>

__MergeFiles.py__

	Description: Permet la fusion de différents shapefiles.

	Usage : MergeFiles.py <mergedfilename> <output_path> <list of files >
	
__MultiPolyToPoly.py__

	Description: Convertie les entités multi-polygone en polygone.

	Usage : MultiPolyToPoly.py <filein.shp> <fileout.shp>

__PolyToMultiPoly.py__

	Description: Convertie les entités polygone en multi-polygone.

	Usage : 

__Pol_in_Pixels.py__

	Description: Retourne l'équivalence de la surface de polygones en pixels.

	Usage : Pol_in_Pixels.py <file.shp> <size of pixel>

__RandomInSituByTile.py__

	Description: Permet de faire des tirages aléatoires d'un shapefile et créé des fichiers pour l'apprentissage et la validation d'après un pourcentage donné. Ce pourcentage d'éntrée correspond à l'apprentissage et le pourcentage restant sera mis dans le fichier validation. (Si 40 = 40% pour le fichier apprentissage et 60% pour le fichier validation)
	Usage : RandomInSituByTile.py -shape <file.shp> -field <attribute_field> --sample <nb_sample> -ratio <percentage> -out <output path>

__SelectBySize.py__

	Description: Permet de faire une séléction basée sur une requete sur la taille de polygones.

	Usage : SelectBySize.py <file.shp> <Area> <1>

__SelecNbPol.py__

	Description: Permet de faire des tirages aléatoires d'un shapefile pour l'apprentissage et la validation en nombre de polygones.

	Usage : SelecNbPol.py <file.shp> <attribute_field> <outpath> <nb_polygons>

__SelecByPerc.py__

	Description: Permet de faire un séléction aléatoire de l'ensemble de polygones 

	Usage : SelecByPerc.py <file.shp> <attribute_field> <percentage> <outpath>

__SimplifyPoly.py__

	Description: Permet de simplifier les polygones avec une tolérance specifiée.

	Usage : SimplifyPoly.py <file1.shp> <tolerance>


__ToDataModelSudFrance.py__

	Description: Permet de convertir un shapefile dans le modèle de données utilisé dans le cadre de CES-OSO.

	Usage : ToDataModelSudFrance.py <outfilename> <EPSGCode> <infile.shp>

__ToDataModel.py__

	Description: Permet de convertir un shapefile dans le modèle de données utilisé dans le cadre de S2-Agri.

	Usage : ToDataModel.py <outfilename> <EPSGCode> <infile.shp>

__DifferenceQGIS.py__

	Description: Permet de calculer la dfférence géometrique entre deux shapefiles.
	
	Usage : DfferenceQGIS.py <file1.shp> <file2.shp> <outfile.shp>

__IntersectionQGIS.py__

	Description: Permet de calculer l'intersection entre deux shapefiles.

	Usage : IntersectionQGIS.py <file1.shp> <file2.shp> <outfile.shp>






