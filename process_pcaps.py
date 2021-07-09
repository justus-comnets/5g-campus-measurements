import os
import subprocess
import argparse
from multiprocessing import Pool
import pcap_parser as pp


def create_log_dir(log_dir="/tmp/measurements"):
    try:
        # os.mkdir(log_dir)
        os.system("sudo mkdir -p {}".format(log_dir))
    except OSError:
        print("Creation of the log directory {} failed".format(log_dir))
    else:
        print("Successfully created the log directory {}".format(log_dir))

if __name__ == "__main__":
    # sudo tshark -r /tmp/throughput-test.pcap -w /tmp/throughput-test-filtered.pcap -Y "ip.addr == 10.40.18.2"

    parser = argparse.ArgumentParser()

    parser.add_argument('indir', help='Specify directory of unfiltered logs/pcaps.',
                        default='../logs/measurements/VarParams/download')
    parser.add_argument('outdir', help='Specify directory of unfiltered logs/pcaps.',
                        default='../logs/measurements/VarParams/download-filtered')
    parser.add_argument('--core', help='Process core pcaps of specified core type (Nokia or Open5GS). Note: --upload or --download is needed')
    parser.add_argument('--upload', help='Upload core measurement.', action='store_true')
    parser.add_argument('--download', help='Download core measurement.', action='store_true')
    args = parser.parse_args()

    if args.core:
        # NOTE: better to explicitly specify if it is upload or download and not use default argument
        assert args.upload or args.download, "--upload or --download is needed, if core pcap is analyzed."
        assert args.upload != args.download, "--upload and --download cannot be simultaneously chosen."

    measurements_dir = os.path.abspath(args.indir) + "/"
    processed_measurements_dir = os.path.abspath(args.outdir) + "/"

    create_log_dir(processed_measurements_dir)

    files = pp.find_pcap_files(measurements_dir, core=args.core)

    pp_dict = {}

    with Pool() as pool:
        workers_dict = {}
        print("Processing pcaps: ")
        if args.core:
            opts = {"save_pickle": True, "save_pickle_dir": args.outdir, "core_type": args.core, "upload": args.upload}
            for cfile in files:
                pp_dict[cfile] = pp.PCAPParser(cfile=cfile)
                workers_dict[cfile] = pool.apply_async(pp_dict[cfile].analyze_core, args=[cfile], kwds=opts)
        else:
            opts = {"save_pickle": True, "save_pickle_dir": args.outdir}
            for file in files:
                pp_dict[file] = pp.PCAPParser(file=file)
                workers_dict[file] = pool.apply_async(pp_dict[file].analyze, args=[file], kwds=opts)

        for worker in workers_dict.keys():
            workers_dict[worker].get()

print("Finished processing pcaps.")