import os
import time
import csv

from curriculum import Curriculum
from evaluator import Evaluator
from visualizer import Visualizer
from session import Session

class Trainer(object):
    """
        The main trainer class that wraps the neural network
        and inject the hyperparameter to it

        Args:
            curriculum (Curriculum): the curriculum for the training
            visualizer (Visualizer): the Visualizer used to produce figures for the Curriculum
            evaluator (Evaluator): the Evaluator used to compare the training and the objectives
    """
    def __init__(self, curriculum, visualizer=None, evaluator=None):
        self._curriculum = curriculum
        self._visualizer = visualizer
        self._evaluator = evaluator if isinstance(evaluator, Evaluator) else Evaluator()
        self._session = None

    def train(self, output_path, training_callback, session_name="default"):
        """
            Execute the training process for the network
            For each new iteration inside the curriculum call the training_callback
            to start the training of the network

            Args:
                output_path (str): output path for the training results
                training_callback (function(activities):dict): called for each iteration
                session_name (str): name of the training session
        """
        if not os.path.exists(output_path):
            raise ValueError("Provided output path does not exists")

        # File configuration
        training_file_name = "{0}.csv".format(time.strftime("%Y%m%d-%H%M%S"))
        training_visualization_name = "{0}.png".format(time.strftime("%Y%m%d-%H%M%S"))
        training_file_data = []
        # The headers are built using these default values + the name of the activies, objectives, results and evaluation
        training_file_headers = ["id", "time_start", "time_stop", "time_diff"]
        current = self._curriculum.current()
        training_file_headers = training_file_headers + [key + "_activity" for key in current.get_activities().keys()]
        training_file_headers = training_file_headers + map(lambda objective: objective.get_objective() + "_objective", current.get_objectives())
        # The objective and evaluation corresponds to the resuls map
        training_file_headers = training_file_headers + map(lambda objective: objective.get_objective() + "_result", current.get_objectives())
        training_file_headers = training_file_headers + map(lambda objective: objective.get_objective() + "_evaluation", current.get_objectives())

        # The training Session use to train the network with the Curriculum
        self._session = Session(session_name)
        
        # Each time results are yield from the network
        def results_callback(results, program, time_start, time_stop):
            activities = program.get_activities()
            objectives = program.get_objectives()

            evaluation = self._evaluator.compare(results, objectives)
            
            # Save the data of this training
            data = [time_start, time_stop, time_stop-time_start, activities, objectives, results, evaluation]
            training_file_data.append(data)
            self.save_data(output_path, training_file_name, training_file_headers, training_file_data)
            # Add the data to the Visualization if defined
            if self._visualizer is not None:
                self._visualizer.add_results(activities, objectives, results, evaluation)
                # Output the plot at each iteration
                plt = self._visualizer.visualize()
                plt.savefig(output_path + "/" + training_visualization_name)
                plt.cla()

        self._session.start(self._curriculum, training_callback, results_callback)

    def save_data(self, output_path, file_name, headers, data):
        with open(output_path + "/" + file_name, "wb") as csvfile:
            writer = csv.writer(csvfile, delimiter=",")
            # @TODO: should write at the bottom of the file and not overwrite each time
            writer.writerow(headers)
            for index in xrange(len(data)):
                line = data[index]
                buff = [index, line[0], line[1], line[2]]
                # activity
                buff = buff + line[3].values()
                for objective in line[4]:
                    # objective
                    buff.append(objective.get_value())
                for objective in line[4]:
                    if objective.get_objective() in line[5]:
                        # results
                        buff.append(line[5][objective.get_objective()])
                buff = buff + line[6].values()
                writer.writerow(buff)


