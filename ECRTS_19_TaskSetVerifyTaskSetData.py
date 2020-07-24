'''
******************************* Task Set Data Verification **********************
* Author:       Muhammad Junaid Aslam
* Contact:      junaidaslam1@gmail.com
* Rank:         PhD Candidate
* Institute:    Technical University of Delft, Netherlands
*
* ---------------------------------------------------------------------
* This software is governed by the Null license under M.J law and     |
* abiding by the rules of distribution of free software. You can use, |
* modify and redistribute the software under the condition of citing  |
* or crediting the authors of this software in your work.             |
* ---------------------------------------------------------------------
*
* This is part of a research project funded by the EWI EEMCS Group of
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
CRP_W_COLOR = "dodgerblue"

LONGEST_WCET_PATH_COLOR = 11
MS_TO_US = 1000
TASK_SET_FILE = "Null"
WANT_GRAPH = False

SE	=	-1
PA	=	-2

DUMMY_NUMBER	=	99999999

RSC_Type = 0
Cores_Per_RSC_Type = []

def NUM_TO_STR(num):
	if num == SE:
		return 'SE'
	elif num == PA:
		return 'PA'
	else:
		return num

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
	elif RSC_TYPE == LONGEST_WCET_PATH_COLOR:
		return CRP_W_COLOR

def parse_args():
	parser = argparse.ArgumentParser(description="Create task sets file")

	parser.add_argument('-w', '--workload_location', dest='root_folder', default='Null', 
						action='store', type=str, metavar="WORKLOAD_LOCATION",
						required=False,
						help='The place to pickup task-set files')

	parser.add_argument('-t', '--task_set', dest='task_set', default='Null', 
						action='store', type=str, metavar="TASK_SET_FILE",
						required=False,
						help='The task_set file to operate.')

	parser.add_argument('-g', '--graph', dest='graph', action='store_const',
						const=True, required=False,
						help='This option generates visuals of task set')

	return parser.parse_args()

def run_command(incommand):
	p = subprocess.Popen(incommand.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	outstring = p.stdout.read()
	return outstring

def ms2us(x):
	return int(ceil(MS_TO_US * x))

class TestResults:	 
	def __init__(self): 
		self.Filename = "Dummy"
		self.Schedulable = 1
		self.Jobs = 0

	def DisplayResult(self):
		print("Executed_File: %s      Schedulable: %d      Jobs: %d"%(self.Filename, self.Schedulable, self.Jobs))

class NodeData:
	def __init__(self): 
		self.TID 			= 0
		self.JID 			= 0
		self.r_min 			= 0
		self.r_max 			= 0
		self.BCET 			= 0
		self.WCET 			= 0
		self.ResourceType 	= 1
		self.Pred 			= []
		self.Succ 			= []
		self.Par_v 			= []
		self.Desc 			= []
		self.Ancs 			= []

	def Copy(self, CopyTo):
		CopyTo.TID 			= 	self.TID
		CopyTo.JID 			= 	self.JID
		CopyTo.r_min 		= 	self.r_min
		CopyTo.r_max 		= 	self.r_max
		CopyTo.BCET 		= 	self.BCET
		CopyTo.WCET 		= 	self.WCET
		CopyTo.ResourceType = 	self.ResourceType
		CopyTo.Pred 		=	self.Pred.copy()
		CopyTo.Succ 		=	self.Succ.copy()

	def DisplayData(self):
		print("T%dJ%d BCET:%d WCET:%d RSC:%d Deadline:%d Pred:"%(self.TID, self.JID, self.BCET, self.WCET, self.ResourceType, self.Deadline, self.Pred))

class TaskData:
	def __init__(self):
		self.TID 		= 	0
		self.Period 	=	0
		self.Priority 	= 	0
		self.Deadline 	= 	0
		self.CRP_WCET 	=	0
		self.Nodes 		= 	[]
		self.AllPaths 	= 	[]
		self.CRP 		= 	[]

	def DisplayData(self):
		print("T%d Period:%d Deadline:%d Number_of_Nodes:%d"%(self.TID, self.Period, self.Deadline, len(self.Nodes)))

	def ClearData(self):
		self.TID 		= 	0
		self.Period 	=	0
		self.Priority 	= 	0
		self.Deadline 	= 	0
		self.CRP_WCET 	=	0
		self.Nodes.clear()
		self.AllPaths.clear() 
		self.CRP.clear()

	def Copy(self, inTask):
		inTask.TID 			= self.TID
		inTask.Period 		= self.Period
		inTask.Priority		= self.Priority
		inTask.Deadline 	= self.Deadline
		inTask.CRP_WCET 	= self.CRP_WCET
		inTask.Nodes 		= self.Nodes.copy()
		inTask.AllPaths		= self.AllPaths.copy()
		inTask.CRP 			= self.CRP.copy()

def PrintTaskSetData(RSC_Type, Cores_Per_RSC_Type, TaskSetInfo, PrintFull=False):

	print("<<<<<<<<<<< Number of Tasks:%d >>>>>>>>>>>>>>>"%len(TaskSetInfo))
	print("ResourceTypes:%d"%RSC_Type)
	for n in range(0, RSC_Type):
		print("Cores_Per_RSC_Type[%d]=%d"%(n+1, Cores_Per_RSC_Type[n]))

	for n in range(0, len(TaskSetInfo)):
		print("Task:%d Period:%d Deadline:%d CRP_WCET:%d"%(TaskSetInfo[n].TID,TaskSetInfo[n].Period, TaskSetInfo[n].Deadline, TaskSetInfo[n].CRP_WCET))
		if TaskSetInfo[n].CRP_WCET > TaskSetInfo[n].Period:
			print("-----------------------------------------------------")
			print("Error in Generated DAG Task... For example above task has CRP_WCET > Period")
			print("-----------------------------------------------------")
			exit(1)
		if PrintFull == True:
			for l in range(0, len(TaskSetInfo[n].Nodes)):
				pNode = ""
				pNode = "V,"+str(TaskSetInfo[n].Nodes[l].TID)+","+str(TaskSetInfo[n].Nodes[l].JID)+","+str(TaskSetInfo[n].Nodes[l].r_max)
				pNode += ","+str(TaskSetInfo[n].Nodes[l].r_max)+","+str(TaskSetInfo[n].Nodes[l].BCET)+","+str(TaskSetInfo[n].Nodes[l].WCET)
				pNode += ","+str(TaskSetInfo[n].Nodes[l].ResourceType)+", predecessors, "
				for p in range(0, len(TaskSetInfo[n].Nodes[l].Pred)):
					pNode += str(TaskSetInfo[n].Nodes[l].Pred[p])+","
				pNode += ","+" successors"+", "
				for s in range(0, len(TaskSetInfo[n].Nodes[l].Succ)):
					pNode += str(TaskSetInfo[n].Nodes[l].Succ[s])+","
				print(pNode)

def get_hyper_period(numbers):
	return reduce(lambda x, y: (x*y)/gcd(x,y), numbers, 1) 

def UpdateSuccessors(TaskSetInfo):
	for n in range(0, len(TaskSetInfo)):
		for m in range(0, len(TaskSetInfo[n].Nodes)):			
			for p in range(0, len(TaskSetInfo[n].Nodes[m].Pred)):
				TaskSetInfo[n].Nodes[TaskSetInfo[n].Nodes[m].Pred[p]].Succ.clear()

	for n in range(0, len(TaskSetInfo)):
		for m in range(0, len(TaskSetInfo[n].Nodes)):			
			for p in range(0, len(TaskSetInfo[n].Nodes[m].Pred)):
				TaskSetInfo[n].Nodes[TaskSetInfo[n].Nodes[m].Pred[p]].Succ.append(TaskSetInfo[n].Nodes[m].JID)

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
				if (AllPaths[n].Succ[m] == AllPaths[n+1].JID):
					Skip = False
					break
		if Skip == False:
			newPath = AllPaths.copy()
			outAllPaths.append(newPath)
		

def getCriticalPaths_wrt_WCET(inAllPaths):
	WCET = 0
	CriticalPaths = []

	WCET_SUM = 0
	
	if (len(inAllPaths) > 0):
		for n in range(0, len(inAllPaths[0])):
			WCET_SUM += inAllPaths[0][n].WCET
		WCET = WCET_SUM
		CriticalPaths.append(inAllPaths[0])    
		WCET_SUM = 0

		for n in range(1, len(inAllPaths)):
			for m in range(0, len(inAllPaths[n])):
				WCET_SUM += inAllPaths[n][m].WCET
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

	return CriticalPaths, WCET

def getTaskCriticalPathInfo(TaskNodes, Print=False):
	outAllPaths = []
	AllPaths = []
	getAllPaths(TaskNodes, TaskNodes[0], outAllPaths, AllPaths)
	if Print == True:
		for p in range(0, len(outAllPaths)):
			PrintList(outAllPaths[p], True)
	CRP, CRP_WCET = getCriticalPaths_wrt_WCET(outAllPaths)
	return (CRP, CRP_WCET, outAllPaths)

def addLegendtoGraph(fp, CriticalPaths_WCET):

	if CriticalPaths_WCET > 0:
		LStr = "label = "+"\""+"I`M LEGEND CRP-WCET:"+str(CriticalPaths_WCET)+"\""+";\n"
	else:
		LStr = "label = "+"\""+"I`M LEGEND"+"\""+";\n"

	header = 'rankdir=LR\n' \
			  'node [shape=plaintext]\n' \
			  'subgraph cluster_01 {\n' + LStr + 'key [label=<<table border="0" cellpadding="0" cellspacing="0" cellborder="0">\n' 

	fp.write("%s"%(header)) 

	for n in range(0, RSC_Type+1):
		fp.write('<tr><td align="right" port="i%d">RSC:%d </td></tr>\n'%(n, n))
	fp.write('<tr><td align="right" port="i%d">CRP:%d </td></tr>\n'%(RSC_Type+1, RSC_Type+1))

	fp.write("</table>>]\n" \
			 'key2 [label=<<table border="0" cellpadding="0" cellspacing="0" cellborder="0">\n'
			)

	for n in range(0, RSC_Type+1):
		fp.write('<tr><td port="i%d">&nbsp;</td></tr>\n'%(n))
	fp.write('<tr><td port="i%d">&nbsp;</td></tr>\n'%(RSC_Type+1))

	fp.write("</table>>]\n")

	for n in range(0, RSC_Type+1):
		lvColor = getColor(n)
		fp.write('key:i%d:e -> key2:i%d:w [color=%s]\n'%(n,n,lvColor))

	lvColor = getColor(LONGEST_WCET_PATH_COLOR)
	fp.write('key:i%d:e -> key2:i%d:w [color=%s]\n'%(RSC_Type+1,RSC_Type+1,lvColor))

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
		JobInfo = "\""+"J"+str(Nodes[n].JID)+" RSC:"+str(Nodes[n].ResourceType)+"\nBCET:"+str(Nodes[n].BCET)+"\nWCET:"+str(Nodes[n].WCET)+"\""
		Label = "[label="+JobInfo+", color="+nodecolor+", fontcolor="+fontcolor+", fontsize="+fontsize+"]"
		fp.write("\tJ%d%s\n"%(Nodes[n].JID, Label))

	fp.write("subgraph Main {\n")

	for n in range(0, len(Nodes)):
		for m in range(0, len(Nodes[n].Pred)):
			if Nodes[n].Pred[m] >= 0:
				fp.write("\tJ%d -> J%d\n"%(Nodes[n].Pred[m], Nodes[n].JID))
	fp.write("}\n")
	
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

def getTotalJobsPerHyperPeriod(TaskSetInfo):
	TotalJobsPerHyperPeriod = 0

	Periods = []
	for n in range(0, len(TaskSetInfo)):		
		Periods.append(TaskSetInfo[n].Period)

	HyperPeriod = get_hyper_period(Periods)

	for n in range(0, len(TaskSetInfo)):
		TotalJobsPerHyperPeriod += (HyperPeriod/Periods[n])*len(TaskSetInfo[n].Nodes)

	return int(TotalJobsPerHyperPeriod)

def Vertex_in_List(vertex, List):
	for n in range(0, len(List)):
		if vertex.JID == List[n].JID:
			return True
	return False

def VertexID_in_List(JID, List):
	for n in range(0, len(List)):
		if JID == List[n].JID:
			return True
	return False

def UpdateAncestors_of_EachVertex(TaskInfo, Print=False):
	for vertex in range(0, len(TaskInfo.Nodes)):
		TaskInfo.Nodes[vertex].Ancs.clear()
		CommonPaths = []
		for path in range(0, len(TaskInfo.AllPaths)):
			# print("VTX:%d UAEV:%d = %s"%(TaskInfo.Nodes[vertex].JID, path+1, PrintList(TaskInfo.AllPaths[path])))
			if (Vertex_in_List(TaskInfo.Nodes[vertex], TaskInfo.AllPaths[path]) == True):
				CommonPaths.append(TaskInfo.AllPaths[path])			
				# print("VTX:%d CP = %s"%(TaskInfo.Nodes[vertex].JID, PrintList(CommonPaths[len(CommonPaths)-1])))

		for path in range(0, len(CommonPaths)):		
			for uVertex in range(0, len(CommonPaths[path])):
				if CommonPaths[path][uVertex].JID < TaskInfo.Nodes[vertex].JID:
					if (Vertex_in_List(CommonPaths[path][uVertex], TaskInfo.Nodes[vertex].Ancs) == False):
						TaskInfo.Nodes[vertex].Ancs.append(CommonPaths[path][uVertex])
		CommonPaths.clear()

		TaskInfo.Nodes[vertex].Ancs.sort(key=lambda v:v.JID)

		if Print == True:
			PrintVertex_Ancs(TaskInfo.Nodes[vertex], True)

def ExtractTaskSetData(FileName, scale=ms2us):
	'''
	Implementation Note: Decrease Node.JID and Node.TID by 1, so that It is easier to handle
	the lists of predecessors and successors with respect to the Job IDs. Final results
	can be reported for each vertex by increasing the JIDs and TIDs by 1 again.
	'''
	global RSC_Type
	global Cores_Per_RSC_Type
	TaskSetInfo = []
	FP = open(FileName, 'r')
	data = csv.reader(FP, skipinitialspace=True)
	FirstEntryFound = False
	TotalJobsPerHyperPeriod = 0

	Task = TaskData()

	for row in data:
		if row[0] == 'R':
			RSC_Type = int(row[1])
		elif row[0] == 'M':
			cores = int(row[1])
			Cores_Per_RSC_Type.append(cores) 
		elif row[0] == '#':
			continue
		elif row[0] == 'T':
			if FirstEntryFound == True:				
				lvTask = TaskData()
				Task.Copy(lvTask)
				TaskSetInfo.append(lvTask)
				Task.ClearData()
			else:
				FirstEntryFound = True
			# parse new task declaration
			# A ’T’ row consists of the following columns:
			# 	1) ’T’
			# 	2) a unique numeric ID
			# 	3) the period (in milliseconds, fractional is ok)
			# 	4) the relative deadline        
			Task.TID = int(row[1])
			Task.Period  = scale(float(row[2]))
			Task.Deadline = scale(float(row[3]))
			Task.Priority  = Task.Deadline
			
			if Task.Priority == int(row[3]):
				Task.Priority = scale(Task.Priority)
			

			assert Task.TID >= 0
			assert Task.Period > 0
			assert Task.Deadline > 0

		elif row[0] == 'V':
			Node = NodeData()
			# parse vertex information
			# A ‘V’ row consists for the following columns (unbounded number):
			# 	1) ‘V’
			# 	2) task ID to which it belongs
			# 	3) a numeric vertex ID (unique w.r.t. its task)
			# 	4) earliest release time r^min (relative to start of period, may be zero)
			# 	5) latest release time r^max (relative to start of period)
			# 	6) BCET
			# 	7) WCET
			#   8) ResourceType
			# 	9) first predecessor (vertex ID), if any
			# 	10) second predecessor (vertex ID), if any
			# 	11) third predecessor (vertex ID), if any
			# 	… and so on …  
			Node.TID = int(row[1]) - 1
			Node.JID = int(row[2]) - 1
			Node.r_min = scale(float(row[3]))
			Node.r_max = scale(float(row[4]))
			Node.BCET  = scale(float(row[5]))
			Node.WCET  = scale(float(row[6]))
			Node.ResourceType  = 1
			Node.Pred = [int(Node.Pred) for Node.Pred in row[7:] if Node.Pred != '']
			
			for n in range(0, len(Node.Pred)):
				Node.Pred[n] = Node.Pred[n] - 1

			assert 0 <= Node.r_min <= Node.r_max
			assert 0 <= Node.BCET <= Node.WCET
			assert Node.JID >= 0
			assert Node.TID >= 0

			Task.Nodes.append(Node)
		else:
			print(row)
			assert False # badly formatted input???
	
	TaskSetInfo.append(Task)

	UpdateSuccessors(TaskSetInfo)

	Periods = []
	for n in range(0, len(TaskSetInfo)):
		TaskSetInfo[n].CRP, TaskSetInfo[n].CRP_WCET, TaskSetInfo[n].AllPaths = getTaskCriticalPathInfo(TaskSetInfo[n].Nodes)
		Periods.append(TaskSetInfo[n].Period)
		UpdateAncestors_of_EachVertex(TaskSetInfo[n])
		if WANT_GRAPH == True:
			createTaskGraphFile(TaskSetInfo[n].Nodes, n+1, TaskSetInfo[n].CRP, TaskSetInfo[n].CRP_WCET, FileName)

	TotalJobsPerHyperPeriod = getTotalJobsPerHyperPeriod(TaskSetInfo)

	# TaskSetInfo.sort(key=lambda v:v.Priority)
	
	return (TaskSetInfo, TotalJobsPerHyperPeriod)

def VerifyPredAncsRelations(TaskSetInfo):
	lvCounterAvg = 0
	print("Printing the Average Node Ancestor Predecessor Relations")
	for TaskInfo in TaskSetInfo:
		# print("Task:%d Relations..."%TaskInfo.TID)
		for Node in TaskInfo.Nodes:
			if len(Node.Pred) > 0:
				for Pred in Node.Pred:
					for lvNode in TaskInfo.Nodes:
						if (lvNode.JID != Node.JID) and (Vertex_in_List(Node, lvNode.Ancs) == False):
							if VertexID_in_List(Pred, lvNode.Ancs) == True:
								# print("Node:%d Related to Node:%d through Pred:%d"%(Node.JID, lvNode.JID, Pred))
								lvCounterAvg += 1
	print("Average Number of Pred Ancs Relations:%d"%(lvCounterAvg/10))

def Execute_Test(Taskset):
	Results = TestResults()
	Results.Filename = Taskset

	TaskSetInfo = []
	ResponseTime_G = []

	# Extracting Task set Details
	TaskSetInfo, Results.Jobs = ExtractTaskSetData(Taskset)

	# Printing Task set System Configurations
	PrintTaskSetData(RSC_Type, Cores_Per_RSC_Type, TaskSetInfo)
	# VerifyPredAncsRelations(TaskSetInfo)

	return Results 
	
def DispatchTests(directory):
	
	for dirName, subdirList, fileList in os.walk(directory):
		
		if len(fileList) > 0:
			print("Executing %s ..."%dirName)

		for Files in range(0, len(fileList)):
			if ("Report" not in fileList[Files]) and ("NOT_FEASIBLE" not in fileList[Files]) and ("TasksetSettings" not in fileList[Files]) and ("Results" not in fileList[Files]) and ("Jobs" not in fileList[Files]) and ("Pred" not in fileList[Files]) and (".png" not in fileList[Files]):
				results = TestResults()
				print("Executing Verification for:%s"%(directory+"/"+fileList[Files]))
				results = Execute_Test(directory+"/"+fileList[Files])

def main():
	global TASK_SET_FILE
	global WANT_GRAPH

	opts = parse_args()

	rootfolder = opts.root_folder
	TASK_SET_FILE = opts.task_set
	WANT_GRAPH = opts.graph

	if rootfolder == "Null" and TASK_SET_FILE == "Null":
		print("error: Provide proper arguments, use -h for options.")
		return

	if TASK_SET_FILE == "Null":
		for dirName, subdirList, fileList in os.walk(rootfolder):
			if "Results" in dirName or "FEASIBILITY" in dirName or "Visuals" in dirName or "Results" in dirName:
				continue
			if len(fileList) > 0:
				DispatchTests(dirName)
	else:
		results = TestResults()
		results = Execute_Test(TASK_SET_FILE)
		results.DisplayResult()

	print("Finished all tests ... ")

if __name__ == '__main__': 
	main()