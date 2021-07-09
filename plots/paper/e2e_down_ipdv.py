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
    parser = argparse.ArgumentParser()
    parser.add_argument('--show', help='Show plot.', action='store_true')
    args = parser.parse_args()

    save = "/home/justus/Pictures/plots/end2end/download/"
    logdirs = ["/media/justus/1TB/SA/VarParams/download", "/media/justus/1TB/NSA/VarParams/download"]
    labels = ["SA", "NSA"]

    p = plot.Plot(logdirs=logdirs, scenario="VarParams", labels=labels)
    p.analyze(core=False)
    p.analyze_scenario("multiplebp-ipdv")

    nested_ipdv_lists = []
    nested_labels = []
    for label in p.labels:
        pktSize = "128"
        pktRates_label = []
        ipdv_lists = []
        for pktRate in sorted(list(p.scenario_results_dict[label][pktSize].keys()), key=int)[:-1]:
            pktRates_label.append(pktRate)
            ipdv_lists.append(p.scenario_results_dict[label][pktSize][pktRate])
        nested_labels.append(pktRates_label)
        nested_ipdv_lists.append(ipdv_lists)

    var_params.show_ipdv_bp_multiple(nested_ipdv_lists, labels=nested_labels,
                                     categories=p.labels, show=args.show,
                                     xlabel="Packet rates (packets per second)", paper=True,
                                     save=save + "multiplebp-ipdv-pktRates.pdf" if save else None)

    var_params.show_ipdv_cdf_multiple(nested_ipdv_lists, labels=nested_labels,
                                      categories=p.labels, show=args.show, paper=True, xlim=[-4.5, 6],
                                      save=save + "multiplecdf-ipdv-pktRates.pdf" if save else None)

    nested_ipdv_lists = []
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
        nested_ipdv_lists.append(ipdv_lists)

    var_params.show_ipdv_bp_multiple(nested_ipdv_lists, labels=nested_labels, show=args.show,
                                     categories=p.labels, xlabel="Packet sizes (bytes)",
                                     paper=True, save=save + "multiplebp-ipdv-pktSizes.pdf" if save else None)

    var_params.show_ipdv_cdf_multiple(nested_ipdv_lists, labels=nested_labels,
                                      categories=p.labels, show=args.show, paper=True, xlim=[-3, 7],
                                      save=save + "multiplecdf-ipdv-pktSizes.pdf" if save else None)
