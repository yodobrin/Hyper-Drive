# The use case
So you have thousands of videos to process, your processing of videos takes roughly 20 sec per video. Processing maybe, using ffmpeg to extract frames from a video and then perform a feature extraction using KERAS, it could be a training job. If you use a single VM, running sequentially would take dozens of hours.
20K videos at 20 sec per video -> over 111 hours, or a week of work.

What if your data scientist cost more, and can achieve more with his time?

With Azure Machine learning service, you will be able to spin as many nodes as permitted by your quota. You will also be able to leverage low cost nodes by using low-priority VMs. 

So at the end of the day, your data scientist or data engineer would be able to achieve more in less time with lower cost, interested - continue reading. 

# The set Up
Your IP, is yours to keep, the information provided here is allowing you to execute your code in paralleled on multiple nodes - is your code ready for it?
* Does your code accept input as files?
* Consider changing it to accept input as queue
* Do you have specific docker container ?
  * Either public or private - the service supports both
  * If you use custom weights, or just want to avoid downloading runtime libraries, weights and other artifacts use an image
* Do you use fileshare to produce your results?
  * Don’t, it is better to leverage blob as it support much higher concurrency 
* Make sure you submit a request for quota, without sufficient quota, you will not be able to spin multiple nodes
* Familiar yourself with Azure Machine Learning Service this document refer to 'compute' 'experiment' 'job' & workspace throughout, here is a single line description:
  * Compute - represent the physical node(s) and cluster(s)
  * Experiment - logical container of your current work
  * Job - single execution, in this document it would run on a single node
  * Workspace - service hosting all the jobs, experiments, compute and other components

# The Architecture

## Logical Overview

![High Level Architecture](https://user-images.githubusercontent.com/37622785/54086849-13350100-4356-11e9-961c-8922b8f373d6.jpg)

## Physical Overview

![High Level Architecture](https://user-images.githubusercontent.com/37622785/54086868-25af3a80-4356-11e9-9277-77d87d53c8c9.jpg)

### Execution Notebook
Hosted on a dsvm (small scale - dependent on the number of concurrent users), the notebook leverage azureml sdk to facilitate experiments, compute and jobs. The notebook also uses few functions created in specific module.
#### The notebook flow will: 
+ Use or create a workspace, 
+ Name an experiment, 
+ Create or obtain required compute,
+ Configure required resources for the experiment (image, input, output etc.)
+ Create an estimator and submit the estimator via hyperdrive 
#### AML Service
PaaS service deployed in the region as the input blob. The service host all the required components, such as compute, experiments and jobs

#### Process Queues
Used to enable parallel and even distribution between the working nodes.
There are 3 queues: 
+ Input - url or path to the video
+ Failures - the failed video and the exception as captured from the process
+ Success - per video, a set of measurement captured during the run, currently only capturing the process elapsed time

**Output blob** - specific container and directories are used to save the products of the scripts

**Registry** - the image to be used by the working nodes

**Media Files** - the container in which the video files are hosted

**Compute** - an array of clusters, each up to 100 nodes with the type of VMs as required by the actual script

# What is not covered
* How is the image created?
* What is the internal script which perform the actual work? 
	* In this repo only an example script is provided
* Setting up the DSVM with Jupyter (with required conda packages)
	* I might add another article covering it

