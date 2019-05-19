from azure.storage.queue import QueueService
import csv

def resetq(queue_service, queue):
    """delete a queue, all data is lost.
    Keyword arguments:    
    queue_name -- a queue which will be reset
    queue_service -- a handle to create and push messages to queues    
    """        
    queue_service.clear_messages(queue)
    print('Cleared:'+queue)


def createq(queue_service, queue):
    """create a queue.
    Keyword arguments:    
    queue_name -- a queue which will be created
    queue_service -- a handle to create and push messages to queues    
    """    
    queue_service.create_queue(queue)
    print('created:'+queue)


# obtain the number of records within a provided queue, this is used to ensure all records are processed
def getQSzie(queue_service, input_q):
    """return the queue message depth
    queue_name -- a queue which depth is requested
    queue_service -- a handle to create and push messages to queues    
    """    
    metadata = queue_service.get_queue_metadata(input_q)
    return metadata.approximate_message_count



def queue_to_csv(file_name, queue_name, queue_service):    
    """Use the messages from a queue and create an output csv file.
    Keyword arguments:
    file_name -- the csv file name to be created
    queue_name -- a queue which contain the values to be logged
    queue_service -- a handle to create and push messages to queues    
    """
    # verify the queue exist
    queue_service.create_queue(queue_name)    
    # open file for write
    f1=open('./{0}.csv'.format(file_name), 'w+')
    while queue_service.get_queue_metadata(queue_name).approximate_message_count > 0:
        messages = queue_service.get_messages(queue_name,1)
        if len(messages)>0 :
            for message in messages:                            
                line = '{0},{1},{2}'.format(message.id,message.insertion_time,message.content)                
                f1.write(line)
                f1.write('\n')
                queue_service.delete_message(queue_name, message.id, message.pop_receipt)
    f1.close()


def csv_to_queue(csv_file_name, queue_name, queue_service,column_no):
    """fill a queue with values from a csv specific column.
    Keyword arguments:
    csv_file_name -- the csv file name
    queue_name -- a queue which should contain the values
    queue_service -- a handle to create and push messages to queues
    column_no -- the column number from the csv
    """
    # verify the queue exist
    queue_service.create_queue(queue_name)
    # read the csv
    mycsv = csv.reader(open(csv_file_name, 'r',encoding="utf8", newline=''))
    # iterate through the lines
    for i,row in enumerate(mycsv):
        video_input_file_url = row[column_no]
        queue_service.put_message(queue_name,video_input_file_url)

        
def csv_to_queue_all(csv_file_name, queue_name, queue_service):
    """fill a queue with values from a csv takes an entire line as is and push to a queue.
    Keyword arguments:
    csv_file_name -- the csv file name
    queue_name -- a queue which should contain the values
    queue_service -- a handle to create and push messages to queues    
    """
    print('filling input queue ' + queue_name)
    # verify the queue exist
    #queue_service.create_queue(queue_name)
    # read the csv
    mycsv = csv.reader(open(csv_file_name, 'r',encoding="utf8", newline=''))
    # iterate through the lines
    for i,row in enumerate(mycsv):
        row_line = ', '.join(row)
        queue_service.put_message(queue_name,row_line)
