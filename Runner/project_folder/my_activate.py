from node_runner import NodeRunner
from node_runner import setup
# import specific modules required for the run
# from process_data_function import *


class CustNodeRunner(NodeRunner):
    # override basic implementation with specific resource handeling
    # def set_up_args(self):     
    #     return load_paramters_and_resources(self.config)

    # sample override, rearanging argument order
    def send_to_loop_method(self, arg_per_node, csv_line):
        outfolder = self.cli_args.path_for_output_folder
        vidpath = self.cli_args.video_path
        return self.loop_method(outfolder, vidpath, arg_per_node[2], csv_line[2],csv_line[1],csv_line[0])
    # override and cast csv line to specific type
    def read_csv_line(self,line):
        csv_line = line.strip().split(',')
        csv_line[1] = [float(csv_line[1])]
        csv_line[2] = [csv_line[2]]
        return csv_line

args = setup()
myrunner = CustNodeRunner()
myrunner.set_up(args)
node_args = myrunner.set_up_args()

myrunner.ini_file = args.init_file
# process_data is the name of a function within specific imported custom module
myrunner.set_loop_method(process_data)

myrunner.run_on_node(node_args)
