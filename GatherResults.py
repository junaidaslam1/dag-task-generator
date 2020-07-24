'''
******************************* Gather and Format Test Results **********************
* Author:       Muhammad Junaid Aslam
* Contact:      junaidaslam1@gmail.com
* ---------------------------------------------------------------------
* This software is governed by the Null license under M.J law and     |
* abiding by the rules of distribution of free software. You can use, |
* modify and redistribute the software under the condition of citing  |
* or crediting the authors of this software in your work.             |
* ---------------------------------------------------------------------
*
* This was part of a research project funded by the EWI EEMCS Group of
* Technical University of Delft, Netherlands.
**********************************************************************************
'''
#!/usr/bin/env python3
import subprocess
import argparse
import time
from math import ceil, floor, log10
import csv
import os
import copy
import numpy as np
from fractions import gcd
from functools import reduce

DUMMY_NUMBER = 999999999
PERCENTILE = 90
DIVIDER = 1

def parse_args():
	parser = argparse.ArgumentParser(description="Create task sets file")

	parser.add_argument('-w', '--workload_location', dest='root_folder', default='Null', 
						action='store', type=str, metavar="WORKLOAD_LOCATION",
						required=True,
						help='The place to pickup task-set files')

	parser.add_argument('-p', '--percentile', dest='percentile', default='90', 
						action='store', type=int, required=False,
						help='Percentile to calculate CPU Time and Mem Usage')

	parser.add_argument('-d', '--percentile-divider', dest='divider', default='1', 
						action='store', type=int, required=True,
						help='divide for CPU time if multi-threaded execution')

	return parser.parse_args()

def run_command(incommand):
	p = subprocess.Popen(incommand.split(), stdout=subprocess.PIPE,
stderr=subprocess.STDOUT)
	outstring = p.stdout.read()
	return outstring

def DispatchTests(directory, overallFp = 0):
	encoding = 'utf-8'
	for dirName, subdirList, fileList in os.walk(directory):
		
		if len(fileList) > 0:
			print("Executing %s ..."%dirName)
			ResultsPath = directory+"/"+"Results.csv"
			FP = open(ResultsPath, "a+")
			FP.write("# file name, schedulable?, #jobs, #states, #edges, max width, CPU time, memory, timeout, #CPUs, BatchStates\n")
			FP.flush()
			FP.close()
			schedulable_tasksets = 0
			TotalTaskSets = 0
			AnalyzedFiles = 0
			OutOfResources= 0
			MIN_CPU_TIME  = DUMMY_NUMBER
			MAX_CPU_TIME  = 0
			AVG_CPU_TIME  = 0
			MIN_MEM_USAGE = DUMMY_NUMBER
			MAX_MEM_USAGE = 0
			AVG_MEM_USAGE = 0
			ARRAY_CPU_TIME = []
			ARRAY_MEM_USAGE = []
			with open(ResultsPath, 'a+') as csvfile:
				ResultWriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
				for Files in range(0, len(fileList)):
					if ("JobResult" in fileList[Files]):
						TotalTaskSets += 1
						print(directory, fileList[Files])
						filepath = directory+"/"+fileList[Files]
						lvFP = open(filepath, 'r')
						data = csv.reader(lvFP, skipinitialspace=True)
						RowFound = False
						for row in data:
							RowFound = True
							print(row)
							ResultWriter.writerow(row)
							lvSchedResult = int(row[1])
							schedulable_tasksets += int(row[1])

							if lvSchedResult == 1:
								ARRAY_CPU_TIME.append(float(row[6]))
								ARRAY_MEM_USAGE.append(float(row[7]))

								AnalyzedFiles += 1
								if float(row[6]) < MIN_CPU_TIME:
									MIN_CPU_TIME = float(row[6])
								elif float(row[6]) > MAX_CPU_TIME:
									MAX_CPU_TIME = float(row[6])
								AVG_CPU_TIME += float(row[6])

								if float(row[7]) < MIN_MEM_USAGE:
									MIN_MEM_USAGE = float(row[7])
								elif float(row[7]) > MAX_MEM_USAGE:
									MAX_MEM_USAGE = float(row[7])
								AVG_MEM_USAGE += float(row[7])
						
						if RowFound == False:
							OutOfResources += 1

						lvFP.close()
						lvCMD = "rm -rf "+filepath
						# run_command(lvCMD)

			FP = open(ResultsPath, "a+")
			cpu_time = 0.0
			mem_usage = 0.0
			if len(ARRAY_CPU_TIME) > 0:
				cpu_time = (np.percentile(ARRAY_CPU_TIME, PERCENTILE)) / DIVIDER
			if len(ARRAY_MEM_USAGE) > 0:
				mem_usage = np.percentile(ARRAY_MEM_USAGE, PERCENTILE)

			lvSTR = "TOTAL_TASKS, SCHED_RATIO, MIN_CPU_TIME, MAX_CPU_TIME, AVG_CPU_TIME, MIN_MEM_USAGE, MAX_MEM_USAGE, AVG_MEM_USAGE, TIME_"+str(PERCENTILE)+"_PER,"+"MEM_"+str(PERCENTILE)+"_PER"+"\n"
			FP.write(lvSTR)
			if AnalyzedFiles > 0:
				lvSTR = str(TotalTaskSets)+","+str((schedulable_tasksets/TotalTaskSets)*100)+","+str(MIN_CPU_TIME)+","+str(MAX_CPU_TIME)+","+str((AVG_CPU_TIME/AnalyzedFiles))+","\
				+str(MIN_MEM_USAGE)+","+str(MAX_MEM_USAGE)+","+str((AVG_MEM_USAGE/AnalyzedFiles))+","+str(cpu_time)+","+str(mem_usage)+",\n"
			else:
				AnalyzedFiles = len(fileList)
				lvSTR = str(TotalTaskSets)+","+str((schedulable_tasksets/TotalTaskSets)*100)+","+str(MIN_CPU_TIME)+","+str(MAX_CPU_TIME)+","+str((AVG_CPU_TIME/AnalyzedFiles))+","\
				+str(MIN_MEM_USAGE)+","+str(MAX_MEM_USAGE)+","+str((AVG_MEM_USAGE/AnalyzedFiles))+","+str(cpu_time)+","+str(mem_usage)+",\n"

			if OutOfResources > 0:
				print("Nr of Jobs went Out Of Resources Jobs:%d"%OutOfResources)
				
			if overallFp != 0:
				lvSTRov = directory+","+str(TotalTaskSets)+","+str((schedulable_tasksets/TotalTaskSets)*100)+","+str(MIN_CPU_TIME)+","+str(MAX_CPU_TIME)+","+str((AVG_CPU_TIME/AnalyzedFiles))+","\
				+str(MIN_MEM_USAGE)+","+str(MAX_MEM_USAGE)+","+str((AVG_MEM_USAGE/AnalyzedFiles))+","+str(cpu_time)+","+str(mem_usage)+","+str(float((OutOfResources/TotalTaskSets)*100))+",\n"				
				overallFp.write(lvSTRov)

			FP.write(lvSTR)
			FP.flush()
			FP.close()

def main():
	global PERCENTILE
	global DIVIDER

	opts = parse_args()
	PERCENTILE = opts.percentile
	DIVIDER = opts.divider

	OverallRes = opts.root_folder+"/OverallOutcome/"
	try:
		os.mkdir(OverallRes)
	except OSError:
		if os.path.isdir(OverallRes) != True:
			print ("Creation of the directory %s failed" % OverallRes)
			return

	overallRes_File = OverallRes+"/OverallResults.csv"
	overallFp = open(overallRes_File, "a+")
	lvSTR = "Directory, TOTAL_TASKS, SCHED_RATIO, MIN_CPU_TIME, MAX_CPU_TIME, AVG_CPU_TIME, MIN_MEM_USAGE, MAX_MEM_USAGE, AVG_MEM_USAGE, TIME_"+str(PERCENTILE)+"_PER,"+"MEM_"+str(PERCENTILE)+"_PER,"+"OUT_OF_SYS_RESC,"+"\n"
	if overallFp != 0:
		overallFp.write(lvSTR)

	for dirName, subdirList, fileList in os.walk(opts.root_folder):
		if "SOA" in dirName or "FEASIBILITY" in dirName or "Visuals" in dirName or "OverallOutcome" in dirName:
			continue
		if ("Results" in dirName) and (len(fileList) > 0):
			DispatchTests(dirName, overallFp)

	print("Finished Collecting Results ... ")
	overallFp.close()

if __name__ == '__main__': 
	main()