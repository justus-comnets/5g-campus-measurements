import plot
import argparse

# python3.8 plot.py --scenario VarParams --logdirs /media/justus/1TB/SA/VarParams/download /media/justus/1TB/NSA/VarParams/download
# --labels SA NSA --plot-type multiplecdf-owd --load-pickle --paper --save ~/Pictures/plots/end2end/download

plot_types = ["multiplecdf-owd", "multiplebp-owd",
              "multiplecdf-ipdv", "multiplebp-ipdv",
              "multiplecdf-pdv", "multiplebp-pdv",
              "multiplebp-downtime"]
loads = ["download", "upload"]

# plot_types = ["multiplecdf-owd", "multiplebp-owd"]
# loads = ["download"]


def autogen_plots(plot_types, loads, e2e=False, core=False):


    if e2e:
        labels = ["SA", "NSA"]
        save = "/home/justus/Pictures/plots/end2end/{}"
        for load in loads:
            logdirs = ["/media/justus/1TB/SA/VarParams/{}".format(load), "/media/justus/1TB/NSA/VarParams/{}".format(load)]
            # logdirs = ["/home/justus/porsche/RTPanalyzer/logs/measurements/SA/VarParams/{}".format(load),
            #            "/home/justus/porsche/RTPanalyzer/logs/measurements/NSA/VarParams/{}".format(load)]
            p = plot.Plot(logdirs=logdirs, scenario="VarParams", labels=labels)
            p.analyze(core=False)
            last_scenario = None
            for i, plot_type in enumerate(plot_types):
                scenario = plot_type.split("-")[1]
                if not scenario == last_scenario:
                    print("Analyze: ", plot_type)
                    p.analyze_scenario(plot_type)
                print("Plot: ", plot_type)
                p.plot_scenario(plot_type, paper=True, save_dir=save.format(load))
                last_scenario = scenario

    if core:
        labels = ["Open5GS", "Nokia"]
        save = "/home/justus/Pictures/plots/core/{}"
        for load in loads:
            logdirs = ["/media/justus/1TB/SA/VarParams/{}".format(load), "/media/justus/1TB/NSA/VarParams/{}".format(load)]
            p = plot.Plot(logdirs=logdirs, scenario="VarParams", labels=labels)
            p.analyze(core=True)
            last_scenario = None
            for plot_type in plot_types:
                scenario = plot_type.split("-")[1]
                if not scenario == last_scenario:
                    print("Analyze: ", plot_type)
                    p.analyze_scenario(plot_type)
                print("Plot: ", plot_type)
                p.plot_scenario(plot_type, paper=True, save_dir=save.format(load))
                last_scenario = scenario


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--print-plot-types', help='Specify plot types (List can be printed with --print-plot-types).',
                        action="store_true")
    parser.add_argument('--plot-types', help='Specify plot types (List can be printed with --print-plot-types).', nargs="*")
    parser.add_argument('--loads', help='Specify direction (download, upload).', nargs="*")
    parser.add_argument('--e2e', help='Create End-2-End plots.', action="store_true")
    parser.add_argument('--core', help='Create core plots.', action="store_true")
    args = parser.parse_args()

    if args.print_plot_types or len(args.plot_types) == 0:
        print(plot_types)
    else:
        autogen_plots(args.plot_types, args.loads, e2e=args.e2e, core=args.core)
