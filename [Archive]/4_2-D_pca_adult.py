# File name: 4_2-D_pca_adult.py
# Last Edit: 10/06/2019
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
# Using the compiled data, generate a 2-D PCA graph
# and record the contribution of factors to the components

import numpy as np
import math
import csv
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.decomposition import PCA

# Constants used for directory names
#
# raw_data - file with raw data
# gen_data - file with generated data
# imp_data - file with data imported from uniprot.org
# write_cell_dir - additional extension for file to write data to
raw_data_dir = './raw_data/'
gen_data_dir = './gen_data/'
imp_data_dir = './imp_data/'
analysis_dir = './analysis/'
read_cell_dir = 'adult_aged/'
write_cell_dir = 'adult/'
save_dir = ''
data_dir = '3_gene_intensity_norm.txt'

# Constants used for cell_ordering
cell_order = ['HSC', 'MPPa', 'MPPb', 'MPPc', 'CLP', 'CMP', 'MEP', 'GMP']
rainbow_color = {'HSC' : 'lightcoral', 'MPPa' : 'orange', 'MPPb' : 'forestgreen', 
'MPPc' : 'mediumturquoise', 'CLP' : 'dodgerblue', 'CMP' : 'darkblue', 'MEP' : 'violet', 'GMP' : 'crimson'}

# Reads the raw data from the given directory and returns the list of cells, genes, and the data
# Removes cells that are not used; removes genes that are not used
def read_data(directory):
	cells = [] # List of cells used
	genes = [] # List of genes
	data = [] # Intensity values
	with open(directory, 'rb') as r:
		reader = csv.reader(r, delimiter = ',')
	# Record all cell names in the file
		for row in reader:
			for i in range(len(row) - 2):
				cells.append(row[i + 2])
			break
	# Record all gene names in the file
		for row in reader:
			genes.append(row[1])
			data.append(row[2:])

	# Find cell names independent of run detail
	cells = np.array(cells)
	def reduce_cell_name(cell):
		cell = cell[:cell.find('t') - 1]
		if cell.find('Aged') == -1:
			return cell
		else:
			return 'a' + cell[4:]
	f = np.vectorize(reduce_cell_name)
	unique_cells = f(cells)

	# Remove cells that were not used
	to_keep = np.zeros(len(unique_cells)).astype(bool)
	for i in range(len(unique_cells)):
		if unique_cells[i] not in cell_order:
			to_keep[i] = False
		else:
			to_keep[i] = True
	cells = cells[to_keep]; unique_cells = unique_cells[to_keep]; data = np.array(data, dtype = float)[:, to_keep]

	# Remove genes that are not expressed in any cell types
	data_TF = (data > 0).astype(int)
	data_TF = np.sum(data_TF, axis = 1)
	data_TF = (data_TF > 0).astype(bool)
	data = data[data_TF, :]
	genes = np.array(genes, dtype = str)[data_TF]

	return cells, unique_cells, genes, data

# Return data noramlized by column. Data is normalized such that the smallest value
# throughout the entire dataset will be scaled to about 1
def norm_per_col(data):
	non_zero_min = np.min(data[np.nonzero(data)])
	indices = np.where(data == non_zero_min)
	column = indices[1][0]
	sums = np.sum(data, axis = 0)
	sums_y = sums[column] # The column sum at which the non-zero minimum occurs
	parts_per = math.ceil(sums_y / non_zero_min) # The sum total scaling factor that is applied to all columns

	return (data * parts_per) / sums

# Make a graph and return the figure and axes. Contains predetermined variables,
# unless otherwise stated.
def make_graph(title, x_axis, y_axis, width, height, 
	scale_width, scale_height, font_title, font_axes, font_ticks, 
	pad_title, pad_x, pad_y, shift_x, shift_y):

	fig, ax = plt.subplots(figsize = (width ,height))

	ax.set_title(title, size = font_title, pad = pad_title)
	ax.set_xlabel(x_axis, size = font_axes, labelpad = pad_x)
	ax.set_ylabel(y_axis, size = font_axes, labelpad = pad_y)

	plt.setp(ax.get_xticklabels(), fontsize = font_ticks)
	plt.setp(ax.get_yticklabels(), fontsize = font_ticks)

	ax.spines['top'].set_visible(False)
	ax.spines['right'].set_visible(False)

	box = ax.get_position()
	ax.set_position([box.x0 + shift_x * box.width, box.y0 + shift_y * box.width, box.width * scale_width, box.height * scale_height])

	return fig, ax

# Given PCA transformed values & the relative PC contributions,
# plot the PCA & save the file
def plot_PCA(pca, ratios, cells, unique_cells):
	# Create an ordered color list
	colors = []
	for i in range(len(unique_cells)):
		colors.append(rainbow_color[unique_cells[i]])

	# Determine graphing parameters
	fig, ax = make_graph(title = 'Adult Mouse Hematopoietic Cells', 
		x_axis = 'PC 1 (%.1f' %(ratios[0] * 100) + '%)', y_axis = 'PC 2 (%.1f' %(ratios[1] * 100) + '%)',
		width = 4.0, height = 3.2, scale_width = 0.72, scale_height = 0.9, # scale_value represents size of graph wrt entire screen
		font_title = 14.2, font_axes = 12.5, font_ticks = 12.0, 
		pad_title = 5.0, pad_x = 6.0, pad_y = -2.0, shift_x = 0.11, shift_y = 0.10) # pad_value = 

	# Create legend handles
	leg_handles = []
	for i in range(len(cell_order)):
		leg_handles.append(mpatches.Patch(color = rainbow_color[cell_order[i]], label = cell_order[i]))

	# Create legend, determining the parameters
	x_shift = 0.78 # Increase -> 
	y_shift = 0.53 # Increase -> 
	font_size = 11.75
	color_length = 0.3
	fig.legend(handles = leg_handles, loc = 'center left', bbox_to_anchor = (x_shift, y_shift), 
		frameon = False, handlelength = color_length, fontsize = font_size)

	# Adjust axes
	x_min = -500; x_max = 700
	y_min = -310; y_max = 310
	ax.set_xlim([x_min, x_max])
	ax.set_ylim([y_min, y_max])

	# Create the plot, determining the parameters
	dot_size = 35
	ax.scatter(pca[:, 0], pca[:, 1], s = dot_size, c = colors) 
	plt.show()

	# Save the figure
	fig.savefig(analysis_dir + write_cell_dir + '4_2-D_pca_adult' + save_dir + '.png')

# Given PCA transformation, save the component contributions
# to files in both raw and absolute values
def save_PCA(component_vec, genes):
	for i in range(len(component_vec)):
		component = component_vec[i]
		w1 = open(analysis_dir + write_cell_dir + '4_pc%i_adult' %(i + 1) + save_dir + '.csv', 'w+')
		for j in range(len(genes)):
			w1.write(genes[j] + ',' + str(component[j]) + ',' + str(np.abs(component[j])) + '\n')
		w1.close()

# Main function	
def main():
	# Starting message
	print('Starting [4_2-D_pca_adult]\n')

	# Read the data generated in 3_data_compile.py
	cells, unique_cells, genes, data = read_data(gen_data_dir + read_cell_dir + data_dir)

	# Transpose the data (as per PCA) and find the log2 of column-normalized data
	norm_T_data = norm_per_col(np.transpose(data))
	lognorm_T_data = np.log2(norm_T_data + np.min(norm_T_data[np.nonzero(norm_T_data)])/1000.)

	#Fit PCA	
	pca = PCA(n_components = 2)
	fitted = pca.fit_transform(lognorm_T_data)
	
	#Plot and save PCA
	plot_PCA(fitted, pca.explained_variance_ratio_, cells, unique_cells)
	save_PCA(pca.components_, genes)

	# Closing message
	print('\n[4_2-D_pca_adult] complete')

main()