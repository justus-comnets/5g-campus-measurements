#! /usr/bin/python3

import numpy as np
import statsmodels.api as sm
# https://stackoverflow.com/questions/19518352/tkinter-tclerror-couldnt-connect-to-display-localhost18-0/44922799
# import matplotlib
# matplotlib.use('pdf')
import matplotlib.pyplot as plt
import sys
import tabulate

sys.path.append("..")
sys.path.append("../..")
import pcap_parser
import plot
import var_params
import os
from multiprocessing import Pool
import argparse
import plotting


def calc_eps_ran(eps_e2e, eps_core):
    return (eps_e2e - eps_core) / (1 - eps_core)


def e_fmt(val):
    strs = "{:.2E}".format(val).split("E")
    val_fmt = "{}e{}".format(strs[0], int(strs[1]))
    return val_fmt


def show_losses(nested_losses_e2e, nested_losses_core, labels=None, categories=None, xlabel=None, save=None,
                        show=False):
    assert len(labels) == len(categories)
    plotting.setup()

    fig, ax = plt.subplots(tight_layout=True)

    ax.set_ylabel(r'Losses (\%)')
    ax.set_xlabel(r'{}'.format(xlabel))
    ax.set_yscale('log')
    ax.grid(True)

    width = 0.4
    # linestyles = ["solid", "dotted", "dashed", "dashdot"]
    colors = ["salmon", "limegreen", "royalblue", "lightgray", "m"]
    hatch_patterns = ('//', 'ooo', '+++', 'xxx', '*')

    table = []

    for c, losses_list in enumerate(nested_losses_e2e):
        ax.set_prop_cycle(None)
        offs = width / len(nested_losses_e2e)
        lpos = [tick - width/4 - offs + ((c + c % 2) * offs) for tick in range(len(losses_list))]
        rpos = [tick + width/4 - offs + ((c + c % 2) * offs) for tick in range(len(losses_list))]

        losses_core = [sum(loss_core) / total for (loss_core, total) in nested_losses_core[c]]
        losses_e2e = [(sum(loss) / total) for i, (loss, total) in enumerate(losses_list)]

        losses_core_sum = [sum(loss_core) for (loss_core, total) in nested_losses_core[c]]
        losses_e2e_sum = [sum(loss) for i, (loss, total) in enumerate(losses_list)]

        losses_core_perc = [loss_core * 100 for loss_core in losses_core]
        losses_ran_perc = [calc_eps_ran(loss_e2e, losses_core[i]) * 100 for i, loss_e2e in enumerate(losses_e2e)]
        losses_e2e_perc = [loss_e2e * 100 for loss_e2e in losses_e2e]

        for (loss_e2e, e2e_sum, loss_ran, loss_core, core_sum) in zip(losses_e2e_perc, losses_e2e_sum, losses_ran_perc, losses_core_perc, losses_core_sum):
            print("Cat: {}  Losses_e2e: {},{}  Losses_ran: {}  Losses_core: {},{}".format(categories[c], loss_e2e, e2e_sum,loss_ran, loss_core, core_sum))

        # https://stackoverflow.com/questions/5195466/matplotlib-does-not-display-hatching-when-rendering-to-pdf
        ax.bar(lpos, losses_core_perc, width/2, label=r'{}-Core'.format(categories[c]), hatch=hatch_patterns[0], alpha=0.99, color=colors[c])
        ax.bar(rpos, losses_ran_perc, width/2, label=r'{}-RAN'.format(categories[c]), hatch=hatch_patterns[1], alpha=0.99, color=colors[c])

        table.append([r'{}-Core'.format(categories[c])] + [r"{}%".format(e_fmt(loss)) for loss in losses_core_perc])
        table.append([r'{}-RAN'.format(categories[c])] + [r"{}%".format(e_fmt(loss)) for loss in losses_ran_perc])

    ax.set_xticks(range(len(labels[0])))
    ax.set_xticklabels(labels[0])
    ax.legend(ncol=len(labels))
    # fig.text(0.95, 0.05, r'Preliminary result', fontsize=50, color='gray', ha='right', va='bottom', alpha=0.5)

    print(tabulate.tabulate(table, headers=labels[0], tablefmt='latex'))

    if save:
        print("Save: ", save)
        plt.savefig(save)

        table_save = save.split(".")[0] + "-table.tex"
        with open(table_save, "w") as f:
            f.write(tabulate.tabulate(table, headers=labels[0], tablefmt='latex'))

    if show:
        plt.show()
    plt.close()


if __name__ == "__main__":
    save = "/home/justus/Pictures/plots/end2end/upload/losses"
    logdirs = ["/media/justus/1TB/SA/VarParams/upload", "/media/justus/1TB/NSA/VarParams/upload"]

    labels = ["SA", "NSA"]
    labels_core = ["Open5GS", "Nokia"]

    p = plot.Plot(logdirs=logdirs, scenario="VarParams", labels=labels)
    p.analyze(core=False)
    p.analyze_scenario("multiplebp-losses")

    p_core = plot.Plot(logdirs=logdirs, scenario="VarParams", labels=labels_core)
    p_core.analyze(core=True)
    p_core.analyze_scenario("multiplebp-losses")

    nested_losses = []
    nested_losses_core = []
    nested_labels = []
    for label, label_core in zip(p.labels, p_core.labels):
        pktSize = "128"
        pktRates_label = []
        losses_list = []
        losses_list_core = []
        for pktRate in sorted(list(p.scenario_results_dict[label][pktSize].keys()), key=int):
            pktRates_label.append(pktRate)
            losses = p.scenario_results_dict[label][pktSize][pktRate]
            losses_list.append(losses)
            losses_core = p_core.scenario_results_dict[label_core][pktSize][pktRate]
            losses_list_core.append(losses_core)
            # print("{},{}:  {}  {}".format(pktSize, pktRate, losses[1], losses_core[1]))
        nested_labels.append(pktRates_label)
        nested_losses.append(losses_list)
        nested_losses_core.append(losses_list_core)

    show_losses(nested_losses, nested_losses_core, labels=nested_labels,
                        categories=p.labels, show=False,
                        xlabel="Packet rates (packets per second)",
                        save=save + "-pktRates.pdf" if save else None)

    nested_losses = []
    nested_losses_core = []
    nested_labels = []
    for label, label_core in zip(p.labels, p_core.labels):
        pktRate = "10000"
        pktSizes_label = []
        losses_list = []
        losses_list_core = []
        for pktSize in sorted(
                [size for size in list(p.scenario_results_dict[label].keys()) if
                 pktRate in p.scenario_results_dict[label][size].keys()],
                key=int):
            pktSizes_label.append(pktSize)
            losses = p.scenario_results_dict[label][pktSize][pktRate]
            losses_list.append(losses)
            losses_core = p_core.scenario_results_dict[label_core][pktSize][pktRate]
            losses_list_core.append(losses_core)
            # print("{},{}:  {}  {}".format(pktSize, pktRate, losses[1], losses_core[1]))
        nested_labels.append(pktSizes_label)
        nested_losses.append(losses_list)
        nested_losses_core.append(losses_list_core)

    show_losses(nested_losses, nested_losses_core, labels=nested_labels,
                        categories=p.labels, show=False,
                        xlabel="Packet sizes (bytes)",
                        save=save + "-pktSizes.pdf" if save else None)
