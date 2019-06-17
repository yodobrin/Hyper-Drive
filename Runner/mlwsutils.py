from azureml.core.workspace import Workspace
from azureml.core import Experiment
from azureml.core import RunConfiguration
from azureml.train.estimator import *
from azureml.train.hyperdrive import RandomParameterSampling, BanditPolicy, HyperDriveConfig, PrimaryMetricGoal
from azureml.core import Datastore
from azureml.train.dnn import TensorFlow


def create_workspace():
    ws = Workspace.from_config()
    return ws



def create_run_configuration(config):
    rc = RunConfiguration()
    rc.environment.docker.enabled = True
    # point to an image in a private ACR      
    rc.environment.docker.base_image = config['image_registry']['base_image']  
    rc.environment.docker.base_image_registry.address = config['image_registry']['address']  
    rc.environment.docker.base_image_registry.username = config['image_registry']['acr_username'] 
    rc.environment.docker.base_image_registry.password = config['image_registry']['acr_pass'] 
    rc.environment.docker.gpu_support = True
    # don't let the system build a new conda environment
    rc.environment.python.user_managed_dependencies = True
    # point to an existing python environment within the custom image - change to your specific location
    rc.environment.python.interpreter_path = '/usr/bin/python3'
    return rc

def create_random_sampling():
    
    return RandomParameterSampling( {  } )



def create_mount(ds,dummy,path):
    # ensure target exist
    ds.upload(src_dir=dummy, target_path='./'+path)
    # create the path on the target ds and return as mount
    return ds.path(path).as_mount()

def create_script_parm(config,init_file,ds):
    out_path = config['experiment']['output_directory']
    work_path = config['experiment']['working_directory']
    resources_path = config['experiment']['resources_directory']
    dummy = config['experiment']['dummy_file']
    out_mount = create_mount(ds,dummy,out_path)
    work_mount = create_mount(ds,dummy,work_path)
    # future use: resources_mount = create_mount(ds,dummy,resources_path)

    script_params = {
    '--init_file' : init_file,
    '--video_path': work_mount, 
    '--path_for_output_folder': out_mount     
    }
    return script_params

def create_private_ds(config, ws):

    prvt_ds_name = config['experiment']['data_store_name']      
    prvt_ds_account_name = config['experiment']['storage_account'] 
    prvt_ds_container_name = config['experiment']['storage_container'] 
    prvt_ds_key = config['experiment']['storage_account_key'] 
    prvt_ds = Datastore.register_azure_blob_container(workspace=ws, 
                                             datastore_name=prvt_ds_name, 
                                             container_name=prvt_ds_container_name,
                                             account_name=prvt_ds_account_name, 
                                             account_key=prvt_ds_key,
                                             create_if_not_exists=True)
    return prvt_ds


#  an estimator per compute target
def create_estimator(self, ct):
    print('creating an estimator')
    est = TensorFlow(source_directory=self.project_folder,
                 script_params=self.script_params,
                 compute_target=ct,
                 entry_script=self.entry_script,
                 environment_definition=self.rc.environment,
                 source_directory_data_store=self.ds
                )
    return est

def create_hyper_drive(self, est):
    htc = HyperDriveConfig(estimator=est, 
                          hyperparameter_sampling=self.ps, 
                          primary_metric_name='wsc', 
                          primary_metric_goal=PrimaryMetricGoal.MAXIMIZE, 
                          max_total_runs=self.cluster_size,
                          max_concurrent_runs=self.cluster_size)
    return htc




    
