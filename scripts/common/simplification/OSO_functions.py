# -*- coding: utf-8 -*-
"""
Some functions for OSO treatments

"""
import sys
import os
from osgeo import gdal,ogr,osr
import time
import string
import numpy as np
#import clump
import otbApplication as otb
from operator import itemgetter
#from skimage.measure import regionprops
import matplotlib.pyplot as plt
import subprocess

#------------------------------------------------------------------------------
class Timer(object):
    """
    Classe pour mesurer le temps d'execution.
    """  
    def start(self):  
        if hasattr(self, 'interval'):  
            del self.interval  
        self.start_time = time.time()  
  
    def stop(self):  
        if hasattr(self, 'start_time'):  
            self.interval = time.time() - self.start_time  
            del self.start_time # Force timer reinit
            
def raster_open(name, bande):
    """
    Open raster and return some information about it.
    
    in :
        name : raster name
    out :
        datas : numpy array from raster dataset
        xsize : xsize of raster dataset
        ysize : ysize of raster dataset
        projection : projection of raster dataset
        transform : coordinates and pixel size of raster dataset
    """    
    raster = gdal.Open(name, 0)
    raster_band = raster.GetRasterBand(bande)
    
    #property of raster
    projection = raster.GetProjectionRef()
    transform = raster.GetGeoTransform()
    xsize = raster.RasterXSize
    ysize = raster.RasterYSize
    
    #convert raster to an array
    datas = raster_band.ReadAsArray()
    
    return datas, xsize, ysize, projection, transform, raster_band

def shape_open(in_name, mode):
    """
    Open shapefile
    
    in:
        in_name : name of shapefile
    
    out :
        shape_layer : shape layer
    """
    #ouverture du shape 
    driver_shapefile = ogr.GetDriverByName("ESRI Shapefile")
    shape = driver_shapefile.Open(in_name, mode)
    
    return shape
        
def raster_save(name, xsize, ysize, transform, datas, projection, encode):
    """
    Save an array to a raster.
    
    in :
        name : raster name
        xsize : xsize of raster to be created
        ysize : ysize of raster to be created
        transform : coordinates and pixel size of raster to be created
        data : data of raster to be created
        projection : projection of raster to be created
        encode : encode of raster (gdal.GDT_UInt32, gdal.GDT_Byte) 
    """
    driver = gdal.GetDriverByName("GTiff")
    outRaster = driver.Create(name, xsize, ysize, 1, encode)
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(datas)
    outRaster.SetProjection(projection)
    outRaster.SetGeoTransform(transform)

    del outRaster, outband
    
def raster_save_zone(name, xsize, ysize, transform, data, projection, encode, minx, miny):
    """
    Save an array to a raster.

    in :
        name : raster name
        xsize : xsize of raster to be created
        ysize : ysize of raster to be created
        transform : coordinates and pixel size of raster to be created
        data : data of raster to be created
        projection : projection of raster to be created
        encode : encode of raster (gdal.GDT_UInt32, gdal.GDT_Byte) 
    """
    driver = gdal.GetDriverByName("GTiff")
    outRaster = driver.Create(name, xsize, ysize, 1, encode)
    outband = outRaster.GetRasterBand(1)
    outband.WriteArray(data)
    outRaster.SetProjection(projection)
    outRaster.SetGeoTransform((((minx * transform[1]) + transform[0]), \
                               transform[1], \
                               transform[2], \
                               ((miny * transform[5]) + transform[3]), \
                               transform[4], \
                               transform[5]))

    del outRaster, outband
    
def create_shape(name, epsg):
    #cree un fichier de fusion
    outDriver = ogr.GetDriverByName('ESRI Shapefile')
    if os.path.exists(name):
        os.remove(name)
    out_coordsys = osr.SpatialReference()
    out_coordsys.ImportFromEPSG(epsg)
    outDataSource = outDriver.CreateDataSource(name)
    outLayer = outDataSource.CreateLayer(name,srs = out_coordsys,geom_type=ogr.wkbPolygon)
    outDataSource.Destroy()
    
def extent(list_index, xsize, ysize):  
    """
    A partir d'une liste d'index, defini les coordonnees
    max en X et Y
    
    in :
        liste_index : liste contenant des index
    out :
        Xmin
        Xmax
        Ymin
        Ymax
    """    
    #index de la zone à extraire
    index_miny = min(list_index[:,0])
    index_maxy = max(list_index[:,0])+1
    index_minx = min(list_index[:,1])
    index_maxx = max(list_index[:,1])+1
    
    #permet de recuperer une ligne de pixel en plus pour supprimer
    #le probleme de simplification en bord de mer
    if index_miny != 0 :
        index_miny = index_miny - 1
    if index_maxy != ysize :
        index_maxy = index_maxy + 1
    if index_minx != 0 :
        index_minx = index_minx - 1
    if index_maxx != xsize :
        index_maxx = index_maxx + 1
    
    return index_miny,index_maxy,index_minx,index_maxx
    
def index_value(index_miny,index_maxy,index_minx,index_maxx, ysize_tuile, xsize_tuile, ysize_max, xsize_max):
    """
    """
    if (index_miny - ysize_max) < 0 :
        index_miny = 0
    else :
        index_miny = index_miny - ysize_max
    
    if (index_maxy + ysize_max) > ysize_tuile :
        index_maxy = ysize_tuile
    else :
        index_maxy = index_maxy + ysize_max
    
    if (index_minx - xsize_max) < 0 :
        index_minx = 0
    else :
        index_minx = index_minx - xsize_max
    
    if (index_maxx - xsize_max) > xsize_tuile :
        index_maxx = xsize_tuile
    else :
        index_maxx = index_maxx + xsize_max
    
    return index_miny,index_maxy,index_minx,index_maxx
        
def coords_cell(feature,transform):
    """
    For feature from grid, generate coordinates.
    
    in :
        feature : feature from grid (osgeo format)
        transform : coordinates from raster     
            transform[0] = Xmin;             // Upper Left X
            transform[1] = CellSize;         // W-E pixel size
            transform[2] = 0;                // Rotation, 0 if 'North Up'
            transform[3] = Ymax;             // Upper Left Y
            transform[4] = 0;                // Rotation, 0 if 'North Up'
            transform[5] = -CellSize;        // N-S pixel size
    out :
        cols_xmin : cols_xmin of cell
        cols_xmax : cols_xmax of cell
        cols_ymin : cols_ymin of cell
        cols_ymax : cols_ymax of cell
    """

    geom = feature.GetGeometryRef()
    ring = geom.GetGeometryRef(0)
    pointsX = []
    pointsY = []

    #recupere les coordonnees de chacun des sommets de la cellule
    for point in range(ring.GetPointCount()):
        #coord xy du sommet
        X = ring.GetPoint(point)[0]
        Y = ring.GetPoint(point)[1]
        pointsX.append(X)
        pointsY.append(Y)
        
    #Converti les coordonnees en ligne/colonne
    cols_xmin = int((min(pointsX)-transform[0])/transform[1])
    cols_xmax = int((max(pointsX)-transform[0])/transform[1])
    cols_ymin = int((max(pointsY)-transform[3])/transform[5])
    cols_ymax = int((min(pointsY)-transform[3])/transform[5])
    
    return cols_xmin, cols_xmax, cols_ymin, cols_ymax


def genere_cpp_BandMath(basefile, condition):
    jobFile = open(basefile,"w")
    jobFile.write( '#include "otbBandMathImageFilter.h"\n\
#include "otbVectorImage.h"\n\
#include "otbImageFileReader.h"\n\
#include "otbImageFileWriter.h"\n\
#include "otbMultiToMonoChannelExtractROI.h"\n\
#include "otbObjectList.h"\n\
#include "otbImageList.h"\n\
\n\
typedef otb::Image<double,2> ImageType;\n\
typedef otb::VectorImage<double,2> VectorImageType;\n\
typedef otb::ImageList<VectorImageType> ImageListType;\n\
typedef otb::MultiToMonoChannelExtractROI<VectorImageType::InternalPixelType,\n\
                                          ImageType::PixelType>    ExtractROIFilterType;\n\
typedef otb::ObjectList<ExtractROIFilterType>                           ExtractROIFilterListType;\n\
typedef otb::BandMathImageFilter<ImageType>                             BandMathImageFilterType;\n\
typedef otb::ImageFileReader<VectorImageType> ReaderType;\n\
typedef otb::ObjectList<ReaderType>                           ReaderListType;\n\
typedef otb::ImageFileWriter<ImageType> WriterType;\n\
\n\
int main(int argc, char* argv[])\n\
{\n\
    if(argc<3)\n\
    {\n\
    std::cout<< \"Usage: \" << argv[0] << %r;\n\
    return EXIT_FAILURE;\n\
    }\n\
  const unsigned int nbImages = argc-2;\n\
  const std::string expression = "%s";\n\
  const std::string outputImageFile{argv[argc-1]};\n\
  std::vector<std::string> inputImageFiles{};\n\
  for(size_t i=0; i<nbImages; ++i)\n\
    {\n\
    inputImageFiles.push_back(argv[i+1]);\n\
    }\n\
\n\
  auto imageList = ImageListType::New();\n\
  auto  readerList = ReaderListType::New();\n\
  auto  channelExtractorList = ExtractROIFilterListType::New();\n\
  auto  bmFilter               = BandMathImageFilterType::New();\n\
\n\
  unsigned int bandId = 0;\n\
  unsigned int imageId = 0;\n\
\n\
  for (unsigned int i = 0; i < nbImages; i++)\n\
    {\n\
    std::cout << "Reading image " << inputImageFiles[i] << %r;\n\
    auto reader = ReaderType::New();\n\
    reader->SetFileName(inputImageFiles[i]);\n\
    reader->UpdateOutputInformation();\n\
    readerList->PushBack(reader);\n\
    VectorImageType::Pointer currentImage = reader->GetOutput();\n\
    currentImage->UpdateOutputInformation();\n\
    imageList->PushBack(currentImage);\n\
\n\
    for (unsigned int j = 0; j < currentImage->GetNumberOfComponentsPerPixel(); j++)\n\
      {\n\
      std::ostringstream tmpParserVarName;\n\
      tmpParserVarName << "im" << imageId + 1 << "b" << j + 1;\n\
\n\
      auto extractROIFilter = ExtractROIFilterType::New();\n\
      extractROIFilter->SetInput(currentImage);\n\
      extractROIFilter->SetChannel(j + 1);\n\
      extractROIFilter->GetOutput()->UpdateOutputInformation();\n\
      channelExtractorList->PushBack(extractROIFilter);\n\
      bmFilter->SetNthInput(bandId, channelExtractorList->Back()->GetOutput(), tmpParserVarName.str());\n\
\n\
      bandId++;\n\
      }\n\
    imageId++;\n\
    }\n\
\n\
  bmFilter->SetExpression(expression);\n\
\n\
  WriterType::Pointer writer = WriterType::New();\n\
  writer->SetFileName(outputImageFile);\n\
  writer->SetInput(bmFilter->GetOutput());\n\
  writer->Update();\n\
  // Set the output image\n\
\n\
    }\n'%("image1 [image2 ... imageN] expression outputimage \n", condition, "\n"))    
    jobFile.close()
    print "ecriture terminée"
    
def genere_liste_conditions(list_id, bande, listfile=None):
    """
    Generate a list with conditions for id in array.

    in :
        list_id : list of id
    out :
        list_conds : list with conditions from list id
    """
    list_conds = []
    list_id.append(-1000)
    pos = 0
      
    while pos < len(list_id)-1:
        npos = pos+1
        if list_id[pos]+1 != list_id[pos+1] :
            list_conds.append("(im1b%s=="%(bande)+str(list_id[pos])+")")
            pos += 1
        else :
            tmppos = pos
            while (tmppos < len(list_id)-1) and \
                  (list_id[tmppos]+1 == list_id[tmppos+1]):
                tmppos += 1
            list_conds.append("((im1b%s>="%(bande)+str(list_id[pos])+") && (im1b%s<="%(bande)+str(list_id[tmppos])+"))")
            pos = tmppos+1
        
    list_id.remove(-1000)

    if listfile is not None:
            condFile = open(listfile,"w")
            condFile.write(string.join(list_conds, "||") + "?1:0")
            
    return string.join(list_conds, "||") + "?1:0"
    
def otb_bandmath_1(raster, output, conditions, ram, dtype):
    """
    Apply an expression on raster and save the result in .tif.
    
    in :
        raster : raster name
        output : result raster name
        conditions : expression
        
    out :
        raster.tif
    """
    
    bmApp = otb.Registry.CreateApplication("BandMath")
    bmApp.SetParameterStringList("il",[raster])
    bmApp.SetParameterString("out",output,"?&streaming:type=stripped \
    &streaming:sizemode=nbsplits&streaming:sizevalue=%s"%(ram))
    if dtype == 8 :
        bmApp.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint8)
    elif dtype == 32 :
        bmApp.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint32) 
    bmApp.SetParameterString("exp",conditions)
    bmApp.ExecuteAndWriteOutput()
    
def otb_bandmath_2_ram(raster1, raster2, output, conditions, ram, dtype):
    """
    Apply an expression on raster and save the result in .tif.
    The difference with otb_bandmath_1 is the utilisation of 2 rasters.
    
    in :
        raster1 : raster 1 name
        raster2 : raster 2 name
        output : result raster name
        conditions : expression
        
    out :
        raster.tif
    """

    bmApp = otb.Registry.CreateApplication("BandMath")
    bmApp.SetParameterStringList("il",[raster1])
    bmApp.AddImageToParameterInputImageList("il",[raster2])
    bmApp.SetParameterString("out",output,"?&streaming:type=stripped \
    &streaming:sizemode=nbsplits&streaming:sizevalue=%s"%(ram))
    if dtype == 8 :
        bmApp.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint8)
    elif dtype == 32 :
        bmApp.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint32)
    bmApp.SetParameterString("exp",conditions)
    bmApp.ExecuteAndWriteOutput()
    
def otb_bandmath_2(raster1, raster2, output, conditions, ram, dtype, memory=False):
    """
    Apply an expression on raster and save the result in .tif.
    The difference with otb_bandmath_1 is the utilisation of 2 rasters.
    
    in :
        raster1 : raster 1 name
        raster2 : raster 2 name
        output : result raster name
        conditions : expression
        
    out :
        raster.tif
    """

    bmApp = otb.Registry.CreateApplication("BandMath")
    if not memory :
        bmApp.SetParameterStringList("il",[raster1, raster2])
    else :
        bmApp.AddImageToParameterInputImageList("il",raster1.GetParameterOutputImage("out"))
        bmApp.AddImageToParameterInputImageList("il",raster2.GetParameterOutputImage("out"))
    bmApp.SetParameterString("out",output,"?&streaming:type=stripped \
    &streaming:sizemode=nbsplits&streaming:sizevalue=%s"%(ram))
    if dtype == 8 :
        bmApp.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint8)
    elif dtype == 32 :
        bmApp.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint32)
    bmApp.SetParameterString("exp",conditions)
    bmApp.ExecuteAndWriteOutput()
    
    if memory :
        bmApp.Execute()
        return bmApp, output
    
def otb_bandmaths(rasters,output,conditions,ram,dtype):
    """
    Apply an expression on raster and save the result in .tif.
    The difference with otb_bandmath_1 is the utilisation of 2 rasters.
    
    in :
        raster1 : raster 1 name
        raster2 : raster 2 name
        output : result raster name
        conditions : expression
        
    out :
        raster.tif
    """

    bmApp = otb.Registry.CreateApplication("BandMath")
    bmApp.SetParameterStringList("il",rasters)
    bmApp.SetParameterString("out",output,"?&streaming:type=stripped \
    &streaming:sizemode=nbsplits&streaming:sizevalue=%s"%(ram))
    if dtype == 8 :
        bmApp.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint8)
    elif dtype == 32 :
        bmApp.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint32)
    bmApp.SetParameterString("exp",conditions)
    bmApp.ExecuteAndWriteOutput()

def otb_bandmathX(raster,output,conditions,ram,dtype):
    """
    Apply an expression on raster and save the result in .tif.
    
    in :
        raster : raster name
        output : result raster name
        conditions : expression
        
    out :
        raster.tif
    """

    bmApp = otb.Registry.CreateApplication("BandMathX")
    bmApp.SetParameterStringList("il",raster)
    bmApp.SetParameterString("out",output,"?&streaming:type=stripped \
    &streaming:sizemode=nbsplits&streaming:sizevalue=%s"%(ram))
    if dtype == 8 :
        bmApp.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint8)
    elif dtype == 32 :
        bmApp.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint32)
    bmApp.SetParameterString("exp",conditions)
    bmApp.ExecuteAndWriteOutput()

    
def otb_Superimpose(xl_raster, xs_raster, ram, dtype, memory=False):
    """
    Apply an expression on raster and save the result in .tif.
    The difference with otb_bandmath_1 is the utilisation of 2 rasters.
    
    in :
        raster1 : raster 1 name
        raster2 : raster 2 name
        output : result raster name
        conditions : expression
        
    out :
        raster.tif
    """

    siApp = otb.Registry.CreateApplication("Superimpose")
    if not memory :
        siApp.SetParameterString("inr",xl_raster)
        siApp.SetParameterString("inm",xs_raster)
    else :
        siApp.SetParameterInputImage("inr",xl_raster.GetParameterOutputImage("out"))
        siApp.SetParameterInputImage("inm",xs_raster.GetParameterOutputImage("out"))
    siApp.SetParameterFloat("fv",2)
    siApp.SetParameterString("interpolator","nn")
    siApp.SetParameterFloat("lms",1000000)
    siApp.Execute()
    return siApp                 
    
def otb_SuperimposeJobTifv2(xl_raster, xs_raster, ram, dtype, memory=False):
    """
    Apply an expression on raster and save the result in .tif.
    The difference with otb_bandmath_1 is the utilisation of 2 rasters.
    
    in :
        raster1 : raster 1 name
        raster2 : raster 2 name
        output : result raster name
        conditions : expression
        
    out :
        raster.tif
    """

    siApp = otb.Registry.CreateApplication("Superimpose")
    if not memory :
        siApp.SetParameterString("inr",xl_raster)
        siApp.SetParameterString("inm",xs_raster)
    else :
        siApp.SetParameterInputImage("inr",xl_raster.GetParameterOutputImage("out"))
        siApp.SetParameterInputImage("inm",xs_raster.GetParameterOutputImage("out"))
    #siApp.SetParameterFloat("fv",0)
    siApp.SetParameterString("interpolator","nn")
    siApp.SetParameterFloat("lms",1000000)
    siApp.Execute()
    return siApp                    

def otb_dilate(inraster, ram, dtype, memory=False, write=False, outraster=None):
    """
    Do a dilatation from a raster.
    
    in :
        inraster : in raster name
        outraster : out raster name
        
    out :
        raster.tif
    """

    mmApp = otb.Registry.CreateApplication("BinaryMorphologicalOperation")
    if not memory :
        mmApp.SetParameterString("in",inraster)
    else :
        mmApp.SetParameterInputImage("in",inraster.GetParameterOutputImage("out"))
    if write :
        mmApp.SetParameterString("out",outraster,"?&streaming:type=stripped \
        &streaming:sizemode=nbsplits&streaming:sizevalue=%s"%(ram))
    if dtype == 8 :
        mmApp.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint8)
    elif dtype == 32 :
        mmApp.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint32)
    mmApp.SetParameterString("structype", "ball")
    mmApp.SetParameterInt("structype.ball.xradius", 1)
    mmApp.SetParameterInt("structype.ball.yradius", 1)
    mmApp.SetParameterString("filter", "dilate")
    mmApp.SetParameterFloat("filter.dilate.foreval", 1)
    mmApp.SetParameterFloat("filter.dilate.backval", 0)
    
    if write :
        mmApp.ExecuteAndWriteOutput()
        return outraster
    else :
        mmApp.Execute()
        return mmApp
    
def otb_bandmath_ram(rasters, conditions, strippe, dtype, memory=False, ram = 10000, write=False, output=None):
    """
    Apply an expression on raster and save the result in .tif.
    
    in :
        raster : raster name
        output : result raster name
        conditions : expression
        
    out :
        raster.tif
    """

    bmApp = otb.Registry.CreateApplication("BandMath")
    if not memory :
        bmApp.SetParameterStringList("il", rasters)
    else :
        for raster in rasters :
            bmApp.AddImageToParameterInputImageList("il", raster.GetParameterOutputImage("out"))
        
    if write :
        bmApp.SetParameterString("out",output,"?&streaming:type=stripped \
        &streaming:sizemode=nbsplits&streaming:sizevalue=%s"%(strippe))
    if dtype == 8 :
        bmApp.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint8)
    elif dtype == 32 :
        bmApp.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint32) 
    bmApp.SetParameterString("exp", conditions) 
    bmApp.SetParameterString("ram", ram)
    if write :
        bmApp.ExecuteAndWriteOutput()
        return output
    else :
        bmApp.Execute()
        return bmApp
        
def otb_MiseEnRam(rasters, conditions, dtype):
    """
    Passe en ram un raster pour faire de l'enchainement memoire.
    """
    bmApp = otb.Registry.CreateApplication("BandMath")
    bmApp.SetParameterStringList("il",rasters)
    if dtype == 8 :
        bmApp.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint8)
    elif dtype == 32 :
        bmApp.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint32) 
    bmApp.SetParameterString("exp",conditions) 
    bmApp.SetParameterString("ram","10000")
    bmApp.Execute()
    return bmApp

def otb_MiseEnRamConcatenate(rasters, dtype):
    """
    
    """
    ConcaImage = otb.Registry.CreateApplication("ConcatenateImages")
    for raster in rasters :
        ConcaImage.AddImageToParameterInputImageList("il",raster.GetParameterOutputImage("out"))
    if dtype == 8 :
        ConcaImage.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint8)
    elif dtype == 32 :
        ConcaImage.SetParameterOutputImagePixelType("out", otb.ImagePixelType_uint32) 
    ConcaImage.SetParameterString("ram","10000")
    ConcaImage.Execute()
    return ConcaImage
    
def otb_concatenate_image(raster1, raster2, raster3):
    """
    
    """
    
    ConcaImage = otb.Registry.CreateApplication("ConcatenateImages")
    ConcaImage.AddImageToParameterInputImageList("il",raster1.GetParameterOutputImage("out"))
    ConcaImage.AddImageToParameterInputImageList("il",raster2.GetParameterOutputImage("out"))
    ConcaImage.AddImageToParameterInputImageList("il",raster3.GetParameterOutputImage("out"))
    ConcaImage.SetParameterString("ram","10000")
    ConcaImage.Execute()
    return ConcaImage

def otb_polygon_class_stats(raster, vecteur, field, out, version,split=""):
    """
    
    """
    print out+"/stats"+split+".xml"
    if not os.path.exists(out+"/stats"+split+".xml"):
        if str(version) == "5.8":
            PolyClassStats = otb.Registry.CreateApplication("PolygonClassStatistics")
            PolyClassStats.SetParameterInputImage("in",raster.GetParameterOutputImage("out"))
            PolyClassStats.SetParameterString("vec",vecteur)
            PolyClassStats.SetParameterString("field",field)  
            PolyClassStats.SetParameterString("ram","10000")
            PolyClassStats.SetParameterString("out", out+"/stats"+split+".xml")
            PolyClassStats.ExecuteAndWriteOutput()
        else:
            #5.9 OTB  
            PolyClassStats = otb.Registry.CreateApplication("PolygonClassStatistics")
            PolyClassStats.SetParameterInputImage("in",raster.GetParameterOutputImage("out"))
            PolyClassStats.SetParameterString("vec",vecteur)  
            PolyClassStats.SetParameterString("ram","10000")
            PolyClassStats.SetParameterString("out", out+"/stats"+split+".xml")
            PolyClassStats.UpdateParameters()
            PolyClassStats.SetParameterStringList("field",[field])
            PolyClassStats.ExecuteAndWriteOutput()

    return out+"/stats"+split+".xml"
        
def otb_sample_selection(raster, vecteur, field, stats, out, version, split="", mask=""):
    """
    
    """
    if not os.path.exists(out+"/sample_selection"+split+".sqlite"):
        SampleSelection = otb.Registry.CreateApplication("SampleSelection")
        SampleSelection.SetParameterInputImage("in",raster.GetParameterOutputImage("out"))
        SampleSelection.SetParameterString("vec",vecteur)
        if mask != '':
            SampleSelection.SetParameterString("mask",mask)
        SampleSelection.SetParameterString("instats",stats)
        if str(version) == "5.8":
            SampleSelection.SetParameterString("field",field)
        else :
            SampleSelection.UpdateParameters()
            SampleSelection.SetParameterStringList("field",[field])
        SampleSelection.SetParameterString("sampler","random")
        SampleSelection.SetParameterString("strategy","all")
        SampleSelection.SetParameterString("ram","10000")
        SampleSelection.SetParameterString("out", out+"/sample_selection"+split+".sqlite")
        SampleSelection.ExecuteAndWriteOutput()
        #SampleSelection.Execute()
    return out+"/sample_selection"+split+".sqlite"
    
def otb_sample_extraction(raster,vecteur,field, out, version,split=""):
    """
    
    """
    
    SampleExtraction = otb.Registry.CreateApplication("SampleExtraction")
    SampleExtraction.SetParameterInputImage("in",raster.GetParameterOutputImage("out"))
    SampleExtraction.SetParameterString("vec",vecteur)
    if str(version) == "5.8":
        SampleExtraction.SetParameterString("field",field)
    else :
        SampleExtraction.UpdateParameters()
        SampleExtraction.SetParameterStringList("field",[field])
    SampleExtraction.SetParameterString("ram","10000")
    SampleExtraction.SetParameterString("out",out+"/sample_extract"+split+".sqlite","?&streaming:type=stripped \
    &streaming:sizemode=nbsplits&streaming:sizevalue=%s"%(2))
    SampleExtraction.ExecuteAndWriteOutput()
    return out+"/sample_extract"+split+".sqlite"    
    
def otb_ExtractROI(inraster, outraster, startx, starty, sizex, sizey, ram):
    """
    
    """

    ExtractROI = otb.Registry.CreateApplication("ExtractROI")
    ExtractROI.SetParameterString("in",inraster)
    ExtractROI.SetParameterInt("startx",startx)
    ExtractROI.SetParameterInt("starty",starty)
    ExtractROI.SetParameterInt("sizex",sizex)
    ExtractROI.SetParameterInt("sizey",sizey)
    ExtractROI.SetParameterString("out",outraster)#,"?&streaming:type=stripped \
    #&streaming:sizemode=nbsplits&streaming:sizevalue=%s"%(2))
    ExtractROI.ExecuteAndWriteOutput()
    #ExtractROI.Execute()
    return outraster#, ExtractROI
    
def XYStart(cols_xmin, cols_ymin, xsize_tile, ysize_tile):
    """
        Determine les XY de depart pour extraire une zone selon 3x3 tuiles
    """
    Xstart = cols_xmin - xsize_tile -1
    Ystart = cols_ymin - ysize_tile 
    
    return Xstart, Ystart
    
def ClumpSurfaceRaster(rasterFile, outpath, outcsv):
    """
        A partir d'un raster clump, genere un dictionnaire identifiant:nbpixels, 
        Genere un graphique de distribution, un fichier csv contenant les valeurs et
        genere un raster pour chacune des x plus grandes entités.
    """
    #ouvre le clump   
    clumpArr,xsize,ysize,projection,transform,raster_band = raster_open(rasterFile, 2)

    #calcul un ensemble de donnees sur le clump
    regionsDatas = regionprops(clumpArr)
    
    #tant qu'il y a des entites, recupere son label et son nombre de pixels dans
    #un dictionnaire
    i=0
    dic = {}
    while regionsDatas:
        try:
            dic.update({regionsDatas[i].label:regionsDatas[i].area})
            i+=1
        except:
            IndexError
            print "Fin"
            break
    
    #trie les valeurs (nb pixels) et genere un tableau ensuite
    trie = dic.items()
    trie.sort(key=itemgetter(1),reverse=True)
    arr = np.asarray(trie)
    
    #sauvegarde le tableau dans un fichier csv
    np.savetxt(outcsv, arr, fmt='%i', header="id, nbpixels", delimiter=",")
    
    #affiche la distribution croissante des valeurs
    #plt.bar(range(len(trie)), arr[:,1], align='center')
    #plt.show()
    
    #recupere les x plus grandes surfaces
    #nbMax = int(arr.shape[0]*0.01)
    #clumpMax = arr[-nbMax:]
    clumpMax = arr[:10]
    
    liste_id_entite = []
    #pour chaque identifiant, recupere son etendue sur le clump entier et
    #l'enregistre dans un raster
    for ID in np.nditer(clumpMax[:,0]):
        clump_id_binary = otb_bandmath_ram([rasterFile], "im1b2==%s?1:0"%(ID), 2, 8, False, True, outpath+"/erase.tif")
        #ouverture du raster
        entite,xsize,ysize,projection,transform,raster_band = raster_open(clump_id_binary, 1)
        #recupere l'index de l'entite
        index_entite = np.argwhere(entite == 1)
        #calcule la bbox
        entite_miny,entite_maxy,entite_minx,entite_maxx = extent(index_entite, xsize, ysize)
        entite_ysize = entite_maxy - entite_miny
        entite_xsize = entite_maxx - entite_minx
        #reduit la taille de la matrice
        array = entite[entite_miny:entite_maxy, entite_minx:entite_maxx]
        #reenregistre le raster selon cette bbox
        raster_save_zone(outpath+"/entite_%s.tif"%(ID), \
                         entite_xsize, \
                         entite_ysize, \
                         transform, \
                         array, \
                         projection, \
                         gdal.GDT_Byte, \
                         entite_minx, \
                         entite_miny)
        #ajoute dans une liste les identifiants des entites sauvegardee        
        liste_id_entite.append(ID)
        
    os.remove(outpath + "/erase.tif")    
    #diminution de la taille des rasters
    return arr, liste_id_entite
