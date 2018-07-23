# -*- coding: utf-8 -*-
""" 
Cancer Subtype Analysis

Note that Tybalt uses python version 3.5
The associated environment can be activated via:
    conda activate tybalt
"""
import os
import csv
import numpy as np
from scipy.stats import skew, norm
from sklearn import preprocessing
from tybalt_util import Util

import matplotlib as mpl
mpl.use('TkAgg')
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# our helper class
util = Util()

# save gene list to txt file, with one gene per row
def save_gene_list (data, fn):
    fn = os.path.join(util.base, 'results', fn)
    with open(fn, 'w', newline='') as f:
        writer = csv.writer(f)
        for d in data:
            writer.writerow([d])

# replicate the result in hgsc_subtypes_tybalt.ipynb, Out[9]
def subtype_mean ():
    # get the indices of the four subtypes
    meta = util.read_meta()
    ids = util.join_meta()
    names = ['Differentiated', 'Immunoreactive', 'Mesenchymal', 'Proliferative']
    groups = [util.subtype_group(meta, ids, name) for name in names]

    # aggregate LS based on types
    z = util.read_ls()
    z_agg = []
    for g in groups:
        z_agg.append(np.mean(z[g], axis=0))
    z_agg = np.asarray(z_agg, dtype=float)

    # pretty print
    for i in range(4):
        print('{} {}'.format(names[i], np.around(z_agg[i, :10], decimals=3)))
    
    return z_agg

# turn array into a dictionary
def arr_to_dict (arr):
    res = {}
    for i in arr:
        res[i] = 1
    return res

def plot_vector (vec, fn):
    # 1. make the axis a unit vector
    v = preprocessing.normalize(vec.reshape(1, -1))

    # 2. get z coordinates of all subtypes
    header = util.read_header()
    meta = util.read_meta()
    ids = util.join_meta()
    names = ['Mesenchymal', 'Immunoreactive', 'Proliferative', 'Differentiated']
    groups = [util.subtype_group(meta, ids, name) for name in names]
    z = util.read_ls()
    groups = [z[g] for g in groups]

    # 3. project
    dist = [np.dot(g, v.T).flatten() for g in groups]

    # 3. plot
    x = []
    y = []
    for i in range(len(names)):
        x += [names[i]] * dist[i].shape[0]
        y = np.append(y, dist[i])
    print(len(x), y.shape)
    df = pd.DataFrame({'Subtype': x, 'Attribute Vector': y})
    plt.figure()
    sns.swarmplot(x = 'Subtype', y = 'Attribute Vector', data = df)
    plt.savefig('./result/{}.png'.format(fn))

# decode the centroid of mesen or immuno group, and find the max diff genes
# compare our gene list with their list
def im_vector ():
    # get the indices of the two subtypes
    header = util.read_header()
    meta = util.read_meta()
    ids = util.join_meta()
    names = ['Mesenchymal', 'Immunoreactive']
    groups = [util.subtype_group(meta, ids, name) for name in names]

    # compute centroid
    z = util.read_ls()
    means = np.asarray([np.mean(z[g], axis=0) for g in groups], dtype=float)

    # decode centroid
    decoder = util.read_decoder()
    genes = decoder.predict(means)
    diff = genes[0] - genes[1] # mesenchymal - immunoreactive

    # histogram, skewness test and plot distrubtion along vector
    plot_vector(means[0] - means[1], 'mesen-immuno-swarm')
    plt.figure()
    plt.hist(diff, 20, facecolor='pink', alpha=0.75)
    plt.title('Mesenchymal - Immunoreactive')
    plt.xlabel('Gene expression diff')
    plt.ylabel('Count')
    plt.savefig('./result/mesen-immuno-diff.png')
    print('Skewness: {}'.format(skew(diff)))

    # output our "high weight genes"
    pos, neg = high_weight_genes_quantile(diff, header, 2.5)
    save_gene_list(pos, 'mesenchymal_genes_sd.txt')
    save_gene_list(neg, 'immunoreactive_genes_sd.txt')
    print('Totol genes 2.5 standard deviation away:')
    print('{} mesenchymal, {} immunoreactive'.format(len(pos), len(neg)))

# decode the centroid of proliferative or differentiated group, and find the max diff genes
def pd_vector ():
    # get the indices of the two subtypes
    header = util.read_header()
    meta = util.read_meta()
    ids = util.join_meta()
    names = ['Proliferative', 'Differentiated']
    groups = [util.subtype_group(meta, ids, name) for name in names]

    # compute centroid
    z = util.read_ls()
    means = np.asarray([np.mean(z[g], axis=0) for g in groups], dtype=float)

    # decode centroid
    decoder = util.read_decoder()
    genes = decoder.predict(means)
    diff = genes[0] - genes[1] # mesenchymal - immunoreactive

    # histogram and skewness test
    plot_vector(means[0] - means[1], 'pro-def-swarm')
    plt.figure()
    plt.hist(diff, 20, facecolor='pink', alpha=0.75)
    plt.title('Proliferative - Differentiated')
    plt.xlabel('Gene expression diff')
    plt.ylabel('Count')
    plt.savefig('./result/pro-def-diff.png')
    print('Skewness: {}'.format(skew(diff)))

    # output our "high weight genes"
    pos, neg = high_weight_genes_quantile(diff, header, 2.5)
    save_gene_list(pos, 'proliferative_genes_sd.txt')
    save_gene_list(neg, 'differentiated_genes_sd.txt')
    print('Totol genes 2.5 standard deviation away:')
    print('{} proliferative, {} differentiated'.format(len(pos), len(neg)))

# helper function
def high_weight_genes (w, header, highsd=2):
    sd = np.std(w)
    mean = np.mean(w)
    print('Mean: {}, SD: {}'.format(mean, sd))
    pos = []
    neg = []
    for i in range(header.shape[0]):
        if w[i] > mean + highsd * sd:
            pos.append(header[i])
        if w[i] < mean - highsd * sd:
            neg.append(header[i])
    return pos, neg

# compute quantile for the given SD in a standard normal
# and then use the quantile as threshold
def high_weight_genes_quantile (w, header, highsd=2):
    n = w.shape[0]
    cutoff = n - int(n * norm.cdf(highsd))
    srt = np.argsort(w)
    neg = [header[i] for i in srt[:cutoff]]
    pos = [header[i] for i in srt[-cutoff:]]
    return pos, neg

# like im_vector, but don't do the diff
def im_mean ():
    # get the indices of the two subtypes
    header = util.read_header()
    meta = util.read_meta()
    ids = util.join_meta()
    names = ['Mesenchymal', 'Immunoreactive']
    groups = [util.subtype_group(meta, ids, name) for name in names]

    # compute centroid
    z = util.read_ls()
    means = np.asarray([np.mean(z[g], axis=0) for g in groups], dtype=float)

    # decode centroid
    decoder = util.read_decoder()
    genes = decoder.predict(means)
    save_gene_list(high_weight_genes(genes[0], header)[0], 'mesenchymal_genes.txt')
    save_gene_list(high_weight_genes(genes[1], header)[0], 'immunoreactive_genes.txt')

# cluster quality of mesen or immuno type
def cluster_quality ():
    # get the indices of the two subtypes
    meta = util.read_meta()
    ids = util.join_meta()
    names = ['Mesenchymal', 'Immunoreactive', 'Proliferative', 'Differentiated']
    groups = [util.subtype_group(meta, ids, name) for name in names]

    z = util.read_ls()

    print('Cluster score in z space:')
    l = len(names)
    for i in range(l):
        score = util.cluster_score(groups[i], z)
        print('{}: {}%'.format(names[i], int(score * 100)))

    print('Cluster score in raw X')
    X = util.read_raw()
    for i in range(l):
        score = util.cluster_score(groups[i], X)
        print('{}: {}%'.format(names[i], int(score * 100)))

# compare their and our high weight genes
def compare_gene_list ():
    l = 8
    ours = ['mesenchymal', 'immunoreactive', 'proliferative', 'differentiated']
    ours = [ours[int(i/2)] for i in range(l)]
    prefix = ['87', '56', '56', '87', '79', '38', '38', '79']
    suffix = ['pos', 'neg'] * 4
    theirs = ['hgsc_node{}genes_{}.tsv'.format(prefix[i], suffix[i]) for i in range(l)]

    for i in range(l):
        p_ours = os.path.join(util.base, 'results', '{}_genes_sd.txt'.format(ours[i]))
        p_theirs = os.path.join(util.base, 'results', theirs[i])
        gene_ours = util.read_tsv(p_ours, str, 0, 0)[:, 0]
        gene_theirs = util.read_tsv(p_theirs, str, 0, 0)[:, 0]
        lookup = arr_to_dict(gene_theirs)
        count = 0
        for gene in gene_ours:
            if gene in lookup:
                count += 1
        print('Comparing {} and {} {}:'.format(ours[i], prefix[i], suffix[i]))
        print('Overlap | Ours | Theirs: {} | {} | {}'.format(count, gene_ours.shape[0], gene_theirs.shape[0]))

if __name__ == '__main__':
    # cluster_quality ()
    im_vector()
    pd_vector()
    compare_gene_list()
