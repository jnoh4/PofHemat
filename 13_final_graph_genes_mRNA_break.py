# File name: 12_final_graph_genes_mRNA_break.py
# Last Edit: 10/22/2019
#
# Coded by: Joseph Noh
# Coded for: ZaroNoh et al. 2019
#
# PLEASE REFER TO THE READ_ME TO SEE HOW EACH .PY FILE RELATES TO
# THE PAPER
# 
# https://github.com/jnoh4/PofHemat
#
# Description: 
# Using the GMM parameters derived from the program 8_mRNA_adult.py,
# make a graph similar to the one produced in 10_final_graph_mRNA.py,
# but indicate where some of the genes of interest lie. The genes of
# of interest are currently identified only by comparing against MPPa,
# but this can be generalized with minor modifications to the code.

import sys
import numpy as np
import csv
import matplotlib.pyplot as plt

# Constants used for directory names
#
# raw_data - file with raw data
# gen_data - file with generated data
# imp_data - file with data imported from uniprot.org
# analysis - file with analysis
# read_cell_dir - additional extension for file to read data from
# write_cell_dir - additional extension for file to write data to
# data_dir - directory of the data
raw_data_dir = './raw_data/'
gen_data_dir = './gen_data/'
imp_data_dir = './imp_data/'
analysis_dir = './analysis/'
read_cell_dir = 'adult_aged/'
write_cell_dir = 'adult/mRNA/'
data_dir = '3_gene_intensity_navg.txt'
data_dir_2 = 'adult/mRNA/8_GMM_parameters.csv'
mRNA_dir = './raw_data/adult/mRNA.csv'

# Change this for analysis
cell_order = ['HSC', 'MPPa', 'MPPb', 'MPPc']
rainbow_color = {'HSC' : 'lightcoral', 'MPPa' : 'orange', 'MPPb' : 'forestgreen', 'MPPc' : 'mediumturquoise'}
MPPa_genes_reg = ['Hprt1', 'Ciapin1', 'Ssbp2']
MPPa_genes = ['Adnp']
MPPa_tick_pads = [8, 0, 16, 0]

# Constant for ease
PI = np.pi
def flush():
	sys.stdout.flush()

# Reads previously generated GMM parameters and returns the stats
# for the indicated cell type
def read_stats(cell, directory):
	with open(directory, 'rb') as r:
		reader = csv.reader(r, delimiter = ',')
		for row in reader:
			I_mu1 = row.index('mu1'); I_mu2 = row.index('mu2'); I_var1 = row.index('var1'); I_var2 = row.index('var2')
			I_weight1 = row.index('weight1'); I_weight2 = row.index('weight2'); I_UE = row.index('UE'); I_OE = row.index('OE')
			break;
		for row in reader:
			if row[0] == cell:
				return (float(row[I_mu1]), float(row[I_var1]), float(row[I_weight1]), 
					float(row[I_mu2]), float(row[I_var2]), float(row[I_weight2]), 
					float(row[I_UE]), float(row[I_OE]))

# Reads the raw data from the given directory and returns the list of cells, genes, and the data
# Removes cells that are not used; removes genes that are not used
def read_data_ordered(directory):
	cells = [] # List of cells used
	genes = [] # List of genes
	data = [] # Intensity values
	with open(directory, 'rb') as r:
		reader = csv.reader(r, delimiter = ',')
	# Record all cell names in the file
		for row in reader:
			for i in range(len(row) - 2):
				cell = row[i + 2]
				if cell.find('Aged') != -1:
					cell = 'a' + cell[4:]
				cells.append(cell)
			break
	# Record all gene names in the file
		for row in reader:
			genes.append(row[1])
			data.append(row[2:])
	cells = np.array(cells)
	data = np.array(data, dtype = float)

	# Only include cells that are used
	data_copy = []
	for i in range(len(cell_order)):
		cell = cell_order[i]
		index = (cells == cell)
		data_copy.append(data[:, index])
	data = np.transpose(np.array(np.squeeze(data_copy), dtype = float))

	# Remove genes that are not expressed in any cell types
	data_TF = (data > 0).astype(int)
	data_TF = np.sum(data_TF, axis = 1)
	data_TF = (data_TF > 0).astype(bool)
	data = data[data_TF, :]
	genes = np.array(genes, dtype = str)[data_TF]

	return genes, data

# Retrieve mappings generated in 2_gene_prot_mappings.py
# prot_gene_map - UniprotID : gene name mapping
# gene_prot_map - gene name : UniprotID mapping
# prot_aliases - List of sets of UniprotID (k) to sets of gene name (k + 1) mappings where 0 <= k <= n / 2
def retrieve_mappings():
	prot_gene_map = {}; gene_prot_map = {}; prot_aliases = []

	# UniprotID : gene name mapping bidirectionally
	with open(gen_data_dir + '2_prot_gene_single.txt', 'rb') as f:
		reader = csv.reader(f, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
		for row in reader:
			prot_gene_map[row[0]] = row[1]
			gene_prot_map[row[1]] = row[0]

	# {UniprotIDs} : {gene names}
	with open(gen_data_dir + '2_prot_gene_group.txt', 'rb') as f:
		reader = csv.reader(f, delimiter = ',', quotechar = '"', quoting = csv.QUOTE_MINIMAL)
		for row in reader:
	# Parse out row into {UniprotIDs} and {gene names}
			length = len(row)
			prots = set(('dummy',)) # 'dummy' used to initialize set of set
			genes = set(('dummy',))
			counter = 0 # Tracks column along row of a {UniprotIDs} : {gene names}
			while row[counter] != 'PROT:GENE': # Indicates end of list of UniprotIDs
				prots.add(row[counter])
				counter += 1
			counter += 1
			while counter < length: # Now at genes
				genes.add(row[counter])
				counter += 1
			prots.remove('dummy')
			genes.remove('dummy')
	# Add to prot_aliases
			prot_aliases.append(prots)
			prot_aliases.append(genes)

	return prot_gene_map, gene_prot_map, prot_aliases

# Reads the raw mRNA data from the given directory and returns an ordered, TPM mRNA
# dataset, removing cells that are not used; removes genes that are not used. Records
# genes that are not used. The recorded genes should theoretically be identical to
# the list generated from 8_mRNA_adult.py
def read_mRNA_ordered(directory, genes, prot_gene_map, gene_prot_map, prot_aliases):
	mRNA_only_genes = [] # Genes expressed in mRNA, but not in proteins
	mRNA_unmapped = [] # Genes expressed in mRNA, but unable to be mapped to anything
	mRNA_genes = [] # List of genes expressed in mRNA AND in proteins
	mRNA_data = [] # Data from the mRNA file
	mRNA_cells = [] # Order of cells as given in the mRNA file; used only for temporary reasons

	# Read from the TPM data
	with open(directory, 'rb') as r:
		reader = csv.reader(r, delimiter = ',')
		for row in reader:
			for i in range(len(row) - 1):
				mRNA_cells.append(row[i + 1])
			break
		for row in reader:
			gene = row[0] # mRNA gene name
			if gene in gene_prot_map: # Already mapped properly
				if gene not in genes: # Yes gene, no protein
					mRNA_only_genes.append(gene)
				else:
					mRNA_genes.append(gene)
					ROI = row[1:]
					for i in range(len(ROI)):
						if ROI[i] == '':
							ROI[i] = '0'
					mRNA_data.append(ROI)
			else: # Has not yet been mapped properly
				# Search in prot_aliases
				for i in range(len(prot_aliases) / 2):
					index = (2 * i) + 1
					if gene in prot_aliases[index]:
						for ele in prot_aliases[index]:
							if ele in gene_prot_map:
								gene = ele
								break
						break
				if gene not in gene_prot_map: # If gene is never found
					mRNA_unmapped.append(gene)
				else:
					if gene not in genes: # Yes gene, no protein
						mRNA_only_genes.append(gene)
					else:
						mRNA_genes.append(gene)
						ROI = row[1:]
						for i in range(len(ROI)):
							if ROI[i] == '':
								ROI[i] = '0'
						mRNA_data.append(ROI)

	# Order based on cells
	mRNA_data = np.array(np.squeeze(mRNA_data), dtype = float)
	mRNA_genes = np.array(mRNA_genes, dtype = str)
	new_data = []
	for i in range(len(cell_order)):
		cell = cell_order[i]
		index = mRNA_cells.index(cell)
		new_data.append(mRNA_data[:, index])
	mRNA_data = np.transpose(np.array(np.squeeze(new_data), dtype = float))

	# Record mRNA expressed, protein unexpressed
	w1 = open(analysis_dir + write_cell_dir + '12_mRNA_no_prot.csv', 'w+')
	for i in range(len(mRNA_only_genes)):
		w1.write(mRNA_only_genes[i] + '\n')
	w1.close()
	# Record mRNA expressed, no mappable protein
	w2 = open(analysis_dir + write_cell_dir + '12_mRNA_unmapped.csv', 'w+')
	for i in range(len(mRNA_unmapped)):
		w2.write(mRNA_unmapped[i] + '\n')
	w2.close()

	return mRNA_data, mRNA_genes

# Order the mRNA_data such that it is compatible with genes. Add 0 for any time the gene is not expressed
def expand_mRNA_genes(genes, mRNA_genes, mRNA_data):
	new_mRNA_data = []
	for i in range(len(genes)):
		gene = genes[i]
		if gene in mRNA_genes:
			index = mRNA_genes.tolist().index(gene)
			new_mRNA_data.append(mRNA_data[index,:])
		else:
			new_mRNA_data.append(np.zeros(len(mRNA_data[0,:]), dtype = float))

	return np.array(np.squeeze(new_mRNA_data), dtype = float)

# Find the log 2 of fold change differences between mRNA and protein
# of cell_order[i] against combinations of all other cells 
def comb_fold(i, data, mRNA_data, prot_mRNA_TF):
	fold_diff_cont = [] # Tracks fold changes in an ordered, continuous list
	fold_diff_arr = [] # Tracks fold changes in an array
	highs_names = [] # Order of cells compared to ith cell
	highs_genes = [] # Ordered indices of gene names wrt 'genes' that are recorded in fold_diff_cont
	# Compare against all other cell types except for itself
	for j in range(len(cell_order)):
		if j != i:
	# Find mutual expressions and calculate the difference between log2 fold changes for protein and mRNA
			both_express_ind = (prot_mRNA_TF[:, i] * prot_mRNA_TF[:, j]).astype(bool)
			prot_fold_change = np.log2(data[both_express_ind, i] / data[both_express_ind, j])
			mRNA_fold_change = np.log2(mRNA_data[both_express_ind, i] / mRNA_data[both_express_ind, j])
			fold_change_diff = prot_fold_change - mRNA_fold_change
	# Record the results
			fold_diff_cont = fold_diff_cont + fold_change_diff.tolist()
			fold_diff_arr.append(fold_change_diff)
			highs_names.append(cell_order[j])
			highs_genes.append(np.sort(np.where(both_express_ind))) # Sorting assumes that high_in_former is still in order
	fold_diff_dist = np.array(fold_diff_cont, dtype = float)

	return fold_diff_dist, fold_diff_arr, highs_names, highs_genes

# Directly modify the values and labels vector to include the gene label
# and the fold change difference value of the gene of interest
def get_gene_values(genes, highs_genes, highs_names, fold_diff_arr, OE, UE, values, labels):
	# Assumes that the gene is neither overexpressed nor underexpressed
	for i in range(len(MPPa_genes_reg)):
		gene = MPPa_genes_reg[i]
		my_list = genes[highs_genes[highs_names.index('MPPa')]].tolist()[0]
		if gene in my_list:
			index = my_list.index(gene)
			values.append(fold_diff_arr[i][index])
			labels.append(gene)

	# Assumes that the gene should be overexpressed or underexpressed, and error-checks otherwise
	for i in range(len(fold_diff_arr)):
		if highs_names[i] == 'MPPa':
			high = fold_diff_arr[i] # Fold changes in proteins that are detected in both cell types
			gene_indices = highs_genes[i] # Indices of genes that are expressed in both cell types, order-matched to the data
			gene_names = genes[np.squeeze(gene_indices)].tolist()
			for j in range(len(MPPa_genes)):
				try:
					gene_index = gene_names.index(MPPa_genes[j])
					value = high[gene_index]
					if value > OE or value < UE:
						values.append(value)
						labels.append(MPPa_genes[j])
					else:
						print('Debugger: an indicated gene is not actually either UE/OE by value'); flush()
				except ValueError:
   					print('Debugger: an indicated gene cannot be found in UE/OE list'); flush()		

# Make a graph and return the figure and axes. Contains predetermined variables,
# unless otherwise stated.
def make_graph(title, x_axis, y_axis, width, height, 
	scale_width, scale_height, font_title, font_axes, x_ticks, y_ticks, 
	pad_title, pad_x, pad_y, shift_x, shift_y):

	fig, (ax1, ax3, ax2) = plt.subplots(1, 3, sharey = False, figsize = (width ,height))
	fig.subplots_adjust(wspace = 0.05)

	ax1.set_title(title, size = font_title, pad = pad_title)
	ax1.set_xlabel(x_axis, size = font_axes, labelpad = pad_x)
	ax1.set_ylabel(y_axis, size = font_axes, labelpad = pad_y)

	plt.setp(ax1.get_xticklabels(), fontsize = x_ticks)
	plt.setp(ax2.get_xticklabels(), fontsize = x_ticks)
	plt.setp(ax3.get_xticklabels(), fontsize = x_ticks)
	plt.setp(ax1.get_yticklabels(), fontsize = y_ticks)

	ax1.spines['top'].set_visible(False)
	ax1.spines['right'].set_visible(False)
	ax3.spines['top'].set_visible(False)
	ax3.spines['right'].set_visible(False)
	ax3.tick_params(left = False, labelleft = False)

	ax2.spines['top'].set_visible(False)
	ax2.spines['right'].set_visible(False)
	ax2.spines['left'].set_visible(False)
	ax2.tick_params(left = False, labelleft = False)

	box = ax1.get_position()
	ax1.set_position([box.x0 + shift_x * box.width, box.y0 + shift_y * box.width, box.width * scale_width, box.height * scale_height])
	box = ax2.get_position()
	ax2.set_position([box.x0 + shift_x * box.width - box.width * scale_width * 0.5, box.y0 + shift_y * box.width, box.width * scale_width, box.height * scale_height])
	box = ax3.get_position()
	ax3.set_position([box.x0 + shift_x * box.width, box.y0 + shift_y * box.width, box.width * scale_width * 0.5, box.height * scale_height])

	pos = ['data', 0]
	ax3.spines['left'].set_position(pos)

	return fig, ax1, ax2, ax3

# Plot the distribution given
def plot_distribution(i, fold_diff_dist, mu1, mu2, var1, var2, weight1, weight2, UE, OE, value, gene):
	# Vectorizable functions to use for plotting distributions
	def GMM_dist1(x):
		return weight1 * (np.exp(-((x - mu1)**2) / (2 * var1)) / (np.sqrt(2 * PI * var1))) 
	def GMM_dist2(x):
		return weight2 * (np.exp(-((x - mu2)**2) / (2 * var2)) / (np.sqrt(2 * PI * var2)))

	# Define parameters of legend
	x_shift = 0.68 # Increase -> 
	y_shift = 0.53 # Increase -> 
	font_size = 11.75
	tick_rotation = 0
	tick_length = 6.0
	gene_mark_offset = 0
	graph_side_offset = 0.080
	y_max_val = 0.01 # For the side graphs
	y_max_val_2 = 0.3 # For the center graph
	
	# Plot the histogram against split Gaussians & save the figure
	fig, ax1, ax2, ax3 = make_graph(title = 'Protein/mRNA', 
		x_axis = '', y_axis = 'Normalized Count',
		width = 4.0, height = 3.2, scale_width = 0.9, scale_height = 0.9, # scale_value represents size of graph wrt entire screen
		font_title = 14.2, font_axes = 12.5, x_ticks = 8.0, y_ticks = 12.0,
		pad_title = 5.0, pad_x = 6.0, pad_y = 0.0, shift_x = 0.50, shift_y = 0.10) # pad_value = 
	for ax in [ax1, ax2, ax3]:
		n, bins, patches = ax.hist(fold_diff_dist, density = 1, bins = 500, alpha = 1, color = 'silver')
		ax.plot(bins, np.vectorize(GMM_dist1)(bins), 'k', label = 'K = 2/1', color = 'green')
		ax.plot(bins, np.vectorize(GMM_dist2)(bins), 'k', label = 'K = 2/2', color = 'blue')
		ax.plot([UE, UE], [0, 0.3], 'r--', linewidth = 1.0, label = 'UE/OE', color = 'red') # UE cutoff location
		ax.plot([OE, OE], [0, 0.3], 'r--', linewidth = 1.0, color = 'red') # OE cutoff location
		x = np.array([value, value]).flatten() 
		y = np.concatenate((np.zeros(len(value), dtype = float), np.vectorize(GMM_dist2)(value))).flatten()
		for j in range(len(x) / 2):
			ax.plot(x[[j, j + len(x) / 2]] + gene_mark_offset, y[[j, j + len(x) / 2]], linewidth = 1.0, color = 'purple')

	for ax in [ax1, ax2, ax3]:
		ax.xaxis.set_ticks(value)
		ax.xaxis.set_ticklabels(gene)
		ax.tick_params(length = tick_length, rotation = tick_rotation)
		for ind, tick in enumerate(ax.xaxis.get_major_ticks()):
			tick.set_pad(MPPa_tick_pads[ind])
	
	ax1.set_xlim([np.min(bins), UE + graph_side_offset])
	ax1.set_ylim([0, y_max_val])
	ax2.set_xlim([OE - 0.5 * graph_side_offset, np.max(bins)])
	ax2.set_ylim([0, y_max_val])
	ax3.set_xlim([UE - graph_side_offset, OE + 5 * graph_side_offset])
	ax3.set_ylim([0, y_max_val_2])

	plt.savefig(analysis_dir + write_cell_dir + '12_' + cell_order[i] + '_genes_mRNA_break')
	plt.close(fig)

# Main function
def main():
	# Starting message
	print('Starting [12_final_graph_genes_mRNA_break]\n'); flush()

	# Reads previously generated GMM parameters and returns the stats for the indicated cell type
	mu1, var1, weight1, mu2, var2, weight2, UE, OE = read_stats('HSC', analysis_dir + data_dir_2)

	# Read the data generated in 3_data_compile.py
	genes, data = read_data_ordered(gen_data_dir + read_cell_dir + data_dir)
	print('Regular data reading complete...\n'); flush()
	# Retrieve mappings generated in 2_gene_prot_mappings.py
	prot_gene_map, gene_prot_map, prot_aliases = retrieve_mappings()
	# Read the raw TPM mRNA data & return as TPM
	mRNA_data, mRNA_genes = read_mRNA_ordered(mRNA_dir, genes, prot_gene_map, gene_prot_map, prot_aliases)
	# Order the mRNA_data such that it is compatible with genes. Add 0 for any time the gene is not expressed
	mRNA_data = expand_mRNA_genes(genes, mRNA_genes, mRNA_data)
	print('mRNA data reading complete...\n'); flush()

	# Determine locations where both prot and mRNA are found
	data_TF = (data > 0).astype(int)
	mRNA_data_TF = (mRNA_data > 0).astype(int)
	prot_mRNA_TF = data_TF * mRNA_data_TF

	# Find the log 2 of fold change differences between mRNA and protein of cell_order[i] against combinations of all other cells 
	fold_diff_dist, fold_diff_arr, highs_names, highs_genes = comb_fold(cell_order.index('HSC'), data, mRNA_data, prot_mRNA_TF)

	# Get the gene label and the fold change difference value for genes I want to mark
	values = [] # Values of ticks on x-axis
	labels = [] # Labels of ticks on x-axis
	get_gene_values(genes, highs_genes, highs_names, fold_diff_arr, OE, UE, values, labels)

	# Plot the possible distributions against the data histogram
	plot_distribution(cell_order.index('HSC'), fold_diff_dist, mu1, mu2, var1, var2, weight1, weight2, UE, OE, values, labels)
	
	# Closing message
	print('\n[12_final_graph_genes_mRNA_break] complete')

main()