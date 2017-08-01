# -*- coding: utf-8 -*-
"""

"""

import sys
import os
import OSO_functions as osof
import argparse
import shutil
    
def zonal_stats_otb(vecteur, r_validity, r_classif, r_classifier, field, outwd, version, out, ndept, mask, split=""):
    
    timer = osof.Timer()
    #ouverture en ram des rasters
    raster_validity = osof.otb_MiseEnRam([r_validity], "im1b1", 8)
    raster_classif = osof.otb_MiseEnRam([r_classif], "im1b1", 8)
    raster_classifier = osof.otb_MiseEnRam([r_classifier], "im1b1", 8)

    timer.start()
    #concatenation des rasters (memoire)
    print "Concatenation"
    stack_raster = osof.otb_concatenate_image(raster_classif, raster_validity, raster_classifier)
    timer.stop()
    time_concatenation = timer.interval
    """
    with open(out +"/dept_%s"%(ndept) + "/log_%s_stats_otb.csv"%(ndept), "a") as csvfile :
        csvfile.write("Concatenation : %s\n"%(round(time_concatenation,0)))
        csvfile.close()
    """
    timer.start()
    #polygon class stats (stats.xml)
    print "stats"
    poly_class_stats = osof.otb_polygon_class_stats(stack_raster, vecteur, field, outwd, float(version),split)
    print "après stats"
    timer.stop()
    time_poly_class_stats = timer.interval
    """
    with open(out +"/dept_%s"%(ndept) + "/log_%s_stats_otb.csv"%(ndept), "a") as csvfile :
        csvfile.write("Polygone class stats : %s\n"%(round(time_poly_class_stats,0)))
        csvfile.close()
    """
    poly_class_stats_name = os.path.basename(poly_class_stats)
    shutil.copy(poly_class_stats, \
                out + '/' + poly_class_stats_name)    
    
    timer.start()
    #sample selection (sample_selection.sqlite)
    print "SampleSelection"
    sample_selection = osof.otb_sample_selection(stack_raster,vecteur, field, poly_class_stats, outwd, float(version), split, mask)
    print "Apres SampleSelection"
    timer.stop()
    time_sample_selection = timer.interval

    sample_selection_name = os.path.basename(sample_selection)
    shutil.copy(sample_selection, \
                out + '/' + sample_selection_name)    
    """
    with open(out +"/dept_%s"%(ndept) + "/log_%s_stats_otb.csv"%(ndept), "a") as csvfile :
        csvfile.write("Sample selection : %s\n"%(round(time_sample_selection,0)))
        csvfile.close()
    """
    timer.start()
    #sample extraction (sample_extraction.sqlite)
    print "SampleExtraction"
    sample_extract = osof.otb_sample_extraction(stack_raster,sample_selection,field, outwd, float(version),split)
    print "Après sampleExtraction"
    timer.stop()
    time_sample_extract = timer.interval
    """
    with open(out +"/dept_%s"%(ndept) + "/log_%s_stats_otb.csv"%(ndept), "a") as csvfile :
        csvfile.write("Sample extraction : %s\n"%(round(time_sample_extract,0)))
        csvfile.close()    
    """
    #sqlite file name
    return sample_extract, time_poly_class_stats, time_sample_selection, time_sample_extract
    
if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
 
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "Regulararize a raster")
        parser.add_argument("-wd", dest="path", action="store", \
                            help="Input path where classification is located", required = True)

        parser.add_argument("-vecteur", dest="vecteur", action="store", \
                            help="departements shapefile", required = True)
        
        parser.add_argument("-validity", dest="validity", action="store", \
                            help="validity raster", required = True)
                            
        parser.add_argument("-classif", dest="classif", action="store", \
                            help="classification without regularization", required = True)
        
        parser.add_argument("-confid", dest="confidence", action="store", \
                            help="confidence raster", required = True)
                            
        parser.add_argument("-nbcore", dest="core", action="store", \
                            help="Number of cores to use for OTB applications", required = True)
                            
        parser.add_argument("-strippe", dest="ram", action="store", \
                            help="Number of strippe for otb process", required = True)
                            
        parser.add_argument("-out", dest="out", action="store", \
                            help="out directory name", required = True)
                            
        parser.add_argument("-otbversion", dest="otbversion", action="store", \
                            help="otb application version") 
                
        #parser.add_argument("-tmp", action="store_true", \
                            #help="keep temporary files ?", default = False) 
                            
        parser.add_argument("-ndept", dest="ndept", action="store", \
                            help="departement number for directory and selection", required = True)

	parser.add_argument("-split", dest="split", action="store", \
                            help="departement number for directory and selection",default = "",required = False)

        parser.add_argument("-mask", dest="mask", action="store", \
                            help="mask for sample selection", required = False)

        parser.add_argument("-field", dest="field", action="store", \
                            help="mask for sample selection", default = "value", required = False)         
                                
        args = parser.parse_args()
        print args.core
        os.environ["ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS"]= str(args.core)
    
        
        #if not os.path.exists(args.out+"/dept_%s"%(args.ndept)) :
        #    print "Le dossier correspondant au departement %s n'existe pas dans le dossier de sortie. L'etape oso_extract n'a pas ete effectuee. Arret"%(args.ndept)
        #    sys.exit()
            
        #if not os.path.exists(args.path+"/dept_%s"%(args.ndept)) :  
        #    os.mkdir(args.path+"/dept_%s"%(args.ndept))
        #else :
        #    print "le dossier %s existe deja, ajout des donnees dans celui-ci."%("dept_"+args.ndept)
   	"""
        with open(args.out+"/dept_%s"%(args.ndept)+"/log_%s_stats_otb.csv"%(args.ndept), "w") as csvfile :
            csvfile.write("Temps des traitements\n")
            csvfile.close()
	"""
        sample_extract, time_poly_class_stats, \
            time_sample_selection, time_sample_extract = zonal_stats_otb(args.vecteur, \
                                                                         args.validity, \
                                                                         args.classif, \
                                                                         args.confidence, \
                                                                         args.field, \
                                                                         args.path, \
                                                                         args.otbversion, \
                                                                         args.out, \
                                                                         args.ndept,\
                                                                         args.mask, \
                                                                         args.split)
        
        #initialise un fichier log de serialisation tif
	"""
        with open(args.out+"/dept_%s"%(args.ndept)+"/log_%s_stats_otb.csv"%(args.ndept), "a") as csvfile :
            csvfile.write("%s;%s;%s\n"%(round(time_poly_class_stats,0), round(time_sample_selection,0),\
            round(time_sample_extract,0)))
            csvfile.close()
	"""
        shutil.copy(args.path+"/sample_extract"+args.split+".sqlite", \
                    args.out+"/sample_extract"+args.split+".sqlite")    
        #shutil.copy(args.path+"/dept_%s"%(args.ndept)+"/log_%s_stats_otb.csv"%(args.ndept), \
        #            args.out+"/dept_%s"%(args.ndept)+"/log_%s_stats_otb.csv"%(args.ndept))
