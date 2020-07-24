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
import csv
import os
import copy
import math
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

Current_Results_File_Data = []
Current_Deadline_Miss_Data = []
Current_Deadline_Miss_Path = ""

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
	return int(math.ceil(MS_TO_US * x))

class TestResults:	 
	def __init__(self): 
		self.Filename = "Dummy"

	def DisplayResult(self):
		print("ReadFile: %s"%(self.Filename))

class IndexData:
	def __init__(self):
		self.index = 0
		self.TID = 0
		self.JID = 0
		self.VTX_ID = 0
		self.r_min = 0
		self.r_max = 0
		self.BCET  = 0
		self.WCET  = 0
		self.Period = 0
		self.Priority = 0
		self.Deadline = 0
		self.ResourceType = 0		
		self.Par_v = []
		self.Par_idx = []
		self.Pred_idx = []

	def PrintPar_Idx(self):
		List = "{"
		for idx in self.Par_idx:
			List += str(idx.index)+", "
		List += "}"
		return List

	def PrintPred_Idx(self):
		List = "{"
		for idx in self.Pred_idx:
			List += str(idx.index)+", "
		List += "}"
		return List

	def Display(self):
		print("Index:%d T%dJ%d r_min:%d r_max:%d BCET:%d WCET:%d Period:%d DL:%d RSC:%d Par_idx:%s Pred_idx:%s"\
			%(self.index, self.TID, self.VTX_ID, self.r_min/1000, self.r_max/1000, self.BCET/1000, self.WCET/1000, self.Period/1000,\
			 self.Deadline/1000, self.ResourceType, self.PrintPar_Idx(), self.PrintPred_Idx()))

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
		self.IndexSets  =   []

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
		self.IndexSets.clear()

	def Copy(self, inTask):
		inTask.TID 			= self.TID
		inTask.Period 		= self.Period
		inTask.Priority		= self.Priority
		inTask.Deadline 	= self.Deadline
		inTask.CRP_WCET 	= self.CRP_WCET
		inTask.Nodes 		= self.Nodes.copy()
		inTask.AllPaths		= self.AllPaths.copy()
		inTask.CRP 			= self.CRP.copy()
		inTask.IndexSets	= self.IndexSets.copy()

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
			printList += "T"+str(List[m].TID)+"J"+str(List[m].JID)+", "

	printList += "}"

	if PRINT == True:
		print("Vertex:%d %s:%s"%(VertexID, Attribute, printList))

	return printList

def PrintTaskSetData(TasksetFile, RSC_Type, Cores_Per_RSC_Type, TaskSetInfo, PrintFull="Full"):

	print("TaskSetFile: %s Tasks:%d"%(TasksetFile, len(TaskSetInfo)))

	print("ResourceTypes:%d"%RSC_Type)
	for n in range(0, RSC_Type):
		print("Cores_Per_RSC_Type[%d]=%d"%(n+1, Cores_Per_RSC_Type[n]))

	for n in range(0, len(TaskSetInfo)):
		if PrintFull == "Full":
			print("=============== Task:%d Period:%d Deadline:%d CRP_WCET:%d Priority:%d ==============="\
				%(TaskSetInfo[n].TID,TaskSetInfo[n].Period, TaskSetInfo[n].Deadline, TaskSetInfo[n].CRP_WCET, TaskSetInfo[n].Priority))
			if TaskSetInfo[n].CRP_WCET > TaskSetInfo[n].Period:
				print("-----------------------------------------------------")
				print("Error in Generated DAG Task... For example above task has CRP_WCET > Period")
				print("-----------------------------------------------------")
				exit(1)
			
			for l in range(0, len(TaskSetInfo[n].Nodes)):
				pNode = ""
				pNode = "V,"+str(TaskSetInfo[n].Nodes[l].TID+1)+","+str(TaskSetInfo[n].Nodes[l].JID+1)+","+str(TaskSetInfo[n].Nodes[l].r_max)
				pNode += ","+str(TaskSetInfo[n].Nodes[l].r_max)+","+str(TaskSetInfo[n].Nodes[l].BCET)+","+str(TaskSetInfo[n].Nodes[l].WCET)
				pNode += ","+str(TaskSetInfo[n].Nodes[l].ResourceType)+", predecessors, "
				for p in range(0, len(TaskSetInfo[n].Nodes[l].Pred)):
					pNode += str(TaskSetInfo[n].Nodes[l].Pred[p])+","
				pNode += ","+" successors"+", "
				for s in range(0, len(TaskSetInfo[n].Nodes[l].Succ)):
					pNode += str(TaskSetInfo[n].Nodes[l].Succ[s])+","
				pNode += ", Par_v: "+Print_Pred_Succ_Par_Ancs_Desc(TaskSetInfo[n].Nodes[l].JID, TaskSetInfo[n].Nodes[l].Par_v, "Par_v", False)
				print(pNode)
		else:	
			print("=============== Printing Index Sets of Task: %d ==============="%(n+1))
			for index_set in range(0, len(TaskSetInfo[n].IndexSets)):
				print(">>>>>>>>>>>>>>>>>> Index Set Number:%d <<<<<<<<<<<<<<<<<<<<<<<<"%(index_set+1))
				for index in range(0, len(TaskSetInfo[n].IndexSets[index_set])):
					TaskSetInfo[n].IndexSets[index_set][index].Display()
			

def get_hyper_period(numbers):
	return reduce(lambda x, y: (x*y)/gcd(x,y), numbers, 1) 

def Vertex_in_List(vertex, List):
	for n in range(0, len(List)):
		if vertex.JID == List[n].JID:
			return True
	return False

def Vertex_ID_in_VertexList(ID, List, TID):
	for n in range(0, len(List)):
		if (TID == List[n].TID+1) and (ID == List[n].JID):
			return True
	return False

def UpdateSuccessors(TaskSetInfo):
	for n in range(0, len(TaskSetInfo)):
		for m in range(0, len(TaskSetInfo[n].Nodes)):			
			for p in range(0, len(TaskSetInfo[n].Nodes[m].Pred)):
				TaskSetInfo[n].Nodes[TaskSetInfo[n].Nodes[m].Pred[p]].Succ.clear()

	for n in range(0, len(TaskSetInfo)):
		for m in range(0, len(TaskSetInfo[n].Nodes)):			
			for p in range(0, len(TaskSetInfo[n].Nodes[m].Pred)):
				TaskSetInfo[n].Nodes[TaskSetInfo[n].Nodes[m].Pred[p]].Succ.append(TaskSetInfo[n].Nodes[m].JID)

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

def UpdateParallelVertices_of_EachVertex(TaskData, AllPaths, TaskSetInfo):
	TaskInfo = TaskData.Nodes

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
		
		for task in range(0, len(TaskSetInfo)):
			if TaskData.TID != TaskSetInfo[task].TID:
				for vtx in range(0, len(TaskSetInfo[task].Nodes)):
					if TaskSetInfo[task].Nodes[vtx].ResourceType == TaskInfo[vertex].ResourceType:
						TaskInfo[vertex].Par_v.append(TaskSetInfo[task].Nodes[vtx])

		CommonPaths.clear()
		UncommonPaths.clear()   
		TaskInfo[vertex].Par_v.sort(key=lambda v:v.TID)

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
			Task.Priority  = int(row[4])
			
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
			Node.ResourceType  = (int(row[7]))
			Node.Pred = [int(Node.Pred) for Node.Pred in row[8:] if Node.Pred != '']
			
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

		UpdateParallelVertices_of_EachVertex(TaskSetInfo[n], TaskSetInfo[n].AllPaths, TaskSetInfo)
		UpdateDescendants_of_EachVertex(TaskSetInfo[n].Nodes, TaskSetInfo[n].AllPaths) 
		UpdateAncestors_of_EachVertex(TaskSetInfo[n].Nodes, TaskSetInfo[n].AllPaths)

		if WANT_GRAPH == True:
			createTaskGraphFile(TaskSetInfo[n].Nodes, n+1, TaskSetInfo[n].CRP, TaskSetInfo[n].CRP_WCET, FileName)

	TotalJobsPerHyperPeriod = getTotalJobsPerHyperPeriod(TaskSetInfo)
	
	return (TaskSetInfo, TotalJobsPerHyperPeriod)

def ExtractAllResultRows(ResultsFile):
	# DMP = Deadline Missed Path
	global Current_Results_File_Data
	global Current_Deadline_Miss_Data

	print("ResultsFile: %s "%(ResultsFile))

	FP = open(ResultsFile, 'r')
	data = csv.reader(FP, skipinitialspace=True)
	
	Current_Results_File_Data.clear()

	for row in data:
		if "Jobs" in row[0]:
			Current_Results_File_Data.append(row)
		DMP = [int(DMP) for DMP in row[11:] if (DMP != '}')]
		if len(DMP) > 0:
			Current_Deadline_Miss_Data.append(DMP) 
	
def getTaskFilePath(JobsFile):
	lvFilePath = JobsFile.split('/')
	lvFile = lvFilePath[len(lvFilePath) - 1].split('_')
	
	TaskFilePath = ""
	for element in range(0, len(lvFilePath) - 1):
		TaskFilePath += lvFilePath[element] + '/'

	length = len(lvFile)
	TaskFile = ""

	for n in range(0, length-1):
		TaskFile += lvFile[n]
		if n < length-2:
			TaskFile += "_"
	TaskFile += ".csv"

	TaskFilePath += TaskFile
	return TaskFilePath

def getPredecessorName(JobsFile):
	lvFile = JobsFile.split('_')
	length = len(lvFile)
	PredFile = ""
	for n in range(0, length-1):
		PredFile += lvFile[n]+"_"
	PredFile += "Pred.csv"
	return PredFile

def getPredecessorPath(JobsFile):
	lvFile = JobsFile.split('/')
	length = len(lvFile)
	PredFile = ""
	for n in range(0, length-1):
		PredFile += lvFile[n]+"/"
	PredFile += getPredecessorName(lvFile[length-1])
	return PredFile

def UpdateIdxPar_V(index, TaskSetInfo):
	for Task in TaskSetInfo:
		if index.TID == Task.TID:
			for Node in Task.Nodes:
				if Node.JID == index.VTX_ID:
					# index.Par_v = copy.deepcopy(Node.Par_v)
					index.Par_v = Node.Par_v
					return

def UpdateParIndexOfEachIndex(IndexSet, TaskSetInfo):
	for idx in IndexSet:
		for task in TaskSetInfo:
			if task.TID == idx.TID:
				Pu = (math.ceil(idx.Deadline / idx.Period) - 1)
				for index in task.IndexSets[Pu]:
					if (Vertex_ID_in_VertexList(index.VTX_ID, idx.Par_v, task.TID)) == True:
						# print("1 T%dJ%d is in %s index:%d Added to Par_idx"\
						# 	%(index.TID,index.VTX_ID,Print_Pred_Succ_Par_Ancs_Desc(index.VTX_ID, idx.Par_v, "Par_idx", False), index.index))
						idx.Par_idx.append(index)
			else:
				Pu = math.ceil((idx.Deadline / task.Period)) # * task.Period [If needed range of deadlines then multiply]
				Pl = math.floor(((idx.Deadline - idx.Period) / task.Period)) # * task.Period [If needed range of deadlines then multiply]
				for indexset in range(Pl, Pu):
					for index in task.IndexSets[indexset]:
						if (Vertex_ID_in_VertexList(index.VTX_ID, idx.Par_v, task.TID)) == True:
							# print("2 T%dJ%d is in %s index:%d Added to Par_idx"\
							# 	%(index.TID,index.VTX_ID,Print_Pred_Succ_Par_Ancs_Desc(index.VTX_ID, idx.Par_v, "Par_idx", False), index.index))
							idx.Par_idx.append(index)

		idx.Par_idx.sort(key=lambda v:v.index)

def UpdateIndexPredecessors(index, TaskSetInfo):
	for Task in TaskSetInfo:
		if index.TID == Task.TID:
			Pu = (math.ceil(index.Deadline / index.Period) - 1)
			for Node in Task.Nodes:
				if index.VTX_ID == Node.JID:					
					for pred in range(0, len(Node.Pred)):
						index.Pred_idx.append(Task.IndexSets[Pu][Node.Pred[pred]])

	index.Pred_idx.sort(key=lambda v:v.index)

def ExtractJobsetFileData(JobsetFile, TaskSetInfo):
	#Row = TID, JID, r_min, r_max, BCET, WCET, Deadline, Priority, ResourceType

	IndexSet = []
	Index = 0

	FP = open(JobsetFile, 'r')
	data = csv.reader(FP, skipinitialspace=True)

	for row in data:
		indexdata = IndexData()
		if (row[0] == "Task ID") or (row[0] == "ResourceTypes") or ('M' in row[0]) or (row[0] == '#'):
			continue
		indexdata.index = Index
		indexdata.TID = int(row[0])
		indexdata.JID = int(row[1])
		indexdata.r_min = int(row[2])
		indexdata.r_max = int(row[3])
		indexdata.BCET = int(row[4])
		indexdata.WCET = int(row[5])
		indexdata.Period =  TaskSetInfo[indexdata.TID-1].Period
		indexdata.Deadline = int(row[6])
		indexdata.Priority = int(row[7])
		indexdata.ResourceType = int(row[8])
		IndexSet.append(indexdata)
		Index += 1

	for Task in TaskSetInfo:
		TaskIndexSet = []
		VTXID = 0
		for i in IndexSet:			
			if i.TID == Task.TID:
				i.VTX_ID = VTXID
				VTXID += 1				
				UpdateIdxPar_V(i, TaskSetInfo)
				TaskIndexSet.append(i)
			if (i.TID != Task.TID) and (len(TaskIndexSet) > 0):
				lvTaskIndexSet = copy.deepcopy(TaskIndexSet)
				Task.IndexSets.append(lvTaskIndexSet)
				TaskIndexSet.clear()
				VTXID = 0
		if len(TaskIndexSet) > 0:
			Task.IndexSets.append(TaskIndexSet)

	UpdateParIndexOfEachIndex(IndexSet, TaskSetInfo)
	
	# Update Parallel Indexes of Each Index
	for i in IndexSet:
		UpdateIndexPredecessors(i, TaskSetInfo)

	#Update Parallel Indexes from Each Index of Index Sets
	for Task in TaskSetInfo:
		for Index_Set in Task.IndexSets:
			for index in Index_Set:
				index.Par_idx = IndexSet[index.index].Par_idx 		#copy.deepcopy(IndexSet[index.index].Par_idx)
				index.Pred_idx = IndexSet[index.index].Pred_idx		#copy.deepcopy(IndexSet[index.index].Pred_idx)

	return IndexSet

def Execute_Test(TasksetFile, JobsetFile, PredFile):
	Results = TestResults()
	Results.Filename = TasksetFile

	TaskSetInfo = []
	ResponseTime_G = []
	IndexSet = []

	# Extracting Task set Details
	TaskSetInfo, Results.Jobs = ExtractTaskSetData(TasksetFile)
	IndexSet = ExtractJobsetFileData(JobsetFile, TaskSetInfo)

	# Printing Task set System Configurations
	PrintTaskSetData(TasksetFile, RSC_Type, Cores_Per_RSC_Type, TaskSetInfo, "IndexSets")

	return Results

def ReadFiles(directory):
	global Current_Deadline_Miss_Path
	JobFile  = ""
	PredFile = ""
	TaskFile = ""

	for dirName, subdirList, fileList in os.walk(directory):
		
		if len(fileList) > 0:

			if ("Results" in dirName or "Results" in directory) and ("SOA" not in dirName) and ("Visuals" not in dirName):
				ResultsFile = dirName+"/"+fileList[0]
				ExtractAllResultRows(ResultsFile)
				
				for row in range(0, len(Current_Deadline_Miss_Data)):
					if len(Current_Deadline_Miss_Data[row]) > 0:
						Current_Deadline_Miss_Path	=	Current_Deadline_Miss_Data[row]
						JobFile  = Current_Results_File_Data[row][0]
						PredFile = getPredecessorName(JobFile)
						TaskFile = getTaskFilePath(JobFile)
						print("Current_Deadline_Miss_Path:",Current_Deadline_Miss_Path)
						results = Execute_Test(TaskFile, JobFile, PredFile)

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
			if "SOA_Results" in dirName or "Results" in dirName or "FEASIBILITY" in dirName or "Visuals" in dirName:
				continue
			if len(fileList) > 0:
				ReadFiles(dirName)
	else:
		results = TestResults()
		results = Execute_Test(TASK_SET_FILE)
		results.DisplayResult()

	print("Finished all tests ... ")

if __name__ == '__main__': 
	main()