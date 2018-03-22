# -*- coding: utf-8 -*-
#!/usr/bin/python
"""
Created on Tue May 31 10:22:06 2016

Permet en post-processing de différencier, les forêts, les haies et autres AHF dans une couche forêt récupérée d'une classif. 

@author: achone
"""

import os
import sys
import ogr
import argparse
from osgeo.gdalconst import *
import math
import numpy as np
from scipy.spatial import ConvexHull
import vector_functions as vf
import BufferOgr as bo
import MultiPolyToPoly as mpp
import shapeDifference as sd
import MergeFiles as mf

#%% Fonctions utiles
# Fonction pour calculer le rectangle englobant d'aire minimale
def minimum_bounding_rectangle(hull):
    """
    Find the smallest bounding rectangle from the convexe hull of a polygon.
    Returns a set of points representing the corners of the bounding box.

    :param hull: the polygon hull (OGRGeometry)
    :rval: an nx2 matrix of coordinates
    """
    from scipy.ndimage.interpolation import rotate
    pi2 = np.pi/2.

    # get the points of the convex hull boundary
    hull_points = hull.Boundary().GetPoints()
    hull_points = np.array(hull_points).reshape(len(hull_points),2)
    hull_points = np.delete(hull_points[::-1], len(hull_points)-1, 0)
    
    # calculate edge angles
    edges = np.zeros((len(hull_points)-1, 2))
    edges = hull_points[1:] - hull_points[:-1]

    angles = np.zeros((len(edges)))
    angles = np.arctan2(edges[:, 1], edges[:, 0])

    angles = np.abs(np.mod(angles, pi2))
    angles = np.unique(angles)

    # find rotation matrices
    # XXX both work
    rotations = np.vstack([
        np.cos(angles),
        np.cos(angles-pi2),
        np.cos(angles+pi2),
        np.cos(angles)]).T

    rotations = rotations.reshape((-1, 2, 2))

    # apply rotations to the hull
    rot_points = np.dot(rotations, hull_points.T)

    # find the bounding points
    min_x = np.nanmin(rot_points[:, 0], axis=1)
    max_x = np.nanmax(rot_points[:, 0], axis=1)
    min_y = np.nanmin(rot_points[:, 1], axis=1)
    max_y = np.nanmax(rot_points[:, 1], axis=1)

    # find the box with the best area
    areas = (max_x - min_x) * (max_y - min_y)
    best_idx = np.argmin(areas)

    # return the best box
    x1 = max_x[best_idx]
    x2 = min_x[best_idx]
    y1 = max_y[best_idx]
    y2 = min_y[best_idx]
    r = rotations[best_idx]

    rval = np.zeros((4, 2))
    rval[0] = np.dot([x1, y2], r)
    rval[1] = np.dot([x2, y2], r)
    rval[2] = np.dot([x2, y1], r)
    rval[3] = np.dot([x1, y1], r)
    
    return rval  
    
# Ajout des champs de Convexité, Concavité et Elongation en une seule fois
def addDiscriminationFields(filein):
    source = ogr.Open(filein, 1)
    layer = source.GetLayer()
    # Definition des trois champs servant à la discrimination des forêts et ahf
    new_field1 = ogr.FieldDefn('Convexity', ogr.OFTReal)
    layer.CreateField(new_field1)
    new_field2 = ogr.FieldDefn('Compacity', ogr.OFTReal)
    layer.CreateField(new_field2)
    new_field3 = ogr.FieldDefn('Elongation', ogr.OFTReal)
    layer.CreateField(new_field3)

    # Calcul de leur valeur pour chaque polygone et enregistrement dans la table attributaire
    for feat in layer:
        if feat.GetGeometryRef():
            geom = feat.GetGeometryRef()
            peripoly = geom.Boundary().Length()
            hull = geom.ConvexHull()
            areahull = hull.GetArea()
            coord = minimum_bounding_rectangle(hull)
            Point1 = ogr.Geometry(ogr.wkbPoint)
            Point1.AddPoint(coord[0,0], coord[0,1])    
            Point2 = ogr.Geometry(ogr.wkbPoint)
            Point2.AddPoint(coord[1,0], coord[1,1])
            Point3 = ogr.Geometry(ogr.wkbPoint)
            Point3.AddPoint(coord[2,0], coord[2,1])
            longueur = max(Point1.Distance(Point2), Point2.Distance(Point3))
            largeur = min(Point1.Distance(Point2), Point2.Distance(Point3))
            if areahull != 0 and peripoly !=0 and largeur != 0:
                convexity = geom.GetArea() / areahull
                compacity = 4 * math.pi * (geom.GetArea() / math.pow(peripoly,2))
                elongation = longueur / largeur
            else:
                layer.DeleteFeature(feat.GetFID())
        else:
           print 'not geometry'
           convexity = 0
           compacity = 0
           elongation = 0
        feat.SetField('Convexity', convexity)
        feat.SetField('Compacity', compacity)
        feat.SetField('Elongation', elongation)
        layer.SetFeature(feat)
    source.Destroy()
    layer = None    
    
# Classification des polygones selon les différents critères Convexité, Elongation et Compacité. 
def addClassAHF(filein, convex = 0.7, compa = 0.4, elong = 2.5):
    source = ogr.Open(filein, 1)
    layer = source.GetLayer()
    new_field = ogr.FieldDefn('ClassAHF', ogr.OFTString)
    layer.CreateField(new_field)

    for feat in layer:
        if feat.GetField('Convexity') <= convex:
            if feat.GetField('Compacity') < compa:
                feat.SetField( 'ClassAHF', 'Haie' )
                layer.SetFeature(feat)
            else:
                feat.SetField( 'ClassAHF', 'Foret' )
                layer.SetFeature(feat)
        else: 
            if feat.GetField('Elongation') > elong:
                feat.SetField( 'ClassAHF', 'Haie' )
                layer.SetFeature(feat)
            else:
                feat.SetField( 'ClassAHF', 'AutreAHF' )
                layer.SetFeature(feat)
    source.Destroy()
    layer = None


def foret_non_foret(chemin, FileInit, FileOut, convex = 0.7, compa = 0.4, elong = 2.5):

    os.chdir(chemin)
    print os.path.join(chemin, FileInit)
    
    vf.checkValidGeom(FileInit)
        
    # Erosion puis dilatation du fichier initial pour ne garder que les contours (lissés) des forêts
    bo.bufferPoly(FileInit, 'tmp_Erosion20.shp', -20)
    bo.bufferPoly('tmp_Erosion20.shp', 'tmp_Dilatation20_poly.shp', 20)        
    
    # Dilatation supplémentaire pour récupérer les objets qui disparaissent suite à l'ouverture par selection spatiale
    bo.bufferPoly('tmp_Dilatation20_poly.shp', 'tmp_Extra_Dila_poly.shp', 20)        
    
    mpp.multipoly2poly('tmp_Dilatation20_poly.shp', 'tmp_Dilatation20.shp')
    mpp.multipoly2poly('tmp_Extra_Dila_poly.shp', 'tmp_Extra_Dila.shp')
    
    # Différentiation Forêt / Non-Forêt
    # Soustraction de l'ouverture par rapport au fichier Forêt non différencier
    #os.system('python DifferenceQGIS.py ' + FileInit + ' tmp_Dilatation20.shp True tmp_Non_foret_temp_poly.shp')
    sd.shapeDifference(FileInit, 'tmp_Dilatation20.shp', 'tmp_Non_foret_temp_poly.shp', False, None)
    # Transformation des multipolygones en polygones simples
    mpp.multipoly2poly('tmp_Non_foret_temp_poly.shp', 'tmp_Non_Foret_temp.shp')
    
    
    # Elimination des résidus de la symétries pour obtenir les vrais contours de la forêt
    NF = vf.openToWrite('tmp_Non_Foret_temp.shp')
    ED = vf.openToRead('tmp_Extra_Dila.shp')
    NFLayer = NF.GetLayer()
    EDLayer = ED.GetLayer()
    for fil in EDLayer:
        gfil = fil.GetGeometryRef()
        for f in NFLayer:
            g = f.GetGeometryRef()
            fID = f.GetFID()
            if gfil.Contains(g):
                NFLayer.DeleteFeature(fID)
        NFLayer.ResetReading()
    NF.Destroy()
    ED.Destroy()
    NFLayer = None
    EDLayer = None
        
    # Soustraction de la non-forêt par rapport au fichier initial, pour obtenir les vrais contours de la forêt       
    sd.shapeDifference(FileInit, 'tmp_Non_Foret_temp.shp', 'tmp_Foret_temp_poly.shp', False, None)
        
    vf.checkValidGeom('tmp_Foret_temp_poly.shp')        
    # Transformation des multipolygones en polygones simples
    mpp.multipoly2poly('tmp_Foret_temp_poly.shp', 'tmp_Foret_temp.shp')

    # Tri des forêts, si inférieure à 5000m2, classée en non_forêt
    F = vf.openToWrite('tmp_Foret_temp.shp')
    FLayer= F.GetLayer()
    for f in FLayer:
        g = f.GetGeometryRef()
        fID = f.GetFID()
        if g.GetArea() < 5000:
            FLayer.DeleteFeature(fID)
    F.Destroy()
    FLayer = None
        
    vf.checkValidGeom('tmp_Foret_temp.shp')
        
    # Soustraction des forêts du fichier original pour récupérer les bosquets et boqueteaux dans la couche non-forêt
    sd.shapeDifference(FileInit, 'tmp_Foret_temp.shp', 'tmp_Non_foret_full_poly.shp', False, None)
        
    vf.checkValidGeom('tmp_Non_foret_full_poly.shp')
        
    # Transformation des multipolygones en polygones simples
    mpp.multipoly2poly('tmp_Non_foret_full_poly.shp', 'tmp_Non_Foret_full.shp')        
    vf.checkValidGeom('tmp_Non_Foret_full.shp')

    # Affinage Non-Forêt
    # Calcul des champs de discrimination Elongation, Convexité et Compacité   
    addDiscriminationFields('tmp_Non_Foret_full.shp')  
    # Ajout d'un champs classe qui détermine la classe des polygones en fonction des champs discriminants            
    addClassAHF('tmp_Non_Foret_full.shp', convex, compa, elong)
    
    # Post-processing
    # Si un polygone est classé en forêt est connecté à une plus grande forêt, fusion des deux polygones en une seule et même forêt
    F = vf.openToRead('tmp_Foret_temp.shp') 
    FL = F.GetLayer()
    NF = vf.openToWrite('tmp_Non_Foret_full.shp')
    NFL = NF.GetLayer()
    for foret in FL:
        gforet = foret.GetGeometryRef()
        for nonforet in NFL:
            fID = nonforet.GetFID()
            gnonforet = nonforet.GetGeometryRef()
            if gnonforet.Distance(gforet) == 0 and (nonforet.GetField('ClassAHF') == 'Foret' or nonforet.GetField('ClassAHF') == 'AutreAHF'):
                NFL.DeleteFeature(fID)
        NFL.ResetReading()
    F.Destroy()
    NF.Destroy()
    FL = None
    NFL = None
        
    vf.checkValidGeom('tmp_Non_Foret_full.shp')   
    
    # Différence entre le fichier imitial et les nouvelles forêts
    sd.shapeDifference(FileInit, 'tmp_Non_Foret_full.shp', 'tmp_Foret_full_poly.shp', False, None)
    vf.checkValidGeom('tmp_Foret_full_poly.shp')
    # Transformation des multipolygones en polygones simples
    mpp.multipoly2poly('tmp_Foret_full_poly.shp', 'tmp_Foret_full.shp')        

    # Ajout du champs classe pour les forêts
    F = vf.openToWrite('tmp_Foret_full.shp') 
    FL = F.GetLayer()
    new_field = ogr.FieldDefn('ClassAHF', ogr.OFTString)
    FL.CreateField(new_field)
    for f in FL:
        f.SetField('ClassAHF', 'Foret')
        FL.SetFeature(f)
    F.Destroy()
    FL = None
        
    # Fusion du fichier de forêts avec le fichier de non-forêt
    mf.mergeVectors(['tmp_Foret_full.shp', 'tmp_Non_Foret_full.shp'], FileOut)
        
    # Suppression des fichiers intermédiaires
    os.system('rm tmp_*')

if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Extract forests, hedges, and trees based on an input forest shapefile")
        parser.add_argument("-tmp", dest ="tmp", action="store", \
                            help="List of input shapefiles", required = True)
        parser.add_argument("-s", dest="inputshape", action="store", \
                            help="Folder of input shapefiles", required = True)        
        parser.add_argument("-o", dest="outshapefile", action="store", \
                            help="ESRI Shapefile output filename and path", required = True)
        parser.add_argument("-conv", dest="conv", action="store", \
                            help="Convexity parameter")
        parser.add_argument("-comp", dest="comp", action="store", \
                            help="Compacity parameter")
        parser.add_argument("-elong", dest="elong", action="store", \
                            help="Elongation parameter")
        
	args = parser.parse_args()
        
        foret_non_foret(args.tmp, args.inputshape, args.outshapefile)
        
