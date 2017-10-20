import numpy as np
from indra.util import read_unicode_csv

cell_lines = [
 'BT20',
 'HCC1806',
 'HS578T',
 'MCF10A',
 'MCF7',
 'MDAMB231',
 'PDX1258',
 'PDX1328',
 'SKBR3',
 'MDAMB134',
 'MDAMB157',
 'MDAMB361',
 'MDAMB436',
 'MDAMB453',
 'MDAMB468',
 'CAL51',
 'CAL851',
 'CAL120',
 'BT549',
 'HCC38',
 'HCC70',
 'HCC1395',
 'HCC1419',
 'HCC1500',
 'HCC1937',
 'HCC1954',
 'PDXHCI002',
 'CAMA1',
 'HCC1143',
 'HCC1428',
 'HME1',
 'MCF10AREP2',
 'SUM1315',
 'SUM149',
 'SUM159',
 'T47D',
]

def z_transform(val_arr):
    mu = np.nanmean(val_arr)
    sigma = np.nanstd(val_arr, ddof=1)
    return list((val_arr - mu) / sigma)

pms_col_map = {}
pms_filename = 'sources/Merged_dataset_normalized_subset.csv'
with open(pms_filename, 'rt') as f:
    pms_header = f.readline().strip().split(',')
    for col_ix, col in enumerate(pms_header):
        capcol = col.upper()
        if capcol in cell_lines:
            pms_col_map[capcol] = col_ix

ibaq_col_map = {}
with open('sources/ibaq_normalized.csv', 'rt') as f:
    ibaq_header = f.readline().strip().split(',')
    for col_ix, col in enumerate(ibaq_header):
        capcol = col.upper()
        if capcol in cell_lines:
            ibaq_col_map[capcol] = col_ix

# Get the data

# Get the ibaq data first
prot_labels = []
prot_rows = []
data_rows = []
data_labels = []
for row_ix, row in enumerate(read_unicode_csv('sources/ibaq_normalized.csv',
                                              skiprows=1)):
    values = []
    gene_name = row[0]
    for cell_line in cell_lines:
        col_ix = ibaq_col_map[cell_line]
        if not row[col_ix]:
            val = np.nan
        else:
            val = float(row[col_ix])
        float(val)
        values.append(val)
    values = np.array(values)
    z_scores = z_transform(values)
    prot_labels.append(gene_name)
    prot_rows.append(z_scores)
    data_labels.append(gene_name)
    data_rows.append(z_scores)

# Then get the phospho-MS data
site_labels = []
site_rows = []
for row_ix, row in enumerate(read_unicode_csv(pms_filename, skiprows=1)):
    values = []
    site_name = row[0]
    for cell_line in cell_lines:
        col_ix = pms_col_map[cell_line]
        if not row[col_ix]:
            val = np.nan
        else:
            val = float(row[col_ix])
        float(val)
        values.append(val)
    values = np.array(values)
    z_scores = z_transform(values)
    site_labels.append(gene_name)
    site_rows.append(z_scores)
    data_labels.append(site_name)
    data_rows.append(z_scores)

#prot_arr = np.array(prot_rows).T
#site_arr = np.array(site_rows).T
data_arr = np.array(data_rows)

print("Calculating correlation coefficients")
import scipy.stats
#scipy.stats.spearmanr(site_arr, prot_arr, nan_policy='omit')
corr = scipy.stats.spearmanr(data_arr, nan_policy='omit', axis=1)
np.save('brca_spearman.np', corr)

with open('brca_spearman_labels.txt', 'wt') as f:
    for row in data_labels:
        f.write('%s\n' % row)
