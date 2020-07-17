# dag-task-generator
Author: Muhammad Junaid Aslam
Email: junaidaslam1@gmail.com

This software is a computer program whose purpose is to help the random generation of directed acyclic graph structures and adding
various properties on those structures. Two types of DAG tasks can be generated using this scripts. One of them is nested fork-join using recursive series parallel expansion. The other type of DAG tasks are simple fork-join DAGs. The DAG tasks can generated with various properties like the number of nodes, depth, parallelism etc. 

The following command generates task sets with the default settings provided in TasksetSettings.csv file.

python3 -W ignore generate_typed_hetero_workload.py TaskSetSettings.csv -p -f y

To incorporate further details, like using a particular period or utilization assignment policy or generation of visuals of the DAG tasks
use the following command to get help in the terminal:

python3 -W ignore generate_typed_hetero_workload.py -h

More information about the task set settings file format and help catalogue will be posted soon...
