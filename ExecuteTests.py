#!/usr/bin/env python3
import subprocess
from datetime import datetime
import sys
import os
import threading
import argparse

EMAIL_ID = ""
NR_OF_REQUESTED_NODES = "NA"
NR_OF_JOBS_TO_EXECUTE = 0
WHICH_CLUSTER = "insy"
RUN_SBATCH = False
JOB_SCRIPT_PATH = ""
TIMEOUT = ""
TIMEOUT_CL = ""
CPUS_PER_TASK = ""
MEM = ""
NODE = ""
MAIL = ""
QOS = ""
RUN = ""
PACK_JOBS = False
REMOVE = None
PARTITION = "Null"
MOVE = False

def parse_args():
    parser = argparse.ArgumentParser(description="Create task sets file")

    parser.add_argument('-p', '--test_location', dest='nptest_path', default='/home/nfs/jaslam/np_schedulability_disc_new_eq/', 
                        action='store', type=str, metavar="TEST_BINARY_LOCATION",
                        required=True,
                        help='The place to pickup test executable (e.g. nptest)')

    parser.add_argument('-w', '--workload_location', dest='root_folder', default='$HOME', 
                        action='store', type=str, metavar="WORKLOAD_LOCATION",
                        required=True,
                        help='The place to pickup Workload files')

    parser.add_argument('-s', '--job_script_path', dest='job_script_path', default='$HOME', 
                        action='store', type=str, metavar="JOB_SCRIPT_PATH",
                        required=True,
                        help='The place to save job script files')

    parser.add_argument('-c', '--cpus-per-task', dest='cpus', default='16', 
                        action='store', type=str, metavar="CPUS_PER_TASK",
                        required=False,
                        help='Required CPUs per task in the Node')

    parser.add_argument('-cl', '--cluster', dest='cluster', default='insy', 
			            action='store', type=str,
			            required=True,
			            help='The Cluster; Choices = {insy, das5, surfsara}')

    parser.add_argument('-l', '--timeout_test', dest='timeout_test', default='0', 
	                    action='store', type=str, metavar="TIMEOUT",
	                    required=False,
	                    help='Time out for the test in seconds. This is CPU time')

    parser.add_argument('-t', '--timeout_cl', dest='timeout_cl', default='1:00:00', 
	                    action='store', type=str, metavar="TIMEOUT",
	                    required=False,
	                    help='Time out for the generated cluster job')

    parser.add_argument('-m', '--memory', dest='memory', default='0', 
		                action='store', type=str, metavar="MEMORY",
		                required=False,
		                help='Required Memory Per Task')

    parser.add_argument('-pa', '--pack', dest='pack', action='store_const', 
    					const=True, required=False,
			            help='This option packs number of jobs specified by -nj option')

    parser.add_argument('-N', '--NR_OF_Node', dest='nr_nodes', default='Null', 
			            action='store', type=str,
			            required=False,
			            help='Provide number of nodes to request, e.g. 1, 2, 3 ... etc')

    parser.add_argument('-n', '--Node', dest='node', default='Null', 
			            action='store', type=str, required=False,
			            help='Provide list of requested nodes separated by comma. e.g., insy6, insy8, wis1, etc ...')

    parser.add_argument('-nj', '--Nr_Jobs', dest='Nr_Jobs', default='0', 
			            action='store', type=int,
			            required=False, help='Number of jobs to pack in one job')

    parser.add_argument('-eid', '--Mail_id', dest='mail_id', default='m.j.aslam@tudelft.nl', 
			            action='store', type=str, metavar="MAIL_ID",
			            required=False,
			            help='EMAIL ID to send status at the completion of Job (e.g: END, FAIL etc)')

    parser.add_argument('-e', '--Mail', dest='mail', default='Null', 
			            action='store', type=str, metavar="MAIL_TYPE",
			            required=False,
			            help='MAIL Type at the completion of Job (e.g: END)')

    parser.add_argument('-par', '--partition', dest='partition', default='Null', 
			            action='store', type=str, metavar="partition",
			            required=False,
			            help='partition to be used for running the test.')

    parser.add_argument('-qos', '--quality-of-service', dest='qos', default='short', 
			            action='store', type=str, metavar="QOS",
			            required=False,
			            help='This is for INSY / TUDelft HPC only.')

    parser.add_argument('-sr', '--srun', dest='srun', action='store_const', 
    					const=True, required=False,
			            help='This option starts the created job with sbatch')

    parser.add_argument('-mv', '--move', dest='move', action='store_const', 
    					const=True, required=False,
			            help='This option moves the jobs to jobscript location')

    parser.add_argument('-rm', '--remove', dest='remove', action='store_const', 
    					const=True, required=False,
			            help='This option removes job and pred files after finishing the test')

    parser.add_argument('-r', '--Run', dest='run', default='N', 
			            action='store', type=str, metavar="TEST_RUN",
			            required=False,
			            help='Pass Y to run the test or create job script for cluster')

    return parser.parse_args()

def run_command(incommand):
	p = subprocess.Popen(incommand.split(), stdout=subprocess.PIPE,
stderr=subprocess.STDOUT)
	outstring = p.stdout.read()
	return outstring

'''
Below functions creates an sbatch job script
for running nptest jobs on cluster.
Change the parameters in FP.write with respect
to the number of tasks and requirements of 
test executions
'''
def das5createJobScript(Command, Filename, ScriptPath, Pack):
	FileName = Filename.split('.')
	slocation = ScriptPath+"/"+FileName[0]+".sbatch"
	NR_OF_TASKS = 1

	if Pack == True:
		slocation = ScriptPath+"/Pack_OF_"+str(len(Command))+"_"+Filename+"_Jobs.sbatch"

	FP = open(slocation, "w")
	FP.write("#!/bin/sh\n")
	
	if Pack == False:
		lvSTR = "#SBATCH --time="+TIMEOUT_CL+"\n"
		FP.write(lvSTR)
		
		if CPUS_PER_TASK == "SLURM_CPUS_ON_NODE":
			lvSTR = "#SBATCH --ntasks="+str(NR_OF_TASKS)+" --exclusive\n"
			FP.write(lvSTR)
		else:
			FP.write("#SBATCH --ntasks="+str(NR_OF_TASKS)+"\n")
	
		if CPUS_PER_TASK != "SLURM_CPUS_ON_NODE":	
			lvSTR = "#SBATCH --cpus-per-task="+CPUS_PER_TASK+"\n"
			FP.write(lvSTR)

		if NR_OF_REQUESTED_NODES != "Null":
			lvSTR = "#SBATCH --nodes="+NR_OF_REQUESTED_NODES+"\n"
			FP.write(lvSTR)

		if NODE != "Null":
			lvSTR = "#SBATCH --nodelist="+NODE+"\n"
			FP.write(lvSTR)

	if MEM != '0':
		lvSTR = "#SBATCH --mem="+MEM+"\n"
		FP.write(lvSTR)
	
	lvSTR = "#SBATCH --mail-user="+EMAIL_ID+"\n"
	FP.write(lvSTR)

	if MAIL != "Null":
		lvSTR = "#SBATCH --mail-type="+MAIL+"\n"
		FP.write(lvSTR)
	
	if Pack == False:
		FP.write(Command)
	else:
		for p in range(0, len(Command)):
			if NR_OF_REQUESTED_NODES != "Null":
				lvCMD = "srun "+"-n 1 -t "+TIMEOUT_CL+" -c "+CPUS_PER_TASK+" -N "+NR_OF_REQUESTED_NODES+" "+Command[p]+" &\n"
			else:
				lvCMD = "srun "+"-n 1 -t "+TIMEOUT_CL+" -c "+CPUS_PER_TASK+" "+Command[p]+" &\n"
			FP.write(lvCMD)
		FP.write('wait')

	FP.close()

	if RUN_SBATCH == True:
		lvCMD = "sbatch "+slocation
		print(lvCMD)
		print(run_command(lvCMD))

def surfcreateJobScript(Command, Filename, ScriptPath, Pack):
	FileName = Filename.split('.')
	slocation = ScriptPath+"/"+FileName[0]+".sbatch"
	NR_OF_TASKS = 1

	if Pack == True:
		slocation = ScriptPath+"/Pack_OF_"+str(len(Command))+"_"+Filename+"_Jobs.sbatch"

	FP = open(slocation, "w")
	FP.write("#!/bin/bash\n")

	if PARTITION != "Null":
		lvSTR = "#SBATCH --partition="+PARTITION+"\n"
		FP.write(lvSTR)
	else:
		FP.write("#SBATCH --partition=normal\n")


	if Pack == False:
		lvSTR = "#SBATCH --time="+TIMEOUT_CL+"\n"
		FP.write(lvSTR)
		
		if CPUS_PER_TASK == "SLURM_CPUS_ON_NODE":
			lvSTR = "#SBATCH --ntasks="+str(NR_OF_TASKS)+" --exclusive\n"
			FP.write(lvSTR)
		else:
			FP.write("#SBATCH --ntasks="+str(NR_OF_TASKS)+"\n")
	
		if CPUS_PER_TASK != "SLURM_CPUS_ON_NODE":	
			lvSTR = "#SBATCH --cpus-per-task="+CPUS_PER_TASK+"\n"
			FP.write(lvSTR)

		if NR_OF_REQUESTED_NODES != "Null":
			lvSTR = "#SBATCH --nodes="+NR_OF_REQUESTED_NODES+"\n"
			FP.write(lvSTR)

		if NODE != "Null":
			lvSTR = "#SBATCH --nodelist="+NODE+"\n"
			FP.write(lvSTR)

	if MEM != '0':
		lvSTR = "#SBATCH --mem="+MEM+"\n"
		FP.write(lvSTR)
	
	lvSTR = "#SBATCH --mail-user="+EMAIL_ID+"\n"
	FP.write(lvSTR)

	if MAIL != "Null":
		lvSTR = "#SBATCH --mail-type="+MAIL+"\n"
		FP.write(lvSTR)
	
	if Pack == False:
		FP.write(Command)
	else:
		for p in range(0, len(Command)):
			if NR_OF_REQUESTED_NODES != "Null":
				lvCMD = "srun "+"-n 1 -t "+TIMEOUT_CL+" -c "+CPUS_PER_TASK+" -N "+NR_OF_REQUESTED_NODES+" "+Command[p]+" &\n"
			else:
				lvCMD = "srun "+"-n 1 -t "+TIMEOUT_CL+" -c "+CPUS_PER_TASK+" "+Command[p]+" &\n"
			FP.write(lvCMD)
		FP.write('wait')

	FP.close()

	if RUN_SBATCH == True:
		lvCMD = "sbatch "+slocation
		print(lvCMD)
		print(run_command(lvCMD))

def insycreateJobScript(Command, Filename, ScriptPath, Pack):
	FileName = Filename.split('.')
	slocation = ScriptPath+"/"+FileName[0]+".sbatch"
	NR_OF_TASKS = 1

	if Pack == True:
		slocation = ScriptPath+"/Pack_OF_"+str(len(Command))+"_"+Filename+"_Jobs.sbatch"

	FP = open(slocation, "w")
	FP.write("#!/bin/sh\n")

	if PARTITION != "Null":
		lvSTR = "#SBATCH --partition="+PARTITION+"\n"
		FP.write(lvSTR)
	else:
		FP.write("#SBATCH --partition=general\n")

	lvSTR = "#SBATCH --qos="+QOS+"\n"
	FP.write(lvSTR)

	if Pack == False:
		lvSTR = "#SBATCH --time="+TIMEOUT_CL+"\n"
		FP.write(lvSTR)
		if CPUS_PER_TASK == "SLURM_CPUS_ON_NODE":
			lvSTR = "#SBATCH --ntasks="+str(NR_OF_TASKS)+" --exclusive\n"
			FP.write(lvSTR)
		else:
			FP.write("#SBATCH --ntasks="+str(NR_OF_TASKS)+"\n")
	
		if CPUS_PER_TASK != "SLURM_CPUS_ON_NODE":	
			lvSTR = "#SBATCH --cpus-per-task="+CPUS_PER_TASK+"\n"
			FP.write(lvSTR)

		if NR_OF_REQUESTED_NODES != "Null":
			lvSTR = "#SBATCH --nodes="+NR_OF_REQUESTED_NODES+"\n"
			FP.write(lvSTR)

		if NODE != "Null":
			lvSTR = "#SBATCH --nodelist="+NODE+"\n"
			FP.write(lvSTR)

	if MEM != '0':
		lvSTR = "#SBATCH --mem="+MEM+"\n"
		FP.write(lvSTR)
	
	lvSTR = "#SBATCH --mail-user="+EMAIL_ID+"\n"
	FP.write(lvSTR)

	if MAIL != "Null":
		lvSTR = "#SBATCH --mail-type="+MAIL+"\n"
		FP.write(lvSTR)
	
	FP.write("module use /opt/insy/modulefiles\n")
	FP.write("module load devtoolset/6\n")
	
	if Pack == False:
		FP.write(Command)
	else:
		for p in range(0, len(Command)):
			if NR_OF_REQUESTED_NODES != "Null":
				lvCMD = "srun "+"-n 1 -t "+TIMEOUT_CL+" -c "+CPUS_PER_TASK+" -N "+NR_OF_REQUESTED_NODES+" "+Command[p]+" &\n"
			else:
				lvCMD = "srun "+"-n 1 -t "+TIMEOUT_CL+" -c "+CPUS_PER_TASK+" "+Command[p]+" &\n"
			FP.write(lvCMD)
		FP.write('wait')

	FP.close()

	if RUN_SBATCH == True:
		lvCMD = "sbatch "+slocation
		print(lvCMD)
		print(run_command(lvCMD))

def getPredecessorName(JobsFile):
	lvFile = JobsFile.split('_')
	length = len(lvFile)
	PredFile = ""
	for n in range(0, length-1):
		PredFile += lvFile[n]+"_"
	PredFile += "Pred.csv"
	return PredFile

def Create_sBatch(Command, Filename, ScriptPath, Pack=False):
	if WHICH_CLUSTER == "insy":
		insycreateJobScript(Command, Filename, ScriptPath, Pack)
	elif WHICH_CLUSTER == "das5":
		das5createJobScript(Command, Filename, ScriptPath, Pack)
	elif WHICH_CLUSTER == "surf":
		surfcreateJobScript(Command, Filename, ScriptPath, Pack)

def DispatchTests(directory, nptest):
	encoding = 'utf-8'
	ResultPath = directory+"/Results/"
	SplitPath = directory.split('/')
	ScriptPath = " "

	for n in range(0, len(SplitPath)):
		if "Typed" in SplitPath[n] or "Hetero" in SplitPath[n]:
			ScriptPath = JOB_SCRIPT_PATH+"/"+SplitPath[n]
			# print(ScriptPath)
			break

	if RUN != 'Y':
		try:
			os.mkdir(ScriptPath)
		except OSError:
			if os.path.isdir(ScriptPath) != True:
				print ("Creation of the directory %s failed" % ScriptPath)
				return

	try:
		os.mkdir(ResultPath)
	except OSError:
		if os.path.isdir(ResultPath) != True:
			print ("Creation of the directory %s failed" % ResultPath)
			return

	ResultFile = ResultPath+"Results.csv"

	FP = open(ResultFile, "a+")
	FP.write("Simulation Results for directory %s Run on %s Cluster with %s CPUs/Per_Test and Requested Mem:%s\n"%(directory, WHICH_CLUSTER, CPUS_PER_TASK, MEM))
	FP.flush()

	if RUN == 'Y':
		FP.write("# file name, schedulable?, #jobs, #states, #edges, max width, CPU time, memory, timeout, #CPUs, BatchStates")
		FP.write("\n")
		FP.flush()

	for dirName, subdirList, fileList in os.walk(directory):
		WorkloadFiles = ""
		TotalTested = 0
		Failed = 0
		Passed = 0
		Ratio = 0
		counter = 0 
		Packed = False
		PACKING_ARRAY = []
		Last_File_Name = ""

		if len(fileList) > 1:
			print("Executing %s ..."%dirName)

		for Files in range(0, len(fileList)):

			if ("Jobs" in fileList[Files]) and ("NOT_FEASIBLE" not in fileList[Files]) and ("JobResult_" not in fileList[Files]) and ("Report" not in fileList[Files]) and ("TasksetSettings" not in fileList[Files]) and ("Results" not in fileList[Files]) and (".png" not in fileList[Files]):
				
				counter += 1
				JobPath = directory+"/"+fileList[Files]
				PredPath= directory+"/"+getPredecessorName(fileList[Files])
				WorkloadFiles = JobPath+" -p "+PredPath

				if CPUS_PER_TASK != "SLURM_CPUS_ON_NODE":
					timeout_value = str(int(CPUS_PER_TASK)*(int(TIMEOUT)))

				if (RUN != 'Y') and (RUN != 'y') and (MOVE == True):
					cmd_mv = "mv "+JobPath+" "+PredPath+" "+ScriptPath+"/"
					run_command(cmd_mv)
					
					lvJobFileName = fileList[Files].split('\'')
					lvPredFileName = getPredecessorName(fileList[Files]).split('\'')

					JobPath = ScriptPath+"/"+lvJobFileName[len(lvJobFileName)-1]
					PredPath= ScriptPath+"/"+lvPredFileName[len(lvPredFileName)-1]

					WorkloadFiles = JobPath+" -p "+PredPath

				cmd_rm = ""
				if REMOVE == True:
					cmd_rm = " && rm -rf "+JobPath+" "+PredPath
				
				lvResultFile = ResultPath+"JobResult_"+fileList[Files]
				lvFP = open(lvResultFile, "w")
				lvFP.close()

				if PACK_JOBS == None:
					if CPUS_PER_TASK == "SLURM_CPUS_ON_NODE":
						Command = 'srun --cpus-per-task="$SLURM_CPUS_ON_NODE" '+nptest+"/build/nptest -R hetero -l "+TIMEOUT+" "+WorkloadFiles+" >> "+lvResultFile+cmd_rm
					else:
						Command = "srun "+nptest+"/build/nptest -R hetero --threads="+CPUS_PER_TASK+" -l "+timeout_value+" "+WorkloadFiles+" >> "+lvResultFile+cmd_rm
				else:
					if CPUS_PER_TASK == "SLURM_CPUS_ON_NODE":
						Command = nptest+"/build/nptest -R hetero -l "+TIMEOUT+" "+WorkloadFiles+" >> "+lvResultFile+cmd_rm
					else:
						Command = nptest+"/build/nptest -R hetero --threads="+CPUS_PER_TASK+" -l "+timeout_value+" "+WorkloadFiles+" >> "+lvResultFile+cmd_rm

				Last_File_Name = fileList[Files]
				
				if RUN == 'Y':
					if CPUS_PER_TASK == "SLURM_CPUS_ON_NODE":
						lvCMD = nptest+"/build/nptest -R hetero "+WorkloadFiles
					else:
						if CPUS_PER_TASK == '0':
							lvCMD = nptest+"/build/nptest -R hetero" +" -l "+timeout_value+" "+WorkloadFiles
						else:
							lvCMD = nptest+"/build/nptest -R hetero --threads="+CPUS_PER_TASK+" -l "+timeout_value+" "+WorkloadFiles
					# print("Executing: %s"%lvCMD)
					lvResult_Nptest = run_command(lvCMD)
					Result_Nptest = lvResult_Nptest.decode(encoding)

					FP.write(Result_Nptest)
					FP.flush()
					
					TotalTested += 1
					
					lvres = lvResult_Nptest.decode().split(',')
					
					try:
						if int(lvres[1]) == True:
							Passed += 1
						else:
							Failed += 1
					
						if REMOVE == True:
							lvCMD = "rm -rf "+directory+"/"+fileList[Files] + " " + directory+"/"+getPredecessorName(fileList[Files])
							run_command(lvCMD)
					
					except ValueError:
						print("Error with File:%s"%Last_File_Name)

				else:
					FP.close()

					if PACK_JOBS == None:
						Create_sBatch(Command, Last_File_Name, ScriptPath)
					else:
						PACKING_ARRAY.append(Command)			

				if (NR_OF_JOBS_TO_EXECUTE != 0) and (NR_OF_JOBS_TO_EXECUTE == counter):
					if PACK_JOBS == True:
						Packed = True
						Create_sBatch(PACKING_ARRAY, Last_File_Name, ScriptPath, True)

					break

		if (PACK_JOBS == True) and (Packed == False) and (counter > 0):
			Create_sBatch(PACKING_ARRAY, Last_File_Name, ScriptPath, True)

		if TotalTested > 0:
			Ratio = (Passed / TotalTested)*100
			print("For %s TotalTested:%d Passed:%d Failed:%d Schedulability_Ratio:%d"%(dirName, TotalTested, Passed, Failed, Ratio))

	FP.close()

def main():

	global TIMEOUT
	global TIMEOUT_CL
	global CPUS_PER_TASK
	global MEM
	global NODE
	global JOB_SCRIPT_PATH
	global MAIL
	global RUN
	global RUN_SBATCH
	global WHICH_CLUSTER
	global NR_OF_JOBS_TO_EXECUTE
	global NR_OF_REQUESTED_NODES
	global PACK_JOBS
	global EMAIL_ID
	global REMOVE
	global PARTITION
	global QOS
	global MOVE

	opts = parse_args()

	rootfolder = opts.root_folder 
	nptest = opts.nptest_path
	TIMEOUT = opts.timeout_test
	TIMEOUT_CL = opts.timeout_cl
	CPUS_PER_TASK = opts.cpus
	MEM = opts.memory
	NODE = opts.node
	JOB_SCRIPT_PATH = opts.job_script_path
	MAIL = opts.mail
	RUN = opts.run
	RUN_SBATCH = opts.srun
	WHICH_CLUSTER = opts.cluster
	NR_OF_JOBS_TO_EXECUTE = opts.Nr_Jobs
	NR_OF_REQUESTED_NODES = opts.nr_nodes
	PACK_JOBS = opts.pack
	EMAIL_ID = opts.mail_id
	REMOVE = opts.remove
	PARTITION = opts.partition
	MOVE = opts.move
	QOS = opts.qos

	for dirName, subdirList, fileList in os.walk(rootfolder):
		if ("Results" in dirName) or ("FEASIBILITY" in dirName) or ("Visuals" in dirName):
			continue
		if len(fileList) > 0:
			DispatchTests(dirName, nptest)

	print("Finished all tests")

if __name__ == '__main__': 
	main()
