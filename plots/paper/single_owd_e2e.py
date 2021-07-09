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
import os
from multiprocessing import Pool
import argparse
import plotting


if __name__ == "__main__":
    files = ["/media/justus/1TB/SA/VarParams/download/256.100.pcap",
             "/media/justus/1TB/SA/VarParams/download/256.1000.pcap"]
    pp0 = pcap_parser.PCAPParser(file=files[0])
    result0 = pp0.analyze(files[0], load_pickle=True)
    delta_t_list0 = pp0.owdelay(*result0)

    pp1 = pcap_parser.PCAPParser(file=files[1])
    result1 = pp1.analyze(files[1], load_pickle=True)
    delta_t_list1 = pp1.owdelay(*result1)

    paper=True
    if not paper:
        rc = {'backend': 'ps',
              'text.usetex': True,
              # 'text.latex.preamble': ['\\usepackage{gensymb}'],
              'axes.labelsize': 30,  # fontsize for x and y labels (was 10)
              'axes.titlesize': 30,
              'font.size': 30,  # was 10
              'legend.fontsize': 30,  # was 10
              'xtick.labelsize': 30,
              'ytick.labelsize': 30,
              'font.family': 'serif',
              'savefig.dpi': 300,
              'lines.linewidth': 3,
              'errorbar.capsize': 2,
              }
        rc.update({})
    else:
        plotting.setup()

    fig_cont, ax_cont = plt.subplots(tight_layout=True)
    # ax_cont = fig.add_subplot(212)
    # ax_cont.set_title(r"One-way Delay over Time")
    ax_cont.set_ylabel(r'One-Way Delay (ms)')
    ax_cont.set_xlabel(r'Time (ms)')
    ax_cont.grid(True)

    ax_cont.plot([i * 10 for i in range(len(delta_t_list0[2000:2040]))], [delta_t * 1000 for delta_t in delta_t_list0[2000:2040]], label="100 Packets per second")
    ax_cont.plot(range(len(delta_t_list1[20000:20400])), [delta_t * 1000 for delta_t in delta_t_list1[20000:20400]], label="1000 Packets per second")
    ax_cont.legend()

    save = "/home/justus/Pictures/plots/end2end/download/single_owd_e2e.pdf"
    plt.savefig(save)

    # plt.show()
    plt.close()
