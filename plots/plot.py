#! /usr/bin/python3

import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import sys

sys.path.append("..")
import pcap_parser
import os
from multiprocessing import Pool
from pathos.multiprocessing import ProcessPool
import argparse
import plotting

scenarios = {"VarParams": "var_params",
             "ThroughputTest": "throughput_test"}


class Plot:
    def __init__(self, logdirs=None, scenario="VarParams", labels=None):
        if logdirs is None:
            self.logdirs = "../logs/measurements/VarParams/download"
        else:
            self.logdirs = logdirs

        assert scenario in scenarios.keys()
        self.scenario = scenario
        assert len(labels) == len(self.logdirs)
        self.labels = labels

        self.pp_dict = {}

        # file_dict = {pktSize: pktRates: numPkts}
        self.file_dict = {}
        self.results_dict = {}
        self.scenario_results_dict = None
        self.core = None

    def analyze(self, core=False):
        self.core = core
        workers_dict = {}
        with Pool() as pool:
            for c, logdir in enumerate(self.logdirs):
                label = self.labels[c]
                workers_dict[label] = {}
                self.file_dict[label] = {}
                measurements_dir_rel = logdir
                measurements_dir = os.path.expanduser(measurements_dir_rel) + "/"

                obj_files = pcap_parser.find_obj_files(measurements_dir, core=core)
                files = pcap_parser.pseudo_pcap_files(obj_files, core=core)

                # params_list : [["128", "256",...], ["1000", "10000"]] [pktSizes, pktRates or burstSizes]
                params_list = [[], []]

                self.pp_dict[label] = {}

                for file in files:
                    params = file.split("/")[-1].split(".")
                    # pktSize = params[0]
                    # pktRate = params[1]

                    params_list[0].append(params[0]) if params[0] not in params_list[0] else params_list[0]
                    params_list[1].append(params[1]) if params[1] not in params_list[1] else params_list[1]

                    if params[0] in self.file_dict[label].keys():
                        self.file_dict[label][params[0]][params[1]] = file
                        workers_dict[label][params[0]][params[1]] = None
                        self.pp_dict[label][params[0]][params[1]] = pcap_parser.PCAPParser(
                            file=file)  # , cfiles=cfiles)
                    else:
                        self.file_dict[label][params[0]] = {}
                        workers_dict[label][params[0]] = {}
                        self.pp_dict[label][params[0]] = {}
                        self.file_dict[label][params[0]][params[1]] = file
                        workers_dict[label][params[0]][params[1]] = None
                        self.pp_dict[label][params[0]][params[1]] = pcap_parser.PCAPParser(file=file)  # ,cfiles=cfiles)

                sorted(params_list[0])
                sorted(params_list[1])

                self.results_dict[label] = workers_dict[label]

                if core:
                    opts = {"save_pickle": False, "load_pickle": True, "core_type": label}
                else:
                    opts = {"save_pickle": False, "load_pickle": True}

                for param0 in self.file_dict[label].keys():
                    for param1 in self.file_dict[label][param0].keys():
                        file = self.file_dict[label][param0][param1]
                        if core:
                            workers_dict[label][param0][param1] = pool.apply_async(
                                self.pp_dict[label][param0][param1].analyze_core,
                                args=[file],
                                kwds=opts)
                        else:
                            workers_dict[label][param0][param1] = pool.apply_async(
                                self.pp_dict[label][param0][param1].analyze,
                                args=[file],
                                kwds=opts)
            for label in workers_dict.keys():
                for param0 in workers_dict[label].keys():
                    for param1 in workers_dict[label][param0].keys():
                        self.results_dict[label][param0][param1] = workers_dict[label][param0][param1].get()

        print("Finished analyzing PCAPs.")

    def analyze_scenario(self, plot_type, **kwargs):

        workers_dict = {}
        self.scenario_results_dict = {}
        for label in self.pp_dict.keys():
            workers_dict[label] = {}
            self.scenario_results_dict[label] = {}
            for param in self.pp_dict[label].keys():
                workers_dict[label][param] = {}
                self.scenario_results_dict[label][param] = {}

        with Pool() as pool:
            if self.scenario == "VarParams":
                plot_types = ["single-owd",
                              "multiplecdf-owd", "multiplebp-owd",
                              "multiplecdf-ipdv", "multiplebp-ipdv",
                              "multiplecdf-pdv", "multiplebp-pdv",
                              "multiplecdf-downtime", "multiplebp-downtime",
                              "multiplebp-losses"]

                assert plot_type in plot_types
                for label in self.labels:
                    for pktSize in self.file_dict[label].keys():
                        for pktRate in self.file_dict[label][pktSize].keys():
                            if "owd" in plot_type:
                                workers_dict[label][pktSize][pktRate] = pool.apply_async(
                                    self.pp_dict[label][pktSize][pktRate].owdelay,
                                    args=[*self.results_dict[label][pktSize][pktRate]])
                            elif "ipdv" in plot_type:
                                workers_dict[label][pktSize][pktRate] = pool.apply_async(
                                    self.pp_dict[label][pktSize][pktRate].ipdv,
                                    args=[*self.results_dict[label][pktSize][pktRate]])
                            elif "pdv" in plot_type:
                                workers_dict[label][pktSize][pktRate] = pool.apply_async(
                                    self.pp_dict[label][pktSize][pktRate].pdv,
                                    args=[*self.results_dict[label][pktSize][pktRate]])
                            elif "downtime" in plot_type:
                                if "threshold" in kwargs:
                                    workers_dict[label][pktSize][pktRate] = pool.apply_async(
                                        self.pp_dict[label][pktSize][pktRate].downtime,
                                        args=[*self.results_dict[label][pktSize][pktRate]],
                                        kwds={"threshold": kwargs["threshold"]})
                                else:
                                    workers_dict[label][pktSize][pktRate] = pool.apply_async(
                                        self.pp_dict[label][pktSize][pktRate].downtime,
                                        args=[*self.results_dict[label][pktSize][pktRate]], kwds={"threshold": 0.01})
                            elif "losses" in plot_type:
                                workers_dict[label][pktSize][pktRate] = pool.apply_async(
                                    self.pp_dict[label][pktSize][pktRate].losses,
                                    args=[*self.results_dict[label][pktSize][pktRate]])

            elif self.scenario == "ThroughputTest":
                for label in self.labels:
                    for pktSize in self.file_dict[label].keys():
                        for burstSize in self.file_dict[label][pktSize].keys():
                            workers_dict[label][pktSize][burstSize] = pool.apply_async(
                                self.pp_dict[label][pktSize][burstSize].throughput_test,
                                args=[*self.results_dict[label][pktSize][burstSize]],
                                kwds={"pause_time": 0.9, "pkt_size": int(pktSize)})

            for label in workers_dict.keys():
                for param0 in workers_dict[label].keys():
                    for param1 in workers_dict[label][param0].keys():
                        self.scenario_results_dict[label][param0][param1] = workers_dict[label][param0][param1].get()

        print("Finished analyzing Scenarios.")

    def plot_scenario(self, plot_type, paper=False, save_dir=None, show=False):
        # TODO: try to remove redundant code
        save = None
        if save_dir:
            save = os.path.expanduser(save_dir) + "/"
            create_dir(save_dir)

        if self.scenario == "VarParams":
            scenario_module = __import__(scenarios[self.scenario])
            if plot_type == "single-owd":
                for label in self.labels:
                    pktSize = "1024"
                    pktRates_label = []
                    delta_t_lists = []
                    for pktRate in sorted(list(self.scenario_results_dict[label][pktSize].keys()), key=int):
                        pktRates_label.append(pktRate)
                        delta_t_lists.append(self.scenario_results_dict[label][pktSize][pktRate])
                    scenario_module.show_owdelay(delta_t_lists, labels=pktRates_label, paper=paper, save=save)

                    pktRate = "10000"
                    pktSizes_label = []
                    delta_t_lists = []
                    for pktSize in sorted(
                            [size for size in list(self.scenario_results_dict[label].keys()) if
                             pktRate in self.scenario_results_dict[label][size].keys()],
                            key=int):
                        pktSizes_label.append(pktSize)
                        delta_t_lists.append(self.scenario_results_dict[label][pktSize][pktRate])
                    scenario_module.show_owdelay(delta_t_lists, labels=pktSizes_label, paper=paper, save=save)

            elif plot_type == "multiplecdf-owd":
                if save:
                    save += plot_type
                nested_delta_t_lists = []
                nested_labels = []
                for label in self.labels:
                    pktSize = "128"
                    pktRates_label = []
                    delta_t_lists = []
                    for pktRate in sorted(list(self.scenario_results_dict[label][pktSize].keys()), key=int):
                        pktRates_label.append(pktRate)
                        delta_t_lists.append(self.scenario_results_dict[label][pktSize][pktRate])
                    nested_labels.append(pktRates_label)
                    nested_delta_t_lists.append(delta_t_lists)

                scenario_module.show_owdelay_cdf_multiple(nested_delta_t_lists, labels=nested_labels,
                                                          categories=self.labels, paper=paper, show=show,
                                                          save=save + "-pktRates.pdf" if save else None, core=self.core)

                nested_delta_t_lists = []
                nested_labels = []
                for label in self.labels:
                    pktRate = "10000"
                    pktSizes_label = []
                    delta_t_lists = []
                    for pktSize in sorted(
                            [size for size in list(self.scenario_results_dict[label].keys()) if
                             pktRate in self.scenario_results_dict[label][size].keys()],
                            key=int):
                        pktSizes_label.append(pktSize)
                        delta_t_lists.append(self.scenario_results_dict[label][pktSize][pktRate])
                    nested_labels.append(pktSizes_label)
                    nested_delta_t_lists.append(delta_t_lists)

                scenario_module.show_owdelay_cdf_multiple(nested_delta_t_lists, labels=nested_labels,
                                                          categories=self.labels, paper=paper, show=show,
                                                          save=save + "-pktSizes.pdf" if save else None, core=self.core)

            elif plot_type == "multiplebp-owd":
                if save:
                    save += plot_type
                nested_delta_t_lists = []
                nested_labels = []
                for label in self.labels:
                    pktSize = "128"
                    pktRates_label = []
                    delta_t_lists = []
                    for pktRate in sorted(list(self.scenario_results_dict[label][pktSize].keys()), key=int):
                        pktRates_label.append(pktRate)
                        delta_t_lists.append(self.scenario_results_dict[label][pktSize][pktRate])
                    nested_labels.append(pktRates_label)
                    nested_delta_t_lists.append(delta_t_lists)

                scenario_module.show_owdelay_bp_multiple(nested_delta_t_lists, labels=nested_labels,
                                                         categories=self.labels, show=show,
                                                         xlabel="Packet rates (packets per second)", paper=paper,
                                                         save=save + "-pktRates.pdf" if save else None, core=self.core)

                nested_delta_t_lists = []
                nested_labels = []
                for label in self.labels:
                    pktRate = "10000"
                    pktSizes_label = []
                    delta_t_lists = []
                    for pktSize in sorted(
                            [size for size in list(self.scenario_results_dict[label].keys()) if
                             pktRate in self.scenario_results_dict[label][size].keys()],
                            key=int):
                        pktSizes_label.append(pktSize)
                        delta_t_lists.append(self.scenario_results_dict[label][pktSize][pktRate])
                    nested_labels.append(pktSizes_label)
                    nested_delta_t_lists.append(delta_t_lists)

                scenario_module.show_owdelay_bp_multiple(nested_delta_t_lists, labels=nested_labels, show=show,
                                                         categories=self.labels, xlabel="Packet sizes (bytes)",
                                                         paper=paper, save=save + "-pktSizes.pdf" if save else None, core=self.core)

            elif plot_type == "multiplecdf-ipdv":
                if save:
                    save += plot_type
                nested_ipdv_lists = []
                nested_labels = []
                for label in self.labels:
                    pktSize = "128"
                    pktRates_label = []
                    ipdv_lists = []
                    for pktRate in sorted(list(self.scenario_results_dict[label][pktSize].keys()), key=int):
                        pktRates_label.append(pktRate)
                        ipdv_lists.append(self.scenario_results_dict[label][pktSize][pktRate])
                    nested_labels.append(pktRates_label)
                    nested_ipdv_lists.append(ipdv_lists)

                scenario_module.show_ipdv_cdf_multiple(nested_ipdv_lists, labels=nested_labels,
                                                       categories=self.labels, paper=paper, show=show,
                                                       save=save + "-pktRates.pdf" if save else None)

                nested_ipdv_lists = []
                nested_labels = []
                for label in self.labels:
                    pktRate = "10000"
                    pktSizes_label = []
                    ipdv_lists = []
                    for pktSize in sorted(
                            [size for size in list(self.scenario_results_dict[label].keys()) if
                             pktRate in self.scenario_results_dict[label][size].keys()],
                            key=int):
                        pktSizes_label.append(pktSize)
                        ipdv_lists.append(self.scenario_results_dict[label][pktSize][pktRate])
                    nested_labels.append(pktSizes_label)
                    nested_ipdv_lists.append(ipdv_lists)

                scenario_module.show_ipdv_cdf_multiple(nested_ipdv_lists, labels=nested_labels,
                                                       categories=self.labels, paper=paper, show=show,
                                                       save=save + "-pktSizes.pdf" if save else None)
            elif plot_type == "multiplebp-ipdv":
                if save:
                    save += plot_type
                nested_ipdv_lists = []
                nested_labels = []
                for label in self.labels:
                    pktSize = "128"
                    pktRates_label = []
                    ipdv_lists = []
                    for pktRate in sorted(list(self.scenario_results_dict[label][pktSize].keys()), key=int):
                        pktRates_label.append(pktRate)
                        ipdv_lists.append(self.scenario_results_dict[label][pktSize][pktRate])
                    nested_labels.append(pktRates_label)
                    nested_ipdv_lists.append(ipdv_lists)

                scenario_module.show_ipdv_bp_multiple(nested_ipdv_lists, labels=nested_labels,
                                                      categories=self.labels, show=show,
                                                      xlabel="Packet rates (packets per second)", paper=paper,
                                                      save=save + "-pktRates.pdf" if save else None)

                nested_ipdv_lists = []
                nested_labels = []
                for label in self.labels:
                    pktRate = "10000"
                    pktSizes_label = []
                    ipdv_lists = []
                    for pktSize in sorted(
                            [size for size in list(self.scenario_results_dict[label].keys()) if
                             pktRate in self.scenario_results_dict[label][size].keys()],
                            key=int):
                        pktSizes_label.append(pktSize)
                        ipdv_lists.append(self.scenario_results_dict[label][pktSize][pktRate])
                    nested_labels.append(pktSizes_label)
                    nested_ipdv_lists.append(ipdv_lists)

                scenario_module.show_ipdv_bp_multiple(nested_ipdv_lists, labels=nested_labels, show=show,
                                                      categories=self.labels, xlabel="Packet sizes (bytes)",
                                                      paper=paper, save=save + "-pktSizes.pdf" if save else None)

            elif plot_type == "multiplecdf-pdv":
                if save:
                    save += plot_type
                nested_pdv_lists = []
                nested_labels = []
                for label in self.labels:
                    pktSize = "128"
                    pktRates_label = []
                    pdv_lists = []
                    for pktRate in sorted(list(self.scenario_results_dict[label][pktSize].keys()), key=int):
                        pktRates_label.append(pktRate)
                        pdv_lists.append(self.scenario_results_dict[label][pktSize][pktRate])
                    nested_labels.append(pktRates_label)
                    nested_pdv_lists.append(pdv_lists)

                scenario_module.show_pdv_cdf_multiple(nested_pdv_lists, labels=nested_labels,
                                                      categories=self.labels, paper=paper, show=show,
                                                      save=save + "-pktRates.pdf" if save else None)

                nested_pdv_lists = []
                nested_labels = []
                for label in self.labels:
                    pktRate = "10000"
                    pktSizes_label = []
                    pdv_lists = []
                    for pktSize in sorted(
                            [size for size in list(self.scenario_results_dict[label].keys()) if
                             pktRate in self.scenario_results_dict[label][size].keys()],
                            key=int):
                        pktSizes_label.append(pktSize)
                        pdv_lists.append(self.scenario_results_dict[label][pktSize][pktRate])
                    nested_labels.append(pktSizes_label)
                    nested_pdv_lists.append(pdv_lists)

                scenario_module.show_pdv_cdf_multiple(nested_pdv_lists, labels=nested_labels,
                                                      categories=self.labels, paper=paper, show=show,
                                                      save=save + "-pktSizes.pdf" if save else None)
            elif plot_type == "multiplebp-pdv":
                if save:
                    save += plot_type
                nested_pdv_lists = []
                nested_labels = []
                for label in self.labels:
                    pktSize = "128"
                    pktRates_label = []
                    pdv_lists = []
                    for pktRate in sorted(list(self.scenario_results_dict[label][pktSize].keys()), key=int):
                        pktRates_label.append(pktRate)
                        pdv_lists.append(self.scenario_results_dict[label][pktSize][pktRate])
                    nested_labels.append(pktRates_label)
                    nested_pdv_lists.append(pdv_lists)

                scenario_module.show_pdv_bp_multiple(nested_pdv_lists, labels=nested_labels,
                                                     categories=self.labels, show=show,
                                                     xlabel="Packet rates (packets per second)", paper=paper,
                                                     save=save + "-pktRates.pdf" if save else None)

                nested_pdv_lists = []
                nested_labels = []
                for label in self.labels:
                    pktRate = "10000"
                    pktSizes_label = []
                    pdv_lists = []
                    for pktSize in sorted(
                            [size for size in list(self.scenario_results_dict[label].keys()) if
                             pktRate in self.scenario_results_dict[label][size].keys()],
                            key=int):
                        pktSizes_label.append(pktSize)
                        pdv_lists.append(self.scenario_results_dict[label][pktSize][pktRate])
                    nested_labels.append(pktSizes_label)
                    nested_pdv_lists.append(pdv_lists)

                scenario_module.show_pdv_bp_multiple(nested_pdv_lists, labels=nested_labels, show=show,
                                                     categories=self.labels, xlabel="Packet sizes (bytes)",
                                                     paper=paper, save=save + "-pktSizes.pdf" if save else None)

            elif plot_type == "multiplecdf-downtime":
                if save:
                    save += plot_type
                nested_downtimes = []
                nested_consecutives = []
                nested_labels = []
                for label in self.labels:
                    pktSize = "128"
                    pktRates_label = []
                    downtimes = []
                    consecutives = []
                    for pktRate in sorted(list(self.scenario_results_dict[label][pktSize].keys()), key=int):
                        pktRates_label.append(pktRate)
                        down, cons = self.scenario_results_dict[label][pktSize][pktRate]
                        downtimes.append(down)
                        consecutives.append(cons)
                    nested_labels.append(pktRates_label)
                    nested_downtimes.append(downtimes)

                scenario_module.show_downtime_cdf_multiple(nested_downtimes, labels=nested_labels,
                                                           categories=self.labels, paper=paper, show=show,
                                                           save=save + "-pktRates.pdf" if save else None)

                nested_downtimes = []
                nested_consecutives = []
                nested_labels = []
                for label in self.labels:
                    pktRate = "10000"
                    pktSizes_label = []
                    downtimes = []
                    consecutives = []
                    for pktSize in sorted(
                            [size for size in list(self.scenario_results_dict[label].keys()) if
                             pktRate in self.scenario_results_dict[label][size].keys()],
                            key=int):
                        pktSizes_label.append(pktSize)
                        down, cons = self.scenario_results_dict[label][pktSize][pktRate]
                        downtimes.append(down)
                        consecutives.append(cons)
                    nested_labels.append(pktSizes_label)
                    nested_downtimes.append(downtimes)

                scenario_module.show_downtime_cdf_multiple(nested_downtimes, labels=nested_labels,
                                                           categories=self.labels, paper=paper, show=show,
                                                           save=save + "-pktSizes.pdf" if save else None)
            elif plot_type == "multiplebp-downtime":
                if save:
                    save += "multiplebp"
                nested_downtimes = []
                nested_consecutives = []
                nested_labels = []
                for label in self.labels:
                    pktSize = "128"
                    pktRates_label = []
                    downtimes = []
                    consecutives = []
                    for pktRate in sorted(list(self.scenario_results_dict[label][pktSize].keys()), key=int):
                        pktRates_label.append(pktRate)
                        down, cons = self.scenario_results_dict[label][pktSize][pktRate]
                        downtimes.append(down)
                        consecutives.append(cons)
                    nested_labels.append(pktRates_label)
                    nested_downtimes.append(downtimes)
                    nested_consecutives.append(consecutives)

                scenario_module.show_downtime_bp_multiple(nested_downtimes, labels=nested_labels,
                                                          categories=self.labels, show=show,
                                                          xlabel="Packet rates (packets per second)",
                                                          paper=paper,
                                                          save=save + "-downtime-pktRates.pdf" if save else None)

                scenario_module.show_consecutive_bp_multiple(nested_consecutives, labels=nested_labels,
                                                             categories=self.labels, show=show,
                                                             xlabel="Packet rates (packets per second)",
                                                             paper=paper,
                                                             save=save + "-consecutive-pktRates.pdf" if save else None)

                nested_downtimes = []
                nested_consecutives = []
                nested_labels = []
                for label in self.labels:
                    pktRate = "10000"
                    pktSizes_label = []
                    downtimes = []
                    consecutives = []
                    for pktSize in sorted(
                            [size for size in list(self.scenario_results_dict[label].keys()) if
                             pktRate in self.scenario_results_dict[label][size].keys()],
                            key=int):
                        pktSizes_label.append(pktSize)
                        down, cons = self.scenario_results_dict[label][pktSize][pktRate]
                        downtimes.append(down)
                        consecutives.append(cons)
                    nested_labels.append(pktSizes_label)
                    nested_downtimes.append(downtimes)
                    nested_consecutives.append(consecutives)

                scenario_module.show_downtime_bp_multiple(nested_downtimes, labels=nested_labels,
                                                          categories=self.labels, xlabel="Packet sizes (bytes)",
                                                          show=show,
                                                          paper=paper,
                                                          save=save + "-downtime-pktSizes.pdf" if save else None)

                scenario_module.show_consecutive_bp_multiple(nested_consecutives, labels=nested_labels,
                                                             categories=self.labels, show=show,
                                                             xlabel="Packet rates (packets per second)",
                                                             paper=paper,
                                                             save=save + "-consecutive-pktSizes.pdf" if save else None)

        elif self.scenario == "ThroughputTest":
            pass


def create_dir(log_dir="/tmp/measurements"):
    try:
        # os.mkdir(log_dir)
        os.system("mkdir -p {}".format(log_dir))
    except OSError:
        print("Creation of the log directory {} failed".format(log_dir))
    else:
        print("Successfully created the log directory {}".format(log_dir))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', help='Specify scenario ("VarParams", "ThroughputTest").',
                        default='VarParams')
    parser.add_argument('--logdirs', help='Specify directories for logs/pcaps.',
                        default=['../logs/measurements/VarParams/download'], nargs='+')
    parser.add_argument('--labels', help='Specify labels for the logs specified with --logdirs. ',
                        default=['None'], nargs='+')
    parser.add_argument('--plot-type', help='Specify plot type ("single", "multiple").',
                        default='single')
    parser.add_argument('--core', help='Analyze core pcaps.', action='store_true')
    parser.add_argument('--show', help='Show plot.', action='store_true')
    parser.add_argument('--paper', help='Plots are formatted for paper.', action='store_true')
    parser.add_argument('--save', help='Save plot at specified directory.', default=None)

    args = parser.parse_args()

    p = Plot(logdirs=args.logdirs, scenario=args.scenario, labels=args.labels)
    p.analyze(core=args.core)
    p.analyze_scenario(args.plot_type)
    p.plot_scenario(args.plot_type, paper=args.paper, save_dir=args.save, show=args.show)
