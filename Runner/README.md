# Using AML Service - Simplified
The Azure Machine Learning Service provides an extensive [SDK](https://aka.ms/aml-sdk) that controls the service and its components.
The overall use case for leveraging this repository is to allow your Data Science team to run hyper scale workloads in a more simplified manner. 
**Note: This repository does not provide extensive overview of the SDK.  However, it is intended to provide insight on what can be done with it.**

## Workload explanation
You can make use of Hyper scale can when a large scale of similar activities need to be performed which have no limitation on the order of execution. 

## How does it work?
Prior to running in large scale, it is highly recommended to attempt a simple run with 10-20 rows. Once that smaller sample set works properly, you can assume that the larger run will execute as expected.

You need to perform *az login* from your command line window (powershell, cmd, or any other shell window). If you have multiple subscriptions, you would need to run *az account set --subscription <subscription_id>* to ensure your commands are associated with the correct subscription. 
Next, run this sample command:
*python .\experiment_configuration.py --init_file_ml init_ml.ini --init_file_func init.ini*

Keep in mind that running this command will create resources in your subscription. It creates an experiment, compute clusters, folders within the specified storage account(s), queues, fills the queues with the lines from the csv, AND commences the experiment on all available clusters. 

### Additional Resources
Loading large amount of messages to a queue could be a long running task as it depends on network bandwidth. The first suggestion on how to load the input queue with messages is to use a VM within the same region as your storage account in which your queues are created.
Another option is to leverage a serverless solution with Azure function to handle this load of data.
I've created such solution and it can be found ![here](https://github.com/yodobrin/csv2q)

![High Level Overview](https://user-images.githubusercontent.com/37622785/57983123-fc4a1380-7a56-11e9-8bd9-3f97a68fc025.png)


## What is provided

### experiment_configuration
This module reads the ini files specified as part of the command line, and performs the following tasks:
1. creates all required resources for the experiment run: compute, mounts, workspace, queues
2. fills the input queue with all of the lines from the csv file, specified in the ini file
3. calculates the number of clusters and nodes required to fulfil the parallel requirements specified in the ini file
4. submits the experiments on all available clusters within the workspace
5. waits for the experiments to complete (specific heuristic used to determine if the jobs ended)
6. deletes all of the compute resources

There are few supporting modules provided:

#### mlwsutils
Workspace, docker image, mount creation method are provided, abstracting the use of aml sdk.

#### mlclusters
Functions that provide cluster creation capabilities leveraging the aml sdk. As of now it supports NC6 as the size.  Any type can be used.

### config.json
This file needs to be in you directory structure. It has the information pointing to the subscription, resource group, and workspace name - which needs to be provisioned before the first run.

### project_folder
this folder is copied to each node running on each cluster - within these folders, one should have the required additional modules for the experiment.
The main class provided here is node_runner - the utility mlqueue is provided in this directory although it is also used by the experiment_configuration.

#### node_runner
This class runs on each of the nodes. It provides a few supporting methods that can be overridden by an implementing class. 
It also addresses the polling of messages from a queue, providing the specified arguments to the customized function. Once the activity succeeds or fails, a message with the corresponding result will be pushed to a queue.

#### mlqueue
Provides a few abstract functions for the azure storage queue [SDK](https://azure-storage.readthedocs.io/)

#### my_activate
Sample implementation of the NodeRunner class. 

#### dummy
Blob storage has no real directories structure. Therefore if one wishes to pass a specific folder as a mount point, there needs to be a file within that location.  The experiment_configuration addresses this by copying a dummy txt file to the designated location. 
