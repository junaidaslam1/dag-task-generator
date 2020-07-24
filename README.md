# dag-task-generator
Author: Muhammad Junaid Aslam
Email: junaidaslam1@gmail.com

This is a collection of computer programs whose purpose is to help the random generation of directed acyclic graph structures and adding
various properties on those structures. Two types of DAG tasks can be generated using this scripts. One of them is nested fork-join using recursive series parallel expansion. The other type of DAG tasks are simple fork-join DAGs. The DAG tasks can generated with various properties like the number of nodes, depth, parallelism etc. A full detail of such properties can be specified using the TasksetSettings.csv file as well as command line arguments. For a list of command line arguments use the -h option as stated below.

The following command generates task sets with the default settings provided in TasksetSettings.csv file.

python3 -W ignore generate_typed_hetero_workload.py TaskSetSettings.csv -p -f y

To incorporate further details, like using a particular period or utilization assignment policy or generation of visuals of the DAG tasks
use the following command to get help in the terminal:

python3 -W ignore generate_typed_hetero_workload.py -h

The option to check the feasibility of a task-set is not yet generic. Soon, it will be made generic by providing an option to spicy complete command string to execute for checking the feasibility of each of the generated task-sets.

#...........................................................................


