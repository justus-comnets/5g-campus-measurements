#! /usr/bin/python3

import numpy as np
import statsmodels.api as sm
# https://stackoverflow.com/questions/19518352/tkinter-tclerror-couldnt-connect-to-display-localhost18-0/44922799
# import matplotlib
# matplotlib.use('pdf')
import matplotlib.pyplot as plt
import sys

sys.path.append("..")
sys.path.append("../..")
import pcap_parser
import plot
import var_params
import os
from multiprocessing import Pool
import argparse
import plotting


if __name__ == "__main__":
    save = "/home/justus/Pictures/plots/end2end/upload/multiplebp"
    logdirs = ["/media/justus/1TB/SA/VarParams/upload", "/media/justus/1TB/NSA/VarParams/upload"]

    labels = ["SA", "NSA"]

    p = plot.Plot(logdirs=logdirs, scenario="VarParams", labels=labels)
    p.analyze(core=False)
    p.analyze_scenario("multiplebp-downtime")


    nested_downtimes = []
    nested_consecutives = []
    nested_labels = []
    for label in p.labels:
        pktSize = "128"
        pktRates_label = []
        downtimes = []
        consecutives = []
        for pktRate in sorted(list(p.scenario_results_dict[label][pktSize].keys()), key=int):
            if pktRate == "100000":
                continue
            pktRates_label.append(pktRate)
            down, cons = p.scenario_results_dict[label][pktSize][pktRate]
            downtimes.append(down)
            consecutives.append(cons)
            print("Lengths Rate: {} Down: {} Cons: {}".format(pktRate,len(down), len(cons)))
        nested_labels.append(pktRates_label)
        nested_downtimes.append(downtimes)
        nested_consecutives.append(consecutives)

    var_params.show_downtime_bp_multiple(nested_downtimes, labels=nested_labels,
                                             categories=p.labels, show=False,
                                             xlabel="Packet rates (packets per second)",
                                             paper=True,
                                             save=save + "-downtime-pktRates.pdf" if save else None)

    var_params.show_consecutive_bp_multiple(nested_consecutives, labels=nested_labels,
                                              categories=p.labels, show=False,
                                              xlabel="Packet rates (packets per second)",
                                              paper=True,
                                              save=save + "-consecutive-pktRates.pdf" if save else None)

    nested_downtimes = []
    nested_consecutives = []
    nested_labels = []
    for label in p.labels:
        pktRate = "1000"
        pktSizes_label = []
        downtimes = []
        consecutives = []
        for pktSize in sorted(
                [size for size in list(p.scenario_results_dict[label].keys()) if
                 pktRate in p.scenario_results_dict[label][size].keys()],
                key=int):
            pktSizes_label.append(pktSize)
            down, cons = p.scenario_results_dict[label][pktSize][pktRate]
            downtimes.append(down)
            consecutives.append(cons)
        nested_labels.append(pktSizes_label)
        nested_downtimes.append(downtimes)
        nested_consecutives.append(consecutives)

    var_params.show_downtime_bp_multiple(nested_downtimes, labels=nested_labels,
                                            categories=p.labels, xlabel="Packet sizes (bytes)", show=False,
                                            paper=True, save=save + "-downtime-pktSizes.pdf" if save else None)

    var_params.show_consecutive_bp_multiple(nested_consecutives, labels=nested_labels,
                                              categories=p.labels, xlabel="Packet sizes (bytes)", show=False,
                                              paper=True, save=save + "-consecutive-pktSizes.pdf" if save else None)