# -*- coding: utf-8 -*-
"""
Created on Fri Mar 10 09:44:11 2017

@author: donatien
"""

#initialise un fichier log
with open(out+"/"+log, "w") as csvfile :
    csvfile.write("tile;nb_feature_tile;time_condition_tile;time_extent_tile;\
    time_select_id_neighbors;nb_features_neighbors;time_extent_neighbors;extent_xmin;\
    extent_xmax;extent_ymin;extent_ymax;time_vectorisation;time_douglas;\
    time_hermite;time_simplification;time_treatment_total\n")
    csvfile.close()