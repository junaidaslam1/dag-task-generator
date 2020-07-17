''' 
*********************** Fork Join DAG Generator (DG) ************************
* Author:           Muhammad Junaid Aslam                                   *
* Private Email:    junaidaslam1@gmail.com                                  *
* Work Email:       m.j.aslam@tudelft.nl                                    *
* Rank:             PhD Candidate                                           *
* Institute:        Technical University of Delft, Netherlands              *
*                                                                           *
* This software is a computer program whose purpose is to help the          *
* random generation of directed acyclic graph structures and adding         *
* various properties on those structures.                                   *
*                                                                           *
* ---------------------------------------------------------------------     *
* This software is governed by the Null license under M.J law and     |     *
* abiding by the rules of distribution of free software. You can use, |     *
* modify and redistribute the software under the condition of citing  |     *
* or crediting the authors of this software in your work.             |     *
* ---------------------------------------------------------------------     *
*                                                                           *
* FJDG is a random graph generator:                                         *
* it provides means to generate a directed acyclic graph following a        *
* method of the nested fork join. This is part of a research project funded *
* by the EWI EEMCS Group of Technical University of Delft, Netherlands.     *
*                                											*
* Note: In order to generate the visual graphs of DAG Tasks, you need to    *
* install the "graphviz" package, otherwise it will throw error about 'dot' *
* command.                                                                  *
*****************************************************************************
#TODO: Fix EdgeExists_in_Paths Function, which is Called with "-n R" CLI option
'''
#!/usr/bin/env python3
import argparse
import csv
import numpy as np
import random
import math
import time
import signal, os
import subprocess
import datetime
import sys
import os
import threading
import copy
import random
from fractions import gcd
from functools import reduce

RSC0_COLOR = "blue"
RSC1_COLOR = "black"
RSC2_COLOR = "green"
RSC3_COLOR = "cyan4"
RSC4_COLOR = "violet"
RSC5_COLOR = "red"
RSC6_COLOR = "orange"
RSC7_COLOR = "grey"
RSC8_COLOR = "brown"
RSC9_COLOR = "purple"
RSC10_COLOR = "goldenrod"
CRP_J_COLOR = "saddlebrown"
CRP_W_COLOR = "dodgerblue"

'''
Global Fixed Variables
'''
DUMMY_NUMBER	=	20000000
ERROR = DUMMY_NUMBER
UTILIZATION_TOLERANCE = 0.1
UTILIZATION_TOLERANCE_PERCENTAGE = 75 # (Utilization/Tasks)*100 
DEFAULT_TASK_EXPANSION_TRIES = DUMMY_NUMBER
DEFAULT_TASK_GENERATION_TRIES = 1000000
DEFAULT_FEASIBLE_TASK_GENERATION_TRIES = 25000
DEFAULT_TASK_UUFD_TRIES = DUMMY_NUMBER
DEFAULT_MIN_REQUIRED_FEASIBILITY = 0.000 
LONGEST_JOB_PATH_COLOR = 11
LONGEST_WCET_PATH_COLOR = 12
IS_TERMINAL =   1
IS_PARALLEL =   2
IS_JOIN     =   3
MAX_PERIOD_GENERATED = 0

'''
Specifications of Generation specified @ Command line
'''
DEBUG = 'Off'
WANT_ALL_RSC_TYPE_NODES = False
WANT_GRAPH = False
WANT_JOBSET = False
WANT_TASKJOB_SET = False
WANT_HETEROGENEOUS  =   False
WANT_CRITICAL_PATH_JOBS  =   False
WANT_CRITICAL_PATH_WCET  =   False
WANT_TASKSET_FILES  =   False
WANT_MORE_SIBLINGS 	=	False
SS_RSC  =   0
SELF_SUSPENDING = False
UTILIZATION_METHOD = ""
RESERVED    =   2
FULL        =   1
CONVERT_TO_NFJ_DAG = FULL
FEASIBILITY_ANALYSIS = ""
SCHEDULABILITY_TEST_PATH = ""
FEASIBILITY_ANALYSIS_THREADS = 0
PERIOD_CONDITIONING = False
PERIOD_ASSIGNMENT = ""
PERIODS_ARRAY = []
PRIORITY_ARRAY = []
PRIORITY_POLICY = ""
MULTI_THREADING = False
EQUAL_DEADLINE_TASKS_GENERATION = True
EQUAL_PRIORITY_TASKS_GENERATION = False
DEFAULT_ECRTS_19_MIN_PERIOD		= 500
NON_NESTED_FORK_JOIN	=	False

'''
Specifications of Task Set Generation specified in TasksetSettings.csv
'''
NR_OF_RUNS = 0
NR_OF_WORKLOADS = 0 # Works only with Resource Range Specifications
MIN_N = 0 # Minimum Number of Tasks
MAX_N = 0 # Maximum Number of Tasks
TASK_MULTIPLES = 0
RESOURCE_TYPES = 0
RESOURCE_RANGE_MIN = 0
RESOURCE_RANGE_MAX = 0
CORES_RANGE_MIN = 0
CORES_RANGE_MAX = 0
CORES_PER_RESOURCE = []
TOTAL_COMPUTING_NODES = 0
MIN_PERIOD = 0
MAX_PERIOD = 0
MAX_HYPER_PERIOD = 0
MIN_PAR_BRANCHES = 1
MAX_PAR_BRANCHES = 3
JITTER_TYPE = "FIXED" # Options: FIXED, VARIABLE or WITH_PRECEDENCE (This option assign release times w.r.t precedecessors max{release+finish times}
PROB_TERMINAL = 0
PROB_PARALLEL = 0
PROB_ADD_EDGE = 0
MAX_LENGTH = 0
MIN_NODES  = 0
MAX_NODES = 0
MAX_NODES_FOR_ALL_TASKS = 0
MAX_NODE_WCET = 0
MAX_RECURSION_DEPTH = 0
RELEASE_JITTER_R_Min = 0 
RELEASE_JITTER_R_Max = 0
TOTAL_NR_OF_UTILIZATION = 0
UTILIZATION_VECTOR = []
EXEC_TIME_VARIATION = 0
MAX_JOBS_PER_HYPER_PERIOD = 0
RSC_ASSIGNMENT_BY_PROBABILITY = False

class NodeInfo:
	
	def __init__(self): 
		self.TID   = 0
		self.JID   = 0
		self.r_min = 0
		self.r_max = 0
		self.BCET  = 0
		self.WCET  = 0
		self.Pred  = []
		self.Succ  = []
		self.Par_v = []
		self.Desc  = []
		self.Ancs  = []
		self.Term  = False
		self.ResourceType = 1
		self.Deadline = 0
		self.Length = 0

	def DisplayData(self):
		print("T%dJ%d BCET:%d WCET:%d RSC:%d Deadline:%d"%\
			(self.TID, self.JID, self.BCET, self.WCET, self.ResourceType, self.Deadline))

class TaskData:
	def __init__(self): 
		self.TID      = 0
		self.Nodes    = 0
		self.Period   = 0
		self.Deadline = 0
		self.Priority = 0

class myThread(threading.Thread):
	def __init__(self, path, Utilization, FA):
		threading.Thread.__init__(self)
		self.path  = path
		self.Utilization  = Utilization
		self.FA = FA
	def run(self):
		print("Starting " + self.path)
		CreateWorkloadRuns(self.path, self.Utilization, self.FA)
		print("Exiting " + self.path)

def getColor(RSC_TYPE):
	if RSC_TYPE == 0:
		return RSC0_COLOR
	elif RSC_TYPE == 1:
		return RSC1_COLOR
	elif RSC_TYPE == 2:
		return RSC2_COLOR
	elif RSC_TYPE == 3:
		return RSC3_COLOR
	elif RSC_TYPE == 4:
		return RSC4_COLOR
	elif RSC_TYPE == 5:
		return RSC5_COLOR
	elif RSC_TYPE == 6:
		return RSC6_COLOR
	elif RSC_TYPE == 7:
		return RSC7_COLOR
	elif RSC_TYPE == 8:
		return RSC8_COLOR
	elif RSC_TYPE == 9:
		return RSC9_COLOR
	elif RSC_TYPE == 10:
		return RSC10_COLOR
	elif RSC_TYPE == LONGEST_JOB_PATH_COLOR:
		return CRP_J_COLOR
	elif RSC_TYPE == LONGEST_WCET_PATH_COLOR:
		return CRP_W_COLOR

def run_command(incommand):
	p = subprocess.Popen(incommand.split(), stdout=subprocess.PIPE,
stderr=subprocess.STDOUT)
	outstring = p.stdout.read()
	return outstring

def getRandomSample(min, max):
	return np.random.random_sample(min, max)

def getRandomInteger(min, max):
	return np.random.random_integers(min, max)

def getSiblingsCount(NodesCreated = 2):
	values = []
	p_values = []

	if NodesCreated >= MAX_NODES:
		return 0
	elif (MAX_NODES - NodesCreated) < MAX_PAR_BRANCHES:
		return (MAX_NODES - NodesCreated)

	if WANT_MORE_SIBLINGS == True:
		for n in reversed(range(MAX_PAR_BRANCHES)):
			values.append(n+1)
			if n == MAX_PAR_BRANCHES-1:
				lval = (1/MAX_PAR_BRANCHES) + (0.5/MAX_PAR_BRANCHES)
				p_values.append(lval)
			elif n == 0:
				p_values.append(0.5/MAX_PAR_BRANCHES)
			else:
				p_values.append(1/MAX_PAR_BRANCHES)
	else:
		return getRandomInteger(MIN_PAR_BRANCHES, MAX_PAR_BRANCHES)

	return np.random.choice(values, p = p_values)

def getUniform(min, max):
	return np.random.uniform(min, max)

def isTerminalNodeOrParallelSubGraph():
	values = [IS_TERMINAL, IS_PARALLEL, IS_JOIN]
	p_values = [PROB_TERMINAL, PROB_PARALLEL, 1 - PROB_TERMINAL - PROB_PARALLEL]
	return np.random.choice(values, p = p_values)

def getResourcebyProbability():
	values = []
	p_values = []

	for n in range(0, RESOURCE_TYPES):
		RSC = n+1
		values.append(RSC)
		p_values.append((float)(CORES_PER_RESOURCE[n] / TOTAL_COMPUTING_NODES))

	return np.random.choice(values, p = p_values)

def isTerminalNode():
	values = [IS_TERMINAL, IS_JOIN]
	p_values = [PROB_TERMINAL, 1 - PROB_TERMINAL]
	return np.random.choice(values, p = p_values)

def isJoinOrParallelSubGraph():
	values = [IS_PARALLEL, IS_JOIN]
	p_values = [PROB_PARALLEL, 1 - PROB_TERMINAL - PROB_PARALLEL]
	return np.random.choice(values, p = p_values)

def ShouldAddEdge():
	values = [True, False]
	p_values = [PROB_ADD_EDGE, 1 - PROB_ADD_EDGE]
	return np.random.choice(values, p = p_values)

def getRandomResourceAssignment(SelfSuspending = False):
	if SelfSuspending == True:
		return getRandomInteger(0, RESOURCE_TYPES)
	else:
		return getRandomInteger(1, RESOURCE_TYPES)

def getResourceAssignmentbyProbability(SelfSuspending = False):
	'''
	The probability of each resource is calculated as:
		P(sigma_i) = M(sigma_i) / M
		Probability = CoresOfRSC_i / TotalCoresOfAllRSC
	'''
	if SelfSuspending == True:
		# fix this with probability
		return getRandomInteger(0, RESOURCE_TYPES)
	else:
		return getResourcebyProbability()

def RandFixSum(Utilizations_Per_Task, List_of_Nodes_Per_Task):
	nums = []
	for i in totals:
		if i == 0: 
			nums.append([0 for i in range(6)])
			continue
		total = i
		temp = []
		for i in range(5):
			val = np.random.randint(0, total)
			temp.append(val)
			total -= val
		temp.append(total)
		nums.append(temp)

	print(nums)

def PrintNodes(Nodes):
	for n in range(0, len(Nodes)):
		Nodes[n].DisplayData()

def Print_Pred_Succ_Par_Ancs_Desc(VertexID, List, Attribute="Predecessors", PRINT=False):
	printList = "{"

	if (Attribute == "Predecessors"):
		for m in range(0, len(List)):
			printList += "J"+str(List[m])+", "
	elif (Attribute == "Successors"):
		for m in range(0, len(List)):
			printList += "J"+str(List[m])+", "
	else:
		for m in range(0, len(List)):
			printList += "J"+str(List[m].JID)+", "

	printList += "}"

	if PRINT == True:
		print("Vertex:%d %s:%s"%(VertexID, Attribute, printList))

	return printList

def getLogUniformPeriod():
	s = math.log(MIN_PERIOD)
	e = math.log(MAX_PERIOD + MIN_PERIOD)
	ri = getUniform(s, e)
	Period = int((math.floor(math.exp(ri)/MIN_PERIOD))*MIN_PERIOD)
	return Period;

def Print_TaskSet(TaskSet, Utilizations, Periods, PRINT=False):
	for Task in range(0, len(TaskSet)):
		outAllPaths = []
		AllPaths = []
		CriticalPaths = []
		getAllPaths(TaskSet[Task], TaskSet[Task][0], outAllPaths, AllPaths)
		CriticalPaths, CriticalPaths_WCET = getCriticalPaths_wrt_WCET(outAllPaths)

		if PRINT:
			print("---CRP_WCET:%d----Util:%f%% = %f-------Period:%d---VOL_G=%d-----"\
				%(CriticalPaths_WCET, Utilizations[Task]/TOTAL_COMPUTING_NODES, Utilizations[Task], Periods[Task], Utilizations[Task]*Periods[Task]))
			
			for Vertex in range(0, len(TaskSet[Task])):
				print("J%d BCET:%d WCET:%d"%(TaskSet[Task][Vertex].JID, TaskSet[Task][Vertex].BCET, TaskSet[Task][Vertex].WCET))

def PrintExtractedParameters():
	lvTotalResources = 0
	print("NR_OF_RUNS:%d"%(NR_OF_RUNS))
	print("NR_OF_WORKLOADS:%d ... This option only works with ResourceRange Settings"%(NR_OF_WORKLOADS))
	print("MIN_N:%d"%(MIN_N))
	print("MAX_N:%d"%(MAX_N))
	print("TASK_MULTIPLES:%d"%(TASK_MULTIPLES))

	if RESOURCE_RANGE_MAX == 0:
		print("RESOURCE_TYPES:%d"%(RESOURCE_TYPES))
		for n in range(0,RESOURCE_TYPES):
			print("CORES_OF_%d = %d"%(n+1,CORES_PER_RESOURCE[n]))
			lvTotalResources += CORES_PER_RESOURCE[n]
	else:
		print("Workload will be generated by selecting total resource types and cores per resource type from following ranges uniformly.")
		print("RESOURCE_RANGE_MIN:%d"%(RESOURCE_RANGE_MIN))
		print("RESOURCE_RANGE_MAX:%d"%(RESOURCE_RANGE_MAX))
		print("CORES_RANGE_MIN:%d"%(CORES_RANGE_MIN))
		print("CORES_RANGE_MAX:%d"%(CORES_RANGE_MAX))

	print("RSC_ASSIGNMENT_BY_PROBABILITY:%s"%(RSC_ASSIGNMENT_BY_PROBABILITY))
	print("MIN_PERIOD:%d"%MIN_PERIOD)
	print("MAX_PERIOD:%d"%MAX_PERIOD)

	if MAX_HYPER_PERIOD == 0:
		print("MAX_HYPER_PERIOD:%d ... Warning!!! It may allow a large HyperPeriod"%(MAX_HYPER_PERIOD))
	else:
		print("MAX_HYPER_PERIOD:%d"%(MAX_HYPER_PERIOD))

	if MAX_JOBS_PER_HYPER_PERIOD == 0:
		print("MAX_JOBS_PER_HYPER_PERIOD:%d ... Warning!!! It may create large job-set"%(MAX_JOBS_PER_HYPER_PERIOD))
	else:
		print("MAX_JOBS_PER_HYPER_PERIOD:%d"%(MAX_JOBS_PER_HYPER_PERIOD))
	print("MIN_PAR_BRANCHES:%d"%(MIN_PAR_BRANCHES))
	print("MAX_PAR_BRANCHES:%d"%(MAX_PAR_BRANCHES))
	
	if JITTER_TYPE == "WITH_PRECEDENCE":
		print("JITTER_TYPE:%s ... This option assigns release times w.r.t max{release+finish times} out of all precedecessors of the node"%(JITTER_TYPE))
	else:
		print("JITTER_TYPE:%s"%(JITTER_TYPE))

	print("PROB_TERMINAL:%f"%(PROB_TERMINAL))
	print("PROB_PARALLEL:%f"%(PROB_PARALLEL))
	print("PROB_ADD_EDGE:%f"%(PROB_ADD_EDGE))
	print("MAX_LENGTH:%d"%(MAX_LENGTH))
	print("MIN_NODES:%d"%(MIN_NODES))
	print("MAX_NODES:%d"%(MAX_NODES))
	print("MAX_NODES_FOR_ALL_TASKS:%d"%(MAX_NODES_FOR_ALL_TASKS))
	print("MAX_NODE_WCET:%d"%(MAX_NODE_WCET))
	print("MAX_RECURSION_DEPTH:%d"%(MAX_RECURSION_DEPTH))
	print("RELEASE_JITTER_R_Min:%d"%(RELEASE_JITTER_R_Min))
	print("RELEASE_JITTER_R_Max:%d"%(RELEASE_JITTER_R_Max))

	print("Nr_OF_UTILIZATIONs:%d"%(TOTAL_NR_OF_UTILIZATION))
	for n in range(0, TOTAL_NR_OF_UTILIZATION):
		print("UTILIZATION_%d = %f%%"%(n+1, UTILIZATION_VECTOR[n]))
	
	print("EXEC_TIME_VARIATION:%f"%(EXEC_TIME_VARIATION))

	print("--------------------------------------------")

def isPeriodDuplicate(Periods, inPeriod=0):
	if inPeriod == 0:
		for Period in range(0, len(Periods)):
			if Periods.count(Periods[Period]) > 0:
				if DEBUG == 'e':
					print("Failed for Duplicate Period:%d in List of Periods:"%(Periods[Period]))
					print(Periods)
					print("------------------------------------------------------")	
				return True
	else:	
		if Periods.count(inPeriod) > 0:
			if DEBUG == 'e': 
				print("Failed for Duplicate Period:%d in List of Periods:"%(inPeriod))
				print(Periods)
				print("------------------------------------------------------")		
			return True
	return False

def ExtractParameters(Settings):
	global NR_OF_RUNS
	global MIN_N
	global MAX_N
	global RESOURCE_TYPES
	global CORES_PER_RESOURCE
	global TOTAL_COMPUTING_NODES
	global MIN_PERIOD
	global MAX_PERIOD
	global MAX_HYPER_PERIOD
	global MIN_PAR_BRANCHES
	global MAX_PAR_BRANCHES
	global JITTER_TYPE 
	global PROB_TERMINAL
	global PROB_PARALLEL
	global PROB_ADD_EDGE
	global MAX_LENGTH
	global MIN_NODES
	global MAX_NODES
	global MAX_NODES_FOR_ALL_TASKS
	global MAX_NODE_WCET
	global MAX_RECURSION_DEPTH
	global RELEASE_JITTER_R_Min
	global RELEASE_JITTER_R_Max
	global TOTAL_NR_OF_UTILIZATION
	global EXEC_TIME_VARIATION
	global TASK_MULTIPLES
	global RSC_ASSIGNMENT_BY_PROBABILITY
	global MAX_JOBS_PER_HYPER_PERIOD
	global RESOURCE_RANGE_MIN
	global RESOURCE_RANGE_MAX	
	global CORES_RANGE_MIN
	global CORES_RANGE_MAX
	global NR_OF_WORKLOADS

	TotalComputingNodes =   0
	MaxUtilizationPercentage    =   0

	fp = open(Settings, 'r')
	Start = 0
	settings = csv.reader(fp, skipinitialspace=True)
	for row in settings:

		if row[0] != "TypedDagTask" and Start == False:
			print("InvalidFileHeader")
			exit(1)

		Start = True

		if row[0] == "Runs":
			NR_OF_RUNS = int(row[1])
		elif row[0] == "NR_OF_WORKLOADS":
			NR_OF_WORKLOADS = int(row[1])
		elif row[0] == "Min_N":
			MIN_N = int(row[1])
		elif row[0] == "Max_N":
			MAX_N = int(row[1])
		elif row[0] == "N_Multiples":
			TASK_MULTIPLES = int(row[1])
		elif row[0] == "ResourceTypes":
			NR_OF_WORKLOADS = 1
			RESOURCE_TYPES = int(row[1])
			for n in range(0,RESOURCE_TYPES):
				CORES_PER_RESOURCE.append(int(row[n+2]))
				TotalComputingNodes += int(row[n+2])
		elif row[0] == "ResourceRange":
			RESOURCE_RANGE_MIN = int(row[1])
			RESOURCE_RANGE_MAX = int(row[2])
			CORES_RANGE_MIN = int(row[3])
			CORES_RANGE_MAX = int(row[4])
		elif row[0] == "ResourcebyProbability":
			RSC_ASSIGNMENT_BY_PROBABILITY = row[1]
			if RSC_ASSIGNMENT_BY_PROBABILITY == "TRUE":
				RSC_ASSIGNMENT_BY_PROBABILITY = True
			else:
				RSC_ASSIGNMENT_BY_PROBABILITY = False
		elif row[0] == "Min_Period":
			MIN_PERIOD = int(row[1])
		elif row[0] == "Max_Period":
			MAX_PERIOD = int(row[1])
		elif row[0] == "Max_Hyper_Period":
			MAX_HYPER_PERIOD = int(row[1])
		elif row[0] == "Max_Jobs_Per_HP":
			MAX_JOBS_PER_HYPER_PERIOD = int(row[1])
		elif row[0] == "Branches":
			MIN_PAR_BRANCHES = int(row[1])
			MAX_PAR_BRANCHES = int(row[2])
		elif row[0] == "Jitter_Type":
			JITTER_TYPE = row[1]
		elif row[0] == "Prob_Terminal":
			PROB_TERMINAL = float(row[1])
		elif row[0] == "Prob_Parallel":
			PROB_PARALLEL = float(row[1])
		elif row[0] == "Prob_Add_Edge":
			PROB_ADD_EDGE = float(row[1])
		elif row[0] == "Max_Critical_Path_Nodes":
			MAX_LENGTH = int(row[1])
		elif row[0] == "Min_Nodes":
			MIN_NODES = int(row[1])
		elif row[0] == "Max_Nodes":
			MAX_NODES = int(row[1])
		elif row[0] == "Max_Nodes_For_All_Tasks":
			MAX_NODES_FOR_ALL_TASKS = int(row[1])
		elif row[0] == "Max_Node_WCET":
			MAX_NODE_WCET = int(row[1])
		elif row[0] == "Max_Depth":
			MAX_RECURSION_DEPTH = int(row[1])
		elif row[0] == "ReleaseJitter":
			RELEASE_JITTER_R_Min = int(row[1])
			RELEASE_JITTER_R_Max = int(row[2])
		elif row[0] == "Utilizations":
			TOTAL_NR_OF_UTILIZATION = int(row[1])
			for n in range(0,TOTAL_NR_OF_UTILIZATION):
				UTILIZATION_VECTOR.append(float(row[n+2]))
		elif row[0] == "ExecTimeVariation":
			EXEC_TIME_VARIATION = float(row[1])
		elif row[0] == "EndSpecification":
			print("File Traversing Finished")
			break

		TOTAL_COMPUTING_NODES   =   TotalComputingNodes
		# TOTAL_UTILIZATION =  float(TotalComputingNodes * MaxUtilizationPercentage)

def UUniFast(Number_of_Items, Quantity):
	# Classic UUniFast algorithm:
	Separated_Quantities = []
	sumU = Quantity
	nextSumU = 0

	for i in range(0, Number_of_Items-1):
		nextSumU = sumU * (random.random() ** (1.0 / (Number_of_Items - i)))
		Separated_Quantities.append(sumU - nextSumU)
		sumU = nextSumU
		
	Separated_Quantities.append(sumU)

	return Separated_Quantities

def getTotalTaskWCET(Nodes):
	WCET_SUM = 0
	
	for n in range(0, len(Nodes)):
		WCET_SUM += Nodes[n].WCET

	return WCET_SUM

def getTaskPeriod(utilization, Nodes):
	
	WCET_SUM = 0
	
	for n in range(0, len(Nodes)):
		WCET_SUM += Nodes[n].WCET

	Period = int(WCET_SUM / (utilization))

	return Period

def checkCoPrime(Periods):
	if len(Periods) > 2:
		x = reduce(gcd, Periods)
		return x
	elif len(Periods) == 2:
		return math.gcd(Periods[0], Periods[1])

def csvWriteRow(Writer, List):
	Writer.writerow(List)
	List.clear()

def create_job_set(FileName): 
	lvFileName = FileName.split('.')
	
	lvJobFileName   =   lvFileName[0]+"_Jobs.csv"
	lvPredFileName   =   lvFileName[0]+"_Pred.csv"

	pwd = str(run_command("pwd")).split("\\")
	lvpwd = pwd[0].split("'")

	lvCMD = "python3 -W ignore "+lvpwd[1]+"/dag-tasks-to-jobs_hetero.py -p "+PRIORITY_POLICY+" "+FileName+" "+lvJobFileName+" "+lvPredFileName

	res = run_command(lvCMD)

	if WANT_TASKJOB_SET == False:
		lvCMD = "rm -rf "+FileName
		res = run_command(lvCMD)

	return lvJobFileName, lvPredFileName

def create_tasks_file(TaskCount, TaskSetList, FileName, Periods, Priorities):
	TaskSetFileData = []

	TaskSetData = []

	for Task in range(0, TaskCount):
		lvTaskData = TaskData()
		lvTaskData.TID = Task+1
		lvTaskData.Nodes = TaskSetList[Task]
		lvTaskData.Period= Periods[Task]
		lvTaskData.Deadline= Periods[Task]
		lvTaskData.Priority= Priorities[Task]
		TaskSetData.append(lvTaskData)

	TaskSetData.sort(key = lambda x:x.Period)

	with open(FileName, 'w') as csvfile:
		TaskWriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)

		TaskSetFileData.append('R')
		TaskSetFileData.append(RESOURCE_TYPES)
		csvWriteRow(TaskWriter, TaskSetFileData)

		for i in range(0, RESOURCE_TYPES):
			TaskSetFileData.append("M")
			TaskSetFileData.append(CORES_PER_RESOURCE[i])  
			csvWriteRow(TaskWriter, TaskSetFileData)

		TaskSetFileData.append("#")
		csvWriteRow(TaskWriter, TaskSetFileData)

		# A ’T’ row consists of the following columns:
		#
		#   1) ’T’
		#   2) a unique numeric ID
		#   3) the period (in milliseconds, fractional is ok)
		#   4) the relative deadline
		#   5) the priority

		for Task in range(0, TaskCount):
			TaskSetFileData.append('T')
			TaskSetFileData.append(TaskSetData[Task].TID)
			TaskSetFileData.append(TaskSetData[Task].Period)
			TaskSetFileData.append(TaskSetData[Task].Deadline)
			TaskSetFileData.append(TaskSetData[Task].Priority)
			csvWriteRow(TaskWriter, TaskSetFileData)

			# A ‘V’ row consists for the following columns (unbounded number):
			#
			#   1) ‘V’
			#   2) task ID to which it belongs
			#   3) a numeric vertex ID (unique w.r.t. its task)
			#   4) earliest release time r^min (relative to start of period, may be zero)
			#   5) latest release time r^max (relative to start of period)
			#   6) BCET
			#   7) WCET
			#   8) ResourceType
			#   9) first predecessor (vertex ID), if any
			#   10) second predecessor (vertex ID), if any
			#   11) third predecessor (vertex ID), if any
			#   … and so on …
			for Node in range(0, len(TaskSetData[Task].Nodes)):

					TaskSetFileData.append('V')
					TaskSetFileData.append(TaskSetData[Task].TID)
					TaskSetFileData.append(TaskSetData[Task].Nodes[Node].JID+1)
					TaskSetFileData.append(TaskSetData[Task].Nodes[Node].r_min)
					TaskSetFileData.append(TaskSetData[Task].Nodes[Node].r_max)
					TaskSetFileData.append(TaskSetData[Task].Nodes[Node].BCET)
					TaskSetFileData.append(TaskSetData[Task].Nodes[Node].WCET)
					TaskSetFileData.append(TaskSetData[Task].Nodes[Node].ResourceType)

					for p in range(0, len(TaskSetData[Task].Nodes[Node].Pred)):
						TaskSetFileData.append(TaskSetData[Task].Nodes[Node].Pred[p]+1)

					csvWriteRow(TaskWriter, TaskSetFileData)                         
					
def get_hyper_period(numbers):
	return reduce(lambda x, y: (x*y)/gcd(x,y), numbers, 1)     

def getUsedRSCTypes(Nodes):
	UsedRSCTypes = []
	
	for RSC in range(1, RESOURCE_TYPES+1):
		Type_Used = 0
		for v in range(0, len(Nodes)):
			if Nodes[v].ResourceType == RSC:
				Type_Used = RSC
				break

		if Type_Used != 0:
			UsedRSCTypes.append(Type_Used)
			Type_Used = 0

	return UsedRSCTypes
def getNodesCountOfRSCType(Nodes):
	Nodes_Per_RSC_Type = []
	
	for RSC in range(1, RESOURCE_TYPES+1):
		Type_Nodes = 0
		for v in range(0, len(Nodes)):
			if Nodes[v].ResourceType == RSC:
				Type_Nodes += 1
		Nodes_Per_RSC_Type.append(Type_Nodes)
		Type_Nodes = 0

	return Nodes_Per_RSC_Type

def UpdateTaskExecutionTimes_by_RSC_STRICTLY(TaskNodes, Utilization, Period):
	# We skip updation of self suspending jobs since their suspenstion time
	# does not count towards system utilization.

	Nodes_Per_RSC_Type = [] # Number of Nodes per RSC Type
	Utilization_Per_RSC_Type = []
	VOL_G_Per_RSC_Type_Nodes = []

	# Get nodes of each type of each task Nodes_Per_RSC_Type = getNodesOfType(Nodes)
	Nodes_Per_RSC_Type = getNodesCountOfRSCType(TaskNodes)

	# Get Utilization_Per_RSC_Type[RSC-1] = Utilization*(CORES_PER_RESOURCE[RSC-1]/TOTAL_COMPUTING_NODES)
	for RSC in range(0, RESOURCE_TYPES):
		Utilization_Per_RSC_Type.append(Utilization*(CORES_PER_RESOURCE[RSC]/TOTAL_COMPUTING_NODES))
	
	# Get WCET of Each type of nodes based on Type_Utilization*Period
	for RSC in range(0, RESOURCE_TYPES):
		VOL_G_Per_RSC_Type_Nodes.append(math.ceil(Utilization_Per_RSC_Type[RSC]*Period))
		

	# Get WCET  for each type of nodes
	for RSC in range(0, RESOURCE_TYPES):
		WCET_Per_Node = UUniFast(Nodes_Per_RSC_Type[RSC], VOL_G_Per_RSC_Type_Nodes[RSC])
		TypeNodeCounter = 0
		for vertex in range(0, len(TaskNodes)):
			if TaskNodes[vertex].ResourceType == RSC+1:
				TaskNodes[vertex].WCET = math.ceil(WCET_Per_Node[TypeNodeCounter])
				TaskNodes[vertex].BCET = math.ceil(TaskNodes[vertex].WCET * EXEC_TIME_VARIATION)
				if TaskNodes[vertex].BCET > TaskNodes[vertex].WCET:
					TaskNodes[vertex].BCET = TaskNodes[vertex].WCET
				TypeNodeCounter += 1

def UpdateTaskExecutionTimes(TaskNodes, Utilization, Period):
	# Get nodes of each type of each task Nodes_Per_RSC_Type = getNodesOfType(Nodes)
	# Get WCET  for each type of nodes
	Volume = Utilization * Period
	WCET_Per_Node = UUniFast(len(TaskNodes), Volume)
	for vertex in TaskNodes:
		vertex.WCET = math.ceil(WCET_Per_Node[vertex.JID])
		vertex.BCET = math.ceil(vertex.WCET * EXEC_TIME_VARIATION)
		if vertex.BCET > vertex.WCET:
			vertex.BCET = vertex.WCET

def UpdateReleaseTimes(Nodes):
	for vertex in range(1, len(Nodes)):
		MAX_of_r_min_plus_BCET = 0
		MAX_of_r_max_plus_WCET = 0

		for pred in range(0, len(Nodes[vertex].Pred)):
			if (MAX_of_r_min_plus_BCET < (Nodes[Nodes[vertex].Pred[pred]].r_min + Nodes[Nodes[vertex].Pred[pred]].BCET)):
				MAX_of_r_min_plus_BCET = (Nodes[Nodes[vertex].Pred[pred]].r_min + Nodes[Nodes[vertex].Pred[pred]].BCET)
			if (MAX_of_r_max_plus_WCET < (Nodes[Nodes[vertex].Pred[pred]].r_max + Nodes[Nodes[vertex].Pred[pred]].WCET)):
				MAX_of_r_max_plus_WCET = (Nodes[Nodes[vertex].Pred[pred]].r_max + Nodes[Nodes[vertex].Pred[pred]].WCET)

		Nodes[vertex].r_min = MAX_of_r_min_plus_BCET
		Nodes[vertex].r_max = MAX_of_r_max_plus_WCET

def AssignPeriod(Task, Nodes, Utilization, inPeriods=[]):
	#------------------------------- # Assigning Period to the Task # ------------------------ #
	Period = 0
	ScalingFactor = 1.0
	
	if (PERIOD_ASSIGNMENT == "Default") or (PERIOD_ASSIGNMENT == "ECRTS_19"):
		Period = int(getTaskPeriod(Utilization, Nodes))
	elif (PERIOD_ASSIGNMENT == "UNIFORM") or (PERIOD_ASSIGNMENT == "ECRTS_19_FIXED"):
		# Here the periods are automatically scaled
		if EQUAL_DEADLINE_TASKS_GENERATION == True:
			Period = int(random.choice(PERIODS_ARRAY))
		else:			
			while(True):
				Period = int(random.choice(PERIODS_ARRAY))
				if (isPeriodDuplicate(inPeriods, Period) == False): # Check if there is a duplicate period
					break
	elif PERIOD_ASSIGNMENT == "LOG_UNIFORM":
		Period = getLogUniformPeriod()

	if PERIOD_CONDITIONING == True:
		lvWCETSum = getTotalTaskWCET(Nodes)
		if Period < lvWCETSum:
			Period = int(lvWCETSum)

	if Period == 0:
		if DEBUG == 'e':
			print("Failed for Period:%d Invalid Generation:%d"%(Period))
			print("------------------------------------------------------")
		return Period
	
	# Scaling the Period according to given MIN_PERIOD
	if (PERIOD_ASSIGNMENT == "Default") or (PERIOD_ASSIGNMENT == "ECRTS_19"): # Since in Other Methods we always have multiples of MIN_PERIOD
		if Period < MIN_PERIOD:
			ScalingFactor = float(MIN_PERIOD / Period)
			Period = MIN_PERIOD
			for n in range(0, len(Nodes)):
				Nodes[n].WCET = int(math.ceil(Nodes[n].WCET*ScalingFactor))
				Nodes[n].BCET = int(math.ceil(Nodes[n].BCET*ScalingFactor))
				Nodes[n].r_min = int(math.ceil(Nodes[n].r_min*ScalingFactor))
				Nodes[n].r_max = int(math.ceil(Nodes[n].r_max*ScalingFactor))

				if Nodes[n].BCET > Nodes[n].WCET:
					Nodes[n].BCET = Nodes[n].WCET
				if Nodes[n].r_min > Nodes[n].r_max:
					Nodes[n].r_min = Nodes[n].r_max

		elif Period > MAX_PERIOD:
			if DEBUG == 'e':
				print("Failed for Task:%d Period:%d > MAX_PERIOD:%d"%(Task, Period, MAX_PERIOD))
				print("------------------------------------------------------")
			return Period
		elif ((Period % MIN_PERIOD) != 0):
			if (PERIOD_ASSIGNMENT == "Default"): 
				ScalingFactor = float((Period + (MIN_PERIOD - (Period%MIN_PERIOD))) / Period)
				Period += (MIN_PERIOD - (Period%MIN_PERIOD)) 
				for n in range(0, len(Nodes)):
					Nodes[n].WCET = int(math.ceil(Nodes[n].WCET*ScalingFactor))
					Nodes[n].BCET = int(math.ceil(Nodes[n].BCET*ScalingFactor))
					Nodes[n].r_min = int(math.ceil(Nodes[n].r_min*ScalingFactor))
					Nodes[n].r_max = int(math.ceil(Nodes[n].r_max*ScalingFactor))
				
					if Nodes[n].BCET > Nodes[n].WCET:
						Nodes[n].BCET = Nodes[n].WCET
					if Nodes[n].r_min > Nodes[n].r_max:
						Nodes[n].r_min = Nodes[n].r_max
			elif (PERIOD_ASSIGNMENT == "ECRTS_19"):
				ChosenScaledPeriod = min(PERIODS_ARRAY, key=lambda y:abs(y-Period))
				ScalingFactor = float(ChosenScaledPeriod / Period)
				Period = ChosenScaledPeriod
				for n in range(0, len(Nodes)):
					Nodes[n].WCET = int(math.ceil(Nodes[n].WCET*ScalingFactor))
					Nodes[n].BCET = int(math.ceil(Nodes[n].BCET*ScalingFactor))
					Nodes[n].r_min = int(math.ceil(Nodes[n].r_min*ScalingFactor))
					Nodes[n].r_max = int(math.ceil(Nodes[n].r_max*ScalingFactor))
				
					if Nodes[n].BCET > Nodes[n].WCET:
						Nodes[n].BCET = Nodes[n].WCET
					if Nodes[n].r_min > Nodes[n].r_max:
						Nodes[n].r_min = Nodes[n].r_max

	# We do it at the end so that period scaling is taken into account
	if (PERIOD_ASSIGNMENT == "UNIFORM") or (PERIOD_ASSIGNMENT == "LOG_UNIFORM") or (PERIOD_ASSIGNMENT == "ECRTS_19_FIXED"):
		if WANT_ALL_RSC_TYPE_NODES == True:
			UpdateTaskExecutionTimes_by_RSC_STRICTLY(Nodes, Utilization, Period)
		else:
			UpdateTaskExecutionTimes(Nodes, Utilization, Period)

	CRP, CRP_WCET = getCriticalPathInfo(Nodes)
 
	if Period < CRP_WCET:
		if DEBUG == 'e':
			print("Failed for Task:%d Period:%d < CRP_WCET:%d"%(Task, Period, CRP_WCET))
			print("------------------------------------------------------")
		Period = 0 # This marks that this is invalid period
		return Period

	if JITTER_TYPE == "WITH_PRECEDENCE":
		UpdateReleaseTimes(Nodes)

	return Period

def checkNecessaryCondition(TaskSetList, Utilizations, inputUtilization, Periods=[]):
	'''
	Necessary Condition:
	Ui(RSC) = Sum(Uj(RSC)) | j = 1 to N
	Uj(RSC) = Sum(Ck/Tj) | k = 1 to len(Nodes(RSC))
	Ui(RSC) <= m(RSC)
	'''
	FoundSSNode = False
	TotalNrOfTasks = len(TaskSetList)
	TotalJobsPerHyperPeriod = 0
	TotalNodesOfAllTasks = 0

	if (EQUAL_DEADLINE_TASKS_GENERATION == True):
		for Task in range(0, len(TaskSetList)):
			lvPeriod = 0
			lvPeriod = AssignPeriod(Task, TaskSetList[Task], Utilizations[Task], Periods)
			if lvPeriod == 0 or lvPeriod > MAX_PERIOD:
				return False, TotalJobsPerHyperPeriod
			Periods.append(lvPeriod)

	HyperPeriod = get_hyper_period(Periods)

	for n in range(0, len(Periods)):
		TotalJobsPerHyperPeriod += (HyperPeriod/Periods[n])*len(TaskSetList[n])

	if (MAX_HYPER_PERIOD != 0) and (HyperPeriod > MAX_HYPER_PERIOD):
		if DEBUG == 'e':
			print("Failed for HyperPeriods:%d > MAX_HYPER_PERIOD:%d"%(HyperPeriod, MAX_HYPER_PERIOD))
			print("------------------------------------------------------")
		return False, TotalJobsPerHyperPeriod

	if (MAX_JOBS_PER_HYPER_PERIOD != 0) and (TotalJobsPerHyperPeriod > MAX_JOBS_PER_HYPER_PERIOD): 
		if DEBUG == 'e':
			print("Failed for TotalJobsPerHyperPeriod:%d > MAX_JOBS_PER_HYPER_PERIOD:%d"%(TotalJobsPerHyperPeriod, MAX_JOBS_PER_HYPER_PERIOD))
			print("------------------------------------------------------")
		return False, TotalJobsPerHyperPeriod

	U_RSC = []

	for RSC in range(0, RESOURCE_TYPES): 
		Ui_RSC = 0
		for TaskNodes in range(0, TotalNrOfTasks):
			for Node in range(0, len(TaskSetList[TaskNodes])):
				TotalNodesOfAllTasks = TotalNodesOfAllTasks + 1
				if (SELF_SUSPENDING == True) and (TaskSetList[TaskNodes][Node].ResourceType == SS_RSC):
					FoundSSNode = True
				if TaskSetList[TaskNodes][Node].ResourceType == RSC+1: # Added 1 to Elude Self Suspending
					Ui_RSC +=  (float)(TaskSetList[TaskNodes][Node].WCET / Periods[TaskNodes])
		
		if TotalNodesOfAllTasks > MAX_NODES_FOR_ALL_TASKS:
			if DEBUG == 'e':
				print("Failed for TotalNodesOfAllTasks:%d > MAX_NODES_FOR_ALL_TASKS:%d"%(TotalNodesOfAllTasks, MAX_NODES_FOR_ALL_TASKS))
				print("------------------------------------------------------")
			return False, TotalJobsPerHyperPeriod
		'''
		if (inputUtilization > 1) and ((Ui_RSC*inputUtilization) > (CORES_PER_RESOURCE[RSC]*inputUtilization)):
			if DEBUG == 'e':
				print("Failed for RSC:%d Ui_RSC:%f > CORES_PER_RESOURCE[%d]:%f"%(RSC+1, Ui_RSC*inputUtilization, RSC+1, (CORES_PER_RESOURCE[RSC]*inputUtilization)))
				print("------------------------------------------------------")
			return False, TotalJobsPerHyperPeriod
		elif (inputUtilization <= 1) and (Ui_RSC > CORES_PER_RESOURCE[RSC]):
			if DEBUG == 'e':
				print("Failed for RSC:%d Ui_RSC:%f > CORES_PER_RESOURCE[%d]:%d"%(RSC+1, Ui_RSC, RSC+1, CORES_PER_RESOURCE[RSC]))
				print("------------------------------------------------------")
			return False, TotalJobsPerHyperPeriod
		else:
			U_RSC.append(Ui_RSC)
		'''
		if (Ui_RSC > CORES_PER_RESOURCE[RSC]):
			if DEBUG == 'e':
				print("Failed for RSC:%d Ui_RSC:%f%% > %f%% CORES_PER_RESOURCE[%d]:%d"%(RSC+1, Ui_RSC, CORES_PER_RESOURCE[RSC]*inputUtilization, RSC+1, CORES_PER_RESOURCE[RSC]))
				print("------------------------------------------------------")
			return False, TotalJobsPerHyperPeriod
		else:
			U_RSC.append(Ui_RSC)

	'''
	isCoPrime = 10
	isCoPrime = checkCoPrime(Periods)
	if isCoPrime <= 1:
		if DEBUG == 'e':
			print("Failed for Periods being CoPrime.")
			print("------------------------------------------------------")
		return False, TotalJobsPerHyperPeriod
	'''

	if (SELF_SUSPENDING == True) and (FoundSSNode == False):
		if DEBUG == 'e':
			print("Failed for No SS_NODE_FOUND")
		return False, TotalJobsPerHyperPeriod

	return True, TotalJobsPerHyperPeriod

def parse_args():

	parser = argparse.ArgumentParser(description="Create task sets file")

	parser.add_argument('-d', '--debug', dest='debug', default='Off', 
						action='store', type=str, metavar="DEBUG",
						required=False,
						help='Choose "d" for DEBUG and "e" for error Messages')

	parser.add_argument('-j', '--job-set', dest='job_set', default='n', 
						action='store', type=str, metavar="Job_Set",
						required=False,
						help="If taskset file created choose Y to create jobset. If you don`t want to remove taskset file, then choose Z with this option\n\
						This option requires 'dag-tasks-to-jobs_hetero.py' script to be placed in the same location as of this DAG generation script")

	parser.add_argument('-ss', '--self_suspending', dest='self_suspending', default='n', 
						action='store', type=str, metavar="self_suspending",
						required=False,
						help="Choose Y or y to enable self_suspending job generation")

	parser.add_argument('-l', '--max_jobs_in_path', dest='critical_path', default='n', 
						action='store', type=str, metavar="LONGEST_PATH",
						required=False,
						help="Choose J or W to enable longest path w.r.t max number of jobs and WCET respectively")

	parser.add_argument('-p', '--location', dest='parent_folder', default='~/', 
						action='store', type=str, metavar="STORAGE_LOCATION",
						required=True,
						help='The place to generate folders for saving Workload files')

	parser.add_argument('-f', '--taskset_files', dest='taskset_files', default='no', 
						action='store', type=str, metavar="FILES",
						required=False,
						help='Choose Y or y if Want to Generate Task Set files; If this option is not given taskset data is generated without generating files')

	parser.add_argument('-g', '--graph', dest='want_graph', default='no', 
						action='store', type=str, metavar="GRAPH",
						required=False,
						help='Choose Y or y if Want Graph of DAG Tasks, This option requires "graphviz" utility to be installed')

	parser.add_argument('-t', '--type', dest='task_type', default='Typed', 
						action='store', type=str, metavar="TYPE",
						required=False,
						help='Specify Task Nature: "Typed" or "Hetero"')

	parser.add_argument('-pp', '--priority_policy', dest='priority_policy', default='EDF', 
						action='store', type=str, metavar="TYPE",
						required=False,
						help='Specify Priority policy for jobset: "EDF, RM, DM, FP or NC", \n\
						NC = Distinct Fixed Priorities set by this tool w.r.t periods, don`t use -ep option with this.')
	
	parser.add_argument('-ed', '--equal_deadline_tasks', dest='equal_deadline_tasks', default='Y', 
						action='store', type=str, metavar="EDT",
						required=False,
						help='Choose "N/n" to disable generation of tasks with equal deadlines / periods.\n\
						Recommended to use -P UNIFORM or -P ECRTS_19 option with this otherwise it will take a long time.')

	parser.add_argument('-ep', '--equal_priority_tasks', dest='equal_priority_tasks', default='N', 
						action='store', type=str, metavar="EDT",
						required=False,
						help='Choose "Y/y" to enable generation of tasks with equal priorities.')

	parser.add_argument('-mt', '--multi_threading', dest='multi_threading', default='N', 
						action='store', type=str, metavar="TYPE",
						required=False,
						help='Choose Y or y to enable one thread per utilization exploration. \
						Do not use this option with ResourceRange Specifications with NR_OF_WORKLOADS > 1.')

	parser.add_argument('-P', '--period_assignment', dest='period_assignment', default='Default', 
						action='store', type=str, metavar="PERIOD_ASSIGNMENT",
						required=False,
						help='Option: "UNIFORM" and "ECRTS_19" ... UNIFORM generates uniformly b/w [MIN_PERIOD, MAX_PERIOD].\n\
						ECRTS_19 Paper by Nasri et al. generates ECRTS_19 periods. The Default option selects period according to P = Ci/Ti.\n\
						LOG_UNIFORM generates period log-uniformly between [MIN_PERIOD, MAX_PERIOD].\n\
						where Utilization and WCET per node is generated first.')

	parser.add_argument('-T', '--period_conditioning', dest='period_conditioning', default='NA', 
						action='store', type=str, metavar="PERIOD",
						required=False,
						help='Choose Y or y to apply this condition to period: Period = MAX{C/U,C} where C=Sum of WCET of all nodes of a task\n\
						and U=utilization of that task. This condition will be applied before scaling the periods to avoid long HyperPeriods,\n\
						so that scaling is done properly.')

	parser.add_argument('-n', '--nfj-dag', dest='nfj_dag', default='n', 
						action='store', type=str, metavar="NFJ-DAG",
						required=False,
						help='Choose F to not remove redundant edges, Choose R to remove redundant edges without removing conflicting edges on critical path.')

	parser.add_argument('-u', '--utilization_method', dest='util_method', default='UUF', 
						action='store', type=str, metavar="UTILIZATION_METHOD",
						required=False,
						help='Specify Utilization Generation Method: UUF (UUnifast) or UUFD (UUnifastDiscard) (Warning: UUFD may take long time)\
						or UUF_UUFD for generating workloads for both methods.')

	parser.add_argument('-cf', '--check_feasibility', dest='feasibility_check', default='NA', 
						action='store', type=str, metavar="ANALYSIS",
						required=False,
						help='Options: Heterogeneous - Homogeneous - Heterogeneous_Save - Homogeneous_Save .\n\
						Homogeneous_Save_Isolate - Heterogeneous_Save_Isolate - Homogeneous_Create_Feasible - Heterogeneous_Create_Feasible\n\
						Heterogeneous_Save and Homogeneous_Save options will keep the job sets even if task sets are not feasible\n\
						Heterogeneous_Save_Isolate and Homogeneous_Save_Isolate options will save the not feasible job sets in separate directory\n\
						with NOT_FEASIBLE tag. If Homogeneous_Create_Feasible or Heterogeneous_Create_Feasible are chosen then feasible tasksets are created.')

	parser.add_argument('-np', '--schedulability_analysis', dest='nptest', default='NA', 
						action='store', type=str, metavar="np_schedulability_analysis",
						required=False,
						help='Specify path to schedulability_analysis framework binary, It only works if -cf option is used')

	parser.add_argument('-c', '--threads', dest='threads', default='1', 
						action='store', type=str, metavar="NR_OF_THREADS",
						required=False,
						help='Specify number of threads to run schedulability_analysis framework, works only if -np option is used')

	parser.add_argument('-rsc', '--all-resource-usage', dest='rsc', action='store_const', 
						const=True, required=False,
			            help='This option forces to generate DAGs with nodes of all specified resource types')

	parser.add_argument('-sb', '--force-more-branches', dest='sibl', action='store_const', 
						const=True, required=False,
			            help='This option forces to generate DAGs with higher probability of parallel sub-branches in it')

	parser.add_argument('-nnfj', '--non-nested-fork-join', dest='nnfj', action='store_const', 
						const=True, required=False,
			            help='This option Generates non-nested-fork-join DAGs.')

	parser.add_argument('Settings', metavar = 'TASKS_SETTINGS_FILE', help='Creating Tasks to these param')

	return parser.parse_args()

def SortNodes(Nodes):
	Nodes.sort(key = lambda x:x.JID)

def newNode(TaskNr, NodeNr, Pred, ExcludePredResource = False):
	Node = NodeInfo()
	Node.TID = TaskNr 
	Node.JID = NodeNr

	if JITTER_TYPE == "FIXED":
		Node.r_min = RELEASE_JITTER_R_Min
		Node.r_max = RELEASE_JITTER_R_Max
	elif JITTER_TYPE == "VARIABLE":
		Node.r_min = RELEASE_JITTER_R_Min
		Node.r_max = getRandomInteger(RELEASE_JITTER_R_Min, RELEASE_JITTER_R_Max) 
	else:
		Node.r_min = 0
		Node.r_max = 0

	if (PERIOD_ASSIGNMENT == "Default") or (PERIOD_ASSIGNMENT == "ECRTS_19"):
		if NodeNr != -1:
			Node.WCET = getUniform(1, MAX_NODE_WCET)
		else:
			Node.WCET = getUniform(1, (MAX_NODE_WCET * EXEC_TIME_VARIATION))

		Node.BCET = math.ceil(Node.WCET * EXEC_TIME_VARIATION)

		if Node.BCET > Node.WCET:
			Node.BCET = Node.WCET
	
	if Pred >= 0:
		Node.Pred.append(Pred)
	if (SELF_SUSPENDING == False) or (NodeNr == -1):
		if (RSC_ASSIGNMENT_BY_PROBABILITY == False) or (NON_NESTED_FORK_JOIN == True):
			Node.ResourceType = getRandomResourceAssignment(SelfSuspending = False)
		else:
			Node.ResourceType = getResourceAssignmentbyProbability(SelfSuspending = False)
	else:
		if (RSC_ASSIGNMENT_BY_PROBABILITY == False) or (NON_NESTED_FORK_JOIN == True):
			Node.ResourceType = getRandomResourceAssignment(SelfSuspending = True)
		else:
			Node.ResourceType = getResourceAssignmentbyProbability(SelfSuspending = True)

	return Node

def addLegendtoGraph(fp, CriticalPaths_WCET):

	if CriticalPaths_WCET > 0:
		LStr = "label = "+"\""+"I`M LEGEND CRP-WCET:"+str(CriticalPaths_WCET)+"\""+";\n"
	else:
		LStr = "label = "+"\""+"I`M LEGEND"+"\""+";\n"

	header = 'rankdir=LR\n' \
			  'node [shape=plaintext]\n' \
			  'subgraph cluster_01 {\n' + LStr + 'key [label=<<table border="0" cellpadding="0" cellspacing="0" cellborder="0">\n' 

	fp.write("%s"%(header)) 

	for n in range(0, RESOURCE_TYPES+1):
		fp.write('<tr><td align="right" port="i%d">RSC:%d </td></tr>\n'%(n, n))
	fp.write('<tr><td align="right" port="i%d">CRP:%d </td></tr>\n'%(RESOURCE_TYPES+1, RESOURCE_TYPES+1))

	fp.write("</table>>]\n" \
			 'key2 [label=<<table border="0" cellpadding="0" cellspacing="0" cellborder="0">\n'
			)

	for n in range(0, RESOURCE_TYPES+1):
		fp.write('<tr><td port="i%d">&nbsp;</td></tr>\n'%(n))
	fp.write('<tr><td port="i%d">&nbsp;</td></tr>\n'%(RESOURCE_TYPES+1))

	fp.write("</table>>]\n")

	for n in range(0, RESOURCE_TYPES+1):
		lvColor = getColor(n)
		fp.write('key:i%d:e -> key2:i%d:w [color=%s]\n'%(n,n,lvColor))
	if WANT_CRITICAL_PATH_JOBS == True:
		lvColor = getColor(LONGEST_JOB_PATH_COLOR)
		fp.write('key:i%d:e -> key2:i%d:w [color=%s]\n'%(RESOURCE_TYPES+1,RESOURCE_TYPES+1,lvColor))
	elif WANT_CRITICAL_PATH_WCET == True:
		lvColor = getColor(LONGEST_WCET_PATH_COLOR)
		fp.write('key:i%d:e -> key2:i%d:w [color=%s]\n'%(RESOURCE_TYPES+1,RESOURCE_TYPES+1,lvColor))

	fp.write("}\n")

def createTaskGraphFile(Nodes, TaskNr, CriticalPaths, CriticalPaths_WCET, FileName):
	# Creating Nodes File

	if len(Nodes) < 1:
		if DEBUG == 'e':
			print("Failed for creating Graph file due to len(Nodes) < 1")
		return

	lvFileName = FileName.split('.')
	lvstr = lvFileName[0]+"_"+str(TaskNr)+".dot"
	fp = open(lvstr, "w")
	
	fp.write("digraph testing {\n")

	for n in range(0, len(Nodes)):
		nodecolor = getColor(Nodes[n].ResourceType) 
		fontsize = str(10)
		fontcolor = "black"
		JobInfo = "\""+"J"+str(Nodes[n].JID)+" RSC:"+str(Nodes[n].ResourceType)+"\nBCET:"+str(Nodes[n].BCET)+"\nWCET:"+str(Nodes[n].WCET)+"\nDL:"+str(Nodes[n].Length)+"\""
		Label = "[label="+JobInfo+", color="+nodecolor+", fontcolor="+fontcolor+", fontsize="+fontsize+"]"
		fp.write("\tJ%d%s\n"%(Nodes[n].JID, Label))

	fp.write("subgraph Main {\n")

	for n in range(0, len(Nodes)):
		for m in range(0, len(Nodes[n].Pred)):
			if Nodes[n].Pred[m] >= 0:
				fp.write("\tJ%d -> J%d\n"%(Nodes[n].Pred[m], Nodes[n].JID))
	fp.write("}\n")

	if WANT_CRITICAL_PATH_JOBS == True:
		for m in range(0, len(CriticalPaths)):
			fp.write("subgraph CriticalPath_%d {\n"%(m))
	#       print(".*.*.*.*.* Critical Path %d NrNodes:%d WCET:%d .*.*.*.*.*"%(m+1, len(CriticalPaths[m])-1, CriticalPaths[m][len(CriticalPaths[m]) - 1]))
			Edgecolor = getColor(LONGEST_JOB_PATH_COLOR)
			EdgeInfo = "\""+""+"\""
			EdgeLabel = "[label="+EdgeInfo+"color="+Edgecolor+", fontcolor="+Edgecolor+", fontsize="+fontsize+"]"
			for n in range(0, len(CriticalPaths[m])):
				if (CriticalPaths[m][n].JID == 0):
					break 
				elif CriticalPaths[m][n].JID != 0:
					# print("J%d -> J%d"%(CriticalPaths[m][n].JID, CriticalPaths[m][n+1].JID))  
					fp.write("\tJ%d -> J%d %s\n"%(CriticalPaths[m][n+1].JID, CriticalPaths[m][n].JID, EdgeLabel))
			fp.write("}\n")
	
	elif WANT_CRITICAL_PATH_WCET == True:
		for m in range(0, len(CriticalPaths)):
			fp.write("subgraph CriticalPath_%d {\n"%(m))
			# print(".*.*.*.*.* Critical Path %d NrNodes:%d TerminalNode:J%d .*.*.*.*.*"%(m+1, len(CriticalPaths[m])-1, CriticalPaths[m][len(CriticalPaths[m]) - 1].JID))
			Edgecolor = getColor(LONGEST_WCET_PATH_COLOR)
			EdgeInfo = "\""+""+"\""
			EdgeLabel = "[label="+EdgeInfo+"color="+Edgecolor+", fontcolor="+Edgecolor+", fontsize="+fontsize+"]"
			for n in range(0, len(CriticalPaths[m])):
				if (CriticalPaths[m][n].JID == CriticalPaths[m][len(CriticalPaths[m]) - 1].JID):
					break 
				elif CriticalPaths[m][n].JID != CriticalPaths[m][len(CriticalPaths[m]) - 1].JID:
					# print("J%d -> J%d"%(CriticalPaths[m][n].JID, CriticalPaths[m][n+1].JID))  
					fp.write("\tJ%d -> J%d %s\n"%(CriticalPaths[m][n].JID, CriticalPaths[m][n+1].JID, EdgeLabel))
			fp.write("}\n")
	
	addLegendtoGraph(fp, CriticalPaths_WCET)

	fp.write("}")

	fp.close()

	#Convert dot file to Graph File
	lvpng = lvstr.split('.')
	lvCMD = "dot -Tpng "+lvstr+" -o "+lvpng[0]+".png"
	res = run_command(lvCMD)
	lvCMD = "rm "+lvstr
	res = run_command(lvCMD)

def getSelectedChildNodes(ChildSiblings, Nodes):
	SelectedNodes = []
	if len(ChildSiblings) > 0:
		SelectedNodes.append(Nodes[ChildSiblings[0]])        
		if len(ChildSiblings) > 1:
			for n in range(1, len(ChildSiblings)):
				if SelectedNodes[0].WCET < Nodes[ChildSiblings[n]].WCET:
					SelectedNodes.clear()
					SelectedNodes.append(Nodes[ChildSiblings[n]])
				else:
					SelectedNodes.append(Nodes[ChildSiblings[n]])
		else:
			return SelectedNodes

	return SelectedNodes

def getAllPaths(Nodes, InputNode, outAllPaths, AllPaths):
	AllPaths.append(InputNode)
	if len(InputNode.Succ) > 0:
		for m in range(0, len(InputNode.Succ)):
			getAllPaths(Nodes, Nodes[InputNode.Succ[m]], outAllPaths, AllPaths)
			for n in range(0, len(AllPaths)):                
				if AllPaths[n].JID == Nodes[InputNode.Succ[m]].JID:
					del AllPaths[n:]                        
					break
	else:
		Skip = True
		for n in range(0, len(AllPaths) - 1):            
			Skip = True
			for m in range(0, len(AllPaths[n].Succ)):
				if (AllPaths[n].Succ[m] == AllPaths[n+1].JID):# and (AllPaths[n].JID != Nodes[len(Nodes) - 1].JID):
					Skip = False
					break
		if Skip == False:
			# for p in range(0, len(AllPaths)):
			#     print("Node:%d"%(AllPaths[p].JID))
			# print("------------------")
			newPath = AllPaths.copy()
			outAllPaths.append(newPath)
		# else:
		#     print("Path is incomplete")

def getCriticalPaths_wrt_WCET(inAllPaths):
	WCET = 0
	CriticalPaths = []

	WCET_SUM = 0
	
	for n in range(0, len(inAllPaths[0])):
		WCET_SUM += inAllPaths[0][n].WCET
	WCET = WCET_SUM
	CriticalPaths.append(inAllPaths[0])    
	WCET_SUM = 0

	for n in range(1, len(inAllPaths)):
		for m in range(0, len(inAllPaths[n])):
			WCET_SUM += inAllPaths[n][m].WCET
			# print("Node:%d = %d"%(inAllPaths[n][m].JID, WCET))
		if (WCET < WCET_SUM):
			WCET = WCET_SUM
			CriticalPaths.clear()
			CriticalPaths.append(inAllPaths[n])
			WCET_SUM = 0
		elif (WCET == WCET_SUM):
			CriticalPaths.append(inAllPaths[n])            
			WCET_SUM = 0
		else:
			WCET_SUM = 0
		# print("-------WCET:%d---------"%WCET)

	return CriticalPaths, WCET

			  
def getCriticalPathInfo(TaskNodes):
	outAllPaths = []
	AllPaths = []
	CriticalPaths = []

	getAllPaths(TaskNodes, TaskNodes[0], outAllPaths, AllPaths)
	CriticalPaths, CriticalPaths_WCET = getCriticalPaths_wrt_WCET(outAllPaths)

	return CriticalPaths, CriticalPaths_WCET

def getAllLongestJobPathsWithBranches(Nodes, TerminalNode, Length, inPutNodes):
	LongestPathNodes = []
	lvLongestNodes = []
	Max_Length = Length - 1
	Found = False
	
	for n in range(0, len(TerminalNode.Pred)):
		if Max_Length == Nodes[TerminalNode.Pred[n]].Length:
			Found = True

			for m in range(0, len(inPutNodes)):
				LongestPathNodes.append(inPutNodes[m])

			LongestPathNodes.append(Nodes[TerminalNode.Pred[n]])

			if Max_Length >= 1:
				lvLongestNodes = getAllLongestJobPathsWithBranches(Nodes, Nodes[TerminalNode.Pred[n]], Max_Length, LongestPathNodes)
				if len(lvLongestNodes) >= 1:
					for m in range(0, len(lvLongestNodes)):
						LongestPathNodes.append(lvLongestNodes[m])
				else:
					LongestPathNodes.remove(Nodes[TerminalNode.Pred[n]])

	if Found == True:
		return LongestPathNodes
	else:
		DummyNodes = []
		return DummyNodes

def getLongestJobPaths(Nodes, TerminalNode):
	ListsOfLongestPaths = []
	nNodes = []
	nNodes.append(TerminalNode)

	AllLongestPathNodes = getAllLongestJobPathsWithBranches(Nodes, TerminalNode, TerminalNode.Length, nNodes)
	
	PrevID = AllLongestPathNodes[0].JID
	CurrID = PrevID
	listsCounter = 0
	OneLongestPath = [AllLongestPathNodes[0]]
	OneLongestPath.append(AllLongestPathNodes[0])

	for n in range(1, len(AllLongestPathNodes)):
		CurrID = AllLongestPathNodes[n].JID
		if (PrevID != 0) and (CurrID == TerminalNode.JID):
			OneLongestPath.clear()
			OneLongestPath.append(TerminalNode)
			PrevID = CurrID
		elif (PrevID != 0) and (CurrID == 0):
			OneLongestPath.append(AllLongestPathNodes[n])

			Skip = False
			NrOfElementsToCompare = len(OneLongestPath)

			lvMatchedCounter = 0
			for m in range(0, len(ListsOfLongestPaths)):
				for l in range(0, len(ListsOfLongestPaths[m])):
					if OneLongestPath[l].JID == ListsOfLongestPaths[m][l].JID:
						lvMatchedCounter += 1
				if lvMatchedCounter == NrOfElementsToCompare:
					Skip = True
					break
				else:
					lvMatchedCounter = 0
			
			if Skip == False:
				lvList = []
				for m in range(0, len(OneLongestPath)):
					lvList.append(OneLongestPath[m])
				ListsOfLongestPaths.append(lvList)
				listsCounter += 1
			 
			OneLongestPath.clear()
			PrevID = CurrID
		else:
			OneLongestPath.append(AllLongestPathNodes[n])
			PrevID = CurrID

	if (PrevID != 0) and (CurrID == 0):
		
		NrOfElementsToCompare = len(OneLongestPath)

		lvMatchedCounter = 0
		Skip = False

		for m in range(0, len(ListsOfLongestPaths)):
			for l in range(0, len(ListsOfLongestPaths[m])):
				if OneLongestPath[l].JID == ListsOfLongestPaths[m][l].JID:
					lvMatchedCounter += 1
			if lvMatchedCounter == NrOfElementsToCompare:
				Skip = True
				break
			else:
				lvMatchedCounter = 0
		
		if Skip == False:
			lvList = []
			for m in range(0, len(OneLongestPath)):
				lvList.append(OneLongestPath[m])
			ListsOfLongestPaths.append(lvList)
			listsCounter += 1 

	return ListsOfLongestPaths

def getCriticalPaths_wrt_Jobs(AllLongestPaths):

	MAX_WCET_CRITICAL_PATH = 0
	CriticalPaths = []
	for n in range(0, len(AllLongestPaths)):

		lvMaxWCETCriticalPath = 0
		LongestPathNodes = []

		for m in range(0, len(AllLongestPaths[n])):

			lvMaxWCETCriticalPath += AllLongestPaths[n][m].WCET
			LongestPathNodes.append(AllLongestPaths[n][m])

		if MAX_WCET_CRITICAL_PATH < lvMaxWCETCriticalPath:

			MAX_WCET_CRITICAL_PATH = lvMaxWCETCriticalPath
			CriticalPaths.clear()
			LongestPathNodes.append(lvMaxWCETCriticalPath)
			CriticalPaths.append(LongestPathNodes)

		elif MAX_WCET_CRITICAL_PATH == lvMaxWCETCriticalPath:

			LongestPathNodes.append(lvMaxWCETCriticalPath)
			CriticalPaths.append(LongestPathNodes)

	return CriticalPaths, MAX_WCET_CRITICAL_PATH

def updateLengths(Nodes, NodeID, Successors, Length):
	size_l = len(Successors)
	if size_l > 1:
		for n in range(0, size_l):
			if (Successors[n] != -1) and (NodeID != Nodes[Successors[n]].JID):            
				updateLengths(Nodes, Nodes[Successors[n]].JID, Nodes[Successors[n]].Succ, Length+1)
				if (Length + 1) >= Nodes[Successors[n]].Length:
					Nodes[Successors[n]].Length = Length + 1
	elif (size_l == 1) and (NodeID != Nodes[Successors[0]].JID):
		if Successors[0] != -1:
			updateLengths(Nodes, Nodes[Successors[0]].JID, Nodes[Successors[0]].Succ, Length+1)
			if (Length + 1) >= Nodes[Successors[0]].Length:
				Nodes[Successors[0]].Length = Length + 1

def expandSeriesParallelNNFJDAG(NodeCounter, Nodes, TaskNr, RootNode, TermNode, Depth, TaskNodesCreated = 2):
	lvNodeCounter = NodeCounter
	NodesCreated = TaskNodesCreated

	if (RootNode.Length >= MAX_LENGTH) or ((len(Nodes)+1) >= MAX_NODES) or (Depth >= MAX_RECURSION_DEPTH):
		TermNode.Pred.append(RootNode.JID)
		RootNode.Succ.append(TermNode.JID)
		return NodeCounter

	siblings = getSiblingsCount(NodesCreated)

	if siblings == 0:
		TermNode.Pred.append(RootNode.JID)
		RootNode.Succ.append(TermNode.JID)

	NodesCreated += siblings
	
	sibling_indices = []
	JoiningNodes = []
	
	# New Joining Node Here
	lvJoiningNode = newNode(TaskNr, -1, -1)

	if WANT_HETEROGENEOUS == True:
		lvJoiningNode.ResourceType = 1

	lvSelfSuspendingFound = False

	AssignedResources = []

	for n in range(0, siblings):
		sNode = newNode(TaskNr, lvNodeCounter, RootNode.JID)
		sNode.Length = RootNode.Length + 1
		RootNode.Succ.append(sNode.JID)
		sibling_indices.append(sNode.JID)
		Nodes.append(sNode)
		lvNodeCounter += 1

		if WANT_HETEROGENEOUS == True:
			if sNode.ResourceType in AssignedResources:
				sNode.ResourceType = 1
			elif sNode.ResourceType != 1:
				AssignedResources.append(sNode.ResourceType)

		if SELF_SUSPENDING == True: # Check if one sibling is already self suspending
			if (sNode.ResourceType == SS_RSC) and (lvSelfSuspendingFound == False): #if not Found first SS
				lvSelfSuspendingFound = True
			elif (sNode.ResourceType == SS_RSC) and (lvSelfSuspendingFound == True): #if Yes, ReAssign Resource
				if RSC_ASSIGNMENT_BY_PROBABILITY == False:
					sNode.ResourceType = getRandomResourceAssignment(SelfSuspending = False)
				else:
					sNode.ResourceType = getResourceAssignmentbyProbability(SelfSuspending = False)

		Result = isTerminalNodeOrParallelSubGraph()

		if (Result == IS_TERMINAL) and (sNode.ResourceType != SS_RSC) and (lvNodeCounter >= MIN_NODES):
			TermNode.Pred.append(sNode.JID)
			sNode.Succ.append(TermNode.JID)
		else:
			lvJoiningNode.Pred.append(sNode.JID)
			sNode.Succ.append(lvJoiningNode.JID)
						
	if len(lvJoiningNode.Pred) >= 1:
		Max_Length = 0
		for n in range(0, len(lvJoiningNode.Pred)):
			if Max_Length <= Nodes[lvJoiningNode.Pred[n]].Length:
				Max_Length = Nodes[lvJoiningNode.Pred[n]].Length

		lvJoiningNode.JID = lvNodeCounter
		lvNodeCounter += 1
		lvJoiningNode.Length = Max_Length + 1

		# Update all the predecessors of lvJoiningNode with new lvJoiningNode ID
		for n in range(0, len(lvJoiningNode.Pred)):
			for m in range(0, len(Nodes[lvJoiningNode.Pred[n]].Succ)):
				if Nodes[lvJoiningNode.Pred[n]].Succ[m] == -1:
					Nodes[lvJoiningNode.Pred[n]].Succ[m] = lvJoiningNode.JID

		Nodes.append(lvJoiningNode)

	# Adding Random Edges between siblings here
	for n in range(0, len(sibling_indices)):
		for m in range(n+1, len(sibling_indices)):
			AddEdge = ShouldAddEdge()
			if AddEdge == True:
				if Nodes[sibling_indices[n]].ResourceType != SS_RSC: # No random edges between self suspending nodes
					Nodes[sibling_indices[m]].Pred.append(Nodes[sibling_indices[n]].JID)
					Nodes[sibling_indices[n]].Succ.append(Nodes[sibling_indices[m]].JID)
					if Nodes[sibling_indices[m]].Length <= Nodes[sibling_indices[n]].Length:
						Nodes[sibling_indices[m]].Length = Nodes[sibling_indices[n]].Length + 1
						updateLengths(Nodes, Nodes[sibling_indices[m]].JID, Nodes[sibling_indices[m]].Succ, Nodes[sibling_indices[m]].Length)

					while True: 
						try:
							TermNode.Pred.remove(Nodes[sibling_indices[n]].JID)
							Nodes[sibling_indices[n]].Succ.remove(TermNode.JID)
						except ValueError:
							break

	if len(lvJoiningNode.Pred) >= 1:
		lvNodeCounter = expandSeriesParallelNNFJDAG(lvNodeCounter, Nodes, TaskNr, lvJoiningNode, TermNode, Depth+1, NodesCreated)

	return lvNodeCounter

def expandSeriesParallelNestedFJDAG(NodeCounter, Nodes, TaskNr, RootNode, JoiningNode, TermNode, Depth, TaskNodesCreated = 2):
	lvNodeCounter = NodeCounter
	NodesCreated = TaskNodesCreated

	if (RootNode.Length >= MAX_LENGTH) or ((len(Nodes)+1) >= MAX_NODES):
		TermNode.Pred.append(RootNode.JID)
		RootNode.Succ.append(TermNode.JID)
		return NodeCounter
	elif (Depth >= MAX_RECURSION_DEPTH):
		JoiningNode.Pred.append(RootNode.JID)
		RootNode.Succ.append(JoiningNode.JID)
		if JoiningNode.Length <= RootNode.Length:
			JoiningNode.Length = RootNode.Length + 1
		return NodeCounter

	siblings = getSiblingsCount(NodesCreated)

	if siblings == 0:
		TermNode.Pred.append(RootNode.JID)
		RootNode.Succ.append(TermNode.JID)

	NodesCreated += siblings
	
	sibling_indices = []
	JoiningNodes = []
	
	# New Joining Node Here
	lvJoiningNode = newNode(TaskNr, -1, -1)

	if WANT_HETEROGENEOUS == True:
		lvJoiningNode.ResourceType = 1

	lvSelfSuspendingFound = False

	for n in range(0, siblings):
		sNode = newNode(TaskNr, lvNodeCounter, RootNode.JID)
		sNode.Length = RootNode.Length + 1
		RootNode.Succ.append(sNode.JID)
		sibling_indices.append(sNode.JID)
		Nodes.append(sNode)
		lvNodeCounter += 1
		
		if SELF_SUSPENDING == True: # Check if one sibling is already self suspending
			if (sNode.ResourceType == SS_RSC) and (lvSelfSuspendingFound == False): #if not Found first SS
				lvSelfSuspendingFound = True
			elif (sNode.ResourceType == SS_RSC) and (lvSelfSuspendingFound == True): #if Yes, ReAssign Resource
				if RSC_ASSIGNMENT_BY_PROBABILITY == False:
					sNode.ResourceType = getRandomResourceAssignment(SelfSuspending = False)
				else:
					sNode.ResourceType = getResourceAssignmentbyProbability(SelfSuspending = False)

		Result = isTerminalNodeOrParallelSubGraph()

		if (Result == IS_TERMINAL) and (sNode.ResourceType != SS_RSC) and (lvNodeCounter >= MIN_NODES):
			TermNode.Pred.append(sNode.JID)
			sNode.Succ.append(TermNode.JID)
		else:
			if WANT_HETEROGENEOUS == True:
				if sNode.ResourceType == 1:
					lvNodeCounter = expandSeriesParallelNestedFJDAG(lvNodeCounter, Nodes, TaskNr, sNode, lvJoiningNode, TermNode, Depth+1, NodesCreated)
				else:
					lvJoiningNode.Pred.append(sNode.JID)
					sNode.Succ.append(lvJoiningNode.JID)
					if lvJoiningNode.Length <= sNode.Length:
						lvJoiningNode.Length = sNode.Length + 1
			else:
				if sNode.ResourceType == SS_RSC:
					lvJoiningNode.Pred.append(sNode.JID)
					sNode.Succ.append(lvJoiningNode.JID)
					if lvJoiningNode.Length <= sNode.Length:
						lvJoiningNode.Length = sNode.Length + 1                    
				else:
					lvNodeCounter = expandSeriesParallelNestedFJDAG(lvNodeCounter, Nodes, TaskNr, sNode, lvJoiningNode, TermNode, Depth+1, NodesCreated)
						

	if len(lvJoiningNode.Pred) >= 1:
		Max_Length = 0
		for n in range(0, len(lvJoiningNode.Pred)):
			if Max_Length <= Nodes[lvJoiningNode.Pred[n]].Length:
				Max_Length = Nodes[lvJoiningNode.Pred[n]].Length

		lvJoiningNode.JID = lvNodeCounter
		lvNodeCounter += 1
		lvJoiningNode.Length = Max_Length + 1
		
		JoiningNode.Pred.append(lvJoiningNode.JID)
		lvJoiningNode.Succ.append(JoiningNode.JID)
		if JoiningNode.Length <= lvJoiningNode.Length:
			JoiningNode.Length = lvJoiningNode.Length + 1

		# Update all the predecessors of lvJoiningNode with new lvJoiningNode ID
		for n in range(0, len(lvJoiningNode.Pred)):
			for m in range(0, len(Nodes[lvJoiningNode.Pred[n]].Succ)):
				if Nodes[lvJoiningNode.Pred[n]].Succ[m] == -1:
					Nodes[lvJoiningNode.Pred[n]].Succ[m] = lvJoiningNode.JID

		Nodes.append(lvJoiningNode)

	# Adding Random Edges between siblings here
	for n in range(0, len(sibling_indices)):
		for m in range(n+1, len(sibling_indices)):
			AddEdge = ShouldAddEdge()
			if AddEdge == True:
				if Nodes[sibling_indices[n]].ResourceType != SS_RSC: # No random edges between self suspending nodes
					Nodes[sibling_indices[m]].Pred.append(Nodes[sibling_indices[n]].JID)
					Nodes[sibling_indices[n]].Succ.append(Nodes[sibling_indices[m]].JID)
					if Nodes[sibling_indices[m]].Length <= Nodes[sibling_indices[n]].Length:
						Nodes[sibling_indices[m]].Length = Nodes[sibling_indices[n]].Length + 1
						updateLengths(Nodes, Nodes[sibling_indices[m]].JID, Nodes[sibling_indices[m]].Succ, Nodes[sibling_indices[m]].Length)

					while True: 
						try:
							TermNode.Pred.remove(Nodes[sibling_indices[n]].JID)
							Nodes[sibling_indices[n]].Succ.remove(TermNode.JID)
						except ValueError:
							break

	return lvNodeCounter

def Generate_DAG_Task(TaskNr, FileName):
	Nodes = []
	while((len(Nodes) < MIN_NODES)):

		NodeCounter = 0

		RootNode = newNode(TaskNr, NodeCounter, -1)
		RootNode.ResourceType = 1
		RootNode.Length = 0
		RootNode.Deadline = 0

		if JITTER_TYPE == "WITH_PRECEDENCE":
			RootNode.r_min = RELEASE_JITTER_R_Min
			RootNode.r_max = RELEASE_JITTER_R_Max

		Nodes.append(RootNode)
		
		NodeCounter += 1 

		if MAX_NODES > 1:
			
			Result = isTerminalNode()

			TermNode = newNode(TaskNr, -1, -1)

			if NON_NESTED_FORK_JOIN == True:
				NodeCounter = expandSeriesParallelNNFJDAG(NodeCounter, Nodes, TaskNr, RootNode, TermNode, 1)
			else:
				NodeCounter = expandSeriesParallelNestedFJDAG(NodeCounter, Nodes, TaskNr, RootNode, TermNode, TermNode, 1)

			TermNode.JID = NodeCounter
			TermNode.ResourceType = 1

			# Update all the predecessors of TermNode with new TermNode ID
			for n in range(0, len(TermNode.Pred)):
				for m in range(0, len(Nodes[TermNode.Pred[n]].Succ)):
					if Nodes[TermNode.Pred[n]].Succ[m] == -1:
						Nodes[TermNode.Pred[n]].Succ[m] = TermNode.JID

			Max_Length = 0
			for n in range(0, len(TermNode.Pred)):
				if Max_Length <= Nodes[TermNode.Pred[n]].Length:
					Max_Length = Nodes[TermNode.Pred[n]].Length

			TermNode.Length = Max_Length + 1
			Nodes.append(TermNode)

			RSC_Types_Used = getUsedRSCTypes(Nodes)

		if (WANT_ALL_RSC_TYPE_NODES == True) and (len(RSC_Types_Used) < RESOURCE_TYPES):
			Nodes.clear()
		
	return Nodes

def Vertex_in_List(vertex, List):
	for n in range(0, len(List)):
		if vertex.JID == List[n].JID:
			return True
	return False

def UpdateParallelVertices_of_EachVertex(TaskInfo, AllPaths):
	for vertex in range(0, len(TaskInfo)):
		TaskInfo[vertex].Par_v.clear()
		CommonPaths = []
		UncommonPaths = []

		for path in range(0, len(AllPaths)):
			if (Vertex_in_List(TaskInfo[vertex], AllPaths[path]) == False):
				UncommonPaths.append(AllPaths[path])
			else:
				CommonPaths.append(AllPaths[path])

		for uPath in range(0, len(UncommonPaths)):
			for uVertex in range(0, len(UncommonPaths[uPath])):
				if (UncommonPaths[uPath][uVertex].ResourceType == TaskInfo[vertex].ResourceType):
					SkipVertex = False
					for cPath in range(0, len(CommonPaths)):
						for cVertex in range(0, len(CommonPaths[cPath])):
							if ((UncommonPaths[uPath][uVertex].JID == CommonPaths[cPath][cVertex].JID) == True):
								SkipVertex = True
								break
						if SkipVertex == True:
							break
					if SkipVertex == False:
						if (Vertex_in_List(UncommonPaths[uPath][uVertex], TaskInfo[vertex].Par_v) == False):
							TaskInfo[vertex].Par_v.append(UncommonPaths[uPath][uVertex])
		
		CommonPaths.clear()
		UncommonPaths.clear()   
		TaskInfo[vertex].Par_v.sort(key=lambda v:v.JID)

def UpdateDescendants_of_EachVertex(TaskInfo, AllPaths):
	for vertex in range(0, len(TaskInfo)):   
		TaskInfo[vertex].Desc.clear()
		CommonPaths = []
		for path in range(0, len(AllPaths)):
			if (Vertex_in_List(TaskInfo[vertex], AllPaths[path]) == True):
				CommonPaths.append(AllPaths[path])
						
		for path in range(0, len(CommonPaths)):     
			for uVertex in range(0, len(CommonPaths[path])):
				if CommonPaths[path][uVertex].JID > TaskInfo[vertex].JID:
					if (Vertex_in_List(CommonPaths[path][uVertex], TaskInfo[vertex].Desc) == False):
						TaskInfo[vertex].Desc.append(CommonPaths[path][uVertex])
		CommonPaths.clear()
		TaskInfo[vertex].Desc.sort(key=lambda v:v.JID)

def UpdateAncestors_of_EachVertex(TaskInfo, AllPaths):
	for vertex in range(0, len(TaskInfo)):    
		TaskInfo[vertex].Ancs.clear()
		CommonPaths = []
		for path in range(0, len(AllPaths)):
			if (Vertex_in_List(TaskInfo[vertex], AllPaths[path]) == True):
				CommonPaths.append(AllPaths[path])
						
		for path in range(0, len(CommonPaths)):     
			for uVertex in range(0, len(CommonPaths[path])):
				if CommonPaths[path][uVertex].JID < TaskInfo[vertex].JID:
					if (Vertex_in_List(CommonPaths[path][uVertex], TaskInfo[vertex].Ancs) == False):
						TaskInfo[vertex].Ancs.append(CommonPaths[path][uVertex])
		CommonPaths.clear()
		TaskInfo[vertex].Ancs.sort(key=lambda v:v.JID)

def getUtilizationUUnifastDiscard(Tasks, Utilization):
	UtilizationCondition = False
	UtilizationPerTaskList = []
	Hard_Condition = 0.0

	if ((Utilization/Tasks)*100) > UTILIZATION_TOLERANCE_PERCENTAGE:
		Hard_Condition = math.ceil(Utilization/Tasks) + (math.ceil(Utilization/Tasks)*UTILIZATION_TOLERANCE)
	else:
		Hard_Condition = math.ceil(Utilization/Tasks)

	Tries = 0

	while UtilizationCondition == False:
		UtilizationPerTaskList.clear()
		Tries += 1

		if Tries > DEFAULT_TASK_UUFD_TRIES:
			break

		UtilizationPerTaskList = UUniFast(Tasks, Utilization)       

		for n in range(0, len(UtilizationPerTaskList)):
			if UtilizationPerTaskList[n] > Hard_Condition:
				UtilizationCondition = False
				if DEBUG == 'e':
					print("Failed for Generated Utilizations Due to Task:%d Utilization:%f > %f (UUFD)"\
						%(n+1, UtilizationPerTaskList[n], Hard_Condition))
				break
			else:
				UtilizationCondition = True

	return UtilizationPerTaskList

def getUtilizationUUnifast(Tasks, Utilization):
	return UUniFast(Tasks, Utilization)

def CreateGraphFile(TaskNr, TaskInfo, outAllPaths, FileName):
	AllLongestPaths =[]
	CriticalPaths =[]
	CriticalPaths_WCET  =   0
	
	if len(TaskInfo) >= MIN_NODES:

		if WANT_CRITICAL_PATH_JOBS and (MAX_NODES > 1):
			AllLongestPaths = getLongestJobPaths(TaskInfo, TaskInfo[len(TaskInfo) - 1])
			CriticalPaths, CriticalPaths_WCET = getCriticalPaths_wrt_Jobs(AllLongestPaths)
		elif WANT_CRITICAL_PATH_WCET and (MAX_NODES > 1):                    
			CriticalPaths, CriticalPaths_WCET = getCriticalPaths_wrt_WCET(outAllPaths)

		# print("Task%d --> NodeCount:%d Length:%d TerminalNodes:%d"%(n+1, len(TaskSetList[n]), TaskSetList[n][len(TaskSetList[n]) - 1].Length, len(TaskSetList[n][len(TaskSetList[n]) - 1].Pred)))
		
		createTaskGraphFile(TaskInfo, TaskNr+1, CriticalPaths, CriticalPaths_WCET, FileName)

	return CriticalPaths

def EdgeExists_in_Paths(CriticalPaths, Pred, JobID):
	for m in range(0, len(CriticalPaths)):
		for n in range(0, len(CriticalPaths[m])):
			if (CriticalPaths[m][n].JID == CriticalPaths[m][len(CriticalPaths[m])-1]):
				break 
			else:
				if (CriticalPaths[m][n].JID == Pred) and (CriticalPaths[m][n+1].JID == JobID):
					return True        
	return False

def RemoveConflictingEdge(VTX, Pred, TaskNodes):
	try:
		Pred.Succ.remove(VTX.JID)
		VTX.Pred.remove(Pred.JID)
	except ValueError:
		pass
	# Update Necessary Task Information
	outAllPaths = []
	AllPaths = []
	getAllPaths(TaskNodes, TaskNodes[0], outAllPaths, AllPaths)
	UpdateAncestors_of_EachVertex(TaskNodes, outAllPaths)

def Convert_to_NFJ_DAG(cNodes, CriticalPaths):
	for vertex in range(0, len(cNodes)):
		
		if len(cNodes[vertex].Pred) > 1: 
		   
			PredLen = len(cNodes[vertex].Pred)

			for pred in reversed(range(PredLen)):

				try:
					lvPredVertex = cNodes[cNodes[vertex].Pred[pred]]
				except IndexError:
					continue

				ConflictingEdge = False

				for succ in range(0, len(lvPredVertex.Succ)):
					if (lvPredVertex.Succ[succ] != cNodes[vertex].JID) \
					and (Vertex_in_List(cNodes[lvPredVertex.Succ[succ]], cNodes[vertex].Ancs) == False):
						ConflictingEdge = True
						break

				if (ConflictingEdge == True):
					if CONVERT_TO_NFJ_DAG == RESERVED:
						if EdgeExists_in_Paths(CriticalPaths, lvPredVertex.JID, cNodes[vertex].JID) == False:
							RemoveConflictingEdge(cNodes[vertex], cNodes[cNodes[vertex].Pred[pred]], cNodes)
							PredLen = PredLen - 1
					else:
						RemoveConflictingEdge(cNodes[vertex], cNodes[cNodes[vertex].Pred[pred]], cNodes)
						PredLen = PredLen - 1
				
				if ConflictingEdge == False:
					lvPredLen = len(cNodes[vertex].Pred)
					for p in reversed(range(lvPredLen)):
						if cNodes[vertex].Pred[p] in lvPredVertex.Pred:
							if CONVERT_TO_NFJ_DAG == RESERVED:
								if EdgeExists_in_Paths(CriticalPaths, lvPredVertex.JID, cNodes[vertex].JID) == False:
									RemoveConflictingEdge(cNodes[vertex], cNodes[cNodes[vertex].Pred[p]], cNodes)
									lvPredLen = lvPredLen - 1
									PredLen = PredLen - 1
									if(PredLen == 1):
										break
							else:
								RemoveConflictingEdge(cNodes[vertex], cNodes[cNodes[vertex].Pred[p]], cNodes)
								lvPredLen = lvPredLen - 1
								PredLen = PredLen - 1
								if(PredLen == 1):
									break

				if PredLen > 1:
					for n in reversed(range(PredLen)):
						for vtx in reversed(range(PredLen)):
							if (Vertex_in_List(cNodes[cNodes[vertex].Pred[n]], cNodes[cNodes[vertex].Pred[vtx]].Ancs) == True):
								if CONVERT_TO_NFJ_DAG == RESERVED:
									if EdgeExists_in_Paths(CriticalPaths, lvPredVertex.JID, cNodes[vertex].JID) == False:
										RemoveConflictingEdge(cNodes[vertex], cNodes[cNodes[vertex].Pred[n]], cNodes)
										PredLen = PredLen - 1
										if(PredLen == 1):
											break
								else:
									RemoveConflictingEdge(cNodes[vertex], cNodes[cNodes[vertex].Pred[n]], cNodes)
									PredLen = PredLen - 1
									if(PredLen == 1):
										break

						if(PredLen == 1):
								break 

				if(PredLen == 1):
					break

def remove_task_jobset(JobSetFileName, PredFileName, FileName=""):
	if FileName != "":
		lvCMD = "rm -rf "+FileName
		res = run_command(lvCMD)
	if JobSetFileName != "":
		lvCMD = "rm -rf "+JobSetFileName
		res = run_command(lvCMD)
	if PredFileName != "":
		lvCMD = "rm -rf "+PredFileName
		res = run_command(lvCMD)

def rename_task_jobset(JobSetFileName, PredFileName, NF_subPath, FileName=""):
	lvJobSet = JobSetFileName.split('.')
	lvPred = PredFileName.split('.')

	if FileName != "":
		lvFileName = FileName.split('.')
		lvCMD = "mv "+FileName+" "+lvFileName[0]+"_NOT_FEASIBLE.csv"
		res = run_command(lvCMD)
		lvCMD = "mv "+lvFileName[0]+"_NOT_FEASIBLE.csv "+NF_subPath+"/"
		res = run_command(lvCMD) 
	
	if JobSetFileName != "":
		lvCMD = "mv "+JobSetFileName+" "+lvJobSet[0]+"_NOT_FEASIBLE.csv"
		res = run_command(lvCMD)
		lvCMD = "mv "+lvJobSet[0]+"_NOT_FEASIBLE.csv "+NF_subPath+"/"
		res = run_command(lvCMD)

	if PredFileName != "":
		lvCMD = "mv "+PredFileName+" "+lvPred[0]+"_NOT_FEASIBLE.csv"
		res = run_command(lvCMD)
		lvCMD = "mv "+lvPred[0]+"_NOT_FEASIBLE.csv "+NF_subPath+"/"
		res = run_command(lvCMD)

def test_feasibility(Type="Heterogeneous", Workload="", threads=1):
	if threads > 1:
		if (Type == "Heterogeneous") or (Type == "Heterogeneous_Save") or (Type == "Heterogeneous_Save_Isolate") or (Type == "Heterogeneous_Create_Feasible"):
			lvCMD = SCHEDULABILITY_TEST_PATH + " -R hetero --threads="+str(threads)+" "+Workload 
		else:
			lvCMD = SCHEDULABILITY_TEST_PATH + " -m "+ str(CORES_PER_RESOURCE[0]) + " --threads="+str(threads)+" "+Workload 
	else:
		if (Type == "Heterogeneous") or (Type == "Heterogeneous_Save") or (Type == "Heterogeneous_Save_Isolate") or (Type == "Heterogeneous_Create_Feasible"):
			lvCMD = SCHEDULABILITY_TEST_PATH + " -R hetero "+Workload 
		else:
			lvCMD = SCHEDULABILITY_TEST_PATH + " -m "+ str(CORES_PER_RESOURCE[0]) +" "+Workload 
	if DEBUG == 'd':
		print(lvCMD)
	res = run_command(lvCMD)
	if DEBUG == 'd':
		print(res)
	lvres = res.decode().split(',')
	return int(lvres[1])

def ConvertTaskSet_for_Feasibility_Analysis(FA_TaskSetList):
	for Task in range(0, len(FA_TaskSetList)):
		for Vertex in range(0, len(FA_TaskSetList[Task])):
			FA_TaskSetList[Task][Vertex].BCET = FA_TaskSetList[Task][Vertex].WCET

def getTaskSetPriorities(Periods):
	Priorities = []
	Counter = 0

	for n in range(0, len(Periods)):
		Priorities.append(DUMMY_NUMBER)

	for P in range(min(Periods), max(Periods)+MIN_PERIOD, MIN_PERIOD):
		if P in Periods:
			for v in range(0, len(Periods)):
				if (Periods[v] == P):
					Priorities[v] = PRIORITY_ARRAY[Counter]
					Counter += 1

	return Priorities

def getNFJCovertedNodes(TaskSetList, cNodeList=[]):
	for n in range(0, len(TaskSetList)):
		outAllPaths = []
		AllPaths = []
		CriticalPaths = []
		getAllPaths(TaskSetList[n], TaskSetList[n][0], outAllPaths, AllPaths)
		CriticalPaths, CriticalPaths_WCET = getCriticalPaths_wrt_WCET(outAllPaths)
		cNodes = copy.deepcopy(TaskSetList[n])
		Convert_to_NFJ_DAG(cNodes, CriticalPaths)
		cNodeList.append(cNodes)

def createWorkload(Run, Tasks, FileName, Utilization, subPath, GraphFileName):
	global MAX_PERIOD_GENERATED

	FEASIBLE = True

	TaskSetList = []
	cNodeList = []
	UtilizationPerTaskList = []
	
	if (UTILIZATION_METHOD == "UUFD"):
		UtilizationPerTaskList = getUtilizationUUnifastDiscard(Tasks, Utilization) 
	else:
		UtilizationPerTaskList = getUtilizationUUnifast(Tasks, Utilization)

	if len(UtilizationPerTaskList) < 1:
		if DEBUG == 'd':                
			print ("Number of Utilization Generation Tries Exceeded... DEFAULT Value:%d"%DEFAULT_TASK_UUFD_TRIES)
		return ERROR 

	NecessaryConditionPass = False
	Periods = []
	Feasibility_Result = True
	ExtTries = 0
	while NecessaryConditionPass == False:
		ExtTries += 1
		SkipNecessaryConditionCheck = False
		TimedOutTask = 0
		Renew_Utilization = False

		if ExtTries > DEFAULT_TASK_GENERATION_TRIES:
			if DEBUG == 'e':                
				print ("Failed for Number of Taskset Generation Tries Exceeded... DEFAULT Value:%d"%DEFAULT_TASK_GENERATION_TRIES)
			return ERROR 

		for Task in range(1, Tasks+1):                    
			
			TaskGenerated = False
			TaskNodes = []

			Tries = 0

			while (len(TaskNodes) < MIN_NODES):
				Tries += 1
				lvPeriod = 0                        
				TaskNodes =   Generate_DAG_Task(Task, FileName)

				if (EQUAL_DEADLINE_TASKS_GENERATION == False):
					lvPeriod = AssignPeriod(Task, TaskNodes, UtilizationPerTaskList[Task-1], Periods)
					if lvPeriod == 0 or lvPeriod > MAX_PERIOD:
						if DEBUG == 'e':
							print("Failed for lvPeriod:%d Renew Utilization"%lvPeriod)
						Renew_Utilization = True
						break

				if (lvPeriod!=0) and (EQUAL_DEADLINE_TASKS_GENERATION == False): # Check if there is a duplicate period
					if PERIOD_ASSIGNMENT == "Default":
						if (isPeriodDuplicate(Periods, lvPeriod) == True):
							TaskNodes.clear()

				if (EQUAL_DEADLINE_TASKS_GENERATION == False):
					if lvPeriod == 0:
						TaskNodes.clear()
						if DEBUG == 'e':
							print("Failed for lvPeriod:%d Cleared TaskNodes"%lvPeriod)
					elif (len(TaskNodes) >= MIN_NODES):
						Periods.append(lvPeriod)
						TaskGenerated = True
					else:
						if DEBUG == 'e':
							print("Failed for Task:%d Nodes:%d < MIN_NODES:%d"%(Task, len(TaskNodes), MIN_NODES))

				if (PERIOD_ASSIGNMENT == "Default") and (Tries > DEFAULT_TASK_EXPANSION_TRIES):
					break

			if (EQUAL_DEADLINE_TASKS_GENERATION == False):
				if (TaskGenerated == False) and (SkipNecessaryConditionCheck == False) or (Renew_Utilization == True):
					SkipNecessaryConditionCheck = True
					TimedOutTask = Task
					Periods.clear()

			TaskSetList.append(TaskNodes)

		if SkipNecessaryConditionCheck == False:
			if (EQUAL_DEADLINE_TASKS_GENERATION == False) and (len(Periods) == Tasks):
				NecessaryConditionPass, TotalJobsPerHyperPeriod = checkNecessaryCondition(TaskSetList, UtilizationPerTaskList, (Utilization/TOTAL_COMPUTING_NODES), Periods)
			else:
				NecessaryConditionPass, TotalJobsPerHyperPeriod = checkNecessaryCondition(TaskSetList, UtilizationPerTaskList, (Utilization/TOTAL_COMPUTING_NODES), Periods)
		else:
			if DEBUG == 'e':
				print("Failed for Timeout in Exploring the Task:%d NODES Nr_of_Periods:%d"%(TimedOutTask, len(Periods)))

		if NecessaryConditionPass == False:
			if (UTILIZATION_METHOD == "UUFD"):
				UtilizationPerTaskList = getUtilizationUUnifastDiscard(Tasks, Utilization) 
			else:
				UtilizationPerTaskList = getUtilizationUUnifast(Tasks, Utilization)
			if len(UtilizationPerTaskList) < 1:
				if DEBUG == 'e':                
					print ("Number of Utilization Generation Tries Exceeded... DEFAULT Value:%d"%DEFAULT_TASK_UUFD_TRIES)
				return ERROR 
			TaskSetList.clear()
			Periods.clear()
		else:
			JobSetFileName = "" 
			PredFileName = ""

			if EQUAL_PRIORITY_TASKS_GENERATION == False:
				Priorities = getTaskSetPriorities(Periods)
			else:
				Priorities = Periods

			getNFJCovertedNodes(TaskSetList, cNodeList)
			
			if WANT_TASKSET_FILES:
				if CONVERT_TO_NFJ_DAG != False:					
					create_tasks_file(Tasks, cNodeList, FileName, Periods, Priorities)
				else:
					create_tasks_file(Tasks, TaskSetList, FileName, Periods, Priorities)
				if WANT_JOBSET:
					JobSetFileName, PredFileName = create_job_set(FileName)
			else:
				if DEBUG == 'd':
					Print_TaskSet(TaskSetList, UtilizationPerTaskList, Periods, False)

			if FEASIBILITY_ANALYSIS != "NA":
				TestJobSet = ""
				TestPredFile = ""
				NF_subPath = subPath+"/NOT_FEASIBLE_WORKLOAD/"

				if (FEASIBILITY_ANALYSIS == "Heterogeneous_Save_Isolate") or (FEASIBILITY_ANALYSIS == "Homogeneous_Save_Isolate"):
					try:
						os.mkdir(NF_subPath)
					except OSError:
						if os.path.isdir(NF_subPath) != True:    
							if DEBUG == 'e':                
								print ("Creation of the directory %s failed" % NF_subPath)
							exit(1)
				
				if CONVERT_TO_NFJ_DAG != False: 
					FA_TaskSetList = copy.deepcopy(cNodeList)
				else:
					FA_TaskSetList = copy.deepcopy(TaskSetList)

				ConvertTaskSet_for_Feasibility_Analysis(FA_TaskSetList)

				lvFileName = FileName.split('.')
				TestFileName = lvFileName[0]+"_FA.csv"
				
				create_tasks_file(Tasks, FA_TaskSetList, TestFileName, Periods, Priorities)
				TestJobSet, TestPredFile = create_job_set(TestFileName)
				
				Workload = TestJobSet+" -p "+TestPredFile

				if (test_feasibility(FEASIBILITY_ANALYSIS, Workload, FEASIBILITY_ANALYSIS_THREADS) == False):
					
					if DEBUG == 'e':
						print("Failed Necessary Test via schedulability_analysis...")
					
					Feasibility_Result = False

					if (FEASIBILITY_ANALYSIS != "Heterogeneous_Save") and (FEASIBILITY_ANALYSIS != "Homogeneous_Save")\
					 and (FEASIBILITY_ANALYSIS != "Heterogeneous_Save_Isolate") and (FEASIBILITY_ANALYSIS != "Homogeneous_Save_Isolate"):
						remove_task_jobset(JobSetFileName, PredFileName, FileName)
					elif (FEASIBILITY_ANALYSIS == "Heterogeneous_Save_Isolate") or (FEASIBILITY_ANALYSIS == "Homogeneous_Save_Isolate"):
						rename_task_jobset(JobSetFileName, PredFileName, NF_subPath, FileName)				

					FEASIBLE = False
				else:
					FEASIBLE = True
						
				remove_task_jobset(TestJobSet, TestPredFile, TestFileName)
							
	if (WANT_GRAPH == True):

		for n in range(0, len(TaskSetList)):

			if CONVERT_TO_NFJ_DAG == False:
			
				outAllPaths = []
				AllPaths = []
				CriticalPaths = []

				getAllPaths(TaskSetList[n], TaskSetList[n][0], outAllPaths, AllPaths)

				UpdateParallelVertices_of_EachVertex(TaskSetList[n], outAllPaths)
				UpdateDescendants_of_EachVertex(TaskSetList[n], outAllPaths) 
				UpdateAncestors_of_EachVertex(TaskSetList[n], outAllPaths)
		
				CriticalPaths = CreateGraphFile(n, TaskSetList[n], outAllPaths, GraphFileName)

			else:
					
				new_outAllPaths = []
				new_AllPaths = []
				getAllPaths(cNodeList[n], cNodeList[n][0], new_outAllPaths, new_AllPaths)

				UpdateParallelVertices_of_EachVertex(cNodeList[n], new_outAllPaths)
				UpdateDescendants_of_EachVertex(cNodeList[n], new_outAllPaths) 
				UpdateAncestors_of_EachVertex(cNodeList[n], new_outAllPaths)
						   
				lvFileName = GraphFileName.split('.')
				ConvertedFileName = lvFileName[0]+"_NFJ_DAG.csv"
				CreateGraphFile(n, cNodeList[n], new_outAllPaths, ConvertedFileName)
	
	if FEASIBLE:

		lvUtilizationSum = 0
		for Task in range(1, Tasks+1):
			if DEBUG == 'd':			
				for RSC in range(0, RESOURCE_TYPES):
					lvCoreRSC = UtilizationPerTaskList[Task-1]*(CORES_PER_RESOURCE[RSC]/TOTAL_COMPUTING_NODES)
					print("Utilization of RSC:%d = %d%% => %f Cores"%(RSC+1, 100*(lvCoreRSC/UtilizationPerTaskList[Task-1]), lvCoreRSC))	
				print("Task:%d Nodes:%d Given_Utilization:%f ---> Generated_Utilization:%f WCET_SUM:%d Period:%d"%(Task, len(TaskSetList[Task-1]), UtilizationPerTaskList[Task-1], getTotalTaskWCET(TaskSetList[Task-1])/Periods[Task-1], getTotalTaskWCET(TaskSetList[Task-1]), Periods[Task-1]))
			lvUtilizationSum += (getTotalTaskWCET(TaskSetList[Task-1])/Periods[Task-1])

		if MAX_PERIOD_GENERATED < max(Periods):
			MAX_PERIOD_GENERATED = max(Periods)

		print("Generated %d Tasks:: Given Utilization %d%% = %f, Generated Utilization:%d%% = %f Sample_Number:%d = HyperPeriod:%d TotalJobsPerHyperPeriod:%d"\
			%(Tasks, (Utilization/TOTAL_COMPUTING_NODES)*100, Utilization, (lvUtilizationSum/TOTAL_COMPUTING_NODES)*100, lvUtilizationSum, Run, get_hyper_period(Periods), TotalJobsPerHyperPeriod))

	return FEASIBLE

def CreateWorkloadRuns(path, Utilization, FA="NA"):
	fp = 0

	if FA != "NA":
					
		NF_subPath = path+"/FEASIBILITY_ANALYSIS_REPORT/"

		try:
			os.mkdir(NF_subPath)
		except OSError:
			if os.path.isdir(NF_subPath) != True:    
				if DEBUG == 'e':                
					print ("Creation of the directory %s failed" % NF_subPath)
				exit(1)

		Feasibility_Result_File = NF_subPath+"/Report.txt"

		try:
			fp = open(Feasibility_Result_File, "w")
		except IOError:
			if DEBUG == 'e':
				print ("Opening of File %s failed" % Feasibility_Result_File)
				exit(1)

	subPath = ""

	for Tasks in range(MIN_N, MAX_N+TASK_MULTIPLES, TASK_MULTIPLES):
		if UTILIZATION_METHOD == "UUFD":
			lvHardC = 0
			lvUtilTolerancePercentage = ((Utilization*TOTAL_COMPUTING_NODES)/Tasks)*100
			if lvUtilTolerancePercentage > UTILIZATION_TOLERANCE_PERCENTAGE:
				lvHardC = math.ceil(Utilization*TOTAL_COMPUTING_NODES/Tasks)+(math.ceil(Utilization*TOTAL_COMPUTING_NODES/Tasks)*UTILIZATION_TOLERANCE)
			else:
				lvHardC = math.ceil(Utilization*TOTAL_COMPUTING_NODES/Tasks)
			print("***Hard Condition*** Total Utilization:%f Tasks:%d Utilization Per Task Should be <= %f"\
				%(Utilization*TOTAL_COMPUTING_NODES, Tasks, lvHardC))
		else:
			print("***Hard Condition*** Total Utilization:%f Tasks:%d"%(Utilization*TOTAL_COMPUTING_NODES, Tasks))

		subPath = path+"Tasks_"+str(Tasks)+"/"
		try:
			os.mkdir(subPath)
		except OSError:
			if os.path.isdir(subPath) != True:    
				if DEBUG == 'e':                
					print ("Creation of the directory %s failed" % subPath)
				exit(1)

		GraphPath = ""
		if WANT_GRAPH == True:
			GraphPath = path+"Tasks_"+str(Tasks)+"/Visuals/"
			try:
				os.mkdir(GraphPath)
			except OSError:
				if os.path.isdir(GraphPath) != True:    
					if DEBUG == 'e':                
						print ("Creation of the directory %s failed" % GraphPath)
					exit(1)

		FEASIBLE = 0
		NOT_FEASIBLE = 0
		FileName = ""
		GraphFileName = ""

		Run = 0 
		Feasibility_Ratio = 0
		Tries = 0
		while Run < NR_OF_RUNS:
			Tries += 1
			if WANT_HETEROGENEOUS == True:
				FileName = subPath+"Hetero_Tasks_"+str(Tasks)+"_Run_"+str(Run)+".csv"
				if WANT_GRAPH:
					GraphFileName =  GraphPath+"Hetero_Tasks_"+str(Tasks)+"_Run_"+str(Run)+".csv"
			else:
				FileName = subPath+"Typed_Tasks_"+str(Tasks)+"_Run_"+str(Run)+".csv"
				if WANT_GRAPH:
					GraphFileName =  GraphPath+"Typed_Tasks_"+str(Tasks)+"_Run_"+str(Run)+".csv"
			
			Result = createWorkload(Run, Tasks, FileName, Utilization*TOTAL_COMPUTING_NODES, subPath, GraphFileName)

			if ((FEASIBLE+NOT_FEASIBLE) != 0):
				Feasibility_Ratio	=	(FEASIBLE/(FEASIBLE+NOT_FEASIBLE))*100

			if (Result == ERROR) or (Tries > DEFAULT_FEASIBLE_TASK_GENERATION_TRIES)\
			 or (((FEASIBLE+NOT_FEASIBLE) >= DEFAULT_FEASIBLE_TASK_GENERATION_TRIES) and (Feasibility_Ratio < DEFAULT_MIN_REQUIRED_FEASIBILITY)):
				lvSTR = "\nError: Failed to Generate Suitable Workload for "+str(Tasks)+" Tasks"+" Utilization:"+str(Utilization*100)+"% = "+str(Utilization*TOTAL_COMPUTING_NODES)				
				print(lvSTR) 
				break
			elif (Result == False):
				NOT_FEASIBLE += 1
			else:
				FEASIBLE += 1

			if (FEASIBILITY_ANALYSIS == "Heterogeneous_Create_Feasible") or (FEASIBILITY_ANALYSIS == "Homogeneous_Create_Feasible"):
				if Result == True:
					Run += 1
					Tries = 0
			else: 
				Run += 1
				Tries = 0

		if (FEASIBILITY_ANALYSIS != "NA") and ((FEASIBLE+NOT_FEASIBLE) != 0):
			lvSTR = "\nTasks:"+str(Tasks)+" Utilization:"+str(Utilization*100)+"% = "+str(Utilization*TOTAL_COMPUTING_NODES)+\
			" Required_TaskSets:"+str(NR_OF_RUNS)+" Generated:"+str(FEASIBLE+NOT_FEASIBLE)+" => FEASIBLE_TASKSETS:"+str(FEASIBLE)+\
			" NOT_FEASIBLE_TASKSETS:"+str(NOT_FEASIBLE)+" Feasibility_Ratio:"+str(FEASIBLE/(FEASIBLE+NOT_FEASIBLE))+"\n"

			print(lvSTR)

		if fp != 0:
			fp.write("RESOURCE_TYPES:%d\n"%RESOURCE_TYPES)
			for cores in range(0, len(CORES_PER_RESOURCE)):
				fp.write("CORES_PER_RESOURCE[%d]:%d\n"%(cores+1, CORES_PER_RESOURCE[cores]))
			fp.write(lvSTR)
			fp.flush()

		if (WANT_TASKSET_FILES == False) and (WANT_JOBSET == False) and (WANT_GRAPH == False):
			lvCMD = "rm -rf "+subPath
			run_command(lvCMD)

	if fp != 0:
		fp.close()

def main():

	global DEBUG
	global WANT_GRAPH
	global WANT_JOBSET
	global WANT_HETEROGENEOUS
	global WANT_CRITICAL_PATH_JOBS
	global WANT_CRITICAL_PATH_WCET
	global SELF_SUSPENDING
	global WANT_TASKSET_FILES
	global UTILIZATION_METHOD
	global WANT_TASKJOB_SET
	global CONVERT_TO_NFJ_DAG
	global FEASIBILITY_ANALYSIS
	global SCHEDULABILITY_TEST_PATH
	global FEASIBILITY_ANALYSIS_THREADS
	global PERIOD_CONDITIONING
	global PERIOD_ASSIGNMENT
	global PERIODS_ARRAY
	global MIN_PERIOD
	global MAX_PERIOD
	global PRIORITY_POLICY
	global MULTI_THREADING
	global EQUAL_DEADLINE_TASKS_GENERATION
	global EQUAL_PRIORITY_TASKS_GENERATION
	global RESOURCE_TYPES
	global CORES_PER_RESOURCE
	global TOTAL_COMPUTING_NODES
	global WANT_ALL_RSC_TYPE_NODES
	global WANT_MORE_SIBLINGS
	global NON_NESTED_FORK_JOIN

	opts = parse_args()
	
	if(opts.want_graph == 'Y' or opts.want_graph == 'y'):
		WANT_GRAPH = True
	if(opts.task_type == "Hetero"):
		WANT_HETEROGENEOUS  =   True
	if opts.critical_path == 'J': 
		WANT_CRITICAL_PATH_JOBS  = True
	elif opts.critical_path == 'W':
		WANT_CRITICAL_PATH_WCET = True
	if(opts.self_suspending == 'Y' or opts.self_suspending == 'y'):
		SELF_SUSPENDING = True    
	if(opts.job_set == 'Y' or opts.job_set == 'y'):
		WANT_JOBSET = True 
	elif(opts.job_set == 'Z' or opts.job_set == 'z'):
		WANT_TASKJOB_SET = True
		WANT_JOBSET = True
	if(opts.taskset_files == 'Y' or opts.taskset_files == 'y'):
		WANT_TASKSET_FILES = True  
	if(opts.nfj_dag=='F' or opts.nfj_dag=='f'):
		CONVERT_TO_NFJ_DAG = False
	elif(opts.nfj_dag=='R' or opts.nfj_dag=='r'):
		CONVERT_TO_NFJ_DAG = RESERVED 
	if(opts.period_conditioning == 'Y' or opts.period_conditioning == 'y'):
		PERIOD_CONDITIONING = True
	if(opts.multi_threading == 'Y' or opts.multi_threading == 'y'):
		MULTI_THREADING = True
	if(opts.equal_deadline_tasks == 'N' or opts.equal_deadline_tasks == 'n'):
		EQUAL_DEADLINE_TASKS_GENERATION = False
	if(opts.equal_priority_tasks == 'Y' or opts.equal_priority_tasks == 'y'):
		EQUAL_PRIORITY_TASKS_GENERATION = True

	DEBUG 							= opts.debug
	PERIOD_ASSIGNMENT 				= opts.period_assignment
	FEASIBILITY_ANALYSIS 			= opts.feasibility_check
	SCHEDULABILITY_TEST_PATH 		= opts.nptest
	FEASIBILITY_ANALYSIS_THREADS 	= int(opts.threads)
	PRIORITY_POLICY 				= opts.priority_policy
	WANT_ALL_RSC_TYPE_NODES			= opts.rsc
	WANT_MORE_SIBLINGS				= opts.sibl
	NON_NESTED_FORK_JOIN			= opts.nnfj

	UTILIZATION_METHOD = opts.util_method

	UTILIZATION_METHODS_USED = []

	if UTILIZATION_METHOD == "UUF_UUFD":
		UTILIZATION_METHODS_USED.append("UUFD")
		UTILIZATION_METHODS_USED.append("UUF")
	else:
		UTILIZATION_METHODS_USED.append(UTILIZATION_METHOD)

	ExtractParameters(opts.Settings)

	for Task in range(0, MAX_N):
		PRIORITY_ARRAY.append(Task)

	print("Generation of Task Sets:"+ opts.parent_folder)

	if PERIOD_ASSIGNMENT == "UNIFORM":
		counter = 0
		while (counter < (MAX_PERIOD/MIN_PERIOD)):
			PERIODS_ARRAY.append(MIN_PERIOD*(counter+1))
			counter += 1
	elif PERIOD_ASSIGNMENT == "ECRTS_19": # Following values of MIN_PERIOD, MAX_PERIOD, X and Y are in accordance with ECRTS'19 Nasri et al paper.
		print("Periods are generated in accordance with ECRTS'19 Nasri et al paper.")
		PERIODS_ARRAY.append(DEFAULT_ECRTS_19_MIN_PERIOD)
		MIN_PERIOD = DEFAULT_ECRTS_19_MIN_PERIOD
		MAX_PERIOD = (10**5)
		for X in range(1, 11):
			for Y in range(3, 5):
				if X*(10**Y) not in PERIODS_ARRAY:
					PERIODS_ARRAY.append(X*(10**Y))
	elif PERIOD_ASSIGNMENT == "ECRTS_19_FIXED":
		MIN_PERIOD = 1*(10**3)
		MAX_PERIOD = 9*(10**5)
		for X in range(1, 10):
			for Y in range(3, 6):
				PERIODS_ARRAY.append(X*(10**Y))

	PrintExtractedParameters()

	if PERIOD_ASSIGNMENT != "Default":
		PERIODS_ARRAY.sort();
		print(PERIODS_ARRAY)

	path = opts.parent_folder

	if FEASIBILITY_ANALYSIS != "NA":
		if (FEASIBILITY_ANALYSIS != "Heterogeneous_Create_Feasible") and (FEASIBILITY_ANALYSIS != "Homogeneous_Create_Feasible") and (FEASIBILITY_ANALYSIS == "Heterogeneous_Save_Isolate")\
		 or (FEASIBILITY_ANALYSIS == "Homogeneous_Save_Isolate") and (FEASIBILITY_ANALYSIS != "Heterogeneous_Save") and (FEASIBILITY_ANALYSIS != "Homogeneous_Save"):
			print("Feasibility Option InCorrect.... Exitting Generation")
			exit(1)
		else:			
			print("Creating Feasible Task Sets Only via %s"%FEASIBILITY_ANALYSIS)
	
	for workload in range(0, NR_OF_WORKLOADS):

		if RESOURCE_RANGE_MAX != 0:
			TOTAL_COMPUTING_NODES = 0
			CORES_PER_RESOURCE.clear()
			RESOURCE_TYPES = int(getRandomInteger(RESOURCE_RANGE_MIN, RESOURCE_RANGE_MAX))
			for RSC in range(0, RESOURCE_TYPES):
				CORES_PER_RESOURCE.append(int(getRandomInteger(CORES_RANGE_MIN, CORES_RANGE_MAX)))
				TOTAL_COMPUTING_NODES += CORES_PER_RESOURCE[RSC]

		for method in range(0, len(UTILIZATION_METHODS_USED)):
			UTILIZATION_METHOD = UTILIZATION_METHODS_USED[method]
			path = opts.parent_folder+str(workload+1)+"_"+UTILIZATION_METHOD+"_Workload/"
			
			print("Utilization Method: %s Workload %d ... Resource Types:%d TotalComputingNodes:%d"\
				%(UTILIZATION_METHOD, workload+1, RESOURCE_TYPES, TOTAL_COMPUTING_NODES))
			for RSC in range(0, RESOURCE_TYPES):
				print("CORES_PER_RESOURCE[%d]=%d"%(RSC+1, CORES_PER_RESOURCE[RSC]))

			try:
				os.mkdir(path)
			except OSError:
				if os.path.isdir(path) != True:
					if DEBUG == 'e':
						print ("Creation of the directory %s failed" % path)
					exit(1)

			Result = True

			Workloadthreads = []
			for Utilization in range(0, len(UTILIZATION_VECTOR)):

				if WANT_HETEROGENEOUS == True:
					sub_path = path+"HeteroDAGTasks_Util_"+str(int(UTILIZATION_VECTOR[Utilization]*100))+"/"
				else:
					sub_path = path+"TypedDAGTasks_Util_"+str(int(UTILIZATION_VECTOR[Utilization]*100))+"/"
				# define the name of the directory to be created
				try:
					os.mkdir(sub_path)
				except OSError:
					if os.path.isdir(sub_path) != True:
						if DEBUG == 'e':
							print ("Creation of the directory %s failed" % sub_path)
						exit(1)

				if MULTI_THREADING:
					try:
						Workloadthreads.append(myThread(sub_path, UTILIZATION_VECTOR[Utilization], FEASIBILITY_ANALYSIS))
						Workloadthreads[Utilization].start()
					except:
						if DEBUG == 'e':
							print("Error: unable to start thread")
				else:
					CreateWorkloadRuns(sub_path, UTILIZATION_VECTOR[Utilization], FEASIBILITY_ANALYSIS)

				if (WANT_TASKSET_FILES == False) and (FEASIBILITY_ANALYSIS == "NA") and (WANT_GRAPH == False):
					lvCMD = "rm -rf "+sub_path 
					run_command(lvCMD)

			if MULTI_THREADING:
				for Utilization in range(0, len(UTILIZATION_VECTOR)):
					Workloadthreads[Utilization].join()
				print("Maximum Period Generated through all DAG Task Generations:%d"%MAX_PERIOD_GENERATED)
	
if __name__ == '__main__': 
	main()