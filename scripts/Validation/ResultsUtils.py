# !/usr/bin/python
# -*- coding: utf-8 -*-

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


def remove_undecidedlabel(conf_mat_dic, undecidedlabel):
    """
    usage : use to remove samples with the undecidedlabel label from the confusion matrix
    """
    # remove prod labels
    for _, prod_dict in conf_mat_dic.items():
        prod_dict.pop(undecidedlabel, None)

    # remove ref labels
    conf_mat_dic.pop(undecidedlabel, None)

    return conf_mat_dic


def parse_csv(csv_in):
    """
    parse OTB's confusion matrix

    Parameters
    ----------
    csv_in : string
        path to a OTB csv file

    Example
    -------
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

    Return
    ------
    collections.OrderedDict()
        confusion matrix
    """
    import collections
    import csv

    with open(csv_in, 'rb') as csvfile:
        csv_reader = csv.reader(csvfile)
        ref_lab = [elem.replace("#Reference labels (rows):", "") for elem in csv_reader.next()]
        prod_lab = [elem.replace("#Produced labels (columns):", "") for elem in csv_reader.next()]
        all_labels = sorted([int(label) for label in list(set(ref_lab + prod_lab))])

        # construct confusion matrix structure and init it at 0
        matrix = collections.OrderedDict()
        for lab_ref in all_labels:
            matrix[lab_ref] = collections.OrderedDict()
            for lab_prod in all_labels:
                matrix[lab_ref][lab_prod] = 0

        # fill-up confusion matrix
        csv_dict = csv.DictReader(csvfile, fieldnames=prod_lab)
        for row_num, row_ref in enumerate(csv_dict):
            for klass, value in row_ref.items():
                ref = int(ref_lab[row_num])
                prod = int(klass)
                matrix[ref][prod] += float(value)

    return matrix


def get_coeff(matrix):
    """
    use to extract coefficients (Precision, Recall, F-Score, OA, K)
    from a confusion matrix.

    Parameters
    ----------

    matrix : collections.OrderedDict
        a confusion matrix stored in collections.OrderedDict dictionnaries

    Example
    -------
        >>> conf_mat_dic = OrderedDict([(1, OrderedDict([(1, 50), (2, 78), (3, 41)])),
        >>>                             (2, OrderedDict([(1, 20), (2, 52), (3, 31)])),
        >>>                             (3, OrderedDict([(1, 27), (2, 72), (3, 98)]))])
        >>> kappa, oacc, p_dic, r_dic, f_dic = get_coeff(conf_mat_dic)
        >>> print p_dic[1]
        >>> 0.5154639175257731

    Return
    ------
    list
        Kappa, OA, Precision, Recall, F-Score. Precision, Recall, F-Score
        are collections.OrderedDict
    """
    import collections

    nan = -1000
    classes_labels = matrix.keys()

    oacc_nom = sum([matrix[class_name][class_name] for class_name in matrix.keys()])
    nb_samples = sum([matrix[ref_class_name][prod_class_name] for ref_class_name in matrix.keys() for prod_class_name in matrix.keys()])

    # compute overall accuracy
    if nb_samples != 0.0:
        oacc = float(oacc_nom) / float(nb_samples)
    else:
        oacc = nan

    p_dic = collections.OrderedDict()
    r_dic = collections.OrderedDict()
    f_dic = collections.OrderedDict()
    lucky_rate = 0.
    for classe_name in classes_labels:
        oacc_class = matrix[classe_name][classe_name]
        p_denom = sum([matrix[ref][classe_name] for ref in classes_labels])
        r_denom = sum([matrix[classe_name][ref] for ref in classes_labels])
        if float(p_denom) != 0.0:
            p_class = float(oacc_class) / float(p_denom)
        else:
            p_class = nan
        if float(r_denom) != 0.0:
            r_class = float(oacc_class) / float(r_denom)
        else:
            r_class = nan
        if float(p_class + r_class) != 0.0:
            f_class = float(2.0 * p_class * r_class) / float(p_class + r_class)
        else:
            f_class = nan
        p_dic[classe_name] = p_class
        r_dic[classe_name] = r_class
        f_dic[classe_name] = f_class

        lucky_rate += p_denom * r_denom

    k_denom = float((nb_samples * nb_samples) - lucky_rate)
    k_nom = float((oacc * nb_samples * nb_samples) - lucky_rate)
    if k_denom != 0.0:
        kappa = k_nom / k_denom
    else:
        kappa = nan

    return kappa, oacc, p_dic, r_dic, f_dic


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


def get_rgb_mat(norm_conf, diag_cmap, not_diag_cmap):
    """
    usage convert normalise confusion matrix to a RGB image
    """
    rgb_list = []
    for row_num, row in enumerate(norm_conf):
        rgb_list_row = []
        for col_num, col in enumerate(row):
            if col_num == row_num:
                rgb_list_row.append(diag_cmap(col))
            else:
                rgb_list_row.append(not_diag_cmap(col))
        rgb_list.append(rgb_list_row)
    return rgb_list


def get_rgb_pre(pre_val, coeff_cmap):
    """
    convert values to a RGB code thanks to a colormap
    """
    rgb_list = []
    for raw in pre_val:
        raw_rgb = []
        for val in raw:
            raw_rgb.append(coeff_cmap(val))
        rgb_list.append(raw_rgb)
    return rgb_list


def get_rgb_rec(coeff, coeff_cmap):
    """
    usage convert normalise confusion matrix to a RGB image
    """
    rgb_list = []
    for raw in coeff:
        raw_rgb = []
        for val in raw:
            if val != 0.:
                raw_rgb.append(coeff_cmap(val))
            else:
                raw_rgb.append((0, 0, 0, 0))
        rgb_list.append(raw_rgb)
    return rgb_list


def normalize_conf(conf_mat_array, norm="ref"):
    """
    function use to normalize a numpy array representing a confusion matrix
    with ref as row and production in column
    """
    import numpy as np
    nan = -1
    if norm.lower() == "prod":
        conf_mat_array = np.transpose(conf_mat_array)
    norm_conf = []
    for i in conf_mat_array:
        raw_sum = 0
        tmp_arr = []
        raw_sum = sum(i, 0)
        for j in i:
            if float(raw_sum) != 0:
                tmp_arr.append(float(j) / float(raw_sum))
            else:
                tmp_arr.append(nan)
        norm_conf.append(tmp_arr)
    norm_conf = np.array(norm_conf)
    if norm.lower() == "prod":
        norm_conf = np.transpose(norm_conf)
    return norm_conf


def fig_conf_mat(conf_mat_dic, nom_dict, kappa, oacc, p_dic, r_dic, f_dic,
                 out_png, dpi=900, write_conf_score=True,
                 grid_conf=False, conf_score="count",
                 point_of_view="ref"):
    """
    usage : generate a figure representing the confusion matrix
    """
    import numpy as np
    import matplotlib
    matplotlib.get_backend()
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.gridspec as gridspec

    labels_ref = [nom_dict[lab] for lab in conf_mat_dic.keys()]
    labels_prod = [nom_dict[lab] for lab in conf_mat_dic[conf_mat_dic.keys()[0]].keys()]

    # convert conf_mat_dic to a list of lists
    conf_mat_array = np.array([[v for __, v in prod_dict.items()] for _, prod_dict in conf_mat_dic.items()])

    color_map_coeff = plt.cm.RdYlGn
    diag_cmap = plt.cm.RdYlGn
    not_diag_cmap = plt.cm.Reds

    # normalize by ref samples
    norm_conf = normalize_conf(conf_mat_array, norm=point_of_view)
    rgb_matrix = get_rgb_mat(norm_conf, diag_cmap, not_diag_cmap)

    fig = plt.figure(figsize=(10, 10))
    grid_s = gridspec.GridSpec(3, 3, width_ratios=[1, 1.0 / len(labels_ref), 1.0 / len(labels_ref)],
                               height_ratios=[1, 1.0 / len(labels_prod), 1.0 / len(labels_prod)])
    grid_s.update(wspace=0.1, hspace=0.1)
    plt.clf()
    axe = fig.add_subplot(grid_s[0])
    axe.set_aspect(1)
    axe.xaxis.tick_top()
    axe.xaxis.set_label_position('top')
    # confusion's matrix grid
    if grid_conf:
        axe.set_xticks(np.arange(-.5, len(labels_prod), 1), minor=True)
        axe.set_yticks(np.arange(-.5, len(labels_ref), 1), minor=True)
        axe.grid(which='minor', color='gray', linestyle='-', linewidth=1, alpha=0.5)

    maxtrix = norm_conf
    axe.imshow(rgb_matrix,
               interpolation='nearest', alpha=0.8, aspect='auto')

    width, height = maxtrix.shape
    if write_conf_score:
        for x_coord in xrange(width):
            for y_coord in xrange(height):
                if conf_score.lower() == "count":
                    axe.annotate(str(conf_mat_array[x_coord][y_coord]), xy=(y_coord, x_coord),
                                 horizontalalignment='center',
                                 verticalalignment='center',
                                 fontsize='xx-small',
                                 rotation=45)
                elif conf_score.lower() == "percentage":
                    axe.annotate("{:.1f}%".format(maxtrix[x_coord][y_coord] * 100.0),
                                 xy=(y_coord, x_coord),
                                 horizontalalignment='center',
                                 verticalalignment='center',
                                 fontsize='xx-small',
                                 rotation=45)

    plt.xticks(range(width), labels_prod, rotation=90)
    plt.yticks(range(height), labels_ref)

    # Recall
    ax2 = fig.add_subplot(grid_s[1])
    rec_val = np.array([[0, r_val] for _, r_val in r_dic.items()])

    rec_val_rgb = get_rgb_rec(rec_val, color_map_coeff)
    ax2.imshow(rec_val_rgb,
               interpolation='nearest', alpha=0.8,
               aspect='auto')

    ax2.set_xlim(0.5, 1.5)
    ax2.set_title('Rappel', rotation=90, verticalalignment='bottom')
    ax2.get_yaxis().set_visible(False)
    ax2.get_xaxis().set_visible(False)

    for y_coord in xrange(len(labels_ref)):
        ax2.annotate("{:.3f}".format(rec_val[y_coord][1]), xy=(1, y_coord),
                     horizontalalignment='center',
                     verticalalignment='center',
                     fontsize='xx-small')
    # Precision
    pre_val = []
    ax3 = fig.add_subplot(grid_s[3])
    pre_val_tmp = [p_val for _, p_val in p_dic.items()]
    pre_val.append(pre_val_tmp)
    pre_val.append(pre_val_tmp)
    pre_val = np.array(pre_val)

    pre_val_rgb = get_rgb_pre(pre_val, color_map_coeff)
    ax3.imshow(pre_val_rgb,
               interpolation='none', alpha=0.8, aspect='auto')
    ax3.set_ylim(0.5, 1.5)
    ax3.get_yaxis().set_visible(False)

    for x_coord in xrange(len(labels_prod)):
        ax3.annotate("{:.3f}".format(pre_val[0][x_coord]), xy=(x_coord, 1),
                     horizontalalignment='center',
                     verticalalignment='center',
                     fontsize='xx-small')
    ax3.set_xlabel("Precision")
    ax3.set_xticklabels([])

    # F-score
    ax4 = fig.add_subplot(grid_s[2])
    fs_val = np.array([[0, f_val] for _, f_val in f_dic.items()])
    fs_val_rgb = get_rgb_rec(fs_val, color_map_coeff)
    ax4.imshow(fs_val_rgb,
               interpolation='none', alpha=0.8, aspect='auto')
    ax4.set_xlim(0.5, 1.5)
    ax4.set_title('F-Score', rotation=90, verticalalignment='bottom')
    ax4.get_yaxis().set_visible(False)
    ax4.get_xaxis().set_visible(False)

    for y_coord in xrange(len(labels_ref)):
        ax4.annotate("{:.3f}".format(fs_val[y_coord][1]), xy=(1, y_coord),
                     horizontalalignment='center',
                     verticalalignment='center',
                     fontsize='xx-small')
    # Kappa and oacc
    fig.text(0, 1, 'KAPPA : {:.3f} OA : {:.3f}'.format(kappa, oacc), ha='center', va='center')

    plt.savefig(out_png, format='png', dpi=dpi, bbox_inches='tight')


def gen_confusion_matrix_fig(csv_in, out_png, nomenclature_path,
                             undecidedlabel=None, dpi=900,
                             write_conf_score=True,
                             grid_conf=False, conf_score='count',
                             point_of_view="ref"):
    """
    usage : generate a confusion matrix figure

    Parameters
    ----------

    csv_in : string
        path to a csv confusion matrix (OTB's computeConfusionMatrix output)
    out_png : string
        output path
    nomenclature_path : string
        path to the file which describre the nomenclature
    undecidedlabel : int
        undecided label
    dpi : int
        dpi
    write_conf_score : bool
        allow the display of confusion score
    grid_conf : bool
        display confusion matrix grid
    conf_score : string
        'count' / 'percentage'
    point_of_view : string
        'ref' / 'prod' define how to normalize the confusion matrix
    """
    conf_mat_dic = parse_csv(csv_in)

    if undecidedlabel:
        conf_mat_dic = remove_undecidedlabel(conf_mat_dic, undecidedlabel)

    kappa, oacc, p_dic, r_dic, f_dic = get_coeff(conf_mat_dic)

    nom_dict = get_nomenclature(nomenclature_path)

    fig_conf_mat(conf_mat_dic, nom_dict, kappa, oacc, p_dic, r_dic, f_dic,
                 out_png, dpi, write_conf_score, grid_conf, conf_score,
                 point_of_view)


def get_max_labels(conf_mat_dic, nom_dict):
    """
    return the maximum len of all labels
    """
    labels_ref = [nom_dict[lab] for lab in conf_mat_dic.keys()]
    labels_prod = [nom_dict[lab] for lab in conf_mat_dic[conf_mat_dic.keys()[0]].keys()]

    labels = set(labels_prod + labels_ref)
    return max([len(lab) for lab in labels]), labels_prod, labels_ref


def create_cell(string, max_size):
    """
    create a string of size max_size and return input string centered
    """
    if len(string) > max_size:
        max_size = len(string)

    new_string = []
    out = ""
    for i in range(max_size):
        new_string.append(" ")

    start = round((max_size - len(string)) / 2.0)
    for i in range(len(string)):
        new_string[i + int(start)] = string[i]

    for i in range(len(new_string)):
        out = out + new_string[i]
    return out


def get_conf_max(conf_mat_dic, nom_dict):
    """
    get confusion max by class

    Parameters
    ----------
    conf_mat_dic : OrderedDict
        dictionnary representing a confusion matrix
    nom_dict : dict
        dictionnary linking label to class name

    Example
    -------
        >>> conf_mat_dic = OrderedDict([(1, OrderedDict([(1, 20), (2, 10), (3, 11)])),
        >>>                             (2, OrderedDict([(1, 10), (2, 20), (3, 2)])),
        >>>                             (3, OrderedDict([(1, 0), (2, 11), (3, 21)]))])
        >>> nom_dict = {1: 'A', 2: 'B', 3: 'C'}
        >>> print get_conf_max(conf_mat_dic, nom_dict)
        >>> {1:['A','C','B'], 2:['B','A','C'],3:['C','B','A']}

    Return
    ------
    dict
        confusion max between labels
    """
    import collections

    conf_max = {}
    for class_ref, prod in conf_mat_dic.items():
        buff = collections.OrderedDict()
        for class_prod, value in prod.items():
            buff[nom_dict[class_prod]] = value
        buff = sorted(buff.iteritems(), key=lambda (k, v): (v, k))[::-1]
        conf_max[class_ref] = [class_name for class_name, value in buff]

    return conf_max


def compute_interest_matrix(all_matrix, f_interest="mean"):
    """
    thanks to a list of matrix, compute the mean
    """
    import collections
    import numpy as np

    # get all ref' labels
    ref_labels = []
    prod_labels = []
    for c_matrix in all_matrix:
        ref_labels += [ref for ref, _ in c_matrix.items()]
        prod_labels += [prod_label for _, prod in c_matrix.items() for prod_label, _ in prod.items()]

    ref_labels = sorted(list(set(ref_labels)))
    prod_labels = sorted(list(set(prod_labels)))

    # matrix will contains by couple of ref / prod the list of values
    # init matrix
    matrix = collections.OrderedDict()
    output_matrix = collections.OrderedDict()
    for ref_label in ref_labels:
        matrix[ref_label] = collections.OrderedDict()
        output_matrix[ref_label] = collections.OrderedDict()
        for prod_label in prod_labels:
            matrix[ref_label][prod_label] = []
            output_matrix[ref_label][prod_label] = -1
    # fill-up matrix
    for c_matrix in all_matrix:
        for ref_lab, prod in c_matrix.items():
            for prod_lab, prod_val in prod.items():
                matrix[ref_lab][prod_lab].append(prod_val)
    # Compute interest output matrix
    for ref_lab, prod in matrix.items():
        for prod_lab, prod_val in prod.items():
            if f_interest.lower() == "mean":
                output_matrix[ref_lab][prod_lab] = "{0:.2f}".format(np.mean(matrix[ref_lab][prod_lab]))

    return output_matrix


def get_interest_coeff(runs_coeff, nb_lab, f_interest="mean"):
    """
    use to compute mean coefficient and 95% confidence interval.
    store it by class as string
    """
    import collections
    import numpy as np
    from scipy import stats

    nb_run = len(runs_coeff)

    # get all labels
    for run in runs_coeff:
        ref_labels = [label for label, value in run.items()]
    ref_labels = sorted(list(set(ref_labels)))
    # init
    coeff_buff = collections.OrderedDict()
    for ref_lab in ref_labels:
        coeff_buff[ref_lab] = []
    # fill-up
    for run in runs_coeff:
        for label, value in run.items():
            coeff_buff[label].append(value)
    # Compute interest coeff
    coeff_out = collections.OrderedDict()
    for label, values in coeff_buff.items():
        if f_interest.lower() == "mean":
            mean = np.mean(values)
            _, b_sup = stats.t.interval(0.95, nb_lab - 1,
                                        loc=np.mean(values),
                                        scale=stats.sem(values))
            if nb_run > 1:
                coeff_out[label] = "{:.3f} +- {:.3f}".format(mean, b_sup - mean)
            elif nb_run == 1:
                coeff_out[label] = "{:.3f}".format(mean)
    return coeff_out


def stats_report(csv_in, nomenclature_path, out_report, undecidedlabel=None):
    """
    usage : sum-up statistics in a txt file
    """
    import numpy as np
    from scipy import stats

    nb_seed = len(csv_in)
    all_k = []
    all_oa = []
    all_p = []
    all_r = []
    all_f = []
    all_matrix = []
    for csv in csv_in:
        conf_mat_dic = parse_csv(csv)
        if undecidedlabel:
            conf_mat_dic = remove_undecidedlabel(conf_mat_dic, undecidedlabel)
        kappa, oacc, p_dic, r_dic, f_dic = get_coeff(conf_mat_dic)
        all_matrix.append(conf_mat_dic)
        all_k.append(kappa)
        all_oa.append(oacc)
        all_p.append(p_dic)
        all_r.append(r_dic)
        all_f.append(f_dic)

    conf_mat_dic = compute_interest_matrix(all_matrix, f_interest="mean")
    nom_dict = get_nomenclature(nomenclature_path)
    size_max, labels_prod, labels_ref = get_max_labels(conf_mat_dic, nom_dict)
    p_mean = get_interest_coeff(all_p, nb_lab=len(labels_ref), f_interest="mean")
    r_mean = get_interest_coeff(all_r, nb_lab=len(labels_ref), f_interest="mean")
    f_mean = get_interest_coeff(all_f, nb_lab=len(labels_ref), f_interest="mean")

    confusion_max = get_conf_max(conf_mat_dic, nom_dict)

    coeff_summarize_lab = ["Classes", "Precision mean", "Rappel mean", "F-score mean", "Confusion max"]
    label_size_max = max([len(c_title) for c_title in coeff_summarize_lab])
    label_size_max_p = max([len(coeff) for lab, coeff in p_mean.items()])
    label_size_max_r = max([len(coeff) for lab, coeff in r_mean.items()])
    label_size_max_f = max([len(coeff) for lab, coeff in f_mean.items()])
    label_size_max = max([label_size_max, label_size_max_p, label_size_max_r, label_size_max_f, size_max])

    with open(out_report, "w") as res_file:
        res_file.write("#row = reference\n#col = production\n\n*********** Matrice de confusion ***********\n\n")

        # Confusion Matrix
        prod_ref_labels = "".join([" " for _ in range(size_max)]) + "|" + "|".join(create_cell(label, size_max) for label in labels_prod) + "\n"
        res_file.write(prod_ref_labels)

        for lab_ref, prod_conf in conf_mat_dic.items():
            prod = ""
            prod += create_cell(nom_dict[lab_ref], size_max) + "|"
            for _, conf_val in prod_conf.items():
                prod += create_cell(str(conf_val), size_max) + "|"
            prod += create_cell(nom_dict[lab_ref], size_max) + "\n"
            res_file.write(prod)

        # KAPPA and OA
        kappa_mean = np.mean(all_k)
        oacc_mean = np.mean(all_oa)

        kappa = "\nKAPPA : {:.3f}\n".format(kappa_mean)
        oacc = "OA : {:.3f}\n\n".format(oacc_mean)
        if nb_seed > 1:
            _, k_sup = stats.t.interval(0.95, len(labels_ref) - 1, loc=np.mean(all_k), scale=stats.sem(all_k))
            kappa = "\nKAPPA : {:.3f} +- {:.3f}\n".format(kappa_mean, k_sup - kappa_mean)
            _, oa_sup = stats.t.interval(0.95, len(labels_ref) - 1, loc=np.mean(all_oa), scale=stats.sem(all_oa))
            oacc = "OA : {:.3f} +- {:.3f}\n\n".format(oacc_mean, oa_sup - oacc_mean)
        res_file.write(kappa)
        res_file.write(oacc)

        # Precision, Recall, F-score, max confusion
        sum_head = [create_cell(lab, label_size_max) for lab in coeff_summarize_lab]
        sum_head = " | ".join(sum_head) + "\n"
        sep_c = "-"
        sep = ""
        for _ in range(len(sum_head)):
            sep += sep_c
        res_file.write(sum_head)
        res_file.write(sep + "\n")
        for label in p_dic.keys():
            class_sum = [create_cell(nom_dict[label], label_size_max),
                         create_cell(p_mean[label], label_size_max),
                         create_cell(r_mean[label], label_size_max),
                         create_cell(f_mean[label], label_size_max),
                         ", ".join(confusion_max[label][0:3])]
            res_file.write(" | ".join(class_sum) + "\n")
