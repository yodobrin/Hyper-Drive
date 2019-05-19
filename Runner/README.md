# Using AML Service - Simplified
The Azure Machine Learning Service provides an extensive [SDK](https://aka.ms/aml-sdk)  that controls the service and its components.
The overall use case for leveraging this repository, is to allow your Data Science team with an easier fashion to run hyper scale workloads.
**Note: This repository does not provide extensive overview of the SDK, rather a view on what can be done with it**

## Workloads explanations
The use case for hyper scale, is when a large scale of similar activities, which have no impact on the order of execution. 

## How does it work?
Before running in large scale, it is highly recommended to attempt a simple run, with 10-20 rows to execute. this would make sure your experiment is running well, that it produces the required outcome and that your overall configuration is tuned.

You would need to perform *az login* from your command line window (power shell, cmd, or any other shell window)
If you have multiple subscriptions, you would need to run *az account set --subscription <subscription_id>* to make sure your command line is associated with the correct subscription.
and then run this sample command line:
*python .\experiment_configuration.py --init_file_ml init_ml.ini --init_file_func init.ini*

To be clear, running this, will create resources in your subscription. it would create an experiment, compute clusters, folders within the specified storage account(s), queues, fill the queues with the lines from the csv, AND commence the experiment on all available clusters. 

![High Level Overview](https://user-images.githubusercontent.com/37622785/57983123-fc4a1380-7a56-11e9-8bd9-3f97a68fc025.png)


## What is provided

### experiment_configuration
This module reads the ini files specified as part of the command line, and performs the following tasks:
1. create all required resources for the experiment run: compute, mounts, workspace, queues
2. fill the input queue with all lines from the csv file, specified in the ini file
3. it calculate the number of clusters and nodes required to fulfil the parallel requirements specified in the ini file
4. submits the experiments on all available clusters within the workspace
5. waits for the experiments to finish (specific heuristic used to determine if the jobs ended)
6. delete all compute

There are few supporting modules provided:

#### mlwsutils
workspace, docker image, mounts creation method are provided, abstracting the use of aml sdk.

#### mlclusters
few functions that provide cluster creation capabilities leveraging the aml sdk. for now it support NC6 as the size. any type can be used.

### config.json
This file needs to be in you directory structure, it has the information pointing to the subscription, resource group, and workspace name, which needs to be provisioned before the first time use.

### project_folder
this folder is copied to each node running on each cluster, in here one should have the required additional modules for the experiment.
The main class provided here is node_runner, the utility mlqueue is provided in this directory although used also by the experiment_configuration.

#### node_runner
This class would run in each of the nodes. it provide few supportive methods that can be overridden by an implementing class. 
It would address picking up a message from a queue, providing the arguments to the customized function, in case of success push a success message to a queue, and the exception in case of a failure.

#### mlqueue
provide few abstract functions over the azure storage queue [SDK](https://azure-storage.readthedocs.io/)

#### my_activate
a sample implementation of the NodeRunner class. 

#### dummy
in blob storage there are no real directories, thus if one wish to pass specific folder as mount point, there needs to be a file within that location. the experiment_configuration would address this by coping a dummy txt file to the designated location.
