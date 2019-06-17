import argparse
from configparser import ConfigParser
import mlclusters as clusterutils
import project_folder.mlque as qutils
import mlwsutils as mlspace
from azure.storage.queue import QueueService,QueueMessageFormat
from azure.storage.blob import BlockBlobService
from azureml.core.workspace import Workspace
from azureml.core import Experiment
from azureml.core import RunConfiguration

from time import gmtime, strftime, sleep
import time
from datetime import datetime
import os

MAX_PER_CLUST = 70

class ExperimentConfiguration():

    def __init__(self,args_tuple):
        print('initliaze experiment configuration')
        self.ini_file_ml = args_tuple.init_file_ml
        self.ini_file_func = args_tuple.init_file_func
        self.clear_queues = args_tuple.clear_queues
        self.fill_queue = args_tuple.csv_to_queue_op
        self.read_conf()        
        self.update_func_ini()
        print('read ini files for ml wrapper and updated activation function ini file')
        
   
   # reads the two ini files
   
    def read_conf(self):
        self.config = ConfigParser()        
        self.config.read(self.ini_file_ml)
        self.config_func = ConfigParser()
        self.config_func.read(self.ini_file_func)

    def update_func_ini(self):
        self.config_func.set("queue_details","input_queue",self.config['queue_details']['input_queue'])
        self.config_func.set("queue_details","storage_account",self.config['queue_details']['storage_account'])
        self.config_func.set("queue_details","storage_account_key",self.config['queue_details']['storage_account_key'])
        with open(self.ini_file_func,"w") as f:
            self.config_func.write(f)

    """     Compute section       """

    def calculate_clusters(self,config):
        conf_ratio = int(config['parallel_execution']['parallel_ratio'])
        # if someone wants to mess with the current quota (we are limited)
        conf_ratio = (conf_ratio,980)[conf_ratio>=980]
        add_mod = (1,0)[conf_ratio % MAX_PER_CLUST == 0]
        self.num_of_clusters = conf_ratio // MAX_PER_CLUST + add_mod
        self.cluster_size = conf_ratio // self.num_of_clusters 

    def create_compute(self):
        self.calculate_clusters(self.config)
        print('creating compute {0} {1}'.format(self.num_of_clusters,self.cluster_size))
        # currently only NC6 low priority are created
        clusterutils.create_low_clusters(self.ws,self.num_of_clusters,self.cluster_size,30)

    def remove_compute(self):
        print('removed all compute resources')
        clusterutils.remove_compute(self.ws.compute_targets)        


    """   Workspace & Experiment section      """

    def create_workspace(self):
        self.ws = mlspace.create_workspace()
        print('Workspace name: ' + self.ws.name, 
                'Azure region: ' + self.ws.location, 
                'Subscription id: ' + self.ws.subscription_id, 
                'Resource group: ' + self.ws.resource_group, sep = '\n')        
        self.ds = self.ws.get_default_datastore()

    
    def create_experiment(self):
        self.experiment_name = self.config['experiment']['exp_name'] 
        print(self.experiment_name)
        self.exp = Experiment(workspace = self.ws, name = self.experiment_name)

    """    Queue operation section      """

    def obtain_queues_names(self):            
        inq = self.config["queue_details"]["input_queue"]
        sa = self.config["queue_details"]["storage_account"]
        sakey = self.config["queue_details"]["storage_account_key"]        
        self.input_queue = inq
        self.success_queue = '{0}-success'.format(self.input_queue)
        self.fail_queue = '{0}-fail'.format(self.input_queue)
        self.queue_service = QueueService(account_name=sa, account_key=sakey)
        self.queue_service.encode_function = QueueMessageFormat.text_base64encode

    def reset_queues(self):
        # default to clear/delete queues and fill with csv
        print('clearing all queues. all data is removed!')
        qutils.resetq(self.queue_service,self.input_queue)
        qutils.resetq(self.queue_service,self.success_queue)
        qutils.resetq(self.queue_service,self.fail_queue)

    def create_queues(self):
        # default to clear/delete queues and fill with csv
        print('recreating all queues.')
        qutils.createq(self.queue_service,self.input_queue)
        qutils.createq(self.queue_service,self.success_queue)
        qutils.createq(self.queue_service,self.fail_queue)

    def print_queue_size(self):        
        print('input queue: {0} '.format(qutils.getQSzie(self.queue_service,self.input_queue)) )
        print('success queue: {0} '.format(qutils.getQSzie(self.queue_service,self.success_queue)) )
        print('fail queue: {0} '.format(qutils.getQSzie(self.queue_service,self.fail_queue)) )

    def csv_to_queue_via_func(self):
        # obtain the csv file
        csv_file = self.config['experiment']['csv_file']
        # obtain the request queue
        request_q = self.config['queue_details']['request_queue']
        # obtain storage account & key
        sa_name =  self.config['queue_details']['storage_account']
        sa_key =  self.config['queue_details']['storage_account_key']
        container_2_use = self.config['queue_details']['container_2_use']
        records_per_file = int(self.config['queue_details']['records_per_file'])
        split_file_prefix = 'split'        
        messages = []
        filename = 1
        dest_folder = 'split'
        blob_service = BlockBlobService(account_name=sa_name, account_key=sa_key)
        csvfile = open(csv_file, 'r').readlines()
        for i in range(len(csvfile)):
            target_filename = f'{split_file_prefix}_{filename}.csv'
            target_filepath = os.path.join(dest_folder, target_filename)
            if i % records_per_file == 0:
                open(target_filepath, 'w+').writelines(csvfile[i:i+records_per_file])
                messages.append(f'{self.input_queue},{sa_name},{sa_key},{container_2_use},{target_filename}')
                # split the file and save the outcome to the blob container
                blob_service.create_blob_from_path(container_2_use,target_filename,target_filepath)
                filename += 1        
        # create message to the request queue
        for msg in messages:
            self.queue_service.put_message(request_q,msg)
        

    def csv_to_queue(self):
        csv_file = self.config['experiment']['csv_file']
        qutils.csv_to_queue_all(csv_file,self.input_queue,self.queue_service)    
        self.total_rows = qutils.getQSzie(self.queue_service,self.input_queue) 
        self.no_more_rows_ts = None   

    def check_progress(self):
        # total number of rows to handle is stored when csv is read
        # check the number of inq / errorq / successq
        # if the errorq + successq = total_rows -> experiment is over
        # if errorq + successq < total_rows && inq=0 -> there are no more rows to handle, but few might have 'gone' -> wait for 2 min before termination
        # function return false in all other cases
        num_errors = qutils.getQSzie(self.queue_service,self.fail_queue)
        num_success = qutils.getQSzie(self.queue_service,self.success_queue)
        num_left = qutils.getQSzie(self.queue_service,self.input_queue)
        if ( num_left == 0 and (num_errors + num_success == self.total_rows)): return True
        elif (num_left == 0 and self.no_more_rows_ts == None):
            # print('setting the ts')
            self.no_more_rows_ts = datetime.now()
            return False
        elif (num_left == 0 and self.no_more_rows_ts != None):
            now_time = datetime.now() - self.no_more_rows_ts
            # print('checking the ts')
            # check if 2 min had passed
            if(now_time.seconds > 30): return True
        return False

    def create_script_params(self):
        return mlspace.create_script_parm(self.config, self.ini_file_func, self.private_ds)

    """
    
    """

    def pre_activation(self):
        self.create_workspace()        
        self.create_experiment()
        self.rc = mlspace.create_run_configuration(self.config)        
        self.obtain_queues_names()
        if self.clear_queues == 'Yes':
            self.reset_queues()
        #self.create_queues()
        # use either a local method to load messages to main queue. If you installed/deployed an azure function to handle, can leverage that as well.
        # see https://github.com/yodobrin/csv2q
        if self.fail_queue == 'local':
            self.csv_to_queue()
        else : 
            self.csv_to_queue_via_func()
        
        self.print_queue_size()
        self.ps = mlspace.create_random_sampling()

        self.create_compute()

        for name, ct in self.ws.compute_targets.items():
            print(name, ct.type, ct.provisioning_state)
        self.private_ds = mlspace.create_private_ds(self.config,self.ws)
        self.script_params = self.create_script_params() 
        self.entry_script = self.config_func['script']['entry_script'] 
        self.project_folder = self.config['experiment']['project_folder']
        print('experiment setup phase completed:')
        print(self.script_params)        
        print('read init file {0}'.format(self.ini_file_ml))

    def submit_experiments(self):
        print("Submitting experiments::")
        print(strftime("%Y-%m-%d %H:%M:%S", gmtime()))
        htrDic = {}
        for name, ct in self.ws.compute_targets.items():
            est = mlspace.create_estimator(self,ct)
            htc = mlspace.create_hyper_drive(self,est)
            htrDic[name] = self.exp.submit(config=htc)
            print("Submited on cluster: {0} at {1}".format(name,strftime("%Y-%m-%d %H:%M:%S", gmtime())))
            # sleep between submition to multiple clusters
            sleep(46)


    def post_activation(self):
        while( not self.check_progress()):
            sleep(3)        
        print('ended test')
        self.remove_compute()
    
    def run_experiment(self):
        
        self.pre_activation()        
        # experiment submition
        # b_submit_ts = datetime.now()
        # self.submit_experiments()
        # a_submit_ts = datetime.now()
        # # wait for the experiment to complete
        # self.post_activation()
        # exp_end_ts = datetime.now() 
        # exp_total_time = exp_end_ts - a_submit_ts
        # submit_exp = a_submit_ts - b_submit_ts
        # print('submit experiments: {0} seconds'.format(submit_exp.seconds))
        # print('experiment completion {0} seconds'.format(exp_total_time.seconds))
        # total_run_time = exp_end_ts - b_submit_ts
        # print('Total time (setup + run) {0} seconds'.format(total_run_time.seconds))


# reads command line params
def setup():
    parser = argparse.ArgumentParser()
    parser.add_argument("-ini_ml", "--init_file_ml", action="store", default='init_ml.ini',
                    help="an init file holding configuration")
    parser.add_argument("-ini_func", "--init_file_func", action="store", default='init.ini',
                    help="an init file holding configuration")
    parser.add_argument("-re_q", "--clear_queues", action="store", default='No',
                    help="input-output-error queues clear")  
    parser.add_argument("-csv_2_q", "--csv_to_queue_op", action="store", default='local',
                    help="two options: local/func")  

    args = parser.parse_args()
    print(args)
    return args

def main():
    args = setup()
    configurator = ExperimentConfiguration(args)
    configurator.run_experiment()

if __name__ == '__main__':
    main()
    
   
