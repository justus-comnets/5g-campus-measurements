#! /usr/bin/python3

import numpy as np
import statsmodels.api as sm
from KDEpy import FFTKDE
import matplotlib.pyplot as plt
from matplotlib.pyplot import cm
from matplotlib.ticker import (AutoMinorLocator, MultipleLocator, LogLocator, NullFormatter)
from matplotlib.image import NonUniformImage
import sys
import collections

sys.path.append("..")
import pcap_parser
import os
from multiprocessing import Pool
import argparse
import subprocess
import plotting


class Plot:
    def __init__(self, logdir, labels=None):
        self.logdir = os.path.expanduser(logdir) + "/"
        self.pp_dict = {}

        # file_dict = {pktSize: pktRates: numPkts}
        self.file_dict = {}
        self.results_dict = {}
        self.scenario_results_dict = None

    def analyze(self, filter=''):
        workers_dict = {}
        with Pool() as pool:
            files = pcap_parser.find_pcap_files(self.logdir)

            self.pp_dict["req"] = collections.defaultdict(lambda: collections.defaultdict(None))
            self.pp_dict["rpl"] = collections.defaultdict(lambda: collections.defaultdict(None))

            self.file_dict["req"] = collections.defaultdict(lambda: collections.defaultdict(None))
            self.file_dict["rpl"] = collections.defaultdict(lambda: collections.defaultdict(None))

            workers_dict["req"] = collections.defaultdict(lambda: collections.defaultdict(None))
            workers_dict["rpl"] = collections.defaultdict(lambda: collections.defaultdict(None))

            for file in files:
                # print(file)
                if not filter in file:
                    continue
                drct, pktsize, pktrate = file.split("/")[-1].split(".")[:-1]  # .req.128.10.pcap
                self.pp_dict[drct][pktsize][pktrate] = pcap_parser.PCAPParser(file=file)
                self.file_dict[drct][pktsize][pktrate] = file
                workers_dict[drct][pktsize][pktrate] = None

            self.results_dict = workers_dict

            opts = {"save_pickle": False, "load_pickle": True}

            for drct in self.file_dict.keys():
                for pktsize in self.file_dict[drct].keys():
                    for pktrate in self.file_dict[drct][pktsize].keys():
                        file = self.file_dict[drct][pktsize][pktrate]
                        workers_dict[drct][pktsize][pktrate] = pool.apply_async(
                            self.pp_dict[drct][pktsize][pktrate].analyze, args=[file], kwds=opts)

            for drct in workers_dict.keys():
                for pktsize in workers_dict[drct].keys():
                    for pktrate in workers_dict[drct][pktsize].keys():
                        self.results_dict[drct][pktsize][pktrate] = workers_dict[drct][pktsize][pktrate].get()

    def analyze_scenario(self, plot_type, **kwargs):

        workers_dict = {}
        self.scenario_results_dict = {}
        for drct in self.pp_dict.keys():
            workers_dict[drct] = {}
            self.scenario_results_dict[drct] = {}
            for pktSize in self.pp_dict[drct].keys():
                workers_dict[drct][pktSize] = {}
                self.scenario_results_dict[drct][pktSize] = {}

        with Pool() as pool:
            for drct in self.file_dict.keys():
                for pktSize in self.file_dict[drct].keys():
                    for pktRate in self.file_dict[drct][pktSize].keys():
                        if "owd" in plot_type:
                            workers_dict[drct][pktSize][pktRate] = pool.apply_async(
                                self.pp_dict[drct][pktSize][pktRate].owdelay,
                                args=[*self.results_dict[drct][pktSize][pktRate]])
                            # kwds={"return_seqnos": True})
                        elif "ipdv" in plot_type:
                            workers_dict[drct][pktSize][pktRate] = pool.apply_async(
                                self.pp_dict[drct][pktSize][pktRate].ipdv,
                                args=[*self.results_dict[drct][pktSize][pktRate]])

            for drct in workers_dict.keys():
                for pktSize in workers_dict[drct].keys():
                    for pktRate in workers_dict[drct][pktSize].keys():
                        data_seqno = self.results_dict[drct][pktSize][pktRate][0]
                        self.scenario_results_dict[drct][pktSize][pktRate] = (
                            workers_dict[drct][pktSize][pktRate].get(), data_seqno)

        print("Finished analyzing Scenarios.")

    # https://stackoverflow.com/questions/2369492/generate-a-heatmap-in-matplotlib-using-a-scatter-data-set
    # https://stackoverflow.com/questions/6387819/generate-a-heatmap-in-matplotlib-using-a-scatter-data-set
    # https://numpy.org/doc/stable/reference/generated/numpy.histogram2d.html
    def show_correlation(self):
        for pktSize in self.scenario_results_dict["req"].keys():
            for pktRate in self.scenario_results_dict["req"][pktSize].keys():
                req_delta_t, rpl_delta_t = filter_delays(*self.scenario_results_dict["req"][pktSize][pktRate],
                                                         *self.scenario_results_dict["rpl"][pktSize][pktRate])
                req_edges = np.arange(0.003, 0.02, 0.1)
                rpl_edges = np.arange(0.003, 0.02, 0.1)

                heatmap, xedges, yedges = np.histogram2d(s_to_ms(req_delta_t), s_to_ms(rpl_delta_t),
                                                         bins=(req_edges, rpl_edges))
                extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

                fig, ax = plt.subplots(tight_layout=True)

                ax.imshow(heatmap.T, extent=extent, origin='lower', interpolation='nearest', cmap=cm.binary)
                # ax = fig.add_subplot(111, title='NonUniformImage: interpolated', aspect='equal', xlim=xedges[[0, -1]],
                #                      ylim=yedges[[0, -1]])
                # im = NonUniformImage(ax, interpolation='bilinear')
                # xcenters = (xedges[:-1] + xedges[1:]) / 2
                # ycenters = (yedges[:-1] + yedges[1:]) / 2
                # im.set_data(xcenters, ycenters, heatmap.T)
                # ax.images.append(im)

                # ax.scatter(req_delta_t, rpl_delta_t, alpha=0.05, marker='.', s=1)

                ax.set_title(f"{pktSize}.{pktRate}")
                ax.set_ylabel('Upload Delay (ms)')
                ax.set_xlabel('Download Delay (ms)')
                ax.grid(True)
                # label_s_to_ms(ax)
                plt.show()

    def show_rtt_cdf(self, paper=False, save=None, show=True):
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

        fig, ax = plt.subplots(tight_layout=True)
        if not paper:
            ax.set_title(r"Round-Trip Time Distribution (ECDF)")
        ax.set_xscale('log')
        ax.set_ylabel(r'ECDF')
        ax.set_xlabel(r'Round-Trip Time (ms)')
        ax.grid(True)

        pktSize = "128"
        for pktRate in sorted(self.scenario_results_dict["req"][pktSize].keys(), key=int):
            req_delta_t, rpl_delta_t = filter_delays(*self.scenario_results_dict["req"][pktSize][pktRate],
                                                     *self.scenario_results_dict["rpl"][pktSize][pktRate])
            rtt_delta_t = [req + rpl for (req, rpl) in zip(s_to_ms(req_delta_t), s_to_ms(rpl_delta_t))]
            ecdf = sm.distributions.empirical_distribution.ECDF(rtt_delta_t)
            x = np.linspace(min(rtt_delta_t), max(rtt_delta_t), num=1000)
            y = ecdf(x)

            ax.step(x, y, label=pktRate)

        ax.legend()
        if show:
            plt.show()
        plt.close()

    def show_rtt_kde(self, paper=False, save=None, show=True):
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

        fig, ax = plt.subplots(tight_layout=True)
        if not paper:
            ax.set_title(r"Round-Trip Time Density")
        ax.set_xscale('log')
        ax.set_ylabel(r'Density (1/ms)')
        ax.set_xlabel(r'Round-Trip Time (ms)')
        ax.grid(True)

        pktSize = "128"
        for pktRate in sorted(self.scenario_results_dict["req"][pktSize].keys(), key=int):
            req_delta_t, rpl_delta_t = filter_delays(*self.scenario_results_dict["req"][pktSize][pktRate],
                                                     *self.scenario_results_dict["rpl"][pktSize][pktRate])
            rtt_delta_t = [req + rpl for (req, rpl) in zip(s_to_ms(req_delta_t), s_to_ms(rpl_delta_t))]
            ecdf = sm.distributions.empirical_distribution.ECDF(rtt_delta_t)
            x = np.linspace(min(rtt_delta_t), max(rtt_delta_t), num=1000)
            kde = sm.nonparametric.KDEMultivariate(data=rtt_delta_t, var_type='u')
            y = kde.pdf(x)

            ax.step(x, y, label=pktRate)

        ax.legend()
        if show:
            plt.show()
        plt.close()

    def show_correlation_multiple(self, paper=True, save=None, show=True):
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
            plotting.setup(span=True)

        fig, axs = plt.subplots(2, 3, tight_layout=True)

        if "logs/UdpPing/download" in self.logdir:
            plots = {
                "128": {"10": {"req": (6, 10), "rpl": (3, 10)},
                        "1000": {"req": (7, 16), "rpl": (3, 13)},
                        "10000": {"req": (6, 14), "rpl": (3, 22)}},
                "1280": {"10": {"req": (6, 12), "rpl": (8, 15)},
                         "1000": {"req": (7, 15), "rpl": (4, 22)},
                         "10000": {"req": (5, 13), "rpl": (10, 30)}}
            }
        elif "logs/UdpPingPoisson/download" in self.logdir:
            plots = {
                "128": {"10": {"req": (4, 13), "rpl": (3, 9)},
                        "1000": {"req": (4, 14), "rpl": (3, 11)},
                        "10000": {"req": (4, 12), "rpl": (3, 21)}},
                "1280": {"10": {"req": (4, 13), "rpl": (5, 14)},
                         "1000": {"req": (5, 14), "rpl": (3, 21)},
                         "10000": {"req": (5, 12), "rpl": (6, 23)}}
            }
        else:
            plots = {
                "128": {"10": {"req": (0, 40), "rpl": (0, 40)},
                        "1000": {"req": (0, 40), "rpl": (0, 40)},
                        "10000": {"req": (0, 40), "rpl": (0, 40)}},
                "1280": {"10": {"req": (0, 40), "rpl": (0, 40)},
                         "1000": {"req": (0, 40), "rpl": (0, 40)},
                         "10000": {"req": (0, 40), "rpl": (0, 40)}}
            }

        for r, pktSize in enumerate(plots.keys()):
            for c, pktRate in enumerate(plots[pktSize].keys()):
                req_delta_t, rpl_delta_t = filter_delays(*self.scenario_results_dict["req"][pktSize][pktRate],
                                                         *self.scenario_results_dict["rpl"][pktSize][pktRate])
                req_edges = np.arange(*plots[pktSize][pktRate]["req"], 0.1)
                rpl_edges = np.arange(*plots[pktSize][pktRate]["rpl"], 0.1)

                heatmap, xedges, yedges = np.histogram2d(s_to_ms(req_delta_t), s_to_ms(rpl_delta_t),
                                                         bins=(req_edges, rpl_edges))
                extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

                axs[r, c].imshow(heatmap.T, extent=extent, origin='lower', interpolation='nearest', cmap=cm.binary)
                # ax = fig.add_subplot(111, title='NonUniformImage: interpolated', aspect='equal', xlim=xedges[[0, -1]],
                #                      ylim=yedges[[0, -1]])
                # im = NonUniformImage(ax, interpolation='bilinear')
                # xcenters = (xedges[:-1] + xedges[1:]) / 2
                # ycenters = (yedges[:-1] + yedges[1:]) / 2
                # im.set_data(xcenters, ycenters, heatmap.T)
                # ax.images.append(im)

                # ax.scatter(req_delta_t, rpl_delta_t, alpha=0.05, marker='.', s=1)

                axs[r, c].set_title(f"PktSize: {pktSize}\,bytes    PktRate: {pktRate}\,pps")
                if c == 0:
                    axs[r, c].set_ylabel('Uplink Delay (ms)')
                if r == len(plots.keys()) - 1:
                    axs[r, c].set_xlabel('Downlink Delay (ms)')
                axs[r, c].grid(True)
                axs[r, c].set_aspect('auto')

        if save:
            print("Save: ", save)
            plt.savefig(save)

        if show:
            plt.show()

        plt.close()

    def show_owds_cdf(self, paper=False, save=None, show=True):
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

        fig, ax = plt.subplots(tight_layout=True)
        if not paper:
            ax.set_title(r"One-Way Delay Distribution (ECDF)")
        ax.set_xscale('log')
        ax.set_ylabel(r'ECDF')
        ax.set_xlabel(r'One-Way Delay (ms)')
        ax.grid(True)

        dl_delta_t_list = []
        ul_delta_t_list = []
        labels = []

        pktSize = "128"
        for i, pktRate in enumerate(sorted(self.scenario_results_dict["req"][pktSize].keys(), key=int)):
            req_delta_t, rpl_delta_t = filter_delays(*self.scenario_results_dict["req"][pktSize][pktRate],
                                                     *self.scenario_results_dict["rpl"][pktSize][pktRate])
            dl_delta_t_list.append(s_to_ms(req_delta_t))
            ul_delta_t_list.append(s_to_ms(rpl_delta_t))
            labels.append(pktRate)

        for i, dl_delta_t in enumerate(dl_delta_t_list):
            ecdf = sm.distributions.empirical_distribution.ECDF(dl_delta_t)
            x = np.linspace(min(dl_delta_t), max(dl_delta_t), num=1000)
            y = ecdf(x)
            if i == 0:
                lines = ax.step(x, y, label=r"Dl.-Delay", linestyle="solid", alpha=0, color="black")
                lines[0].set_alpha(1)
            ax.step(x, y, label=labels[i], linestyle="solid")

        ax.set_prop_cycle(None)
        for i, ul_delta_t in enumerate(ul_delta_t_list):
            ecdf = sm.distributions.empirical_distribution.ECDF(ul_delta_t)
            x = np.linspace(min(ul_delta_t), max(ul_delta_t), num=1000)
            y = ecdf(x)
            if i == 0:
                lines = ax.step(x, y, label=r"Ul.-Delay", linestyle="dotted", alpha=0, color="black")
                lines[0].set_alpha(1)
            ax.step(x, y, label=labels[i], linestyle="dotted")

        ax.legend(ncol=2)
        if show:
            plt.show()
        plt.close()


def show_rtt_kde_multiple_pktRates(scenario_results_dict_list, labels, paper=False, save=None, show=True):
    linestyles = ["solid", "dotted", "dashed", "dashdot"]
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

    fig, ax = plt.subplots(tight_layout=True)
    if not paper:
        ax.set_title(r"Round-Trip Time Density")
    # ax.set_xscale('log')
    ax.set_ylabel(r'Density (1/ms)')
    ax.set_xlabel(r'Round-Trip Time (ms)')
    ax.grid(True)

    pktSize = "128"
    ax.set_prop_cycle(None)
    for c, scenario_results_dict in enumerate(scenario_results_dict_list):
        ax.set_prop_cycle(None)
        for i, pktRate in enumerate(sorted(scenario_results_dict["req"][pktSize].keys(), key=int)):
            if pktRate == "10000": continue
            req_delta_t, rpl_delta_t = filter_delays(*scenario_results_dict["req"][pktSize][pktRate],
                                                     *scenario_results_dict["rpl"][pktSize][pktRate])
            rtt_delta_t = [req + rpl for (req, rpl) in zip(s_to_ms(req_delta_t), s_to_ms(rpl_delta_t))]
            print(min(rtt_delta_t), max(rtt_delta_t))
            x, y = FFTKDE(kernel='gaussian', bw='ISJ').fit(rtt_delta_t).evaluate()
            if i == 0:
                lines = ax.plot(x, y, label=labels[c], linestyle=linestyles[c], alpha=0, color="black")
                lines[0].set_alpha(1)

            ax.plot(x, y, label=pktRate, linestyle=linestyles[c])

    ax.legend(ncol=len(labels))
    ax.set_xlim([11, 22])
    ax.set_ylim([0, 2])
    ax.xaxis.set_minor_locator(AutoMinorLocator(4))
    ax.grid(True, which="minor", linestyle=':')

    if save:
        print("Save: ", save)
        plt.savefig(save)

    if show:
        plt.show()
    plt.close()


def show_rtt_kde_multiple_pktSizes(scenario_results_dict_list, labels, paper=False, save=None, show=True):
    linestyles = ["solid", "dotted", "dashed", "dashdot"]
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

    fig, ax = plt.subplots(tight_layout=True)
    if not paper:
        ax.set_title(r"Round-Trip Time Density")
    # ax.set_xscale('log')
    ax.set_ylabel(r'Density (1/ms)')
    ax.set_xlabel(r'Round-Trip Time (ms)')
    ax.grid(True)

    pktRate = "1000"
    ax.set_prop_cycle(None)
    for c, scenario_results_dict in enumerate(scenario_results_dict_list):
        ax.set_prop_cycle(None)
        for i, pktSize in enumerate(sorted(
                [size for size in list(scenario_results_dict["req"].keys()) if
                 pktRate in scenario_results_dict["req"][size].keys()], key=int)):
            req_delta_t, rpl_delta_t = filter_delays(*scenario_results_dict["req"][pktSize][pktRate],
                                                     *scenario_results_dict["rpl"][pktSize][pktRate])
            rtt_delta_t = [req + rpl for (req, rpl) in zip(s_to_ms(req_delta_t), s_to_ms(rpl_delta_t))]
            print(min(rtt_delta_t), max(rtt_delta_t))
            x, y = FFTKDE(kernel='gaussian', bw='ISJ').fit(rtt_delta_t).evaluate()
            if i == 0:
                lines = ax.plot(x, y, label=labels[c], linestyle=linestyles[c], alpha=0, color="black")
                lines[0].set_alpha(1)

            ax.plot(x, y, label=pktSize, linestyle=linestyles[c])

    ax.legend(ncol=len(labels))
    ax.set_xlim([15, 32])
    ax.xaxis.set_major_locator(MultipleLocator(2))
    ax.xaxis.set_minor_locator(AutoMinorLocator(4))
    ax.grid(True, which="minor", linestyle=':')

    if save:
        print("Save: ", save)
        plt.savefig(save)

    if show:
        plt.show()
    plt.close()


def show_rtt_cdf_multiple_pktRates(scenario_results_dict_list, labels, paper=False, save=None, show=True):
    linestyles = ["solid", "dotted", "dashed", "dashdot"]
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

    fig, ax = plt.subplots(tight_layout=True)
    if not paper:
        ax.set_title(r"Round-Trip Time Distribution (ECDF)")
    ax.set_xscale('log')
    ax.set_ylabel(r'ECDF')
    ax.set_xlabel(r'Round-Trip Time (ms)')
    ax.grid(True)

    pktSize = "128"
    for c, scenario_results_dict in enumerate(scenario_results_dict_list):
        ax.set_prop_cycle(None)
        for i, pktRate in enumerate(sorted(scenario_results_dict["req"][pktSize].keys(), key=int)):
            req_delta_t, rpl_delta_t = filter_delays(*scenario_results_dict["req"][pktSize][pktRate],
                                                     *scenario_results_dict["rpl"][pktSize][pktRate])
            rtt_delta_t = [req + rpl for (req, rpl) in zip(s_to_ms(req_delta_t), s_to_ms(rpl_delta_t))]
            ecdf = sm.distributions.empirical_distribution.ECDF(rtt_delta_t)
            x = np.linspace(min(rtt_delta_t), max(rtt_delta_t), num=1000)
            y = ecdf(x)
            if i == 0:
                lines = ax.step(x, y, label=labels[c], linestyle=linestyles[c], alpha=0, color="black")
                lines[0].set_alpha(1)

            ax.step(x, y, label=pktRate, linestyle=linestyles[c])

    ax.legend(ncol=len(labels), columnspacing=0.5, borderaxespad=0.1)
    ax.set_xlim([10, 50])
    ax.xaxis.set_major_locator(MultipleLocator(10))
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.grid(True, which="minor", linestyle=':')

    if save:
        print("Save: ", save)
        plt.savefig(save)

    if show:
        plt.show()
    plt.close()


def show_rtt_cdf_multiple_pktSizes(scenario_results_dict_list, labels, paper=False, save=None, show=True):
    linestyles = ["solid", "dotted", "dashed", "dashdot"]
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

    fig, ax = plt.subplots(tight_layout=True)
    if not paper:
        ax.set_title(r"Round-Trip Time Distribution (ECDF)")
    ax.set_xscale('log')
    ax.set_ylabel(r'ECDF')
    ax.set_xlabel(r'Round-Trip Time (ms)')
    ax.grid(True)

    pktRate = "1000"
    for c, scenario_results_dict in enumerate(scenario_results_dict_list):
        ax.set_prop_cycle(None)
        for i, pktSize in enumerate(sorted(
                [size for size in list(scenario_results_dict["req"].keys()) if
                 pktRate in scenario_results_dict["req"][size].keys()], key=int)):
            req_delta_t, rpl_delta_t = filter_delays(*scenario_results_dict["req"][pktSize][pktRate],
                                                     *scenario_results_dict["rpl"][pktSize][pktRate])
            rtt_delta_t = [req + rpl for (req, rpl) in zip(s_to_ms(req_delta_t), s_to_ms(rpl_delta_t))]
            ecdf = sm.distributions.empirical_distribution.ECDF(rtt_delta_t)
            x = np.linspace(min(rtt_delta_t), max(rtt_delta_t), num=1000)
            y = ecdf(x)
            if i == 0:
                lines = ax.step(x, y, label=labels[c], linestyle=linestyles[c], alpha=0, color="black")
                lines[0].set_alpha(1)

            ax.step(x, y, label=pktSize, linestyle=linestyles[c])

    ax.legend(ncol=len(labels), columnspacing=0.5, borderaxespad=0.1)
    ax.set_xlim([10, 50])
    ax.xaxis.set_major_locator(MultipleLocator(10))
    ax.xaxis.set_minor_locator(MultipleLocator(1))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_minor_locator(AutoMinorLocator(2))
    ax.grid(True, which="minor", linestyle=':')

    if save:
        print("Save: ", save)
        plt.savefig(save)

    if show:
        plt.show()
    plt.close()


def show_ipdv_cdf_multiple_pktRates(scenario_results_dict_list, labels, paper=False, save=None, show=True):
    linestyles = ["solid", "dotted", "dashed", "dashdot"]
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

    fig, ax = plt.subplots(tight_layout=True)
    if not paper:
        ax.set_title(r"Inter-Packet Delay Variation (ECDF)")
    ax.set_ylabel(r'ECDF')
    ax.set_xlabel(r'Inter-Packet Delay Variation (ms)')
    ax.grid(True)

    pktSize = "128"
    for c, scenario_results_dict in enumerate(scenario_results_dict_list):
        ax.set_prop_cycle(None)
        for i, pktRate in enumerate(sorted(scenario_results_dict["req"][pktSize].keys(), key=int)):
            req_ipdv, rpl_ipdv = filter_delays(*scenario_results_dict["req"][pktSize][pktRate],
                                               *scenario_results_dict["rpl"][pktSize][pktRate])
            rtt_ipdv = [req + rpl for (req, rpl) in zip(s_to_ms(req_ipdv), s_to_ms(rpl_ipdv))]
            ecdf = sm.distributions.empirical_distribution.ECDF(rtt_ipdv)
            x = np.linspace(min(rtt_ipdv), max(rtt_ipdv), num=1000)
            y = ecdf(x)
            if i == 0:
                lines = ax.step(x, y, label=labels[c], linestyle=linestyles[c], alpha=0, color="black")
                lines[0].set_alpha(1)

            ax.step(x, y, label=pktRate, linestyle=linestyles[c])

    ax.legend(ncol=len(labels), columnspacing=0.5, borderaxespad=0.1)
    ax.set_xlim([-6, 6])

    if save:
        print("Save: ", save)
        plt.savefig(save)

    if show:
        plt.show()
    plt.close()

def show_ipdv_kde_multiple_pktRates(scenario_results_dict_list, labels, paper=False, save=None, show=True):
    linestyles = ["solid", "dotted", "dashed", "dashdot"]
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

    fig, ax = plt.subplots(tight_layout=True)
    if not paper:
        ax.set_title(r"IPDV Density (1/ms)")
    # ax.set_xscale('log')
    ax.set_ylabel(r'Density (1/ms)')
    ax.set_xlabel(r'IPDV (ms)')
    ax.grid(True)

    pktSize = "128"
    ax.set_prop_cycle(None)
    for c, scenario_results_dict in enumerate(scenario_results_dict_list):
        ax.set_prop_cycle(None)
        for i, pktRate in enumerate(sorted(scenario_results_dict["req"][pktSize].keys(), key=int)):
            # if pktRate == "10000": continue
            req_delta_t, rpl_delta_t = filter_delays(*scenario_results_dict["req"][pktSize][pktRate],
                                                     *scenario_results_dict["rpl"][pktSize][pktRate])
            rtt_delta_t = [req + rpl for (req, rpl) in zip(s_to_ms(req_delta_t), s_to_ms(rpl_delta_t))]
            print(min(rtt_delta_t), max(rtt_delta_t))
            x, y = FFTKDE(kernel='gaussian', bw='ISJ').fit(rtt_delta_t).evaluate()
            if i == 0:
                lines = ax.plot(x, y, label=labels[c], linestyle=linestyles[c], alpha=0, color="black")
                lines[0].set_alpha(1)

            ax.plot(x, y, label=pktRate, linestyle=linestyles[c])

    ax.legend(ncol=len(labels))
    # ax.set_xlim([11, 22])
    # ax.set_ylim([0, 2])
    ax.xaxis.set_minor_locator(AutoMinorLocator(4))
    ax.grid(True, which="minor", linestyle=':')

    if save:
        print("Save: ", save)
        plt.savefig(save)

    if show:
        plt.show()
    plt.close()


# filter out lost packets in reply trace
def filter_delays(req_delta_t_list, req_seqnos, rpl_delta_t_list, rpl_seqnos):
    req_delta_t_filtered = []
    rpl_delta_t_filtered = []
    req_indices = np.where(np.in1d(req_seqnos, rpl_seqnos, assume_unique=True))[0]
    for (rpl_delta_t, req_index) in zip(rpl_delta_t_list, req_indices):
        req_delta_t_filtered.append(req_delta_t_list[req_index])
        rpl_delta_t_filtered.append(rpl_delta_t)
    return req_delta_t_filtered, rpl_delta_t_filtered


def label_s_to_ms(ax):
    labels = [int(tick * 1000) for tick in ax.get_xticks()]
    ax.set_xticklabels(labels)
    labels = [int(tick * 1000) for tick in ax.get_yticks()]
    ax.set_yticklabels(labels)


def s_to_ms(delta_t_list):
    return [delta_t * 1000 for delta_t in delta_t_list]


def create_dir(log_dir="/tmp/measurements"):
    try:
        # os.mkdir(log_dir)
        user = subprocess.check_output("whoami").decode("utf-8").strip()
        os.system("sudo mkdir -p {}".format(log_dir))
        os.system("sudo chgrp {} -R {}".format(user, log_dir))
        os.system("sudo chown {} -R {}".format(user, log_dir))
    except OSError:
        print("Creation of the log directory {} failed".format(log_dir))
    else:
        print("Successfully created the log directory {}".format(log_dir))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--logdirs', help='Specify directories for logs/pcaps.',
                        default=['/tmp/udpping/download'], nargs='+')
    parser.add_argument('--labels', help='Specify labels for the logs specified with --logdirs. ',
                        default=[''], nargs='+')
    parser.add_argument('--plot-type', help='Specify plot type ("owd", "ipdv").',
                        default='owd')
    parser.add_argument('--show', help='Show plot.', action='store_true')
    parser.add_argument('--paper', help='Plots are formatted for paper.', action='store_true')
    parser.add_argument('--save', help='Save plot at specified directory.', default=None)
    parser.add_argument('--filter', help='Specify string (e.g ".128.10.") to be in file name.', default='')

    args = parser.parse_args()

    p = {}
    for logdir in args.logdirs:
        p[logdir] = Plot(logdir)
        p[logdir].analyze(filter=args.filter)
        p[logdir].analyze_scenario(args.plot_type)
        # p[logdir].show_correlation()
        # p[logdir].show_rtt_cdf()
        # p[logdir].show_correlation_multiple(save=args.save)
        # p[logdir].show_rtt_hist_pktRates()
        # p[logdir].show_rtt_kde()
        # p[logdir].show_owds_cdf(paper=args.paper, save=args.save)

    assert len(args.labels) == len(args.logdirs)
    scenario_results_dict_list = [p[logdir].scenario_results_dict for logdir in p.keys()]
    # show_rtt_cdf_multiple_pktRates(scenario_results_dict_list, args.labels, paper=True, save=args.save)
    # show_rtt_cdf_multiple_pktSizes(scenario_results_dict_list, args.labels, paper=True, save=args.save)
    # show_ipdv_cdf_multiple_pktRates(scenario_results_dict_list, args.labels, paper=True, save=args.save)
    # show_rtt_kde_multiple_pktRates(scenario_results_dict_list, args.labels, paper=True, save=args.save)
    show_rtt_kde_multiple_pktSizes(scenario_results_dict_list, args.labels, paper=True, save=args.save)
    # show_ipdv_kde_multiple_pktRates(scenario_results_dict_list, args.labels, paper=True, save=args.save)