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

import sys
import os
import argparse
from shutil import copyfile
from math import sqrt
from config import Config
import ogr

import vector_functions as vf
import FileByClass
import AddFieldID
import AddField
import AddFieldArea
import DeleteField
import DeleteDuplicateGeometries
import BufferOgr
import MultiPolyToPoly
import SelectBySize
import MergeFiles
import Intersection
import shapeDifference
import RandomInSituByTile
import CreateGrid
import checkGeometryAreaThreshField

def connect_db(user, database, host, port, password, schema):     
    try:
        connString = "PG: host=%s dbname=%s user=%s password=%s port=%s" %(host,database,user,password,port)     
        conn = ogr.Open(connString)
    except:
        print "I am unable to connect to the database"
    
    return conn    

def read_config_file(Fileconfig):

    f = file(Fileconfig)    
    return Config(f)


def get_sources(cfg):
    
    sources = {}
    
    for classe in cfg.Nomenclature:
        if not isinstance(cfg.Nomenclature[classe].Source, str):
            key = cfg.Nomenclature[classe].Source[0]+ '_' + cfg.Nomenclature[classe].Source[1]
        else:
            key = cfg.Nomenclature[classe].Source

        if key not in sources.keys():
            sources[key] = []
            sources[key].append(classe)
        else:
            sources[key].append(classe)

    return sources

def manageFieldShapefile(shapefile, value, areapix):
  
    # Liste des champs existants
    fieldList = vf.getFields(shapefile)

    # Creation d'un FID unique
    if 'ID' in fieldList:
        DeleteField.deleteField(shapefile, 'ID')
        AddFieldID.addFieldID(shapefile)
        fieldList.remove('ID')
    else:
        AddFieldID.addFieldID(shapefile)

    if cfg.parameters.landCoverField in fieldList:
        DeleteField.deleteField(shapefile, cfg.parameters.landCoverField)
        AddField.addField(shapefile, cfg.parameters.landCoverField, value)
        fieldList.remove(cfg.parameters.landCoverField)
    else:
        AddField.addField(shapefile, cfg.parameters.landCoverField, value)

    if 'Area' in fieldList:
        DeleteField.deleteField(shapefile, 'Area')
        AddFieldArea.addFieldArea(shapefile, areapix)
        fieldList.remove('Area')
    else:
        AddFieldArea.addFieldArea(shapefile, areapix)

    # Suppression des champs initiaux
    for field in fieldList:
        DeleteField.deleteField(shapefile, field)

def gestionFields(cfg, classe, source, ss_source):

    chpValue = []
    if source in cfg.Nomenclature[classe].Source:
        if isinstance(cfg.Nomenclature[classe].Source, config.Sequence):
            indSource = list(cfg.Nomenclature[classe].Source).index(source)
        else:
            if source in cfg: 
                if isinstance(cfg.Nomenclature[classe][source], config.Sequence):
                    indSource = list(cfg.Nomenclature[classe][source]).index(ss_source)

        if isinstance(cfg.Nomenclature[classe].Champs, config.Sequence):
            chp = cfg.Nomenclature[classe].Champs[indSource]
            if isinstance(chp, config.Sequence):
                for i in range(len(chp)):
                    chpValue.append([chp[i], cfg.Nomenclature[classe].CodesSource[indSource][i]])
            else:
                chpValue.append([chp, cfg.Nomenclature[classe].CodesSource[indSource]])
        else:
            chpValue.append([cfg.Nomenclature[classe].Champs, cfg.Nomenclature[classe].CodesSource])

        return chpValue

def gestionSources(cfg, classe, source):
    
    if (cfg.globalPath[source] == 'Database'):
        return lyr, source, field, "database"
    else:
        multival = False
        chpValue = []
        pathList = []
        if source in cfg:
            typesources = cfg.Nomenclature[classe][source]
            if isinstance(typesources, config.Sequence):
                chpValues = []
                for typesource in typesources:
                    filesources = cfg[source][typesource]
                    if isinstance(filesources, config.Sequence):
                        for filesource in filesources:
                            pathList.append(cfg.globalPath[source] + '/' + filesource)
                            chpValue = gestionFields(cfg, classe, source, None)
                    else:
                        multival = True
                        pathList.append(cfg.globalPath[source] + '/')
                        chpValue = gestionFields(cfg, classe, source, typesource)
                        chpValues.append([typesource, filesources, chpValue])
            else:
                filesources = cfg[source][typesources]
                if isinstance(filesources, config.Sequence):
                    for filesource in filesources:
                        pathList.append(cfg.globalPath[source] + '/' + filesource)
                        chpValue = gestionFields(cfg, classe, source, None)
                else:
                    pathList.append(cfg.globalPath[source] + '/' + filesources)
                    chpValue = gestionFields(cfg, classe, source, None)
        else:
            pathList.append(cfg.globalPath[source])
            chpValue = gestionFields(cfg, classe, source, None)

        if multival:
            return pathList, source, chpValues, 'complexe'
        else:
            return pathList, source, chpValue, 'simple'


def gestionTraitementsClasse(cfg, layer, outfile, classe, ss_classe, source, res, area_thresh, pix_thresh, \
                             chp = None, value = None, buff = None):

    if ss_classe not in cfg.parameters.maskLineaire:
        if chp is not None:
            FileByClass.FileByClass(layer, chp, value, outfile)
                
        if os.path.exists(outfile):
            
            manageFieldShapefile(outfile, cfg.Nomenclature[classe].Code, area_thresh)

            # Verification de la géométrie
            vf.checkValidGeom(outfile)            
                        
            # suppression des doubles géométries
            outfile_ssdb = DeleteDuplicateGeometries.DeleteDupGeom(outfile)

            # Gestion du buffer linéaire / surfacique / Erosion des polygones
            ds = vf.openToRead(outfile_ssdb)
            lyr = ds.GetLayer()
            typeGeom = lyr.GetGeomType()
            lyr = None
            if buff == "None" : buff = None
            # wkbLineString/wkbMultiLineString/wkbMultiLineString25D/wkbLineString25D
            if typeGeom in [2, 5, -2147483643, -2147483646] and buff is not None:
                outfile_buffline = outfile_ssdb[:-4] + 'buffline' + str(buff) + '.shp'
                BufferOgr.bufferPoly(outfile_ssdb, outfile_buffline, int(buff))
                outfile_buff = outfile_buffline
            # wkbPolygon/wkbMultiPolygon/wkbPolygon25D/wkbMultiPolygon25D
            elif typeGeom in [3, 6, -2147483645, -2147483642] and buff is not None: 
                outfile_buffsurf_tmp = outfile_ssdb[:-4] + 'buffsurf' + str(buff) + '_tmp.shp'
                outfile_buffsurf = outfile_ssdb[:-4] + 'buffsurf' + str(buff) + '.shp'
                BufferOgr.bufferPoly(outfile_ssdb, outfile_buffsurf_tmp, int(buff))
                BufferOgr.bufferPoly(outfile_buffsurf_tmp, outfile_buffsurf, -int(buff))
                outfile_buff = outfile_buffsurf
            else:
                outfile_buff = outfile_ssdb[:-4] + 'buffinv' + str(res) + '.shp'
                BufferOgr.bufferPoly(outfile_ssdb, outfile_buff, -int(res)) 
        
            # Suppression des multipolygons
            outfile_spoly = outfile_buff[:-4] + 'spoly' + '.shp'
            MultiPolyToPoly.multipoly2poly(outfile_buff, outfile_spoly)

            # recalcul des superficies
            AddFieldArea.addFieldArea(outfile_spoly, area_thresh)

            # Selection en fonction de la surface des polygones
            outfile_area = outfile_spoly[:-4] + 'sup' + str(pix_thresh) + 'pix.shp'
            SelectBySize.selectBySize(outfile_spoly, 'Area', pix_thresh, outfile_area)

            # Verification de la géométrie
            vf.checkValidGeom(outfile_area)    

            return outfile_area
        
        else:
            print 'Aucun échantillon pour la classe {} dans la base de données {}'.format(classe, source)
            return None  

    else:
        if chp is not None:
            FileByClass.FileByClass(layer, chp, value, outfile)

        # Gestion du buffer linéaire
        ds = vf.openToRead(layer)
        lyr = ds.GetLayer()
        typeGeom = lyr.GetGeomType()
        lyr = None
        if buff == "None" : buff = None
        if typeGeom in [2, 5, -2147483643, -2147483646] and buff is not None: 
            outfile_buff_mask = outfile[:-4] + 'buffline' + str(buff) + '_mask.shp'
            BufferOgr.bufferPoly(outfile, outfile_buff_mask, int(buff))
            os.system("ls {}".format(outfile_buff_mask))
            return outfile_buff_mask     
        else:
            print "la donnée n'est pas de type linéaire"
            return None
    
def gestionSamplesClasse(cfg, classe, source, ouputPath, res, area_thresh, pix_thresh, lineBuffer = None):

    if (cfg.globalPath[source] == 'Database'):
        # Connexion à la base et accès à la table 
        conn = connect_db(cfg.DataBase.user, cfg.DataBase[source].base, cfg.DataBase.host, \
                          cfg.DataBase.port, cfg.DataBase.pwd, cfg.DataBase[source].schema)
        lyr = conn.GetLayer('{}.{}'.format(cfg.DataBase[source].schema, cfg.DataBase[source].table))

        # Create shapefile (non testé)
        outshapefile = ouputPath + '/' + source + '_' + classe + '.shp'
        drv = ogr.GetDriverByName('ESRI Shapefile')
        outds = drv.CreateDataSource(outshapefile)
        outlyr = outds.CopyLayer(lyr, source + '_' + classe)
        
        # Champ a traiter
        field = cfg.DataBase[source].field

        # Valeur(s) à sélectionner
        values = list(cfg.Nomenclature[classe].CodesSource)
        
        # outfile
        outfile = ouputPath + '/' + source + '_' + classe + '.shp'
        
        # Creation du fichier 
        out = gestionTraitementsClasse(cfg, layer, outfile, classe, None, source, res, area_thresh, pix_thresh, field, values)

        # Deconnection
        lyrRPG = None
        conn = None
    else:        
        pathList, sourcedb, chpvalue, formatData = gestionSources(cfg, classe, source)
        # Creation d'un fichier shapefile par classe
        if type(chpvalue) != list or len(chpvalue) == 1:
            if chpvalue[0][0] == 'None':
                indfile = 1
                outpathList = []
                for path in pathList:
                    # Outfile names
                    if len(pathList) > 1:
                        outfile = ouputPath + '/' + sourcedb + '_' + classe + '_' + str(indfile) + '.shp'
                    else:
                        outfile = ouputPath + '/' + sourcedb + '_' + classe + '.shp'
                    
                    vf.copyShapefile(path, outfile)
                    out = gestionTraitementsClasse(cfg, path, outfile, classe,  None, source, res, area_thresh, pix_thresh, None, None, lineBuffer)
                    outpathList.append(out)
                    indfile += 1

                # merge files
                if len(pathList) > 1:                    
                    outpathListMerge = ouputPath + '/' + sourcedb + '_' + classe + '.shp'
                    MergeFiles.mergeVectors(outpathList, outpathListMerge)
                    out = None 
                    out = outpathListMerge
            else:
                indfile = 1
                outpathList = []
                for path in pathList:
                    # Outfile names
                    if len(pathList) > 1:
                        outfile = ouputPath + '/' + sourcedb + '_' + classe + '_' + str(indfile) + '.shp'
                    else:
                        outfile = ouputPath + '/' + sourcedb + '_' + classe + '.shp'

                    chp = chpvalue[0][0]
                    value = chpvalue[0][1]
                    out = gestionTraitementsClasse(cfg, path, outfile, classe,  None, source, res, area_thresh, pix_thresh, chp, value, lineBuffer)
                    outpathList.append(out)
                    indfile += 1

                if len(pathList) > 1:
                    outpathListMerge = ouputPath + '/' + sourcedb + '_' + classe + '.shp'
                    MergeFiles.mergeVectors(outpathList, outpathListMerge)
                    out = None 
                    out = outpathListMerge
        else:
            if len(chpvalue[0]) == 2: # une seule source plusieurs conditions vs. plusieurs sous-sources
                indfile = 0
                outpathList = []
                path = pathList[0]
                for expression in chpvalue:
                    if expression[1] == 'None':
                        print 'gestion directe'
                    else:
                        outfile = ouputPath + '/' + sourcedb + '_' + classe + '_' + str(indfile) + '.shp'
                        outpathList.append(outfile)
                        indfile += 1
                
                outpathList[len(outpathList) - 1] = ouputPath + '/' + sourcedb + '_' + classe + '.shp'
                nbfile = 0
                while nbfile < indfile:
                    if nbfile != 0:
                        path = outpathList[nbfile - 1]

                    chp = chpvalue[nbfile][0]
                    value = chpvalue[nbfile][1]
                    # cas des valeurs avec apostrophe 
                    #value = value.replace("'","''")
                    FileByClass.FileByClass(path, chp, value, outpathList[nbfile])
                    #os.system("ls {}".format(outpathList[nbfile]))
                    nbfile += 1

                out = gestionTraitementsClasse(cfg, path, outpathList[len(outpathList) - 1], \
                                               classe, None, source, res, area_thresh, pix_thresh, None, None, lineBuffer)
            else:
                indfile = 1
                out = []
                for expression in chpvalue:
                    if expression[2][0][0] == 'None':                        
                        outfile = ouputPath + '/' + sourcedb + '_' + classe + '_' + str(indfile) + '.shp'
                        infile = pathList[indfile - 1] + expression[1]
                        ss_classe = expression[0]

                        # copy file
                        vf.copyShapefile(infile, outfile)
                        output = gestionTraitementsClasse(cfg, infile, outfile, classe, ss_classe, \
                                                       source, res, area_thresh, pix_thresh, None, None, lineBuffer[indfile - 1])
                        out.append(output)
                        indfile += 1
                    else:                        
                        outfile = ouputPath + '/' + sourcedb + '_' + classe + '_' + str(indfile) + '.shp'

                        ss_classe = expression[0]

                        path = pathList[indfile - 1]
                            
                        if formatData == 'complexe':
                            path =  path + '/' + expression[1]
                            chp = expression[2][0][0]
                            value = expression[2][0][1]
                        else:
                            chp = expression[0]
                            value = expression[1]
                           
                        output = gestionTraitementsClasse(cfg, path, outfile, classe,  ss_classe, \
                                                           source, res, area_thresh, pix_thresh, chp, value, lineBuffer[indfile - 1])
                        out.append(output)
                        indfile += 1
                
    return out
                
def manageListSources(dictSources, path, key):
    if key not in dictSources.keys():
        dictSources[key] = [path]
    else:
        dictSources[key].append(path)

def clipFile(cfg, ouputPath, source):
    # cfg.parameters.cut
    try:
        fileToCut = cfg.globalPath[source]
    except:
        print "No path provide for {} datasource".format(source)
        sys.exit(-1)

    if fileToCut.lower() != 'database':
        baseFileToCut = os.path.splitext(os.path.basename(fileToCut))[0]
        outputCut = ouputPath + '/' + baseFileToCut + '_cut.shp'
        command = "ogr2ogr -clipsrc {} {} {}".format(cfg.globalPath.cutFile, outputCut, fileToCut)
        os.system(command)
    else:
        print "Clip of a database layer will be managed after database extraction"

def gestionFichierFinal(samples_shapefile_source, outfile_area, ouputPath, source, classe):
    if outfile_area is not None:
        if not isinstance(outfile_area, list):
            if 'mask' not in outfile_area:
                outpathfinal = '/'.join([ouputPath,'final']) + '/' + source + '_' + classe + '.shp'
                vf.copyShapefile(outfile_area, outpathfinal)
                manageListSources(samples_shapefile_source, outpathfinal, source)
            else:
                outpathfinal = '/'.join([ouputPath,'final']) + '/' + os.path.basename(outfile_area)
                vf.copyShapefile(outfile_area, outpathfinal)
                manageListSources(samples_shapefile_source, outpathfinal, source)
        else:
            for fileout in outfile_area:
                if 'mask' not in fileout:
                    outpathfinal = '/'.join([ouputPath,'final']) + '/' + source + '_' + classe + '.shp'
                    vf.copyShapefile(fileout, outpathfinal)
                    manageListSources(samples_shapefile_source, outpathfinal, source)
                else:
                    outpathfinal = '/'.join([ouputPath,'final']) + '/' + os.path.basename(fileout)
                    vf.copyShapefile(fileout, outpathfinal)
                    manageListSources(samples_shapefile_source, outpathfinal, source)

    return samples_shapefile_source

def gestion_echantillons(Fileconfig, ouputPath):

    cfg = read_config_file(Fileconfig)

    # Global parameters
    res = cfg.parameters.resolution
    area_thresh = int(res) * int(res)
    pix_thresh = cfg.parameters.spatialThreshold

    # Clip input vector files
    if cfg.parameters.cut != '':
        if isinstance(cfg.parameters.cut, config.Sequence):
            for sourceToCut  in cfg.parameters.cut:
                clipFile(cfg, ouputPath, sourceToCut)
        else:
            clipFile(cfg, ouputPath, cfg.parameters.cut)
            
    buff = False
    sources = get_sources(cfg)
    samples_shapefile_source = {}
    
    os.system("mkdir {}/{}".format(ouputPath,'final'))

    for source in sources:
        if source in cfg.globalPath or (source.split('_')[0] in cfg.globalPath and source.split('_')[1] in cfg.globalPath):
            for classe in sources[source]:

                try:
                    Buffer = cfg.Nomenclature[classe].Buffer
                    buff = True
                except:
                    pass
                
                if not '_' in source:
                    print 'Traitement de la base de données {} pour la classe {}'.format(source, classe)

                    if buff:
                        outfile_area = gestionSamplesClasse(cfg, classe, source, ouputPath, res, area_thresh, pix_thresh, Buffer)
                    else:
                        outfile_area = gestionSamplesClasse(cfg, classe, source, ouputPath, res, area_thresh, pix_thresh)

                    # gestion finale du fichier
                    gestionFichierFinal(samples_shapefile_source, outfile_area, ouputPath, source, classe)

                else:
                    complexDataSets = []
                    for sourceBD in source.split('_'):
                        print 'Traitement de la base de données {} pour la classe {}'.format(sourceBD, classe)

                        try:
                            Buffer = cfg.Nomenclature[classe].Buffer[source.split('_').index(sourceBD)]
                        except:
                            Buffer = None    

                        if buff and Buffer != 'None':
                            outfile_area = gestionSamplesClasse(cfg, classe, sourceBD, ouputPath, res, area_thresh, pix_thresh, Buffer)
                        else:
                            outfile_area = gestionSamplesClasse(cfg, classe, sourceBD, ouputPath, res, area_thresh, pix_thresh)
                        
                        if outfile_area is not None:
                            complexDataSets.append([sourceBD, outfile_area])
                    
                    # intersection des jeux de données
                    try:
                        priorSource = cfg.Nomenclature[classe].PrioTheme

                        if len([x for x in complexDataSets if priorSource == x[0]]) != 0:
                            priorPath = [x for x in complexDataSets if priorSource == x[0]][0][1]
                            secondPath = [x for x in complexDataSets if priorSource != x[0]][0][1]
                            secondSource = [x for x in complexDataSets if priorSource != x[0]][0][0]
                            if cfg.parameters.landCoverField not in vf.getFields(priorPath):
                                print 'No landcover field in {} data source'.format(priorSource)
                        else:
                            print "the priority source {} not present in sources list".format() 

                        if (priorPath is not None) and (secondPath is not None):
                            intersectFilename = ouputPath + '/inter_' + priorSource + '_' + secondSource + '_' +  classe + '.shp'
                            #Intersection.intersection(priorPath, secondPath, intersectFilename)
                            command = 'python /home/thierion/Documents/OSO/Dev/vector_tools/IntersectionQGIS.py {} {} {}'.\
                                      format(priorPath, secondPath, intersectFilename)
                            os.system(command)
                        else:
                            # pas d'intersection possible
                            if secondPath is None:
                                intersectFilename = priorPath
                            else:
                                "This case is not yet managed"
                                sys.exit(-1)
                    
                        # gestion des champs
                        # suppression des champs + génération Aire
                        fieldList = vf.getFields(intersectFilename)
                        idxLC = fieldList.index(cfg.parameters.landCoverField)
                        for field in fieldList:
                            if fieldList.index(field) != idxLC:
                                DeleteField.deleteField(intersectFilename, field)

                        AddFieldID.addFieldID(intersectFilename)
                        AddFieldArea.addFieldArea(intersectFilename, area_thresh)

                        samples_shapefile_source = gestionFichierFinal(samples_shapefile_source, intersectFilename, \
                                                                       ouputPath, source, classe)
                    except:
                        for dataset in complexDataSets:
                            samples_shapefile_source = gestionFichierFinal(samples_shapefile_source, dataset[1], \
                                                                           ouputPath, dataset[0], classe)
                    
                buff = False
        else:
            print "No Path for source {} provided while required for classes {}".format(source,sources[source])            

            
    # Fusion des echantillons des différents classes pour une source donnée

    dataSourcePriorities = {}
    listpriorities = list(cfg.parameters.priorities)

    maskToMerge = []
    outfilemergemask = ouputPath + '/final/' + cfg.parameters.samplesFileName + '_masks.shp'

    for keysource in samples_shapefile_source:
        outfilemerge = ouputPath + '/final/' + cfg.parameters.samplesFileName + '_' + keysource + '.shp'

        # séparer les couches linéaire de masquage / les couches inexistantes (pas d'échantillons)
        listToMerge = []
        for src in samples_shapefile_source[keysource]:
            if len(samples_shapefile_source[keysource]) != 0:
                if src is not None:
                    if 'mask' not in src:
                        listToMerge.append(src)
                    else:
                        maskToMerge.append(src)
                    
        # Merge des classes par source
        if len(listToMerge) != 0:
            MergeFiles.mergeVectors(listToMerge, outfilemerge)
        elif len(listToMerge) == 1:
            vf.copyShapefile(listToMerge[0], outfilemerge)
        else:
            pass

        # Decoupage avec la grille : cas du parametre areaThresh
        if cfg.parameters.areaThresh != '':
            areaT = int(sqrt(float(cfg.parameters.areaThresh))) * 100.
            if not isinstance(cfg.parameters.sourcesAreaThresh, config.Sequence):
                sourcesAreaThresh = [cfg.parameters.sourcesAreaThresh]
            if keysource in sourcesAreaThresh:
                outgrid = outfilemerge[:-4] + '_grid.shp'
                outgridbuff = outgrid[:-4] + '_buff.shp'
                outfilemergeDiff = outfilemerge[:-4] + 'grid_{}ha.shp'.format(cfg.parameters.areaThresh)
                CreateGrid.create_grid(outfilemerge, outgrid, areaT)
                BufferOgr.bufferPoly(outgrid, outgridbuff, 10)
                command = 'python /home/thierion/Documents/OSO/Dev/vector_tools/DifferenceQGIS.py {} {} {} {}'.\
                          format(outfilemerge, outgridbuff, True, outfilemergeDiff)
                os.system(command)
                outfilemerge = outfilemergeDiff
        
        # tri des chemins en fonction des priorités pour les opérations de différence
        if '_' not in keysource:
            idx = listpriorities.index(keysource)
            dataSourcePriorities[idx] = outfilemerge

    for keysource in samples_shapefile_source:
        if '_' in keysource:
            outfilemerge = ouputPath + '/final/' + cfg.parameters.samplesFileName + '_' + keysource + '.shp'
            idx1 = listpriorities.index(keysource.split('_')[0])
            idx2 = listpriorities.index(keysource.split('_')[1])
            if idx1 < idx2:
                if idx1 not in dataSourcePriorities.keys():
                    dataSourcePriorities[idx1] = outfilemerge
                else:
                    dataSourcePriorities[idx1 + 0.5] = outfilemerge                    
            else:
                if idx2 not in dataSourcePriorities.keys():
                    dataSourcePriorities[idx2] = outfilemerge
                else:
                    dataSourcePriorities[idx2 + 0.5] = outfilemerge
                
    orderedSourcesPaths = [value for (key, value) in sorted(dataSourcePriorities.items())] 
    orderedSourcesPaths.reverse()

    # Merge des linéaires de masquage
    if len(maskToMerge) != 0:
        MergeFiles.mergeVectors(maskToMerge, outfilemergemask)

    # Différence + masquage final
    nbfiles = len(orderedSourcesPaths)
    indfile = 0
    outpathList = []
    if nbfiles != 1:
        while indfile < nbfiles - 1:
            if indfile == 0:
                output = orderedSourcesPaths[indfile][:-4] + '_' + \
                         os.path.basename(orderedSourcesPaths[indfile + 1]).split('_')[1][:-4] + '.shp'
                outputmerge = orderedSourcesPaths[indfile][:-4] + '_' +  \
                              os.path.basename(orderedSourcesPaths[indfile + 1]).split('_')[1][:-4] + '_merge.shp'
                outpathList.append([orderedSourcesPaths[indfile], orderedSourcesPaths[indfile + 1], output, outputmerge])
            else:
                output = outpathList[indfile - 1][2][:-4] + '_' +  \
                         os.path.basename(orderedSourcesPaths[indfile + 1]).split('_')[1][:-4] + '.shp'
                outputmerge = outpathList[indfile - 1][3][:-10] + '_' + \
                              os.path.basename(orderedSourcesPaths[indfile + 1]).split('_')[1][:-4] + '_merge.shp'
                outpathList.append([outpathList[indfile - 1][3], orderedSourcesPaths[indfile + 1], output, outputmerge])

            indfile += 1
        
        for listInOuput in outpathList:
            command = 'python /home/thierion/Documents/OSO/Dev/vector_tools/DifferenceQGIS.py {} {} {} {}'.\
                      format(listInOuput[0], listInOuput[1], True,listInOuput[2])
            os.system(command)
            # shapeDifference.shapeDifference(listInOuput[0], listInOuput[1], listInOuput[2], False, None)
            MergeFiles.mergeVectors([listInOuput[1], listInOuput[2]], listInOuput[3])

        subfinal = outpathList[len(outpathList) - 1][3]

    else:
        subfinal = orderedSourcesPaths[0]


    # Difference avec les masques (réseaux)
    if os.path.exists(outfilemergemask):
        subFinalSsReseaux = subfinal[:-4] + 'ssreseaux.shp'
        command = 'python /home/thierion/Documents/OSO/Dev/vector_tools/DifferenceQGIS.py {} {} {} {}'.\
                  format(subfinal, outfilemergemask, True, subFinalSsReseaux)
        os.system(command)
        #shapeDifference.shapeDifference(subfinal, outfilemergemask, subFinalSsReseaux, False, None)
    else:
        subFinalSsReseaux = subfinal
        
    # Harmonisation de la couche finale
    try:
        filefinal = ouputPath + '/final/echantillons_OSO_' + cfg.parameters.samplesFileName + '.shp'
        checkGeometryAreaThreshField.checkGeometryAreaThreshField(subFinalSsReseaux, area_thresh, pix_thresh, filefinal)
        print "Les échantillons de classification pour la zone {}"\
            " ont été produits dans la couche {}".format(cfg.parameters.samplesFileName, filefinal)
    except:
        print "Un problème de copie a été identifié"

    try:
        vf.RandomSelectionPolygons(filefinal, cfg.parameters.landCoverField, 1, ouputPath + '/final/', 0.7)
        print "Les échantillons ont été séparés en deux groupes de validation {} et d'apprentissage {}"\
            .format(filefinal[:-4] + '_seed0_val.shp', filefinal[:-4] + '_seed0_learn.shp')
    except:
        print "Problème de tirage aléatoire"


if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
        usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Prepare training and \
        validation samples for iota2 classification")
        parser.add_argument("-c", dest="config", action="store", \
                            help="configuration file", required = True)
        parser.add_argument("-of", dest="outpath", action="store", \
                            help="output path to store vector files", required = True)        
	args = parser.parse_args()
        gestion_echantillons(args.config, args.outpath)
