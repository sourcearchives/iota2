# -*- coding: utf-8 -*-
"""
Calcule des statistiques d'après un fichier sqlite. Le fichier ainsi produit est
à joindre avec un fichier shapefile.
"""

import sys
import os
import sqlite3 as lite
import pandas as pad
import argparse
import time
import shutil

def stats_sqlite(bd_sqlite, out, idfield='originfid', classiffield='value_0'):
    """
    Utilise la librairie pandas pour calculer des statistiques selon un fichier sqlite
    """
    debut = time.time()
    print idfield, classiffield
    #connection to sqlite file
    con = lite.connect(bd_sqlite)
    df = pad.read_sql_query("SELECT * FROM output", con)
    print "chargement ok"
    # Stats par polygone ('originfid') et par classe
    moy_confidence = df.groupby([idfield, classiffield], as_index=False).\
                     agg({'classe' : {'class_polygon' : 'mean'},\
                          'value_1' : {'mean_validity' : 'mean', 'std_validity' : 'std'},\
                          'value_2' : {'mean_confidence' : 'mean', 'number' : 'size'}})
    print "groupby ok"    
    moy_confidence.columns = moy_confidence.columns.droplevel(0)

    moy_confidence.columns = ['polygon','classif', 'class_polygon', 'std_validity', 'mean_validity', 'mean_confidence',  'number']
    
    moy_confidence["part_occ"] = 100 * moy_confidence["number"] / moy_confidence.groupby(['polygon'])['number'].transform('sum')
    
    moy_confidence = moy_confidence.fillna(0)
    print "sum ok" 
    # Manage polygon FID
    moy_confidence["polygon"] += 1 
    
    #columns names
    columns = ["Classe", "Validmean", "Validstd", "Confidence","Hiver", "Ete", "Feuillus", "Coniferes", "Pelouse", "Landes", "UrbainDens",\
               "UrbainDiff", "ZoneIndCom","Route", "PlageDune", "SurfMin", "Eau", "GlaceNeige", "Prairie", "Vergers", "Vignes"]
    
    index = moy_confidence.polygon.unique()
    
    #create out dataframe
    final_df = pad.DataFrame(index=index, columns=columns)
    final_df[["Validstd","Hiver", "Ete", "Feuillus", "Coniferes", "Pelouse", "Landes", "UrbainDens",\
    "UrbainDiff", "ZoneIndCom","Route", "PlageDune", "SurfMin", "Eau", "GlaceNeige", "Prairie", "Vergers", "Vignes"]] = \
    final_df[["Validstd","Hiver", "Ete", "Feuillus", "Coniferes", "Pelouse", "Landes", "UrbainDens",\
    "UrbainDiff", "ZoneIndCom","Route", "PlageDune", "SurfMin", "Eau", "GlaceNeige", "Prairie", "Vergers", "Vignes"]].apply(pad.to_numeric)
    final_df = final_df.fillna(0)
    
    # Columns correspondance
    correspColumns = {11:'Ete', 12:'Hiver', 31:'Feuillus', 32:'Coniferes', 34:'Pelouse', 36:'Landes',\
            41:'UrbainDens', 42:'UrbainDiff', 43:'ZoneIndCom', 44:'Route', 45:'SurfMin', 46:'PlageDune', 51:'Eau',\
            53:'GlaceNeige', 211:'Prairie', 221:'Vergers', 222:'Vignes'}
    
    non_conformity = 0
    
    for name, group in moy_confidence.groupby(['polygon']):
        # information de la classe du polygone
        classpolygon = group[group['classif'] == group['class_polygon']]
        if not classpolygon.empty:
            poly = classpolygon['polygon'].values[0]
            final_df.set_value(poly, 'Classe', round(classpolygon['class_polygon'].values[0],0))
            final_df.set_value(poly, 'Validstd', round(classpolygon['std_validity'].values[0],2))
            final_df.set_value(poly, 'Validmean', classpolygon['mean_validity'].values[0])
            final_df.set_value(poly, 'Confidence', classpolygon['mean_confidence'].values[0])  
        else:
            classpolygon = group[group['part_occ'] == group['part_occ'].max()]
            poly = classpolygon['polygon'].values[0]
            final_df.set_value(poly, 'Classe', round(classpolygon['class_polygon'].values[0],0))
            final_df.set_value(poly, 'Validstd', round(classpolygon['std_validity'].values[0],2))
            final_df.set_value(poly, 'Validmean', classpolygon['mean_validity'].values[0])
            final_df.set_value(poly, 'Confidence', classpolygon['mean_confidence'].values[0])
            non_conformity += 1
         
        # information des parts de chaque polygone
        for row in group.itertuples():
            rowdict = dict(row._asdict())
	    if rowdict["classif"] in correspColumns.keys():
                final_df.set_value(int(rowdict["polygon"]), correspColumns[int(rowdict["classif"])], round(rowdict['part_occ'], 2))

    print "We get {} cases of non conformity".format(non_conformity)
    
    #export dataframe to csv
    final_df.to_csv(out + '/stats.csv', sep = ',', encoding = 'utf-8', index_label = "FID")
    
    maj_csv(out + '/stats.csv', out)
    
    fin = time.time() - debut
    return fin, non_conformity

def maj_csv(csvfile, out):
    """
    recalcule les pourcentages
    """
    datas = pad.read_csv(csvfile, header = 0)
    recalc = (datas.iloc[:,5:]*100).divide(datas.iloc[:,5:].sum(axis=1), axis=0).round(2)
    #recalc.sum(axis=1)
    merge = pad.concat([datas.iloc[:,0:5], recalc], axis=1)
    os.remove(out + '/stats.csv')
    merge.to_csv(out + '/stats.csv', sep = ',', encoding = 'utf-8',index=False) 

#------------------------------------------------------------------------------           
if __name__ == "__main__":
    if len(sys.argv) == 1:
	prog = os.path.basename(sys.argv[0])
	print '      '+sys.argv[0]+' [options]' 
	print "     Help : ", prog, " --help"
	print "        or : ", prog, " -h"
	sys.exit(-1)  
 
    else:
	usage = "usage: %prog [options] "
	parser = argparse.ArgumentParser(description = "")
        parser.add_argument("-wd", dest="path", action="store", \
                            help="Input path where classification is located", required = True)
                            
        parser.add_argument("-in", dest="sqlite", action="store", \
                            help="name of sqlite database", required = True)
                            
        parser.add_argument("-out", dest="out", action="store", \
                            help="out directory name")

        parser.add_argument("-id", dest="idfield", action="store", \
                            help="id field of the sqlite file", default='originfid')     

        parser.add_argument("-classif", dest="classifield", action="store", \
                            help="classif field of the sqlite file", default='value_0')
        
        parser.add_argument("-ndept", dest="ndept", action="store", \
                        help="departement number for directory and selection", required = True)
                            
        args = parser.parse_args()
 
        #os.chdir(args.path)

        if not os.path.exists(args.out+"/dept_%s"%(args.ndept)) :
            print "Le dossier correspondant au departement %s n'existe pas dans le dossier de sortie. Le departement n'existe pas ou bien, l'etape oso_extract n'a pas ete effectuee. Arret"%(args.ndept)
            sys.exit()
         
        if not os.path.exists(args.path+"/dept_%s"%(args.ndept)) :  
            os.mkdir(args.path+"/dept_%s"%(args.ndept))
        else :
            print "le dossier %s existe deja."%("dept_"+args.ndept)
            
        time_calc_stats, non_conformity = stats_sqlite(args.sqlite, args.path +"/dept_%s"%(args.ndept), args.idfield, args.classifield)
    
        with open(args.path+"/dept_%s"%(args.ndept)+"/log_%s_stats_pandas.csv"%(args.ndept), "w") as csvfile :
            csvfile.write("time_calc_stats;non_conformity\n")
            csvfile.close()
        
        #initialise un fichier log de serialisation tif
        with open(args.path+"/dept_%s"%(args.ndept)+"/log_%s_stats_pandas.csv"%(args.ndept), "a") as csvfile :
            csvfile.write("%s;%s\n"%(round(time_calc_stats,0),non_conformity))
            csvfile.close()
            
        shutil.copyfile(args.path+"/dept_%s"%(args.ndept)+"/stats.csv", args.out+"/dept_%s"%(args.ndept)+"/stats.csv")
        shutil.copyfile(args.path+"/dept_%s"%(args.ndept)+"/log_%s_stats_pandas.csv"%(args.ndept), \
                        args.out+"/dept_%s"%(args.ndept)+"/log_%s_stats_pandas.csv"%(args.ndept))

