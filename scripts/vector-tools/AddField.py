#!/usr/bin/python

from osgeo import ogr
import sys

def addField(filein, nameField, valueField, valueType=None,
             driver_name="ESRI Shapefile", layerName = None):
    
    driver = ogr.GetDriverByName(driver_name)
    source = driver.Open(filein, 1)

    layer = source.GetLayer()
    layer_defn = layer.GetLayerDefn()
    field_names = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]
    if not valueType:
        try :
            int(valueField)
            new_field1 = ogr.FieldDefn(nameField, ogr.OFTInteger)
        except :
            new_field1 = ogr.FieldDefn(nameField, ogr.OFTString)
    elif valueType == str:
        new_field1 = ogr.FieldDefn(nameField, ogr.OFTString)
    elif valueType == int:
        new_field1 = ogr.FieldDefn(nameField, ogr.OFTInteger)  
    
    #ESRI Shapefile does not support SetDefault method
    if driver_name == "ESRI Shapefile":
        layer.CreateField(new_field1)
        for feat in layer:
            layer.SetFeature(feat)
            feat.SetField(nameField, valueField)
            layer.SetFeature(feat)
    else:
        new_field1.SetDefault(valueField)
        layer.CreateField(new_field1)
        
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 1:
        prog = os.path.basename(sys.argv[0])
        print '      '+sys.argv[0]+' [options]' 
        print "     Help : ", prog, " --help"
        print "        or : ", prog, " -h"
        sys.exit(-1)  
    else:
        usage = "usage: %prog [options] "
        parser = argparse.ArgumentParser(description = "Create a field and populate it of an input shapefile")
        parser.add_argument("-s", dest="shapefile", action="store",
                            help="Input shapefile", required = True)
        parser.add_argument("-f", dest="field", action="store",
                            help="Field to add", required = True)
        parser.add_argument("-v", dest="value", action="store",
                            help="Value to insert in the field", required = True) 
        args = parser.parse_args()
        addField(args.shapefile, args.field, args.value)
