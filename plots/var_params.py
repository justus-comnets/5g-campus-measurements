#! /usr/bin/python3

import numpy as np
import statsmodels.api as sm
# https://stackoverflow.com/questions/19518352/tkinter-tclerror-couldnt-connect-to-display-localhost18-0/44922799
# import matplotlib
# matplotlib.use('pdf')
import matplotlib.pyplot as plt
import sys

sys.path.append("..")
import pcap_parser
import os
from multiprocessing import Pool
import argparse
import plotting


def show_owdelay(delta_t_lists, labels=[], paper=False, save=None, show=False):
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

    # fig = plt.figure(tight_layout=True)
    fig, ax = plt.subplots(tight_layout=True)
    # fig.suptitle('Will be multiple plots later', fontsize=12)
    # ax = fig.add_subplot(221)
    ax.set_xscale('log')
    # ax.set_yscale('log')
    ax.set_title(r"One-way Delay Distribution (ECDF)")
    ax.set_ylabel(r'ECDF')
    ax.set_xlabel(r'One-way delay (s)')
    ax.grid(True)

    fig_hist, ax_hist = plt.subplots(tight_layout=True)
    # ax_hist = fig.add_subplot(222)
    ax_hist.set_xscale('log')
    ax_hist.set_title(r"One-way Delay Histogram")
    ax_hist.set_ylabel(r'Probability')
    ax_hist.set_xlabel(r'One-way delay (s)')
    ax_hist.grid(True)

    fig_cont, ax_cont = plt.subplots(tight_layout=True)
    # ax_cont = fig.add_subplot(212)
    ax_cont.set_title(r"One-way Delay over Time")
    ax_cont.set_ylabel(r'Delay (s)')
    ax_cont.set_xlabel(r'Packet number')
    ax_cont.grid(True)

    for i, delta_t_list in enumerate(delta_t_lists):
        ecdf = sm.distributions.empirical_distribution.ECDF(delta_t_list)
        x = np.linspace(min(delta_t_list), max(delta_t_list), num=1000)
        y = ecdf(x)
        ax.step(x, y, label=labels[i])

        ax_hist.hist(delta_t_list, bins=100, weights=np.ones(len(delta_t_list)) / len(delta_t_list), label=labels[i])

        ax_cont.plot(range(len(delta_t_list)), delta_t_list, label=labels[i])

        ax_hist.legend()
        ax_cont.legend()
        ax.legend()

    if save:
        plt.savefig(save)

    if show:
        plt.show()

    plt.close()


def show_owdelay_cdf_multiple(nested_delta_t_lists, labels=None, categories=None, paper=False, save=None, show=False, core=False):
    assert len(labels) == len(categories)
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
        ax.set_title(r"One-way Delay Distribution (ECDF)")
    ax.set_xscale('log')
    ax.set_ylabel(r'ECDF')
    if not core:
        ax.set_xlabel(r'One-way delay (ms)')
    else:
        ax.set_xlabel(r'Core delay (ms)')
    ax.grid(True)

    linestyles = ["solid", "dotted", "dashed", "dashdot"]
    for c, delta_t_lists in enumerate(nested_delta_t_lists):
        ax.set_prop_cycle(None)
        for i, delta_t_list in enumerate(delta_t_lists):
            ms_delta_t_list = [delta_t * 1000 for delta_t in delta_t_list]
            ecdf = sm.distributions.empirical_distribution.ECDF(ms_delta_t_list)
            x = np.linspace(min(ms_delta_t_list), max(ms_delta_t_list), num=1000)
            y = ecdf(x)
            if i == 0:
                lines = ax.step(x, y, label=categories[c], linestyle=linestyles[c], alpha=0, color="black")
                lines[0].set_alpha(1)
            ax.step(x, y, label=labels[c][i], linestyle=linestyles[c])

    ax.legend(ncol=len(labels))

    # fig.text(0.95, 0.05, 'Preliminary result', fontsize=50, color='gray', ha='right', va='bottom', alpha=0.5)

    if save:
        print("Save: ", save)
        plt.savefig(save)
    if show:
        plt.show()
    plt.close()


def show_owdelay_bp_multiple(nested_delta_t_lists, labels=None, categories=None, xlabel=None, paper=False, save=None, show=False, core=False):
    assert len(labels) == len(categories)
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
        ax.set_title(r"Boxplots of One-way Delays")
    if not core:
        ax.set_xlabel(r'One-way delay (ms)')
    else:
        ax.set_xlabel(r'Core delay (ms)')
    ax.set_xlabel(r'{}'.format(xlabel))
    ax.grid(True)

    width = 0.4
    # linestyles = ["solid", "dotted", "dashed", "dashdot"]
    colors = ["salmon", "limegreen", "royalblue", "lightgray", "m"]
    hatch_patterns = ('//', 'ooo', '+++', 'xxx', '*')
    bps = []
    for c, delta_t_lists in enumerate(nested_delta_t_lists):
        ax.set_prop_cycle(None)
        offs = width / len(nested_delta_t_lists)
        pos = [tick - offs + ((c + c % 2) * offs) for tick in range(len(delta_t_lists))]
        ms_delta_t_lists = [[delta_t * 1000 for delta_t in delta_t_list] for delta_t_list in delta_t_lists]

        medianprops = dict(linewidth=1, color='black')
        meanpointprops = dict(marker='D', markeredgecolor='black', markerfacecolor='black', markersize=4)
        boxprops = dict(facecolor=colors[c], hatch=hatch_patterns[c], linewidth=1)
        bps.append(ax.boxplot(ms_delta_t_lists, positions=pos, widths=width, vert=True,  # vertical box aligmnent
                              patch_artist=True,
                              whis=[5, 95],
                              showfliers=False,
                              medianprops=medianprops,
                              meanprops=meanpointprops,
                              boxprops=boxprops,
                              notch=False, showmeans=True))

    ax.legend([bp['boxes'][0] for bp in bps], categories, ncol=len(labels))
    ax.set_xticks(range(len(labels[0])))
    ax.set_xticklabels(labels[0])

    # fig.text(0.95, 0.05, 'Preliminary result', fontsize=50, color='gray', ha='right', va='bottom', alpha=0.5)

    if save:
        print("Save: ", save)
        plt.savefig(save)

    if show:
        plt.show()
    plt.close()


def show_ipdv_cdf_multiple(nested_ipdv_lists, labels=None, categories=None, paper=False, save=None, show=False, xlim=None):
    assert len(labels) == len(categories)
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
    # ax.set_xscale('log')
    ax.set_ylabel(r'ECDF')
    ax.set_xlabel(r'IPDV (ms)')
    ax.grid(True)

    linestyles = ["solid", "dotted", "dashed", "dashdot"]
    for c, ipdv_lists in enumerate(nested_ipdv_lists):
        ax.set_prop_cycle(None)
        for i, ipdv_list in enumerate(ipdv_lists):
            ms_ipdv_list = [ipdv * 1000 for ipdv in ipdv_list]
            ecdf = sm.distributions.empirical_distribution.ECDF(ms_ipdv_list)
            x = np.linspace(min(ms_ipdv_list), max(ms_ipdv_list), num=1000)
            y = ecdf(x)
            if i == 0:
                lines = ax.step(x, y, label=categories[c], linestyle=linestyles[c], alpha=0, color="black")
                lines[0].set_alpha(1)
            ax.step(x, y, label=labels[c][i], linestyle=linestyles[c])

    ax.legend(ncol=len(labels))

    # fig.text(0.95, 0.05, 'Preliminary result', fontsize=50, color='gray', ha='right', va='bottom', alpha=0.5)

    if xlim:
        ax.set_xlim(xlim)

    if save:
        print("Save: ", save)
        plt.savefig(save)

    if show:
        plt.show()
    plt.close()


def show_ipdv_bp_multiple(nested_ipdv_lists, labels=None, categories=None, xlabel=None, paper=False, save=None, show=False):
    assert len(labels) == len(categories)
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
        ax.set_title(r"Boxplots of Inter-Packet Delay Variation")
    ax.set_ylabel(r'IPDV (ms)')
    ax.set_xlabel(r'{}'.format(xlabel))
    ax.grid(True)

    width = 0.4
    # linestyles = ["solid", "dotted", "dashed", "dashdot"]
    colors = ["salmon", "limegreen", "royalblue", "lightgray", "m"]
    hatch_patterns = ('//', 'ooo', '+++', 'xxx', '*')
    bps = []
    for c, ipdv_lists in enumerate(nested_ipdv_lists):
        ax.set_prop_cycle(None)
        offs = width / len(nested_ipdv_lists)
        pos = [tick - offs + ((c + c % 2) * offs) for tick in range(len(ipdv_lists))]
        ms_ipdv_lists = [[ipdv * 1000 for ipdv in ipdv_list] for ipdv_list in ipdv_lists]

        medianprops = dict(linewidth=1, color='black')
        meanpointprops = dict(marker='D', markeredgecolor='black', markerfacecolor='black', markersize=4)
        boxprops = dict(facecolor=colors[c], hatch=hatch_patterns[c], linewidth=1)
        bps.append(ax.boxplot(ms_ipdv_lists, positions=pos, widths=width, vert=True,  # vertical box aligmnent
                              patch_artist=True,
                              whis=[5, 95],
                              showfliers=False,
                              medianprops=medianprops,
                              meanprops=meanpointprops,
                              boxprops=boxprops,
                              notch=False, showmeans=True))

    ax.legend([bp['boxes'][0] for bp in bps], categories, ncol=len(labels))
    ax.set_xticks(range(len(labels[0])))
    ax.set_xticklabels(labels[0])

    # fig.text(0.95, 0.05, 'Preliminary result', fontsize=50, color='gray', ha='right', va='bottom', alpha=0.5)

    if save:
        print("Save: ", save)
        plt.savefig(save)

    if show:
        plt.show()
    plt.close()


def show_pdv_cdf_multiple(nested_pdv_lists, labels=None, categories=None, paper=False, save=None, show=False):
    assert len(labels) == len(categories)
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
        ax.set_title(r"Packet Delay Variation (ECDF)")
    # ax.set_xscale('log')
    ax.set_ylabel(r'ECDF')
    ax.set_xlabel(r'Packet Delay Variation (ms)')
    ax.grid(True)

    linestyles = ["solid", "dotted", "dashed", "dashdot"]
    for c, pdv_lists in enumerate(nested_pdv_lists):
        ax.set_prop_cycle(None)
        for i, pdv_list in enumerate(pdv_lists):
            ms_pdv_list = [pdv * 1000 for pdv in pdv_list]
            ecdf = sm.distributions.empirical_distribution.ECDF(ms_pdv_list)
            x = np.linspace(min(ms_pdv_list), max(ms_pdv_list), num=1000)
            y = ecdf(x)
            if i == 0:
                lines = ax.step(x, y, label=categories[c], linestyle=linestyles[c], alpha=0, color="black")
                lines[0].set_alpha(1)
            ax.step(x, y, label=labels[c][i], linestyle=linestyles[c])

    ax.legend(ncol=len(labels))

    # fig.text(0.95, 0.05, 'Preliminary result', fontsize=50, color='gray', ha='right', va='bottom', alpha=0.5)

    if save:
        print("Save: ", save)
        plt.savefig(save)

    if show:
        plt.show()
    plt.close()


def show_pdv_bp_multiple(nested_pdv_lists, labels=None, categories=None, xlabel=None, paper=False, save=None, show=False):
    assert len(labels) == len(categories)
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
        ax.set_title(r"Boxplots of Inter-Packet Delay Variation")
    ax.set_ylabel(r'Packet Delay Variation (ms)')
    ax.set_xlabel(r'{}'.format(xlabel))
    ax.grid(True)

    width = 0.4
    # linestyles = ["solid", "dotted", "dashed", "dashdot"]
    colors = ["salmon", "limegreen", "royalblue", "lightgray", "m"]
    hatch_patterns = ('//', 'ooo', '+++', 'xxx', '*')
    bps = []
    for c, pdv_lists in enumerate(nested_pdv_lists):
        ax.set_prop_cycle(None)
        offs = width / len(nested_pdv_lists)
        pos = [tick - offs + ((c + c % 2) * offs) for tick in range(len(pdv_lists))]
        ms_pdv_lists = [[pdv * 1000 for pdv in pdv_list] for pdv_list in pdv_lists]

        medianprops = dict(linewidth=1, color='black')
        meanpointprops = dict(marker='D', markeredgecolor='black', markerfacecolor='black', markersize=4)
        boxprops = dict(facecolor=colors[c], hatch=hatch_patterns[c], linewidth=1)
        bps.append(ax.boxplot(ms_pdv_lists, positions=pos, widths=width, vert=True,  # vertical box aligmnent
                              patch_artist=True,
                              whis=[5, 95],
                              showfliers=False,
                              medianprops=medianprops,
                              meanprops=meanpointprops,
                              boxprops=boxprops,
                              notch=False, showmeans=True))

    ax.legend([bp['boxes'][0] for bp in bps], categories, ncol=len(labels))
    ax.set_xticks(range(len(labels[0])))
    ax.set_xticklabels(labels[0])

    # fig.text(0.95, 0.05, 'Preliminary result', fontsize=50, color='gray', ha='right', va='bottom', alpha=0.5)

    if save:
        print("Save: ", save)
        plt.savefig(save)

    if show:
        plt.show()
    plt.close()


def show_downtime_cdf_multiple(nested_downtimes, labels=None, categories=None, paper=False, save=None, show=False):
    assert len(labels) == len(categories)
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
        ax.set_title(r"Downtime Distribution (ECDF)")
    ax.set_xscale('log')
    ax.set_ylabel(r'ECDF')
    ax.set_xlabel(r'Downtime (ms)')
    ax.grid(True)

    linestyles = ["solid", "dotted", "dashed", "dashdot"]
    for c, downtimes in enumerate(nested_downtimes):
        ax.set_prop_cycle(None)
        for i, downtime in enumerate(downtimes):
            ms_downtime = [down * 1000 for down in downtime]
            ecdf = sm.distributions.empirical_distribution.ECDF(ms_downtime)
            x = np.linspace(min(ms_downtime), max(ms_downtime), num=1000)
            y = ecdf(x)
            if i == 0:
                lines = ax.step(x, y, label=categories[c], linestyle=linestyles[c], alpha=0, color="black")
                lines[0].set_alpha(1)
            ax.step(x, y, label=labels[c][i], linestyle=linestyles[c])

    ax.legend(ncol=len(labels))

    # fig.text(0.95, 0.05, 'Preliminary result', fontsize=50, color='gray', ha='right', va='bottom', alpha=0.5)

    if save:
        print("Save: ", save)
        plt.savefig(save)

    if show:
        plt.show()
    plt.close()


def show_downtime_bp_multiple(nested_downtimes, labels=None, categories=None, xlabel=None, paper=False, save=None, show=False):
    assert len(labels) == len(categories)
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
        ax.set_title(r"Boxplots of Downtime")
    ax.set_ylabel(r'Downtime (ms)')
    ax.set_xlabel(r'{}'.format(xlabel))
    ax.set_yscale('log')
    ax.grid(True)

    width = 0.4
    # linestyles = ["solid", "dotted", "dashed", "dashdot"]
    colors = ["salmon", "limegreen", "royalblue", "lightgray", "m"]
    hatch_patterns = ('//', 'ooo', '+++', 'xxx', '*')
    bps = []
    for c, downtimes in enumerate(nested_downtimes):
        ax.set_prop_cycle(None)
        offs = width / len(nested_downtimes)
        pos = [tick - offs + ((c + c % 2) * offs) for tick in range(len(downtimes))]
        ms_downtimes = [[down * 1000 for down in downtime] for downtime in downtimes]

        medianprops = dict(linewidth=1, color='black')
        meanpointprops = dict(marker='D', markeredgecolor='black', markerfacecolor='black', markersize=4)
        boxprops = dict(facecolor=colors[c], hatch=hatch_patterns[c], linewidth=1)
        bps.append(ax.boxplot(ms_downtimes, positions=pos, widths=width, vert=True,  # vertical box aligmnent
                              patch_artist=True,
                              whis=[5, 95],
                              showfliers=False,
                              medianprops=medianprops,
                              meanprops=meanpointprops,
                              boxprops=boxprops,
                              notch=False, showmeans=True))

    ax.legend([bp['boxes'][0] for bp in bps], categories, ncol=len(labels))
    ax.set_xticks(range(len(labels[0])))
    ax.set_xticklabels(labels[0])

    # fig.text(0.95, 0.05, 'Preliminary result', fontsize=50, color='gray', ha='right', va='bottom', alpha=0.5)

    if save:
        print("Save: ", save)
        plt.savefig(save)

    if show:
        plt.show()
    plt.close()


def show_consecutive_bp_multiple(nested_consecutives, labels=None, categories=None, xlabel=None, paper=False, save=None, show=False):
    assert len(labels) == len(categories)
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
        ax.set_title(r"Boxplots of Consecutives")
    ax.set_ylabel(r'Consecutive (packets)')
    ax.set_xlabel(r'{}'.format(xlabel))
    ax.set_yscale('log')
    ax.grid(True)

    width = 0.4
    # linestyles = ["solid", "dotted", "dashed", "dashdot"]
    colors = ["salmon", "limegreen", "royalblue", "lightgray", "m"]
    hatch_patterns = ('//', 'ooo', '+++', 'xxx', '*')
    bps = []
    for c, consecutives in enumerate(nested_consecutives):
        ax.set_prop_cycle(None)
        offs = width / len(nested_consecutives)
        pos = [tick - offs + ((c + c % 2) * offs) for tick in range(len(consecutives))]

        medianprops = dict(linewidth=1, color='black')
        meanpointprops = dict(marker='D', markeredgecolor='black', markerfacecolor='black', markersize=4)
        boxprops = dict(facecolor=colors[c], hatch=hatch_patterns[c], linewidth=1)
        bps.append(ax.boxplot(consecutives, positions=pos, widths=width, vert=True,  # vertical box aligmnent
                              patch_artist=True,
                              whis=[5, 95],
                              showfliers=False,
                              medianprops=medianprops,
                              meanprops=meanpointprops,
                              boxprops=boxprops,
                              notch=False, showmeans=True))

    ax.legend([bp['boxes'][0] for bp in bps], categories, ncol=len(labels))
    ax.set_xticks(range(len(labels[0])))
    ax.set_xticklabels(labels[0])

    # fig.text(0.95, 0.05, 'Preliminary result', fontsize=50, color='gray', ha='right', va='bottom', alpha=0.5)

    if save:
        print("Save: ", save)
        plt.savefig(save)

    if show:
        plt.show()
    plt.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--logdir', help='Specify directory for logs/pcaps',
                        default='../logs/measurements/VarParams/download')
    parser.add_argument('--load-pickle', help='Load analysed pcap metadata objects with pickle', action='store_true')
    args = parser.parse_args()

    measurements_dir_rel = args.logdir
    measurements_dir = os.path.abspath(measurements_dir_rel) + "/"

    all_files = []
    pp_dict = {}

    for (dirpath, dirnames, filenames) in os.walk(measurements_dir):
        all_files.extend(sorted(filenames))
        break

    filespath = [measurements_dir + file for file in all_files if "pcap" in file or "pcapng" in file]
    files = [file for file in all_files if "pcap" in file or "pcapng" in file]
    # print(files)

    # file_dict = {pktSize: pktRates: numPkts}
    file_dict = {}
    results_dict = {}

    pktSizes = []
    pktRates = []
    numPkts = []

    for file in files:
        pp_dict[file] = pcap_parser.PCAPParser(file=file)
        params = file.split(".")
        pktSize = params[0]
        pktRate = params[1]
        numPkt = params[2]

        pktSizes.append(pktSize) if pktSize not in pktSizes else pktSizes
        pktRates.append(pktRate) if pktRate not in pktRates else pktRates
        numPkts.append(numPkt) if numPkt not in numPkts else numPkts

        if pktSize in file_dict.keys():
            if pktRate in file_dict[pktSize].keys():
                file_dict[pktSize][pktRate][numPkt] = file
            else:
                file_dict[pktSize][pktRate] = {}
                results_dict[pktSize][pktRate] = {}
                file_dict[pktSize][pktRate][numPkt] = file
        else:
            file_dict[pktSize] = {}
            results_dict[pktSize] = {}
            file_dict[pktSize][pktRate] = {}
            results_dict[pktSize][pktRate] = {}
            file_dict[pktSize][pktRate][numPkt] = file

    sorted(pktSizes)
    sorted(pktRates)
    sorted(numPkts)

    spickle = not args.load_pickle
    workers_dict = results_dict
    opts = {"save_pickle": spickle, "load_pickle": not spickle}

    with Pool() as pool:
        for pktSize in file_dict.keys():
            for pktRate in file_dict[pktSize].keys():
                for numPkt in file_dict[pktSize][pktRate].keys():
                    file = file_dict[pktSize][pktRate][numPkt]
                    workers_dict[pktSize][pktRate][numPkt] = pool.apply_async(pp_dict[file].analyze,
                                                                              args=[file],
                                                                              kwds=opts)
        for pktSize in file_dict.keys():
            for pktRate in file_dict[pktSize].keys():
                for numPkt in file_dict[pktSize][pktRate].keys():
                    file = file_dict[pktSize][pktRate][numPkt]
                    results_dict[pktSize][pktRate][numPkt] = pp_dict[file].owdelay(*workers_dict[pktSize][pktRate][numPkt].get())
    print("Finished analyzing PCAPs.")

    pktSize = "1024"
    pktRates_label = []
    delta_t_lists = []
    for pktRate in sorted(list(results_dict[pktSize].keys()), key=int):
        pktRates_label.append(pktRate)
        delta_t_lists.append(results_dict[pktSize][pktRate][next(iter(results_dict[pktSize][pktRate]))])
    show_owdelay(delta_t_lists, labels=pktRates_label)

    pktRate = "10000"
    pktSizes_label = []
    delta_t_lists = []
    for pktSize in sorted([size for size in list(results_dict.keys()) if pktRate in results_dict[size].keys()],
                          key=int):
        pktSizes_label.append(pktSize)
        delta_t_lists.append(results_dict[pktSize][pktRate][next(iter(results_dict[pktSize][pktRate]))])
    show_owdelay(delta_t_lists, labels=pktSizes_label)
