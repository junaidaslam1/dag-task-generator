import subprocess
import argparse

def run_command(incommand):
    p = subprocess.Popen(incommand.split(), stdout=subprocess.PIPE,
stderr=subprocess.STDOUT)
    outstring = p.stdout.read()
    return outstring

def parse_args():
    parser = argparse.ArgumentParser(description="Create task sets file")

    parser.add_argument('-j', '--Job_ID', dest='Job_ID', default='Null', 
                        action='store', type=str, metavar="JOB ID TO CANCEL",
                        required=False,
                        help='Provide Job_ID to Cancel, otherwise all jobs will be canceled')

    parser.add_argument('-i', '--Most_Significant_Number', dest='MSN', default='Null',
                        action='store', type=str, metavar="MOST SIGNIFICANT NUM",
                        required=False,
                        help='Most Significant Number to Identify all Job IDs in case of Cancelling ALL IDs')

    return parser.parse_args()

def run_command(incommand):
	p = subprocess.Popen(incommand.split(), stdout=subprocess.PIPE,
stderr=subprocess.STDOUT)
	outstring = p.stdout.read()
	return outstring

def CancelAllJobs(MSD):
    lvCMD = 'squeue -u jaslam'
    Result = run_command(lvCMD)
    encoding = 'utf-8'
    lvResults = str(Result, encoding)
    AllIDs = lvResults.split(' ')
    for row in range(0, len(AllIDs)):
        if str(MSD) in AllIDs[row]:
                if int(AllIDs[row]) > (int(MSD)*10000):
                        #print("ID:%d"%int(AllIDs[row]))
                        lvCMD = "scancel "+(AllIDs[row])
                        print(run_command(lvCMD))

def CancelInputJobs(JobIDs):
    lvIDs = JobIDs.split(' ')
    for n in range(0, len(lvIDs)):
        lvCMD = "scancel "+lvIDs[n]
        print(run_command(lvCMD))

def main():
    opts = parse_args()
    JobIDs = opts.Job_ID
    MSD = opts.MSN

    if MSD != "Null":
        CancelAllJobs(MSD)
    elif JobIDs != "Null":
        CancelInputJobs(JobIDs)
    else:
        print("Enter either JobIDs or common Most Significant 2 or 3 Digits of submitted jobs to cancel all jobs at once")

if __name__ == '__main__': 
    main()
