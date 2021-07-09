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

    save = "/home/justus/Pictures/plots/end2end/upload/multiplecdf-owd"
    logdirs = ["/media/justus/1TB/SA/VarParams/upload", "/media/justus/1TB/NSA/VarParams/upload"]
    # logdirs = ["/home/justus/porsche/RTPanalyzer/logs/measurements/SA/VarParams/download/",
    #            "/home/justus/porsche/RTPanalyzer/logs/measurements/NSA/VarParams/download/"]
    labels = ["SA", "NSA"]

    p = plot.Plot(logdirs=logdirs, scenario="VarParams", labels=labels)
    p.analyze(core=False)
    p.analyze_scenario("multiplecdf-owd")

    nested_delta_t_lists = []
    nested_labels = []
    for label in p.labels:
        pktSize = "128"
        pktRates_label = []
        delta_t_lists = []
        for pktRate in sorted(list(p.scenario_results_dict[label][pktSize].keys()), key=int):
            pktRates_label.append(pktRate)
            delta_t_lists.append(p.scenario_results_dict[label][pktSize][pktRate])
        nested_labels.append(pktRates_label)
        nested_delta_t_lists.append(delta_t_lists)

    var_params.show_owdelay_cdf_multiple(nested_delta_t_lists, labels=nested_labels,
                                              categories=p.labels, paper=True, show=False,
                                              save=save + "-pktRates.pdf" if save else None)

    nested_delta_t_lists = []
    nested_labels = []
    for label in p.labels:
        pktRate = "1000"
        pktSizes_label = []
        delta_t_lists = []
        for pktSize in sorted(
                [size for size in list(p.scenario_results_dict[label].keys()) if
                 pktRate in p.scenario_results_dict[label][size].keys()],
                key=int):
            pktSizes_label.append(pktSize)
            delta_t_lists.append(p.scenario_results_dict[label][pktSize][pktRate])
        nested_labels.append(pktSizes_label)
        nested_delta_t_lists.append(delta_t_lists)

    var_params.show_owdelay_cdf_multiple(nested_delta_t_lists, labels=nested_labels,
                                              categories=p.labels, paper=True, show=False,
                                              save=save + "-pktSizes.pdf" if save else None)