import pandas as pd
import numpy as np
import os
from Datasets import filenames_dictionary
from Model import model

from Parameters import *

def main(): 
	# the amout of times the same model has to be ran
	k = 1
	# the type of order for the vaccination
	vaccination_orders = [1]
	# the names for the datasets to be saved
	file_names = {1: "Old_young", 2: "Young_old", 3: "Danish", 4: "Custom"}
	# load the filenames of the datasets to be used
	filenames = filenames_dictionary()

	for vacc_order in vaccination_orders:
		results = model(filenames, vacc_order, time)
		file_name1 = str(file_names[vacc_order]) + "_" + str(0) + ".csv"
		file_name_2 = os.path.join("Results", file_name1)
		results.data.to_csv(file_name_2)
		print("Saved as:", file_name1)
		results_total = results.data

		for i in range(1, k):
			results = model(filenames, vacc_order, time)

			file_name1 = str(file_names[vacc_order]) + "_" + str(i) + ".csv"
			file_name_2 = os.path.join("Results", file_name1)
			results.data.to_csv(file_name_2)
			print("Saved as:", file_name1)
			results_total = results_total + results.data

		results_total = results_total / k
		#tracker = results_total.astype(int)
		file_name_total_1 = str(file_names[vacc_order]) + "_total.csv"
		file_name_total_2 = os.path.join("Results", file_name_total_1)
		results_total.to_csv(file_name_total_2)

		print("Saved as:", file_name_total_1)
