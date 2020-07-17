# dag-task-generator
This software is a computer program whose purpose is to help the random generation of directed acyclic graph structures and adding
various properties on those structures. The following command generates task sets with the default settings provided in TasksetSettings.csv file.

python3 -W ignore generate_typed_hetero_workload.py TaskSetSettings.csv -p -f y

To incorporate further details, like using a particular period or utilization assignment policy or generation of visuals of the DAG tasks
use the following command to get help in the terminal:

python3 -W ignore generate_typed_hetero_workload.py -h

More information about the task set settings file format and help catalogue will be posted soon...
