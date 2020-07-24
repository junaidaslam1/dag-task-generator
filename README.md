*All of the scripts are self explanatory in their syntax. The comments on the crucial points are inserted.*

# DAG Generator Tool (generate_typed_hetero_workload.py)

This software is a collection of computer programs whose purpose is to help the random generation of directed acyclic graph (DAG) structures while adding
various properties on them. In order to generate a DAG task using default settings, follow the command below:

`python3 -W ignore generate_typed_hetero_workload.py TaskSetSettings.csv -p <PathToStore> -f y`

To incorporate further details, like using a particular period or utilization assignment policy or generation of visuals of the DAG tasks
use the following command to get help in the terminal:

`python3 -W ignore generate_typed_hetero_workload.py -h`

# Job set generator tool (dag-tasks-to-jobs_hetero.py)

This file is used by the `generate_typed_hetero_workload` tool to create job set from the task set file. It accepts priority assignment using rate-monotonic, EDF and deadline monotonic options. These options can be visible from the help command of `generate_typed_hetero_workload`.

# Running the jobs on Computer and Cluster (ExecuteTests.py)

The job set files generated in previous step can be used to run tests on either PC or cluster automatically using this script. It has a wide range of options available to it which can be viewed using the command:

`python3 ExecuteTests.py -h`

A simple command to pick up the bunch of job set files and run them on the computer is given as:

`python3 ExecuteTests.py -p ../../np-schedulability-analysis/ -w <path_to_job_set_files> -s /home/<user>/<directory>/ -cl PC -r Y`

To run the tests on the chosen cluster use `-cl <cluster option>` and do not use `-r Y` option, for rest of the options related to specifying job parameters of a cluster refer to the help command.

This tool automatically generates `JobResult..` files per job set file to store its outcome in a Results directory. 

# Gathering all of the results (GatherResults.py)

This script automatically gathers data from all of the `JobResult...` files and compiles them into a single `Results.csv` file per job set directory. Additionally, if the path of a parent folder is given which contains many many job sets with different utilizations and number of tasks, it automatically generates the summary of all the tests results in a csv file. The command to use this tool is:

`python3 GatherResults.py -w <location_of_analysed_workload> -p 90 -d 1`

Above command gets the location and summarizes all of the results. `-P 90` in the command calculates the 90 percentile CPU Time and Mem usage of job sets per configuration (e.g, XX % utilization and YY number of tasks in a task-set for ZZZ number of samples). The `-d 1` divides the CPU Time by `1` to give CPU-Time with respect to a single CPU analysis time. This can be used to divide the CPU-Time by the number of threads (`-d 16`) to get a rough estimation of wall-clock time.

*Note: This script will work only if the ExecuteTests.py is used to run and gather test results*

# *Verification Scripts*

Below 3 scripts can be used with simple python commands like `python3 VerifyTaskSetData.py -h` The `-h` option provides options and details to use them.

# DeadlineMissVerification 

This script was developed to verify deadline miss verification scenarios. The tool was heavily pessimistic hence it could not be performed. If the pessimism from the tool is removed then this tool can be further developed to implement the algorithm. For now, it is incomplete; however, it can extract the jobs out of a job-set and also various propoerties and dependencies of it. For example, its parallel jobs and ancestors, successors, predecessors etc etc... This script only works with the `Results.csv` file filled by *GatherResults.py* script.

# VerifyTaskSetData

This script was developed to verify task set data. This verification involved checking if the generated periods are correct w.r.t to the critical path length etc. This script can also generate a visual of the input task set.

# ECRTS_19_TaskSetVerifyTaskSetData

This script was developed for a similar purpose as of above; however, this works for the task sets of the ECRTS_19 paper of Mitra Nasri and Bjorn Brandernburg.

# CancelJobs

This script was developed to cancel a single of bulk of jobs submitted to the cluster due to any reason. In order to use this script use the following command:

`python3 CancelJobs.py -i XX` here `XX` refers to the most significant (MS) two digits of the job ID to find and remove all jobs with same MS. To canclen an individual job simple use `-j` option.

# Peng'19 and Han'19 Paper implementations

The script `ResponseTimeAnalysisofTypedDAGTasksfor_G-FP_Scheduling_NNFJ.py` has the implementation of the above mentioned two related works. In order to use Han'19 (which was for single large DAG tasks) for the analysis use the command:

`python3 ResponseTimeAnalysisofTypedDAGTasksfor_G-FP_Scheduling_NNFJ.py -s -w <path_to_task_set_files>`

for Peng'19 (which is for multiple DAG tasks) analysis simple remove the `-s` from the above command.

# Jobset Island Finding Script (Unicore_Jobset_Island_Finding_Script.py)

This script was developed as a proof of concept to identify islands of job sets to be analyzed, so that if in a hyper period a set of jobs has already been analyzed with certain constraints then it should not be analyzed again so as to elude the early state space exploration. 

For further information, you can contact the author at *junaidaslam1@gmail.com*

