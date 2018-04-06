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

def parse_csv(csv_in):
    """
    usage : use to parse OTB's confusion matrix
    IN
    csv_in [string] path to a csv file
    
    OUT
    matrix [collections.OrderedDict of collections.OrderedDict]

    example :
    if csv_in contain :
    #Reference labels (rows):11,12,31,32,34,36,41,42,43,44,45,51,211,221,222
    #Produced labels (columns):11,12,31,32,34,36,41,42,43,44,45,51,211,221,222,255
    11100,586,13,2,54,0,0,25,2,0,0,2,291,47,4,338
    434,14385,12,0,171,1,0,31,43,0,0,3,475,52,10,484
    98,8,3117,109,160,0,0,3,0,0,0,9,33,105,66,494
    4,0,38,571,5,0,0,3,0,0,0,1,13,9,0,47
    53,310,72,52,9062,0,1,431,27,0,0,0,459,56,16,1065
    37,40,4,0,4,0,0,6,1,0,0,0,49,11,1,59
    1,1,0,0,13,0,56,146,24,0,0,0,0,0,0,31
    41,158,6,4,200,0,42,4109,249,1,0,11,390,46,11,642
    50,76,1,3,20,0,17,478,957,3,0,12,58,7,3,315
    1,5,0,0,0,0,0,22,102,12,0,0,0,0,0,20
    0,0,0,0,83,0,0,12,0,0,41,0,3,0,0,109
    95,66,3,4,0,1,0,3,12,0,0,6599,3,9,0,50
    171,425,30,9,348,0,0,9,0,0,0,0,17829,67,3,585
    180,166,111,4,93,0,0,61,5,0,0,5,668,1213,14,451
    159,143,1,0,180,0,0,33,0,0,0,0,149,22,304,258
    
    print matrix[11][221]
    > 4
    print matrix[11][222]
    > 338
    print matrix[255]
    > OrderedDict([(11, 0), (12, 0),..., (255, 0)])
    """
    import collections
    import csv

    with open(csv_in, 'rb') as csvfile:
        csv_reader = csv.reader(csvfile)
        ref_lab = [elem.replace("#Reference labels (rows):","") for elem in csv_reader.next()]
        prod_lab = [elem.replace("#Produced labels (columns):","") for elem in csv_reader.next()]

        all_labels = sorted(map(int, list(set(ref_lab + prod_lab))))

        #construct confusion matrix structure and init it at 0
        matrix = collections.OrderedDict()
        for lab in all_labels:
            matrix[lab] = collections.OrderedDict()
            for l in all_labels:
                matrix[lab][l] = 0

        #fill-up confusion matrix
        csv_dict = csv.DictReader(csvfile, fieldnames=prod_lab)
        for row_num, row_ref in enumerate(csv_dict):
            for klass, value in row_ref.items():
                ref = int(ref_lab[row_num])
                prod = int(klass)
                matrix[ref][prod] += int(value)

    return matrix

def get_coeff(matrix):
    """
    """
    import collections

    nan = -1000
    classes_labels = matrix.keys()

    OA_nom = sum([matrix[class_name][class_name] for class_name in matrix.keys()])
    nb_samples = sum([matrix[ref_class_name][prod_class_name] for ref_class_name in matrix.keys() for prod_class_name in matrix.keys()])


    if nb_samples != 0.0:
        OA = float(OA_nom)/float(nb_samples)
    else:
        OA = nan

    P_dic = collections.OrderedDict()
    R_dic = collections.OrderedDict()
    F_dic = collections.OrderedDict()
    luckyRate = 0.
    for classe_name in classes_labels:
        OA_class = matrix[classe_name][classe_name]
        P_denom = sum([matrix[ref][classe_name] for ref in classes_labels])
        R_denom = sum([matrix[classe_name][ref] for ref in classes_labels])
        if float(P_denom) != 0.0:
            P = float(OA_class) / float(P_denom)
        else:
            P = nan
        if float(R_denom) != 0.0:
            R = float(OA_class) / float(R_denom)
        else:
            R = nan
        if float(P + R) != 0.0:
            F = float(2.0 * P * R) / float(P + R)
        else:
            F = nan
        P_dic[classe_name] = P
        R_dic[classe_name] = R
        F_dic[classe_name] = F
    
        luckyRate += P_denom * R_denom

    K_denom = float((nb_samples * nb_samples) - luckyRate)
    K_nom = float((OA * nb_samples * nb_samples) - luckyRate)
    if K_denom != 0.0:
        K = K_nom / K_denom
    else:
        K = nan
    
    return K, OA, P_dic, R_dic, F_dic

def get_nomenclature(nom_path):
    """
    usage parse nomenclature file and return a python dictionary
    """
    import csv

    nom_dict = {}
    with open(nom_path, 'rb') as csvfile:
        csv = csv.reader(csvfile, delimiter=':')
        for class_name, label in csv:
            nom_dict[int(label)] = class_name
    return nom_dict


def get_RGB_mat(norm_conf, diag_cmap, not_diag_cmap):
    """
    usage convert normalise confusion matrix to a RGB image
    """
    RGB_list = []
    for row_num, row in enumerate(norm_conf):
        RGB_list_row = []
        for col_num, col in enumerate(row):
            if col_num == row_num:
                RGB_list_row.append(diag_cmap(col))
            else:
                RGB_list_row.append(not_diag_cmap(col))
        RGB_list.append(RGB_list_row)
    return RGB_list


def fig_conf_mat(conf_mat_dic, nom_dict, K, OA, P_dic, R_dic, F_dic, outputDir):
    """
    usage : generate a figure representing the confusion matrix
    """
    import os
    import numpy as np
    import matplotlib
    matplotlib.get_backend()
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec
    from matplotlib.axes import Subplot 
    output_results_name = "MajVoteConfusion.png"
    output_results = os.path.join(outputDir, output_results_name)
    nan = 0

    labels_ref = [nom_dict[lab] for lab in conf_mat_dic.keys()]
    labels_prod = [nom_dict[lab] for lab in conf_mat_dic[conf_mat_dic.keys()[0]].keys()]

    #convert conf_mat_dic to a list of lists
    conf_mat_array = np.array([[v for k, v in prod_dict.items()] for ref, prod_dict in conf_mat_dic.items()])

    color_map = plt.cm.RdYlGn
    diag_cmap = plt.cm.RdYlGn
    not_diag_cmap = plt.cm.Reds

    #normalize by ref samples
    norm_conf = []
    for i in conf_mat_array:
        a = 0
        tmp_arr = []
        a = sum(i, 0)
        for j in i:
            if float(a) != 0:
                tmp_arr.append(float(j) / float(a))
            else:
                tmp_arr.append(nan)
        norm_conf.append(tmp_arr)
    norm_conf = np.array(norm_conf)

    RGB_matrix = get_RGB_mat(norm_conf, diag_cmap, not_diag_cmap)
    
    fig = plt.figure(figsize=(10, 10))
    
    #gs = gridspec.GridSpec(2, 2, width_ratios=[1, 1.0 / len(labels_ref)], height_ratios=[1, 1.0 / len(labels_prod)])

    gs = gridspec.GridSpec(3, 3, width_ratios=[1, 1.0 / len(labels_ref), 1.0 / len(labels_ref)],
                           height_ratios=[1, 1.0 / len(labels_prod), 1.0 / len(labels_prod)])

    gs.update(wspace=0.0, hspace=0.0)
    
    plt.clf()
    ax = fig.add_subplot(gs[0])
    ax.set_aspect(1)
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top') 
    maxtrix = norm_conf

    res = ax.imshow(RGB_matrix, 
                    interpolation='nearest', alpha=0.8, aspect='auto')

    width, height = maxtrix.shape
    for x in xrange(width):
        for y in xrange(height):
            ax.annotate(str(conf_mat_array[x][y]), xy=(y, x), 
                        horizontalalignment='center',
                        verticalalignment='center',
                        fontsize='xx-small')

    plt.xticks(range(width), labels_prod, rotation=90)
    plt.yticks(range(height), labels_ref)
    
    #recall
    ax2 = fig.add_subplot(gs[1])
    rec_val= np.array([[0, r_val] for class_name, r_val in R_dic.items()])
    
    R = ax2.imshow(rec_val, cmap=color_map, 
                   interpolation='none', alpha=0.8, aspect='auto')

    ax2.set_xlim(0.5,1.5)
    ax2.title.set_text('Recall')
    ax2.get_yaxis().set_visible(False)
    ax2.get_xaxis().set_visible(False)

    
    for y in xrange(len(labels_ref)):
        ax2.annotate("{:.3f}".format(rec_val[y][1]), xy=(1, y), 
                    horizontalalignment='center',
                    verticalalignment='center',
                    fontsize='xx-small')
    
    #Precision
    pre_val = []
    ax3 = fig.add_subplot(gs[4])
    pre_val_tmp = [p_val for class_name, p_val in P_dic.items()]
    pre_val.append(pre_val_tmp)
    pre_val.append(pre_val_tmp)
    pre_val = np.array(pre_val)

    P = ax3.imshow(pre_val, cmap=color_map, 
                   interpolation='none', alpha=0.8, aspect='auto')
    ax3.set_ylim(0.5,1.5)
    ax3.get_yaxis().set_visible(False)

    for x in xrange(len(labels_prod)):
        ax3.annotate("{:.3f}".format(pre_val[0][x]), xy=(x, 1), 
                    horizontalalignment='center',
                    verticalalignment='center',
                    fontsize='xx-small')
    ax3.set_xlabel("Precision")
    ax3.set_xticklabels([])
    plt.tight_layout()

    plt.savefig(output_results, format='png', dpi=900, bbox_inches='tight')


def print_results(output_directory, nom_path, conf_mat_dic, K, OA, P_dic, R_dic, F_dic):
    """
    usage : print confusion matrix and coefficients in a txt file
    
    IN
    output_final_results [string] output path
    nom_path [string] path to the nomenclature file descriptor
    conf_mat_dic [OrderedDict() of OrderedDict()]
    K [float]
    OA [float]
    P_dic [OrderedDict()]
    R_dic [OrderedDict()]
    F_dic [OrderedDict()]
    """
    nom_dict = get_nomenclature(nom_path)

    fig_conf_mat(conf_mat_dic, nom_dict, K, OA, P_dic, R_dic, F_dic, output_directory)

