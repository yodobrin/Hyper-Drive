import azureml.core
from azureml.core.compute import ComputeTarget, AmlCompute
from azureml.core.compute_target import ComputeTargetException
import random, string
import csv

# for now this is the type and size - can be altered
vmsize = 'Standard_NC6'



def create_low_clusters(ws,number_of_clusters, number_of_nodes, idle_time_out):
    """Create low priority clusters per the input
    Keyword arguments:
    ws -- the workspace in which compute should be created
    number_of_clusters -- how many clusters should be created
    number_of_nodes -- how many (max) nodes in each cluster
    idle_time_out -- idle time of a node before it is recycled 
    """
    clusters = {}
    for i in range (0,number_of_clusters):
        dig = '{0}{1}'.format(''.join(random.sample(string.digits, 2)),''.join(random.sample(string.ascii_letters, 2)))
        cluster_name = 'NC6-L{1}-{0}'.format(dig,number_of_nodes)
        try:
            compute_target = AmlCompute(workspace=ws, name=cluster_name)        
        except ComputeTargetException:
            compute_config = AmlCompute.provisioning_configuration(vm_size=vmsize,
                                                                   vm_priority = 'lowpriority',max_nodes=number_of_nodes, 
                                                                   idle_seconds_before_scaledown=idle_time_out)
            compute_target = AmlCompute.create(ws, cluster_name, compute_config)
            compute_target.wait_for_completion(show_output=True)
            clusters[i] = compute_target
    return clusters

def create_dedicated_clusters(ws,number_of_clusters, number_of_nodes, idle_time_out):
    """Create dedicated clusters per the input
    Keyword arguments:
    ws -- the workspace in which compute should be created
    number_of_clusters -- how many clusters should be created
    number_of_nodes -- how many (max) nodes in each cluster
    idle_time_out -- idle time of a node before it is recycled 
    """
    clusters = {}
    for i in range (0,number_of_clusters):
        dig = '{0}{1}'.format(''.join(random.sample(string.digits, 2)),''.join(random.sample(string.ascii_letters, 2)))
        cluster_name = 'NC6-D{1}-{0}'.format(dig,number_of_nodes)
        try:
            compute_target = AmlCompute(workspace=ws, name=cluster_name)        
        except ComputeTargetException:
            compute_config = AmlCompute.provisioning_configuration(vm_size=vmsize,
                                                                   max_nodes=number_of_nodes, 
                                                                   idle_seconds_before_scaledown=idle_time_out)
            compute_target = AmlCompute.create(ws, cluster_name, compute_config)
            compute_target.wait_for_completion(show_output=True)
            clusters[i] = compute_target
    return clusters

def remove_compute(compute_targets):
    """Remove all compute target(s) cluster(s)
    Keyword arguments:
    compute_targets -- the compute targets to be cleaned
    """
    for name, ct in compute_targets.items():
        compute_targets[name].delete()
        
        
def push_results_to_file(file_name,queue_name, aux_q,queue_service):
    """Use the messages from a queue and create an output csv file.
    Keyword arguments:
    file_name -- the csv file name to be created
    queue_name -- a queue which contain the values to be logged
    queue_service -- a handle to create and push messages to queues
    aux_q -- saving the queue messages for any other addtional handeling
    """
    # verify the queues exist
    queue_service.create_queue(queue_name)
    queue_service.create_queue(aux_q)
    # open file for write
    f1=open('./{0}.csv'.format(file_name), 'w+')
    while queue_service.get_queue_metadata(queue_name).approximate_message_count > 0:
        messages = queue_service.get_messages(queue_name,1)
        if len(messages)>0 :
            for message in messages:                            
                line = '{0},{1},{2}'.format(message.id,message.insertion_time,message.content)
                queue_service.put_message(aux_q,line)
                f1.write(line)
                f1.write('\n')
                queue_service.delete_message(queue_name, message.id, message.pop_receipt)
    f1.close()

    
        
        