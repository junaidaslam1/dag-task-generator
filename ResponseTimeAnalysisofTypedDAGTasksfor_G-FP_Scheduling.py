'''
********** Response Time Analysis of Typed DAG Tasks for G-FP Scheduling *********
* Author:       Muhammad Junaid Aslam
* Contact:      junaidaslam1@gmail.com
* Rank:         Senior Embedded Software Designer
* Company:      ASML Semiconductors
*
* This software is a computer program whose purpose is to evaluate the
* performance of the titled method for schedulability analysis.
*
* ---------------------------------------------------------------------
* This software is governed by the No license. You can use, modify    |
* and redistribute the software under the condition of citing  	      |
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

MS_TO_US = 1000
TASK_SET_FILE = "Null"

SE	=	-1
PA	=	-2

DUMMY_NUMBER	=	99999999

RSC_Type = 0
Cores_Per_RSC_Type = []

REMOVE = None
SINGLE_DAG_ANALYSIS = None

def NUM_TO_STR(num):
	if num == SE:
		return 'SE'
	elif num == PA:
		return 'PA'
	else:
		return num

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

	parser.add_argument('-rm', '--remove', dest='remove', action='store_const', 
						const=True, required=False,
						help='This option removes task_set files after finishing the test')

	parser.add_argument('-s', '--single_dag', dest='single_dag', action='store_const', 
						const=True, required=False,
						help='This option enables analysis of single DAG in the directory of workloads')

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
		CopyTo.Par_v 		=	self.Par_v.copy()
		CopyTo.Desc 		=	self.Desc.copy()
		CopyTo.Ancs 		=	self.Ancs.copy()

	def DisplayData(self):
		print("T%dJ%d BCET:%d WCET:%d RSC:%d Deadline:%d Pred:"%(self.TID, self.JID, self.BCET, self.WCET, self.ResourceType, self.Deadline, self.Pred))

class TaskData:
	def __init__(self):
		self.TID 		= 	0
		self.Period 	=	0
		self.Priority 	= 	0
		self.Deadline 	= 	0
		self.CRP_WCET 	=	0
		self.VOL_G 		=	0
		self.TreeRoot	= 	0
		self.Ikk_WCRT	=	0
		self.WCRT		=	0
		self.Nodes 		= 	[]
		self.AllPaths 	= 	[]
		self.CRP 		= 	[]
		self.ID_Blocks	=	[]

	def DisplayData(self):
		print("T%d Period:%d Deadline:%d Number_of_Nodes:%d"%(self.TID, self.Period, self.Deadline, len(self.Nodes)))

	def ClearData(self):
		self.TID 		= 	0
		self.Period 	=	0
		self.Priority 	= 	0
		self.Deadline 	= 	0
		self.CRP_WCET 	=	0
		self.VOL_G 		=	0
		self.Ikk_WCRT	=	0
		self.WCRT		=	0
		self.Nodes.clear()
		self.AllPaths.clear() 
		self.CRP.clear()
		self.ID_Blocks.clear()

	def Copy(self, inTask):
		inTask.TID 			= self.TID
		inTask.Period 		= self.Period
		inTask.Priority		= self.Priority
		inTask.Deadline 	= self.Deadline
		inTask.CRP_WCET 	= self.CRP_WCET
		inTask.VOL_G 		= self.VOL_G
		inTask.Ikk_WCRT		= self.Ikk_WCRT
		inTask.WCRT 		= self.WCRT
		inTask.Nodes 		= self.Nodes.copy()
		inTask.AllPaths		= self.AllPaths.copy()
		inTask.CRP 			= self.CRP.copy()
		inTask.ID_Blocks	= self.ID_Blocks.copy()

class VertexTuple:
	def __init__(self):
		self.vertex = NodeData()
		self.Delta = []
		self.ResponseTime = 0

class TreeNode: 
	def __init__(self, key): 
		self.key = key
		self.left = None
		self.right = None

	def display(self):
		lines, _, _, _ = self._display_aux()
		for line in lines:
			print(line)

	def _display_aux(self):
		"""Returns list of strings, width, height, and horizontal coordinate of the root."""
		# No child.
		try:
			if self.right is None and self.left is None:
				# if self.key != None:
				key = NUM_TO_STR(self.key)
				if key != 'SE' and key != 'PA' and key != None:
					line = 'J%s' % key
				else:
					line = '%s' % key
				width = len(line)
				height = 1
				middle = width // 2
				return [line], width, height, middle
		except NameError:
			pass

		try:
			# Only left child.
			if self.right is None:
				if self.left != None:
					lines, n, p, x = self.left._display_aux()
				# if self.key != None:
				key = NUM_TO_STR(self.key)
				if key != 'SE' and key != 'PA' and key != None:
					s = 'J%s' % key
				else:
					s = '%s' % key
				# s = 'J%s' % NUM_TO_STR(self.key)
				u = len(s)
				first_line = (x + 1) * ' ' + (n - x - 1) * '_' + s
				second_line = x * ' ' + '/' + (n - x - 1 + u) * ' '
				shifted_lines = [line + u * ' ' for line in lines]
				return [first_line, second_line] + shifted_lines, n + u, p + 2, n + u // 2
		except NameError:
			pass


		try:
			# Only right child.
			if self.left is None:
				if self.right != None:
					lines, n, p, x = self.right._display_aux()
				# if self.key != None:
				key = NUM_TO_STR(self.key)
				if key != 'SE' and key != 'PA' and key != None:
					s = 'J%s' % key
				else:
					s = '%s' % key
				# s = 'J%s' % NUM_TO_STR(self.key)
				u = len(s)
				first_line = s + x * '_' + (n - x) * ' '
				second_line = (u + x) * ' ' + '\\' + (n - x - 1) * ' '
				shifted_lines = [u * ' ' + line for line in lines]
				return [first_line, second_line] + shifted_lines, n + u, p + 2, u // 2
		except NameError:
			pass

		try:
			# Two children.
			if (self.left != None):
				left, n, p, x = self.left._display_aux()
			if (self.right != None):
				right, m, q, y = self.right._display_aux()
			# if self.key != None:
			key = NUM_TO_STR(self.key)
			if key != 'SE' and key != 'PA' and key != None:
				s = 'J%s' % key
			else:
				s = '%s' % key

			u = len(s)
			first_line = (x + 1) * ' ' + (n - x - 1) * '_' + s + y * '_' + (m - y) * ' '
			second_line = x * ' ' + '/' + (n - x - 1 + u + y) * ' ' + '\\' + (m - y - 1) * ' '
			if p < q:
				left += [n * ' '] * (q - p)
			elif q < p:
				right += [m * ' '] * (p - q)
			zipped_lines = zip(left, right)
			lines = [first_line, second_line] + [a + u * ' ' + b for a, b in zipped_lines]
			return lines, n + m + u, max(p, q) + 2, n + u // 2
		except NameError:
			pass

class ID_Block:
	def __init__(self):
		self.Width = 0
		self.Height = 0

def PrintTaskSetData(RSC_Type, Cores_Per_RSC_Type, TaskSetInfo, PrintFull=False):

	print("RSC_Type:%d"%RSC_Type)
	for n in range(0,RSC_Type):
		print("CORES_OF_%d = %d"%(n+1,Cores_Per_RSC_Type[n]))

	print("Number of Tasks:%d"%len(TaskSetInfo))

	if PrintFull == True:
		for n in range(0, len(TaskSetInfo)):
			print("Task:%d Period:%d Deadline:%d CRP_WCET:%d"%(TaskSetInfo[n].TID,TaskSetInfo[n].Period, TaskSetInfo[n].Deadline, TaskSetInfo[n].CRP_WCET))
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

def PrintVertexPathRelation(vertex, Path, Found=False):
	printPath = "{"
	for m in range(0, len(Path)):
		printPath += str(Path[m].JID)+", "
	printPath += "}"
	if Found == True:
		print("-----------------------")
		print("Vertex:%d Found in Path:%s"%(vertex.JID, printPath))
	else:
		print("-----------------------")
		print("Vertex:%d Not in Path:%s"%(vertex.JID, printPath))

def PrintVertex_Par_v(vertex, PRINT=False):
	printPar_v = "{"
	for m in range(0, len(vertex.Par_v)):
		printPar_v += "J"+str(vertex.Par_v[m].JID)+", "
	printPar_v += "}"
	if PRINT == True:
		print("-----------------------")
		print("Vertex:%d Par_v:%s"%(vertex.JID, printPar_v))
	return printPar_v

def PrintVertex_Desc(vertex, PRINT=False):
	printDesc = "{"
	for m in range(0, len(vertex.Desc)):
		printDesc += "J"+str(vertex.Desc[m].JID)+", "
	printDesc += "}"
	if PRINT == True:
		print("-----------------------")
		print("Vertex:%d Descendants:%s"%(vertex.JID, printDesc))
	return printDesc

def PrintVertex_Ancs(vertex, PRINT=False):
	vtxPred = PrintList_Pred_Succ(vertex.Pred)
	printAncs = "{" + vtxPred + " "
	for m in range(0, len(vertex.Ancs)):
		printAncs += "J"+str(vertex.Ancs[m].JID)+", "
	printAncs += "}"
	if PRINT == True:
		print("-----------------------")
		print("Vertex:%d Ancestors:%s"%(vertex.JID, printAncs))
	return printAncs

def PrintList_Pred_Succ(List, PRINT=False):
	PrintList = "Pred {"
	if len(List) > 1:
		for n in range(0, len(List)):
			PrintList += str(List[n])+","
	elif len(List) == 1:
		PrintList += str(List[0])+","
	PrintList += "}"
	if PRINT == True:
		print(PrintList)
	return PrintList

def PrintList(List, PRINT=False):
	PrintList = "{"
	for n in range(0, len(List)):
		PrintList += str(List[n].JID)+","
	PrintList += "}"
	if PRINT == True:
		print(PrintList)
	return PrintList

def PrintTuple(iTuple_t, PredTuple):
	printPar_v = PrintVertex_Par_v(iTuple_t.vertex)
	printDesc = PrintVertex_Desc(iTuple_t.vertex)
	printAncs = PrintVertex_Desc(iTuple_t.vertex)
	printDelta = "{"
	for n in range(0, len(iTuple_t.Delta)):
		printDelta += str(iTuple_t.Delta[n].JID) + ","
	printDelta += "}"
	print("Vertex:%d WCRT:%d Delta:%s Par_v:%s Descendants:%s Ancestors:%s PredVertex:%d PredWCRT:%d" \
		%(iTuple_t.vertex.JID, iTuple_t.ResponseTime, printDelta, printPar_v, printDesc, printAncs, PredTuple.vertex.JID, PredTuple.ResponseTime))
	print("------------") 

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

def Vertex_in_List(vertex, List):
	for n in range(0, len(List)):
		if vertex.JID == List[n].JID:
			return True
	return False

def UpdateParallelVertices_of_EachVertex(TaskInfo):
	for vertex in range(0, len(TaskInfo.Nodes)):
		TaskInfo.Nodes[vertex].Par_v.clear()
		CommonPaths = []
		UncommonPaths = []

		for path in range(0, len(TaskInfo.AllPaths)):
			if (Vertex_in_List(TaskInfo.Nodes[vertex], TaskInfo.AllPaths[path]) == False):
				UncommonPaths.append(TaskInfo.AllPaths[path])
				# PrintVertexPathRelation(TaskInfo.Nodes[vertex], TaskInfo.AllPaths[path], False)
			else:
				CommonPaths.append(TaskInfo.AllPaths[path])
				# PrintVertexPathRelation(TaskInfo.Nodes[vertex], TaskInfo.AllPaths[path], True)

		for uPath in range(0, len(UncommonPaths)):
			for uVertex in range(0, len(UncommonPaths[uPath])):
				if (UncommonPaths[uPath][uVertex].ResourceType == TaskInfo.Nodes[vertex].ResourceType):
					SkipVertex = False
					for cPath in range(0, len(CommonPaths)):
						for cVertex in range(0, len(CommonPaths[cPath])):
							if ((UncommonPaths[uPath][uVertex].JID == CommonPaths[cPath][cVertex].JID) == True):
								SkipVertex = True
								break
						if SkipVertex == True:
							break
					if SkipVertex == False:
						if (Vertex_in_List(UncommonPaths[uPath][uVertex], TaskInfo.Nodes[vertex].Par_v) == False):
							TaskInfo.Nodes[vertex].Par_v.append(UncommonPaths[uPath][uVertex])
		
		CommonPaths.clear()
		UncommonPaths.clear()	
		# PrintVertex_Par_v(TaskInfo.Nodes[vertex], True)
		TaskInfo.Nodes[vertex].Par_v.sort(key=lambda v:v.JID)

def UpdateDescendants_of_EachVertex(TaskInfo):
	for vertex in range(0, len(TaskInfo.Nodes)):
		TaskInfo.Nodes[vertex].Desc.clear()	
		CommonPaths = []
		for path in range(0, len(TaskInfo.AllPaths)):
			if (Vertex_in_List(TaskInfo.Nodes[vertex], TaskInfo.AllPaths[path]) == True):
				CommonPaths.append(TaskInfo.AllPaths[path])
						
		for path in range(0, len(CommonPaths)):		
			for uVertex in range(0, len(CommonPaths[path])):
				if CommonPaths[path][uVertex].JID > TaskInfo.Nodes[vertex].JID:
					if (Vertex_in_List(CommonPaths[path][uVertex], TaskInfo.Nodes[vertex].Desc) == False):
						TaskInfo.Nodes[vertex].Desc.append(CommonPaths[path][uVertex])
		CommonPaths.clear()
		TaskInfo.Nodes[vertex].Desc.sort(key=lambda v:v.JID)
		# PrintVertex_Desc(TaskInfo.Nodes[vertex], True)

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

def UpdateVol_G(TaskInfo):
	VOL_G = 0
	for vertex in range(0, len(TaskInfo.Nodes)):
		VOL_G += TaskInfo.Nodes[vertex].WCET
	TaskInfo.VOL_G = VOL_G
	
def get_Min_Job_Exec_Time(TaskInfo):
	Body_Job_Exec_Time = 0

	for RSC in range(0, RSC_Type):
		VOL_s_G = 0
		for v in range(0, len(TaskInfo.Nodes)):
			if TaskInfo.Nodes[v].ResourceType == RSC+1:
				VOL_s_G += TaskInfo.Nodes[v].WCET
	
		Body_Job_Exec_Time += (VOL_s_G/Cores_Per_RSC_Type[RSC])

	return Body_Job_Exec_Time	

def getBodyJobInt(Nr_Of_Body_Jobs, TaskInfo):
	return (Nr_Of_Body_Jobs*get_Min_Job_Exec_Time(TaskInfo))

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
	RSC_Type = 0
	Cores_Per_RSC_Type = {}
	TaskSetInfo = []
	counter = 0
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
			Cores_Per_RSC_Type[counter] = cores
			counter = counter + 1
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

	TotalJobsPerHyperPeriod = getTotalJobsPerHyperPeriod(TaskSetInfo)

	for Task in range(0, len(TaskSetInfo)):
		UpdateParallelVertices_of_EachVertex(TaskSetInfo[Task])
		UpdateDescendants_of_EachVertex(TaskSetInfo[Task])
		UpdateAncestors_of_EachVertex(TaskSetInfo[Task])
		UpdateVol_G(TaskSetInfo[Task])

	TaskSetInfo.sort(key=lambda v:v.Priority)
	
	return (RSC_Type, Cores_Per_RSC_Type, TaskSetInfo, TotalJobsPerHyperPeriod)

def GetWCETSumPar_v(InputVertex, PredDelta, Cores_Per_RSC_Type):
	WCET_SUM = 0.0

	SelectedPar_v = []
	ClosestNode = NodeData()

	for n in reversed(range(len(PredDelta))):
		if InputVertex.ResourceType == PredDelta[n].ResourceType:
			PredDelta[n].Copy(ClosestNode)
			# print("Vertex:%d ClosestNode:%d"%(InputVertex.JID, ClosestNode.JID))
			break

	for n in range(0, len(InputVertex.Par_v)):
		Conflict = False
		for m in range(0, len(ClosestNode.Par_v)):
			if ClosestNode.Par_v[m].JID == InputVertex.Par_v[n].JID:
				Conflict = True
				break
		if Conflict == False:
			SelectedPar_v.append(InputVertex.Par_v[n])

	for n in range(0, len(SelectedPar_v)):
		WCET_SUM += float(SelectedPar_v[n].WCET/Cores_Per_RSC_Type[SelectedPar_v[n].ResourceType-1])

	return WCET_SUM

def GetPathDelta(vertex, PredDelta, RSC_Type):
	Delta = []
	
	for RSC in range(1, RSC_Type+1):
		if vertex.ResourceType == RSC:
			Delta.append(vertex) 
		else:
			for v in reversed(range(len(PredDelta))):
				if PredDelta[v].ResourceType == RSC:
					Delta.append(PredDelta[v])
					break
	
	Delta.sort(key=lambda v:v.JID)

	return Delta

def RemoveTuples(TupleSet, ParentIDs):
	for m in range(0, len(ParentIDs)):
		for n in range(0, len(TupleSet)):
			if ParentIDs[m] == TupleSet[n].vertex.JID:
				# print("Removing Tuple:%d"%TupleSet[n].vertex.JID)
				TupleSet.remove(TupleSet[n])
				break

def DeltaIntersection(ExistingDelta, NewDelta):
	'''
	If any Par_v of any vertex of ExistingDelta matches descendants 
	of any vertex of NewDelta then return True else False
	'''
	for ed in range(0, len(ExistingDelta)):
		for par_v in range(0, len(ExistingDelta[ed].Par_v)):
			for nd in range(0, len(NewDelta)):
				for desc in range(0, len(NewDelta[nd].Desc)):
					if NewDelta[nd].Desc[desc].ResourceType == ExistingDelta[ed].ResourceType:
						if NewDelta[nd].Desc[desc].JID == ExistingDelta[ed].Par_v[par_v].JID:						
							# print("DeltaIntersection Found")
							return True 
	return False

def If_Tuple_Already_Dominated(iTuple_t, TupleSet, RSC_Type):
	for Tuple in range(0, len(TupleSet)):
		if TupleSet[Tuple].vertex.JID == iTuple_t.vertex.JID:
			if TupleSet[Tuple].ResponseTime >= iTuple_t.ResponseTime:
				if len(TupleSet[Tuple].Delta) == 0:
					# print("Short Tuple:%d -> WCRT:%d Dominated by:%d -> WCRT:%d"%(iTuple_t.vertex.JID, iTuple_t.ResponseTime, TupleSet[Tuple].vertex.JID, TupleSet[Tuple].ResponseTime))
					return True
				elif (len(TupleSet[Tuple].Delta) != 0) and (len(iTuple_t.Delta) != 0) and (DeltaIntersection(TupleSet[Tuple].Delta, iTuple_t.Delta) == False):
					# print("Long Tuple:%d -> WCRT:%d Dominated by:%d -> WCRT:%d"%(iTuple_t.vertex.JID, iTuple_t.ResponseTime, TupleSet[Tuple].vertex.JID, TupleSet[Tuple].ResponseTime))
					return True
	return False

def All_Tuples_are_Sink_Nodes(TupleSet, TaskInfo):
	Result = list(filter(lambda Tuple:(Tuple.vertex.JID != TaskInfo.Nodes[len(TaskInfo.Nodes)-1].JID), TupleSet))
	if len(Result) > 0:
		return False
	return True

def GetMaxRPi(RSC_Type, Cores_Per_RSC_Type, TaskInfo):
	MaxRPi = 0
	TupleSet = []

	iTuple = VertexTuple()
	iTuple.vertex 		= TaskInfo.Nodes[0]
	iTuple.Delta.append(TaskInfo.Nodes[0])
	iTuple.ResponseTime = TaskInfo.Nodes[0].WCET
	TupleSet.append(iTuple)

	while (len(TupleSet) > 0) and (All_Tuples_are_Sink_Nodes(TupleSet, TaskInfo) == False):

		ParentIDs = []
		
		for Tuple in range(0, len(TupleSet)):
			if len(TupleSet[Tuple].vertex.Succ) > 0:
				ParentIDs.append(TupleSet[Tuple].vertex.JID)
			for successor in range(0, len(TupleSet[Tuple].vertex.Succ)):
				iTuple_t = VertexTuple()
				iTuple_t.vertex = TaskInfo.Nodes[TupleSet[Tuple].vertex.Succ[successor]]
				iTuple_t.Delta = GetPathDelta(iTuple_t.vertex, TupleSet[Tuple].Delta, RSC_Type)
				iTuple_t.ResponseTime = TupleSet[Tuple].ResponseTime + iTuple_t.vertex.WCET + GetWCETSumPar_v(iTuple_t.vertex, TupleSet[Tuple].Delta, Cores_Per_RSC_Type)
				if If_Tuple_Already_Dominated(iTuple_t, TupleSet, RSC_Type) == False:
					TupleSet.append(iTuple_t)
				# PrintTuple(iTuple_t, TupleSet[Tuple])
			
		RemoveTuples(TupleSet, ParentIDs)

	for Tuple in range(0, len(TupleSet)):
		if TupleSet[Tuple].ResponseTime > MaxRPi:
			MaxRPi = TupleSet[Tuple].ResponseTime

	return MaxRPi 

def UpdateIntraTaskResponseTimes(RSC_Type, Cores_Per_RSC_Type, TaskSetInfo):
	for TaskInfo in range(0, len(TaskSetInfo)):
		TaskSetInfo[TaskInfo].Ikk_WCRT	=	GetMaxRPi(RSC_Type, Cores_Per_RSC_Type, TaskSetInfo[TaskInfo])
		TaskSetInfo[TaskInfo].WCRT 		=	TaskSetInfo[TaskInfo].Ikk_WCRT
		
def Convert_to_NFJ_DAG(TaskInfo, CriticalPaths):
	cNodes = TaskInfo.Nodes
	for vertex in range(0, len(cNodes)):
		lvPredLen = len(cNodes[vertex].Pred)
		# print("Vertex:%d lv_Predlength:%d"%(cNodes[vertex].JID, lvPredLen))
		# PrintList_Pred_Succ(cNodes[vertex].Pred, True)

		if len(cNodes[vertex].Pred) > 1: 
		   
			PredLen = len(cNodes[vertex].Pred)

			for pred in reversed(range(PredLen)):

				lvPredVertex = cNodes[cNodes[vertex].Pred[pred]]
				ConflictingEdge = False

				for succ in range(0, len(lvPredVertex.Succ)):
					if (lvPredVertex.Succ[succ] != cNodes[vertex].JID) \
					and (Vertex_in_List(cNodes[lvPredVertex.Succ[succ]], cNodes[vertex].Ancs) == False):
						ConflictingEdge = True
						break

				if (ConflictingEdge == True):
						# print("1 Removing connection between J%d <--> J%d"%(cNodes[vertex].JID, cNodes[vertex].Pred[pred]))
						cNodes[cNodes[vertex].Pred[pred]].Succ.remove(cNodes[vertex].JID)
						cNodes[vertex].Pred.remove(cNodes[vertex].Pred[pred])
						# Update Necessary Task Information
						TaskInfo.CRP, TaskInfo.CRP_WCET, TaskInfo.AllPaths = getTaskCriticalPathInfo(TaskInfo.Nodes)
						UpdateAncestors_of_EachVertex(TaskInfo)
						PredLen = PredLen - 1
						if(PredLen == 1):
							break
				
				if ConflictingEdge == False:
					lvPredLen = len(cNodes[vertex].Pred)
					for p in reversed(range(lvPredLen)):
						if cNodes[vertex].Pred[p] in lvPredVertex.Pred:
							# print("2 Removed connection between J%d <--> J%d"%(cNodes[vertex].JID, cNodes[vertex].Pred[p]))							
							cNodes[cNodes[vertex].Pred[p]].Succ.remove(cNodes[vertex].JID)
							cNodes[vertex].Pred.remove(cNodes[vertex].Pred[p])
							# Update Necessary Task Information
							TaskInfo.CRP, TaskInfo.CRP_WCET, TaskInfo.AllPaths = getTaskCriticalPathInfo(TaskInfo.Nodes)							
							UpdateAncestors_of_EachVertex(TaskInfo)
							lvPredLen = lvPredLen - 1
							PredLen = PredLen - 1
							if(PredLen == 1):
								break

				if PredLen > 1:
					for n in reversed(range(PredLen)):
						for vtx in reversed(range(PredLen)):
							if (Vertex_in_List(cNodes[cNodes[vertex].Pred[n]], cNodes[cNodes[vertex].Pred[vtx]].Ancs) == True):
								# print("ConflictingEdge:J%d <---> J%d"%(cNodes[cNodes[vertex].Pred[n]].JID, cNodes[vertex].JID))
								cNodes[cNodes[vertex].Pred[n]].Succ.remove(cNodes[vertex].JID)
								cNodes[vertex].Pred.remove(cNodes[vertex].Pred[n])
								# Update Necessary Task Information
								TaskInfo.CRP, TaskInfo.CRP_WCET, TaskInfo.AllPaths = getTaskCriticalPathInfo(cNodes)
								UpdateAncestors_of_EachVertex(TaskInfo)
								PredLen = PredLen - 1
								if(PredLen == 1):
									break

						if(PredLen == 1):
								break 

				if(PredLen == 1):
					break


def getNFJ_DAG_TaskInfo(TaskSetInfo):
	NFJ_DAG_TaskSetInfo = []
	Converted_TaskSetInfo = copy.deepcopy(TaskSetInfo)
	# PrintTaskSetData(RSC_Type, Cores_Per_RSC_Type, TaskSetInfo, True)
	for Task in range(0, len(Converted_TaskSetInfo)):
		# print("----------- > > > Task:%d Convert to NFJ_DAG"%(Task+1))
		Convert_to_NFJ_DAG(Converted_TaskSetInfo[Task], Converted_TaskSetInfo[Task].CRP)
	# PrintTaskSetData(RSC_Type, Cores_Per_RSC_Type, Converted_TaskSetInfo, True)
	return Converted_TaskSetInfo

def newTreeNode(ID, left=0, right=0):
	Tree_Node = TreeNode(ID)
	if left != 0:
		Tree_Node.left = left
	if right !=0:
		Tree_Node.right = right
	return Tree_Node

def Is_Already_in_Binary_Tree(VertexID, TreeRoot):
	# print("Search:%d vs %s"%(VertexID, NUM_TO_STR(TreeRoot.key)))
	if TreeRoot.key == VertexID:
		return True
	if (TreeRoot.left != None) and (Is_Already_in_Binary_Tree(VertexID, TreeRoot.left)==True):
		return True
	if (TreeRoot.right != None) and (Is_Already_in_Binary_Tree(VertexID, TreeRoot.right)==True):
		return True

	return False

def isJoinNodeCommonForSuccessors(TaskInfo, VTX):
	Nodes = TaskInfo.Nodes

	if len(VTX.Succ) > 1:
		Join = 0
		Join_VTX_ID = Nodes[VTX.Succ[0]].Succ[0]
		for n in range(1, len(VTX.Succ)):
			if Join_VTX_ID != Nodes[VTX.Succ[n]].Succ[0]:
				return False
		return True

# This returns common join node of the successors of node VTX
def getCommonJoinVTX(TaskInfo, VTX):
	Nodes = TaskInfo.Nodes
	return Nodes[Nodes[VTX.Succ[0]].Succ[0]]

def isJoinCommonForMultipleVTX(VTX=[]):
	Join = VTX[0].Succ[0]
	for v in range(0, len(VTX)):
		if Join != VTX[v].Succ[0]:
			return False
	return True

# We can have Parallel_Plain (PA_P), Parallel_Not_Plain (PA_NP), and Series (SE) type next Nodes
def UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode, VTX = [], VTX_Type = "PA_NP"):
	# print("Type:%s Num_Vertices:%d First_VTX_ID:%d"%(VTX_Type, len(VTX), VTX[0].JID))
	Nodes = TaskInfo.Nodes

	if (VTX_Type == "PA_P") and (len(VTX) == 2):
		RootNode.left  = newTreeNode(VTX[0].JID)
		RootNode.right = newTreeNode(VTX[1].JID)

	elif (VTX_Type == "PA_P") and (len(VTX) > 2):
		RootNode.left  = newTreeNode(VTX[0].JID)
		# print("PA_P RootNode.left:%d Remaining:%d"%(VTX[0].JID, len(VTX)-1))
		VTX.pop(0)
		RootNode.right = newTreeNode(PA)
		UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right, VTX, "PA_P")

	elif (VTX_Type == "PA_NP") and len(VTX) == 2:
		if Is_Already_in_Binary_Tree(VTX[0].Succ[0], TreeRoot) == True:
			RootNode.left = newTreeNode(VTX[0].JID)
			VTX.pop(0)
			RootNode.right = newTreeNode(SE)
			UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right, VTX, "SE")
		elif Is_Already_in_Binary_Tree(VTX[1].Succ[0], TreeRoot) == True:
			RootNode.left = newTreeNode(VTX[1].JID)
			VTX.pop(1)
			RootNode.right = newTreeNode(SE)
			UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right, VTX, "SE")
		else:
			if (VTX[0].Succ[0] == Nodes[VTX[1].Succ[0]].Succ[0]):
				RootNode.left = newTreeNode(SE)
				RootNode.right = newTreeNode(SE)
				lvVTX1 = []
				lvVTX1.append(VTX[0])
				VTX.pop(0)
				UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.left, lvVTX1, "SE")
				UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right, VTX, "SE")
			elif (VTX[1].Succ[0] == Nodes[VTX[0].Succ[0]].Succ[0]):
				RootNode.left = newTreeNode(SE)
				RootNode.right = newTreeNode(SE)
				lvVTX1 = []
				lvVTX1.append(VTX[0])
				VTX.pop(0)
				UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.left, VTX, "SE")
				UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right, lvVTX1, "SE")
			else:
				RootNode.left = newTreeNode(SE)
				RootNode.right = newTreeNode(SE)
				lvVTX1 = []
				lvVTX1.append(VTX[0])
				VTX.pop(0)
				UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.left, lvVTX1, "SE")
				UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right, VTX, "SE")

	elif (VTX_Type == "PA_NP") and len(VTX) > 2:
		Found_Leaf = False
		for v in range(0, len(VTX)):
			if Is_Already_in_Binary_Tree(VTX[v].Succ[0], TreeRoot) == True:
				RootNode.left = newTreeNode(VTX[v].JID)
				# print("Found Leaf:%d Remaining VXTs:%d"%(VTX[v].JID, len(VTX)-1))
				VTX.pop(v)
				Found_Leaf = True
				break
		if Found_Leaf:			
			# PrintList(VTX, True)
			if len(VTX) >= 2 and (isJoinCommonForMultipleVTX(VTX) == False):
				RootNode.right = newTreeNode(PA)
				UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right, VTX, "PA_NP")
			elif len(VTX) >= 2 and (isJoinCommonForMultipleVTX(VTX) == True) and (Is_Already_in_Binary_Tree(VTX[0].Succ[0], TreeRoot)==False):
				# print("Yes Common Join %d not in tree"%VTX[0].Succ[0])
				if Is_Already_in_Binary_Tree(Nodes[VTX[0].Succ[0]].Succ[0], TreeRoot) == True: 
					RootNode.right = newTreeNode(SE, newTreeNode(PA), newTreeNode(VTX[0].Succ[0]))
					UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right.left, VTX, "PA_P")
				else:
					RootNode.right = newTreeNode(SE, newTreeNode(PA), newTreeNode(SE))
					UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right.left, VTX, "PA_P")
					lvVTX1 = []
					lvVTX1.append(Nodes[VTX[0].Succ[0]])
					UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right.right, lvVTX1, "SE")
			elif len(VTX) >= 2 and (isJoinCommonForMultipleVTX(VTX) == True) and (Is_Already_in_Binary_Tree(VTX[0].Succ[0], TreeRoot)==True):
				# print("Yes Common Join %d is in tree"%VTX[0].Succ[0])
				RootNode.right = newTreeNode(PA)
				UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right, VTX, "PA_P")
			elif len(VTX) == 1:
				RootNode.right = newTreeNode(SE)
				UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right, VTX, "SE")
		else:
			RootNode.right = newTreeNode(SE)
			lvVTX = []
			lvVTX.append(VTX[0])
			# print("Created Series Nodes with the first:%d "%VTX[0].JID)
			UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right, lvVTX, "SE")
			VTX.pop(0)
			RootNode.left = newTreeNode(PA)
			# print("Created PA_NP Nodes with the first:%d "%VTX[0].JID)
			UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.left, VTX, "PA_NP")

	elif (VTX_Type == "SE"):

		RootNode.left = newTreeNode(VTX[0].JID) # Todo start debug here
		# print("Input SE_VTX_ID:%d"%VTX[0].JID)

		if len(VTX[0].Succ) > 1: # it is a fork node
			
			lvVTX = []
			for n in range(0, len(VTX[0].Succ)):
				lvVTX.append(Nodes[VTX[0].Succ[n]])
			
			if (isJoinNodeCommonForSuccessors(TaskInfo, VTX[0]) == True):
				# print("SE VTX[0].JID:%d ForkNum_0f_Succ:%d Common Join VTX ID:%d"%(VTX[0].JID, len(VTX[0].Succ), getCommonJoinVTX(TaskInfo, VTX[0]).JID))
				if (Is_Already_in_Binary_Tree(getCommonJoinVTX(TaskInfo, VTX[0]).JID, TreeRoot) == False):
					
					if Is_Already_in_Binary_Tree(getCommonJoinVTX(TaskInfo, VTX[0]).Succ[0], TreeRoot) == True:
						RootNode.right = newTreeNode(SE, newTreeNode(PA), newTreeNode(getCommonJoinVTX(TaskInfo, VTX[0]).JID))
						# print("1 Creating PA_P with %d lvVTX"%len(lvVTX))
						UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right.left, lvVTX, "PA_P")
					else:
						RootNode.right = newTreeNode(SE, newTreeNode(PA), newTreeNode(SE))
						lvVTX1 = []
						lvVTX1.append(getCommonJoinVTX(TaskInfo, VTX[0]))
						UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right.right, lvVTX1, "SE")
						# print("2 Creating PA_P with %d lvVTX"%len(lvVTX))
						UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right.left, lvVTX, "PA_P")
				else:
					RootNode.right = newTreeNode(PA)
					UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right, lvVTX, "PA_P")

			else: # Join node is not common
				# print("Succ of %d has no common Join Releasing PA_NP"%VTX[0].JID)
				RootNode.right = newTreeNode(PA)
				UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right, lvVTX, "PA_NP")

		else: # It is not a fork node
			if Is_Already_in_Binary_Tree(Nodes[VTX[0].Succ[0]].Succ[0], TreeRoot) == True:
				# print("No further successors, simply leaf: VTX:%d VTX_Succ:%d VTX_Succ_Succ:%d"%(VTX[0].JID, VTX[0].Succ[0], Nodes[VTX[0].Succ[0]].Succ[0]))
				RootNode.right = newTreeNode(VTX[0].Succ[0])
			else:
				lvVTX = []
				RootNode.right = newTreeNode(SE)
				lvVTX.append(Nodes[VTX[0].Succ[0]])
				UpdateTaskDecompositionTree(TreeRoot, TaskInfo, RootNode.right, lvVTX, "SE")				
	
def Update_NFJ_DAG_DecompositionTree(NFJ_DAG_TaskSetInfo):
	for TaskInfo in range(0, len(NFJ_DAG_TaskSetInfo)):

		VTX_Type = ""
		VTX = []
		lvTaskInfo = NFJ_DAG_TaskSetInfo[TaskInfo]
		Nr_of_Nodes = len(lvTaskInfo.Nodes)
		RootNode = None
		
		# print("------------------ NFJ_DAG_TASK:%d Binary Decomposition Tree----Len(Nodes):%d--"%(lvTaskInfo.TID, Nr_of_Nodes))

		if Nr_of_Nodes < 1:
			return False
		elif Nr_of_Nodes == 1: 
			lvTaskInfo.TreeRoot = newTreeNode(SE, newTreeNode(lvTaskInfo.Nodes[0].JID), newTreeNode(SE))
		elif Nr_of_Nodes == 2: 
			lvTaskInfo.TreeRoot = newTreeNode(SE, newTreeNode(lvTaskInfo.Nodes[0].JID), newTreeNode(lvTaskInfo.Nodes[len(lvTaskInfo.Nodes)-1].JID))
		elif Nr_of_Nodes == 3:
			lvTaskInfo.TreeRoot = newTreeNode(SE, newTreeNode(lvTaskInfo.Nodes[0].JID),\
			 newTreeNode(SE, newTreeNode(lvTaskInfo.Nodes[len(lvTaskInfo.Nodes)-2].JID), newTreeNode(lvTaskInfo.Nodes[len(lvTaskInfo.Nodes)-1].JID)))
		else:
			SecondLastPredID = 0
			for n in range(0, len(lvTaskInfo.Nodes[len(lvTaskInfo.Nodes)-1].Pred)):
				if len(lvTaskInfo.Nodes[lvTaskInfo.Nodes[len(lvTaskInfo.Nodes)-1].Pred[n]].Pred) > 1: # Join node
					SecondLastPredID = lvTaskInfo.Nodes[len(lvTaskInfo.Nodes)-1].Pred[n]
					break

			if len(lvTaskInfo.Nodes[0].Succ) > 1:
						
				if isJoinNodeCommonForSuccessors(lvTaskInfo, lvTaskInfo.Nodes[0]) == False:
				
					VTX_Type = "PA_NP"
				
					for succ in range(0, len(lvTaskInfo.Nodes[0].Succ)):
						VTX.append(lvTaskInfo.Nodes[lvTaskInfo.Nodes[0].Succ[succ]])

					if SecondLastPredID == 0:
						lvTaskInfo.TreeRoot = newTreeNode(SE, newTreeNode(lvTaskInfo.Nodes[0].JID),\
							newTreeNode(SE, newTreeNode(PA), newTreeNode(lvTaskInfo.Nodes[len(lvTaskInfo.Nodes)-1].JID)))
					else:
						lvTaskInfo.TreeRoot = newTreeNode(SE, newTreeNode(lvTaskInfo.Nodes[0].JID),\
							newTreeNode(SE, newTreeNode(PA), newTreeNode(SE, newTreeNode(SecondLastPredID), newTreeNode(lvTaskInfo.Nodes[len(lvTaskInfo.Nodes)-1].JID))))
					
					RootNode 	 	= lvTaskInfo.TreeRoot.right.left	

					UpdateTaskDecompositionTree(lvTaskInfo.TreeRoot, lvTaskInfo, RootNode, VTX, VTX_Type)

				else:
					CommonSuccessorJoinVTX = getCommonJoinVTX(lvTaskInfo, lvTaskInfo.Nodes[0])
					VTX_Type = "PA_P"
					
					for succ in range(0, len(lvTaskInfo.Nodes[0].Succ)):
						VTX.append(lvTaskInfo.Nodes[lvTaskInfo.Nodes[0].Succ[succ]])

					if SecondLastPredID == 0:
						lvTaskInfo.TreeRoot = newTreeNode(SE, newTreeNode(lvTaskInfo.Nodes[0].JID),\
							newTreeNode(SE, newTreeNode(PA), newTreeNode(lvTaskInfo.Nodes[len(lvTaskInfo.Nodes)-1].JID)))
					else:
						lvTaskInfo.TreeRoot = newTreeNode(SE, newTreeNode(lvTaskInfo.Nodes[0].JID),\
							newTreeNode(SE, newTreeNode(PA), newTreeNode(SE, newTreeNode(SecondLastPredID), newTreeNode(lvTaskInfo.Nodes[len(lvTaskInfo.Nodes)-1].JID))))
					
					RootNode 	 	= lvTaskInfo.TreeRoot.right.left
					UpdateTaskDecompositionTree(lvTaskInfo.TreeRoot, lvTaskInfo, RootNode, VTX, VTX_Type)
					
					# for n in range(0, len(lvTaskInfo.Nodes[len(lvTaskInfo.Nodes)-1].Pred)):
					# 	if lvTaskInfo.Nodes[len(lvTaskInfo.Nodes)-1].Pred[n] == CommonSuccessorJoinVTX.JID: # Join node
					# 		lvTaskInfo.TreeRoot = newTreeNode(SE, newTreeNode(lvTaskInfo.Nodes[0].JID),\
					# 			newTreeNode(SE, newTreeNode(PA), newTreeNode(SE, newTreeNode(SecondLastPredID), newTreeNode(lvTaskInfo.Nodes[len(lvTaskInfo.Nodes)-1].JID))))
					# 		RootNode 	 	= lvTaskInfo.TreeRoot.right.left
					# 		UpdateTaskDecompositionTree(lvTaskInfo.TreeRoot, lvTaskInfo, RootNode, VTX, VTX_Type)
					# 		break
			else:
				if SecondLastPredID !=0:
					lvTaskInfo.TreeRoot = newTreeNode(SE, newTreeNode(lvTaskInfo.Nodes[0].JID),\
								newTreeNode(SE, newTreeNode(PA), newTreeNode(SE, newTreeNode(SecondLastPredID), newTreeNode(lvTaskInfo.Nodes[len(lvTaskInfo.Nodes)-1].JID))))
				else:
					lvTaskInfo.TreeRoot = newTreeNode(SE, newTreeNode(lvTaskInfo.Nodes[0].JID),\
					 newTreeNode(SE, newTreeNode(SE), newTreeNode(lvTaskInfo.Nodes[len(lvTaskInfo.Nodes)-1].JID)))
				
				VTX_Type = "SE"
				VTX.append(lvTaskInfo.Nodes[lvTaskInfo.Nodes[0].Succ[0]])
				RootNode 	 	= lvTaskInfo.TreeRoot.right.left

				UpdateTaskDecompositionTree(lvTaskInfo.TreeRoot, lvTaskInfo, RootNode, VTX, VTX_Type)
			
		# lvTaskInfo.TreeRoot.display()

			# break

	return True

def Get_Nodes_with_Max_Parallelism(TreeRoot, Nodes): 
	Pi_L=[]
	Pi_R=[]
	Interference_Left_Nodes = 0
	Interference_Right_Nodes = 0
	Nodes_with_max_parallelism = []
	# print("TreeRoot.left=%s TreeRoot.right=%s"%(NUM_TO_STR(TreeRoot.left.key), NUM_TO_STR(TreeRoot.right.key)))
	try:
		if (TreeRoot.key == SE):
			try:
				if TreeRoot.left.key != SE and TreeRoot.left.key != PA and TreeRoot.left.key != None:
					Pi_L.append(Nodes[TreeRoot.left.key])
				else:
					lvPi_L = Get_Nodes_with_Max_Parallelism(TreeRoot.left, Nodes)
					for v in range(0, len(lvPi_L)):
						Pi_L.append(lvPi_L[v])
			except NameError:
				# print("Error # 1")
				pass

			try:
				if TreeRoot.right.key != SE and TreeRoot.right.key != PA and TreeRoot.right.key != None:
					Pi_R.append(Nodes[TreeRoot.right.key])
				else:
					lvPi_R = Get_Nodes_with_Max_Parallelism(TreeRoot.right, Nodes)
					for v in range(0, len(lvPi_R)):
						Pi_R.append(lvPi_R[v])
			
			except NameError:
				# print("Error # 2")
				pass

			# Get Sum of Interference Parameters of TreeRoot.left
			Interference_Left_Nodes = 0
			for v in range(0, len(Pi_L)):
				Interference_Left_Nodes += (1/(Cores_Per_RSC_Type[Pi_L[v].ResourceType-1]))
			# Get Sum of Interference Parameters of TreeRoot.right
			Interference_Right_Nodes = 0
			for v in range(0, len(Pi_R)):
				Interference_Right_Nodes += (1/(Cores_Per_RSC_Type[Pi_R[v].ResourceType-1]))
		
		elif (TreeRoot.key == PA):
			try:
				if TreeRoot.left.key != SE and TreeRoot.left.key != PA and TreeRoot.left.key != None:
					Pi_L.append(Nodes[TreeRoot.left.key])
				else:
					lvPi_L = Get_Nodes_with_Max_Parallelism(TreeRoot.left, Nodes)
					for v in range(0, len(lvPi_L)):
						Pi_L.append(lvPi_L[v])
			except NameError:
				# print("Error # 3")
				pass

			try:
				if TreeRoot.right.key != SE and TreeRoot.right.key != PA and TreeRoot.right.key != None:
					Pi_R.append(Nodes[TreeRoot.right.key])
				else:
					lvPi_R = Get_Nodes_with_Max_Parallelism(TreeRoot.right, Nodes)
					for v in range(0, len(lvPi_R)):
						Pi_R.append(lvPi_R[v])
			except NameError:
				# print("Error # 4")
				pass			
		
	except NameError:
		# print("Error # 5")
		pass

	# Decide which ones will be part of Nodes_with_max_parallelism based on interference parameter
	if TreeRoot.key == SE:
		if Interference_Left_Nodes >= Interference_Right_Nodes:
			for v in range(0, len(Pi_L)):
				Nodes_with_max_parallelism.append(Pi_L[v])
		else:
			for v in range(0, len(Pi_R)):
				Nodes_with_max_parallelism.append(Pi_R[v])

	elif TreeRoot.key == PA:
		for v in range(0, len(Pi_L)):
			Nodes_with_max_parallelism.append(Pi_L[v])
		for v in range(0, len(Pi_R)):
				Nodes_with_max_parallelism.append(Pi_R[v])

	Nodes_with_max_parallelism.sort(key=lambda v:v.JID)

	return Nodes_with_max_parallelism


def Find_and_Delete_Vertex(NodeID, TreeRoot):
	if TreeRoot.key != None:

		try:
			if TreeRoot.key == NodeID:		
				TreeRoot.key = None	
				TreeRoot = None
				return True
			elif (TreeRoot.left != None) and (Find_and_Delete_Vertex(NodeID, TreeRoot.left)==True):
				# print("1 Deleted TreeRoot.Right:%s TreeRoot.Left:%s"%(NUM_TO_STR(TreeRoot.right.key), NUM_TO_STR(TreeRoot.left.key)))
				if TreeRoot.right.key != None or TreeRoot.left.key != None:
					return True
				else:
					# print("Invalidate %s Node"%NUM_TO_STR(TreeRoot.key))
					TreeRoot.key = None
					TreeRoot = None
					return True
	 
				return True

			elif (TreeRoot.right != None) and (Find_and_Delete_Vertex(NodeID, TreeRoot.right)==True):
				# print("2 Deleted TreeRoot.Right:%s TreeRoot.Left:%s"%(NUM_TO_STR(TreeRoot.right.key), NUM_TO_STR(TreeRoot.left.key)))
				if TreeRoot.left.key != None or TreeRoot.right.key != None:
					return True
				else:
					# print("Invalidate %s Node"%NUM_TO_STR(TreeRoot.key))
					TreeRoot.key = None
					TreeRoot = None
					return True			
		except NameError:

			pass

	return False

def Get_Interference_Distribution_Block(TreeRoot, Nodes):
	lvID_Block = ID_Block()
	# 1 Get Pi(v) = Nodes with maximum parallelism aka interference parameters
	Nodes_max_par = []
		
	Nodes_max_par = Get_Nodes_with_Max_Parallelism(TreeRoot, Nodes)
	# PrintList(Nodes_max_par, True)

	# 2 Get Minimum WCET out of all nodes, it is width
	Min_WCET = DUMMY_NUMBER
	for v in range(0, len(Nodes_max_par)):
		if Nodes_max_par[v].WCET < Min_WCET:
			Min_WCET = Nodes_max_par[v].WCET

	# 3 Get height = sum of their (interference distribution = 1/Ms ; s = gama(v))
	SUM_ID = 0
	for v in range(0, len(Nodes_max_par)):
		SUM_ID += (1/(Cores_Per_RSC_Type[Nodes_max_par[v].ResourceType-1]))

	# 4 Create a ID_Block with width and height
	lvID_Block.Width 	= Min_WCET
	lvID_Block.Height 	= SUM_ID

	# 5 Decrease the min_wcet from all of Pi(v) nodes.
	for v in range(0, len(Nodes_max_par)):
		Nodes[Nodes_max_par[v].JID].WCET -= Min_WCET

	# 6 whicever node out of Nodes has 0 WCET, remove its leaf from  the TreeRoot
	for v in range(0, len(Nodes)):
		if Nodes[v].WCET == 0:
			Find_and_Delete_Vertex(Nodes[v].JID, TreeRoot)

	# 7 return ID_Block
	return lvID_Block

def UpdateInterferenceDistribution(NFJ_DAG_TaskSetInfo):
	for Task in range(0, len(NFJ_DAG_TaskSetInfo)):
		Nodes = copy.deepcopy(NFJ_DAG_TaskSetInfo[Task].Nodes)
		TreeRoot = NFJ_DAG_TaskSetInfo[Task].TreeRoot
		# TreeRoot.display()
		while(TreeRoot.key != None):
			NFJ_DAG_TaskSetInfo[Task].ID_Blocks.append(Get_Interference_Distribution_Block(TreeRoot, Nodes))
			# TreeRoot.display()
		# for i_d in range(0, len(NFJ_DAG_TaskSetInfo[Task].ID_Blocks)):
		# 	print("Task:%d ID_Block:%d Width:%d Height:%f"%(Task+1,i_d+1,NFJ_DAG_TaskSetInfo[Task].ID_Blocks[i_d].Width,NFJ_DAG_TaskSetInfo[Task].ID_Blocks[i_d].Height))

def getCarryInInt(Delta_i_CI, TaskInfo):
	Factor_1 = max(0, (Delta_i_CI - (TaskInfo.Period - TaskInfo.WCRT)))
	Factor_2 = get_Min_Job_Exec_Time(TaskInfo)
	CarryIn_Interference = min(Factor_1, Factor_2)
	return CarryIn_Interference

def getCarryOutInt(Delta_i_CO, TaskInfo):
	CarryOut_Interference = 0

	for ID_Block_Ext in range(0, len(TaskInfo.ID_Blocks)):

		Intermediate_Width = 0

		if ID_Block_Ext > 0:
			for ID_Block_Int in range(0, ID_Block_Ext-1):
				Intermediate_Width += TaskInfo.ID_Blocks[ID_Block_Int].Width

		CarryOut_Interference += TaskInfo.ID_Blocks[ID_Block_Ext].Height * min(TaskInfo.ID_Blocks[ID_Block_Ext].Width, max(0, (Delta_i_CO - Intermediate_Width)))

	return CarryOut_Interference

def getMaxIntSlidingWind(Delta_i, iTask):
	iTask_Int = getCarryOutInt(Delta_i, iTask)

	X1 = iTask.Period - iTask.WCRT

	X1 = X1 + get_Min_Job_Exec_Time(iTask)
	X2 = Delta_i - X1

	iTask_Int = max(iTask_Int, (getCarryInInt(X1, iTask) + getCarryOutInt(X2, iTask)))

	X2 = 0

	for ID_Block in range(0, len(iTask.ID_Blocks)):
		X2 += iTask.ID_Blocks[ID_Block].Width
		X1 = Delta_i - X2
		iTask_Int = max(iTask_Int, (getCarryInInt(X1, iTask) + getCarryOutInt(X2, iTask)))

	return iTask_Int		

def UpdateWorstCaseResponseTime(NFJ_DAG_TaskSetInfo):
	# Delta_i_CI 			=	(ceil(rk/Ti))*Ti - rk
	# Delta_i_CO 			=	(Rk+rk) - (floor((Rk+rk)/Ti))*Ti
	# Nr_of_Task_i_Body_Jobs=	(Rk - Delta_CI - Delta_CO)/Ti

	for Task in range(1, len(NFJ_DAG_TaskSetInfo)):
		cTask = NFJ_DAG_TaskSetInfo[Task]

		Old_WCRT	=	0

		while(((int)(cTask.WCRT) != (int)(Old_WCRT)) and (cTask.WCRT <= cTask.Deadline)):
			Old_WCRT = cTask.WCRT 
			SumInterferences = 0

			for iTask in range(0, len(NFJ_DAG_TaskSetInfo)):
				
				pTask = NFJ_DAG_TaskSetInfo[iTask] 

				if pTask.TID == cTask.TID:
					break

				Delta_i_CI 		=	(ceil(cTask.Nodes[0].r_min/pTask.Period))*pTask.Period - cTask.Nodes[0].r_min
				Delta_i_CO 		=	(cTask.WCRT+cTask.Nodes[0].r_min) - (floor((cTask.WCRT+cTask.Nodes[0].r_min)/pTask.Period))*pTask.Period
				#Delta_i 		= 	Delta_i_CI + Delta_i_CO # This is Just a definition not a value, should not be used

				Delta_i 		= 	cTask.WCRT - (max(0, floor((cTask.WCRT - pTask.CRP_WCET) / pTask.Period)) * pTask.Period)
				Nr_of_Body_Jobs	=	max(0, floor((cTask.WCRT - Delta_i)/pTask.Period))

				SumInterferences += getMaxIntSlidingWind(Delta_i, pTask) + getBodyJobInt(Nr_of_Body_Jobs, pTask)

				# print("cTask_Ikk_WCRT:%d iTask:%d len(Gi):%d Period:%d Delta_i:%d SumInt:%d Nr_Of_Body_Jobs:%d Body_Int:%d"%\
				# 	(cTask.Ikk_WCRT/1000, (pTask.TID), pTask.CRP_WCET/1000, pTask.Period/1000, Delta_i/1000, SumInterferences/1000,\
				# 	 Nr_of_Body_Jobs, getBodyJobInt(Nr_of_Body_Jobs, pTask)/1000))
 
			cTask.WCRT = cTask.Ikk_WCRT + SumInterferences

			# print("<----> Task:%d Priority:%d Period:%d Ikk_WCRT:%d WCRT:%d"%(cTask.TID, cTask.Priority, cTask.Period/1000, cTask.Ikk_WCRT/1000, cTask.WCRT/1000,))

def Update_and_Print_FinalResults(NFJ_DAG_TaskSetInfo, Results, Print=False):

	NFJ_DAG_TaskSetInfo.sort(key = lambda v:v.TID)

	for Task in range(0, len(NFJ_DAG_TaskSetInfo)):

		if NFJ_DAG_TaskSetInfo[Task].Deadline < NFJ_DAG_TaskSetInfo[Task].WCRT:
			Results.Schedulable = 0
			if Print:
				print("<---- Task:%d Failed Utilization:%f Ikk_WCRT= %d WCRT:%d VOL_G:%d Nr_of_Nodes:%d CRP_WCET:%d Deadline:%d Priority:%d---->" \
					%(NFJ_DAG_TaskSetInfo[Task].TID, NFJ_DAG_TaskSetInfo[Task].VOL_G/NFJ_DAG_TaskSetInfo[Task].Period, NFJ_DAG_TaskSetInfo[Task].Ikk_WCRT/1000, \
						NFJ_DAG_TaskSetInfo[Task].WCRT/1000, NFJ_DAG_TaskSetInfo[Task].VOL_G/1000, len(NFJ_DAG_TaskSetInfo[Task].Nodes), NFJ_DAG_TaskSetInfo[Task].CRP_WCET/1000, \
						NFJ_DAG_TaskSetInfo[Task].Deadline/1000, NFJ_DAG_TaskSetInfo[Task].Priority))
		else:
			if Print:
				print("<---- Task:%d Success Utilization:%f Ikk_WCRT= %d WCRT:%d VOL_G:%d Nr_of_Nodes:%d CRP_WCET:%d Deadline:%d Priority:%d---->" \
					%(NFJ_DAG_TaskSetInfo[Task].TID, NFJ_DAG_TaskSetInfo[Task].VOL_G/NFJ_DAG_TaskSetInfo[Task].Period, NFJ_DAG_TaskSetInfo[Task].Ikk_WCRT/1000, \
						NFJ_DAG_TaskSetInfo[Task].WCRT/1000, NFJ_DAG_TaskSetInfo[Task].VOL_G/1000, len(NFJ_DAG_TaskSetInfo[Task].Nodes), NFJ_DAG_TaskSetInfo[Task].CRP_WCET/1000, \
						NFJ_DAG_TaskSetInfo[Task].Deadline/1000, NFJ_DAG_TaskSetInfo[Task].Priority))

def Execute_Test(Taskset):
	global RSC_Type
	global Cores_Per_RSC_Type

	Results = TestResults()
	Results.Filename = Taskset

	TaskSetInfo = []
	ResponseTime_G = []

	# Extracting Task set Details
	RSC_Type, Cores_Per_RSC_Type, TaskSetInfo, Results.Jobs = ExtractTaskSetData(Taskset)

	# Printing Task set System Configurations
	# PrintTaskSetData(RSC_Type, Cores_Per_RSC_Type, TaskSetInfo)
	
	# Get Intra task response time of each task in the task set
	UpdateIntraTaskResponseTimes(RSC_Type, Cores_Per_RSC_Type, TaskSetInfo)

	if SINGLE_DAG_ANALYSIS != True:
		# Convert DAG task in the task sets to NFJ_DAG (Nested Fork Join DAG)
		NFJ_DAG_TaskSetInfo = getNFJ_DAG_TaskInfo(TaskSetInfo)

		# Create Binary Decomposition Tree of Each task in the task set
		Update_NFJ_DAG_DecompositionTree(NFJ_DAG_TaskSetInfo)

		# Create Interference Distribution Blocks of each task in the task set
		UpdateInterferenceDistribution(NFJ_DAG_TaskSetInfo)

		# Get Inter Task Interference
		UpdateWorstCaseResponseTime(NFJ_DAG_TaskSetInfo)
 
		# Update Final Results
		Update_and_Print_FinalResults(NFJ_DAG_TaskSetInfo, Results)
	else:
		# Update Final Results
		Update_and_Print_FinalResults(TaskSetInfo, Results)

	return Results 
	
def DispatchTests(directory):
	
	encoding = 'utf-8'
	ResultPath = directory+"/SOA_Results/"

	try:
		os.mkdir(ResultPath)
	except OSError:
		if os.path.isdir(ResultPath) != True:
			print ("Creation of the directory %s failed" % ResultPath)
			return

	ResultFile = ResultPath+"Results.csv"

	FP = open(ResultFile, "a+")

	FP.write("Simulation Results for %s\n"%directory)
	FP.write("# filename, #jobs, schedulable?\n")
	
	for dirName, subdirList, fileList in os.walk(directory):
		
		TotalTested = 0
		Failed = 0
		Passed = 0
		Ratio = 0
		
		if len(fileList) > 0:
			print("Executing %s ..."%dirName)

		for Files in range(0, len(fileList)):
			if ("Report" not in fileList[Files]) and ("NOT_FEASIBLE" not in fileList[Files]) and ("TasksetSettings" not in fileList[Files]) and ("Results" not in fileList[Files]) and ("Jobs" not in fileList[Files]) and ("Pred" not in fileList[Files]) and (".png" not in fileList[Files]):
				results = TestResults()
				# print("Executing:%s"%(directory+"/"+fileList[Files]))
				results = Execute_Test(directory+"/"+fileList[Files])
				FinalResults = results.Filename+","+str(results.Jobs)+","+str(results.Schedulable)+"\n"
				FP.write(FinalResults)

				if REMOVE == True:
					lvCMD = "rm -rf "+directory+"/"+fileList[Files]
					run_command(lvCMD)

				TotalTested += 1
				if results.Schedulable:
					Passed += 1
				else:
					Failed += 1
				
				# results.DisplayResult() 

		if TotalTested > 0:
			Ratio = (Passed / TotalTested)*100
			lvSTR = "TotalTested, Passed, Failed, Schedulability_Ratio,,\n"
			FP.write(lvSTR)
			lvSTR = str(TotalTested)+","+str(Passed)+","+str(Failed)+","+str(Ratio)+","
			FP.write(lvSTR)
			print("\nFor %s TotalTested:%d Passed:%d Failed:%d Schedulability_Ratio:%d%%\n"%(dirName, TotalTested, Passed, Failed, Ratio))

	FP.close()

def main():
	global TASK_SET_FILE
	global REMOVE
	global SINGLE_DAG_ANALYSIS

	opts = parse_args()

	rootfolder = opts.root_folder
	TASK_SET_FILE = opts.task_set
	REMOVE = opts.remove
	SINGLE_DAG_ANALYSIS = opts.single_dag

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
