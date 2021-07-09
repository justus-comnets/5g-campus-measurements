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
    save = "/home/justus/Pictures/plots/core/download/multiplebp-pdv"
    logdirs = ["/media/justus/1TB/SA/VarParams/download", "/media/justus/1TB/NSA/VarParams/download"]
    labels = ["Open5GS", "Nokia"]

    p = plot.Plot(logdirs=logdirs, scenario="VarParams", labels=labels)
    p.analyze(core=True)
    p.analyze_scenario("multiplebp-pdv")

    nested_pdv_lists = []
    nested_labels = []
    for label in p.labels:
        pktSize = "128"
        pktRates_label = []
        ipdv_lists = []
        for pktRate in sorted(list(p.scenario_results_dict[label][pktSize].keys()), key=int)[:-1]:
            pktRates_label.append(pktRate)
            ipdv_lists.append(p.scenario_results_dict[label][pktSize][pktRate])
        nested_labels.append(pktRates_label)
        nested_pdv_lists.append(ipdv_lists)

    var_params.show_pdv_bp_multiple(nested_pdv_lists, labels=nested_labels,
                                         categories=p.labels, show=False,
                                         xlabel="Packet rates (packets per second)", paper=True,
                                         save=save + "-pktRates.pdf" if save else None)

    nested_pdv_lists = []
    nested_labels = []
    for label in p.labels:
        pktRate = "10000"
        pktSizes_label = []
        ipdv_lists = []
        for pktSize in sorted(
                [size for size in list(p.scenario_results_dict[label].keys()) if
                 pktRate in p.scenario_results_dict[label][size].keys()],
                key=int):
            pktSizes_label.append(pktSize)
            ipdv_lists.append(p.scenario_results_dict[label][pktSize][pktRate])
        nested_labels.append(pktSizes_label)
        nested_pdv_lists.append(ipdv_lists)

    var_params.show_pdv_bp_multiple(nested_pdv_lists, labels=nested_labels, show=False,
                                         categories=p.labels, xlabel="Packet sizes (bytes)",
                                         paper=True, save=save + "-pktSizes.pdf" if save else None)