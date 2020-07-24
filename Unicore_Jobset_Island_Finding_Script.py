import csv
import sys
import os
import copy
import threading
import time
import subprocess
from subprocess import Popen, PIPE
from fractions import gcd

# Global Variables

# Column Numbers for Original Source File
TASK_ID = 0
JOB_ID = 1
ARRIVAL_MIN = 2
ARRIVAL_MAX = 3
COST_MIN = 4
COST_MAX = 5
DEADLINE = 6
PRIORITY = 7

# Column Numbers for List_Jobs lists created in this script
TID = 0
JID = 1
ARR_MAX = 2
CST_MAX = 3
PERIOD= 4

# Global Data
source_csv = ""
list_jobs = []
original_jobs = []
list_response_times = []
island_of_jobs = []
island_name = []
schedule_time = []
schedule_time_counter = 0
island_job_list = []
first_job = 0
last_job = 0
island_counter = 0
time_zero = 0

# Path to nptest binary Bjorn Brandernburg
nptest_path = "/home/junaid/eclipse-workspace/np_schedulability/build/nptest --header -r "

def pause():
    input("System Paused! Press Enter to continue...")
        
def sortRmax(val): 
    return val[2]

def sort_jobs_wrt_Rmax():
     list_jobs.sort(key = sortRmax)

def custom_command(incommand):
	#g_str = ("Executing:",incommand)
	#print(g_str)
	p = subprocess.Popen(incommand, stdout=subprocess.PIPE,
stderr=subprocess.STDOUT)
	outstring = p.stdout.read()
	#print(outstring)
	return outstring

class NP_Test_Thread (threading.Thread):
	def __init__(self, name, filename):
		threading.Thread.__init__(self)
		self.name = name
		self.filename = filename
	def run(self):
      		#print "Starting " + self.name
		#print(self.name)
		lvStr = nptest_path+self.filename
	        print(custom_command(lvStr.split()))

def initialize_np_test(name,filename):
	nptest_thread = NP_Test_Thread(name, filename)
	nptest_thread.start()
	
def create_jobset(filename, job_set):
        jobWriter = 0
        jobReader = 0
        
        with open(source_csv, 'rb') as csvfile:
                jobReader = csv.reader(csvfile, delimiter=',', quotechar='|')
                next(jobReader)
                
                with open(filename, 'wb') as csvfile:
                    jobWriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)            
                    jobWriter.writerow(['Task ID', 'Job ID', 'Arrival Min', 'Arrival Max', 'Cost Min', 'Cost Max', 'Deadline', 'Priority'])

                    for reader_row in jobReader:
                            for writer_row in job_set:                                    
                                if (writer_row[0] != ((int)(reader_row[0]))) or (writer_row[1] != ((int)(reader_row[1]))):
                                    continue
                                else:
                                    jobWriter.writerow(reader_row)

        # Initialize thread to analyse the jobset island
        initialize_np_test(filename, filename)

# Parse jobs to get job list with specific characteristics listed        
def parse_jobs(input_file):
    counter = 0
    with open(input_file, 'rb') as csvfile:
            jobreader = csv.reader(csvfile, delimiter=',', quotechar='|')
            next(jobreader)
            for row in jobreader:
                job = []
                for item in row:                   
                    if (counter == COST_MIN) or (counter == ARRIVAL_MIN) or (counter == PRIORITY):
                        counter = counter + 1
                        continue                    
                    job.append(int(item))                    
                    counter = counter + 1 

                counter = 0    
                list_jobs.append(job)
                original_jobs.append(job)

    print("TID, JID, ARR_MIN, ARR_MAX, Cmax")
    for item in list_jobs:
            print(item)
    print("--------------- NOW Sorted ---------------")
    sort_jobs_wrt_Rmax()
    for item in list_jobs:
            print(item)

def get_current_schedule_time():
        return get_schedule_time(schedule_time_counter)

def get_schedule_time(index):
        return schedule_time[index]

def append_schedule_time(inTime):
        global schedule_time_counter
#        print("time provided:%d"%inTime)
        schedule_time.append(inTime)
#        print("Counter:%d Appended Time:%d"%(schedule_time_counter, get_schedule_time(schedule_time_counter)))
        schedule_time_counter += 1
#        print("Counter:%d Appended Time:%d"%(schedule_time_counter, get_schedule_time(schedule_time_counter)))

def check_recursion_condition(island_list):
        for item in island_list:
                if get_current_schedule_time() <= item[ARR_MAX]:
                        return 0
        return 1

def remove_jobs_from_orig_list(island_job_list):
        lvList_Jobs = copy.deepcopy(list_jobs)
        lvCounter = 0
        for item in lvList_Jobs:
                for island_item in island_job_list:
                       if  (item[TID] == island_item[TID]) and (item[JID] == island_item[JID]):
                               list_jobs.remove(item)
                               lvCounter += 1
                               break
        print("-- Removed:%d -- Remaining Jobs --"%lvCounter)
        for item in list_jobs:
            print(item)
            
def find_island():
        print("Finding Islands and launching threads to perform analysis")
        global first_job
        global island_counter
        
        global_time_summation = 0

        if first_job == 0:
                first_job = 1
                append_schedule_time(list_jobs[0][ARR_MAX])
                
        for item in list_jobs:            
            if (item[ARR_MAX] <= get_current_schedule_time()):                
                island_job_list.append(item)
                global_time_summation += item[CST_MAX]
                print(global_time_summation)

        append_schedule_time(get_current_schedule_time() + global_time_summation)
        
        print("Current Time:%d Previous_Time:%d"%(get_current_schedule_time(), get_schedule_time(schedule_time_counter - 1)))

        if (get_schedule_time(schedule_time_counter - 1) == get_current_schedule_time()) and (check_recursion_condition(island_job_list) == 1):
                print("Removing Jobs for Island")
                print(get_current_schedule_time())
                remove_jobs_from_orig_list(island_job_list)
                island_counter += 1
                filename = 'Island'+str(island_counter)+'.csv'
                create_jobset(filename, island_job_list)
                del island_job_list[:]
        else:
                remove_jobs_from_orig_list(island_job_list)
                find_island()

def find_island_new():
        #print("Finding New Islands and launching threads to perform analysis")
        list_Counter = 0
        
        global first_job
        global island_counter
        global time_zero
        global last_job
        
        global_time_summation = 0

        list_Counter = len(list_jobs)

        if list_Counter == 0:
                print("List_Jobs list is empty")
                
        if first_job == 0:
                first_job = 1
                append_schedule_time(list_jobs[0][ARR_MAX])

        print("New T_0 Value:%d get_current_schedule_time:%d"%(time_zero, get_current_schedule_time()))
        
        for item in list_jobs:
            if len(list_jobs) != 1:
                    if ((item[ARR_MAX]+time_zero) <= get_current_schedule_time()):
                        island_job_list.append(item)
                        append_schedule_time(get_current_schedule_time() + item[CST_MAX])
                    else:
                        append_schedule_time(item[ARR_MAX] + time_zero)
                        #print("An Island is Found. Next Job`s Rmax Time:")
                        #print(get_current_schedule_time())
                        remove_jobs_from_orig_list(island_job_list)
                        island_counter += 1
                        filename = 'Island'+str(island_counter)+'.csv'
                        create_jobset(filename, island_job_list)
                        #print("Flush the Island Job list to fill with new jobs")
                        del island_job_list[:]
            else:
                island_job_list.append(item)
                append_schedule_time(item[PERIOD] + time_zero)
                #print("An Island is Found. final Job in the list:")
                #print(get_current_schedule_time())
                remove_jobs_from_orig_list(island_job_list)
                island_counter += 1
                filename = 'Island'+str(island_counter)+'.csv'
                create_jobset(filename, island_job_list)
                #print("Flush the Island Job list to fill with new jobs")
                del island_job_list[:]                
                last_job = 1
        
def get_hyper_period(numbers):
    return reduce(lambda x, y: (x*y)/gcd(x,y), numbers, 1)       

def get_col(arr, col):
    return map(lambda x : x[col], arr)

if __name__ == '__main__':
    global time_zero
    global last_job
    
    if len(sys.argv) > 1:
        
        print("JobSet Filename:"+sys.argv[1])

        source_csv = sys.argv[1]

        schedule_time.append(0)

        time_zero = get_schedule_time(0)
        
        parse_jobs(source_csv)

        list_of_deadlines = get_col(list_jobs, PERIOD)

        hyper_period = get_hyper_period(list_of_deadlines)
        
        print("HyperPeriod:%d"%hyper_period)

        last_job = 0

        Last_job_period = list_jobs[len(list_jobs) - 1][PERIOD]
        
        while get_current_schedule_time() < Last_job_period:
                if last_job == 1:
                        list_jobs = copy.deepcopy(original_jobs)
                        sort_jobs_wrt_Rmax()
                        time_zero = get_current_schedule_time()
                        last_job = 0
                find_island_new()
#                time.sleep(0.5)

    else:
        print("Please provide Filename")
        exit()
   
