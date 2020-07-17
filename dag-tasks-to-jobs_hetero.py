#!/usr/bin/env python3

import argparse

import csv
import re

from math import ceil, floor, log10

from collections import defaultdict

import fractions

US_TO_NS = 1000
MS_TO_US = 1000
MS_TO_MS = 1
DUMMY_NUMBER    =   99999
PRIORITY_POLICY = ""
PRIO_NC = False

def next_power_of_10(x):
    return 10**(ceil(log10(x)))

def ms2us(x):
    # return int(ceil(MS_TO_US * x))
    return int(ceil(MS_TO_US * x))

def lcm(a,b):
    return abs(a * b) // fractions.gcd(a,b) if a and b else 0

def hyperperiod(periods):
    h = 1
    for p in periods:
        h = lcm(h, p)
    return h

def parse_dag_task_file(fname, scale=ms2us):
    f = open(fname, 'r')
    data = csv.reader(f, skipinitialspace=True)
    nodes_per_resource = {}
    periods = {}
    deadlines = {}
    priorities = {}
    nodes = defaultdict(list)
    max_rcst = 0
    counter = 0   
    nodes_per_resource[counter] = 0
    counter = counter + 1
    for row in data:
        if row[0] == 'R':
            max_rcst = int(row[1]) + 1
        elif row[0] == 'M':
            nodes_per_resource[counter] = row[1]
            counter = counter + 1
        elif row[0] == '#':
            continue
        elif row[0] == 'T':
            # parse new task declaration

            # A ’T’ row consists of the following columns:
            #
            # 	1) ’T’
            # 	2) a unique numeric ID
            # 	3) the period (in milliseconds, fractional is ok)
            # 	4) the relative deadline

            tid = int(row[1])
            p  = scale(float(row[2]))
            dl = scale(float(row[3]))
            pr = int(row[4])

            if pr == int(row[3]):
                pr = scale(pr)

            assert tid >= 0
            assert p > 0
            assert dl > 0
            assert pr != DUMMY_NUMBER 

            periods[tid] = p
            deadlines[tid] = dl
            priorities[tid] = pr

        elif row[0] == 'V':
            # parse vertex information

            # A ‘V’ row consists for the following columns (unbounded number):
            #
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

            tid = int(row[1])
            vid = int(row[2])

            r_min = scale(float(row[3]))
            r_max = scale(float(row[4]))
            bcet  = scale(float(row[5]))
            wcet  = scale(float(row[6]))
            rsct  = (int(row[7]))

            if rsct > max_rcst:
                max_rcst = rsct

            preds = [int(pred) for pred in row[8:]]

            assert 0 <= r_min <= r_max
            assert 0 <= bcet <= wcet
            assert vid >= 0
            assert tid >= 0

            nodes[tid].append((vid, r_min, r_max, bcet, wcet, rsct, preds))

        else:
            print(row)
            assert False # badly formatted input???
    
    return (periods, deadlines, priorities, nodes, max_rcst, nodes_per_resource)

def mkjobs(tid, num_task_instances, period, deadline, priority, nodes, mkprio):
    jobs  = []
    edges = []
    for i in range(0, num_task_instances):
        # release time of this instance
        rel = i * period
        # absolute deadline of this instance
        adl = rel + deadline
        prio = mkprio(tid, adl, period)
        jid = i * next_power_of_10(len(nodes)) + 1
        vid2jid = {}
        for (vid, r_min, r_max, bcet, wcet, rcst, preds) in nodes:
            vid2jid[vid] = jid
            jobs.append(
                (jid, rel + r_min, rel + r_max, bcet, wcet, adl, prio, rcst, tid))
            jid += 1
        for (vid, r_min, r_max, bcet, wcet, rcst, preds) in nodes:
            for p in preds:
                edges.append( (tid, vid2jid[p], tid, vid2jid[vid]) )
    return jobs, edges

def job_format_csv(j):
    return "{8:10}, {0:10}, {1:20}, {2:20}, {3:20}, {4:20}, {5:20}, {6:20}, {7:20}\n".format(*j)

JOBS_CSV_HEADER = \
    "{7:>10s}, {0:>10s}, {1:>20s}, {2:>20s}, {3:>20s}, {4:>20s}, {5:>20s}, " \
    "{6:>20s}, {8:>20s}\n".format(
        "Job ID", "Arrival min", "Arrival max", "Cost min", "Cost max",
        "Deadline", "Priority", "Task ID", "ResourceType")

def write_jobs(fname, jobs, max_rcst, nodes_per_resource):
    f = open(fname, 'w')
    
    Rcst = "ResourceTypes, " + str((max_rcst))+"\n"
    f.write(Rcst)

    for i in range(0, max_rcst):
        lvStr = "M"+str(i)+", "+str(nodes_per_resource[i])+"\n"
        f.write(lvStr)
    
    lvStr = "#\n"
    f.write(lvStr)
    f.write(JOBS_CSV_HEADER)
    for j in jobs:
        f.write(job_format_csv(j))
    f.close()

EDGES_CSV_HEADER = \
    "{0:>8s}, {1:>8s}, {2:>8s}, {3:>8s}\n".format(
        "From TID",	"From JID",	"To TID", "To JID")

def edge_format_csv(e):
    return "{0:8}, {1:8}, {2:8}, {3:8}\n".format(*e)

def write_edges(fname, edges):
    f = open(fname, 'w')
    f.write(EDGES_CSV_HEADER)
    for e in edges:
        f.write(edge_format_csv(e))
    f.close()

def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert a DAG task specification to a job set + edge list")

    parser.add_argument('dag_tasks', metavar = 'DAG-TASKS-CSV-FILE',
        help='the task set that should contribute to this job set')

    parser.add_argument('jobs_file', metavar = 'JOBS-CSV-FILE',
        help='where to store all jobs')

    parser.add_argument('edges_file', metavar = 'EDGES-CSV-FILE',
        help='where to store all edges')

    parser.add_argument('-p', '--policy', dest='priority_policy', default='EDF',
                        action='store',
                        choices=["EDF", "RM", "DM", "FP", "NC"],
                        help='how to assign job prios (EDF, RM, DM, FP, NC) -> NC=Default')

    return parser.parse_args()

def prio_table(params):
    p = [(params[tid], tid) for tid in params]
    p.sort()
    lut = {}
    for i, (_, tid) in enumerate(p):
        lut[tid] = i + 1
    return lut

def main():
    global PRIORITY_POLICY
    global PRIO_NC

    opts = parse_args()
    (periods, deadlines, priorities, nodes, max_rcst, nodes_per_resource) = parse_dag_task_file(opts.dag_tasks)

    h = hyperperiod(periods.values())

    def edf_prio(tid, deadline, period):
        return deadline

    rm_table = prio_table(periods)
    dm_table = prio_table(deadlines)

    def rm_prio(tid, deadline, period):
        return rm_table[tid]

    PRIORITY_POLICY = opts.priority_policy
    
    if PRIORITY_POLICY == 'EDF':
        mkprio = lambda tid, deadline, period: deadline # EDF by default
    elif PRIORITY_POLICY == 'RM':
        mkprio = lambda tid, deadline, period: rm_table[tid]
    elif PRIORITY_POLICY == 'DM':
        mkprio = lambda tid, deadline, period: dm_table[tid]
    elif PRIORITY_POLICY == 'FP':
        # FP == fixed priority => just re-use the given task ID as priority
        mkprio = lambda tid, deadline, period: tid
    elif PRIORITY_POLICY == 'NC':
        # NC ==> NC says to use distinct task priorities set w.r.t priod values and use EDF to set for jobs
        mkprio = lambda tid, deadline, period: priorities[tid]
    else:
        assert False # unsupported prio order

    all_jobs  = []
    all_edges = []

    for tid in periods:
        if nodes[tid]:
            per = periods[tid]
            dl  = deadlines[tid]
            pr  = priorities[tid]
            jobs, edges = mkjobs(tid, h // per, per, dl, pr, nodes[tid], mkprio)
            all_jobs.extend(jobs)
            all_edges.extend(edges)

    all_jobs.sort(key=lambda j: j[1])

    write_jobs(opts.jobs_file, all_jobs, max_rcst, nodes_per_resource)
    write_edges(opts.edges_file, all_edges)

if __name__ == '__main__':
    main()
