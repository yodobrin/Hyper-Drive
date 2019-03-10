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
** Either public or private - the service supports both
** If you use custom weights, or just want to avoid downloading runtime libraries, weights and other artifacts use an image
* Do you use fileshare to produce your results?
** Don’t, it is better to leverage blob as it support much higher concurrency 
* Make sure you submit a request for quota, without sufficient quota, you will not be able to spin multiple nodes
* Familiar yourself with Azure Machine Learning Service this document refer to 'compute' 'experiment' 'job' & workspace throughout, here is a single line description:
** Compute - represent the physical node(s) and cluster(s)
** Experiment - logical container of your current work
** Job - single execution, in this document it would run on a single node
** Workspace - service hosting all the jobs, experiments, compute and other components
