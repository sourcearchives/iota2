#!/usr/bin/python

from osgeo import ogr
import sys

def addFieldID(filein,nameField,valueField):
    source = ogr.Open(filein, 1)
    layer = source.GetLayer()
    layer_defn = layer.GetLayerDefn()
    field_names = [layer_defn.GetFieldDefn(i).GetName() for i in range(layer_defn.GetFieldCount())]
    #
    try :
        int(valueField)
        new_field1 = ogr.FieldDefn(nameField, ogr.OFTInteger)
    except :
        new_field1 = ogr.FieldDefn(nameField, ogr.OFTString)
    
    layer.CreateField(new_field1)
    #i = 1
    for feat in layer:
        layer.SetFeature(feat)
        feat.SetField(nameField, valueField)
        layer.SetFeature(feat)
        #i+=1
    return 0

if __name__=='__main__':
    usage='usage: <infile> <nameField> <value>'
    if len(sys.argv) == 4:
        addFieldID(sys.argv[1],sys.argv[2],sys.argv[3])# == 0:
        print 'Add of field succeeded!'
        #sys.exit(0)
        #else : print "pb"
    else:
        print usage
        sys.exit(1)
