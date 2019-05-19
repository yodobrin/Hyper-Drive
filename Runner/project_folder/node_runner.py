import argparse
from configparser import ConfigParser
import mlque as qutils
from azure.storage.queue import QueueService
from time import gmtime, strftime, sleep
import time
import traceback
from datetime import datetime

class NodeRunner():

    def set_up(self,args_tuple):
        print('initliaze activator')        
        self.ini_file = args_tuple.init_file
        self.cli_args = args_tuple
        self.read_conf()
        self.obtain_queues_names()

    def set_up_args(self):
        # obtain the required const argument per node run
        args_sample = {"one","two"}
        return args_sample

    def read_csv_line(self,line):
        csv_line = line.strip().split(',')
        return csv_line
    
    def set_loop_method(self,method):
        print('set loop method called')
        self.loop_method = method

    def send_to_loop_method(self, arg_per_node, csv_line):
        return self.loop_method(arg_per_node, csv_line)

    def read_conf(self):
        self.config = ConfigParser()
        self.config.read(self.ini_file)

    def obtain_queues_names(self):            
        inq = self.config["queue_details"]["input_queue"]
        sa = self.config["queue_details"]["storage_account"]
        sakey = self.config["queue_details"]["storage_account_key"]       
        self.input_queue = inq 
        self.success_queue = '{0}-success'.format(self.input_queue)
        self.fail_queue = '{0}-fail'.format(self.input_queue)
        self.queue_service = QueueService(account_name=sa, account_key=sakey)

    def run_on_node(self,arg_per_node):
        print("Start processing !!! ")
        while qutils.getQSzie(self.queue_service, self.input_queue) > 0:
            messages = self.queue_service.get_messages(self.input_queue, num_messages=1, visibility_timeout=40)
            # the call returns a list, as of now, the batch size is 1
            if len(messages) > 0:
                message = messages[0]
                line = message.content
                # print(line)
                csv_line = self.read_csv_line(line)

                # delete the message from the qeue

                self.queue_service.delete_message(self.input_queue, message.id, message.pop_receipt)
                try:
                    btime = datetime.now()
                    row_id = csv_line[0]
                    self.send_to_loop_method(arg_per_node,csv_line)                    
                    atime = datetime.now() - btime
                    sline = '{0} ,{1}'.format(row_id, atime.microseconds)
                    # no error so write to the success q
                    self.queue_service.put_message(self.success_queue, sline)
                except Exception as e:
                    # error - write to error queue
                    print(traceback.format_exc())
                    # print(e)
                    error_str = 'ID:{0} failed. Error: {1}'.format(row_id, str(e))
                    self.queue_service.put_message(self.fail_queue, error_str)
        print('Job ended.')

def setup():
    parser = argparse.ArgumentParser()   
    parser.add_argument("-inifile", "--init_file", action="store", default='init_tennis.ini',
                        help="an init file holding configuration")
    parser.add_argument("-workingpath", "--video_path", action="store", default='N/A',
                    help="path to working directory")                        
    parser.add_argument("-outfldr", "--path_for_output_folder", action="store", default='N/A',
                    help="path for output folder")   
    parser.add_argument("-resourcefldr", "--resourcs_path", action="store", default='N/A',
                    help="path for output folder")                                                                              
    args = parser.parse_args()
    return args



