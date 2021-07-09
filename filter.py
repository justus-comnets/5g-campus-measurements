import os
import subprocess
import argparse
from multiprocessing import Pool


def create_log_dir(log_dir="/tmp/measurements"):
    try:
        # os.mkdir(log_dir)
        os.system("mkdir -p {}".format(log_dir))
    except OSError:
        print("Creation of the log directory {} failed".format(log_dir))
    else:
        print("Successfully created the log directory {}".format(log_dir))


def filter_job(file, filtered_filepath):
    cmd = "tshark -r {} -w {} -Y 'udp.dstport == 65001' -F nsecpcap".format(file, filtered_filepath)
    print(cmd)
    filter = subprocess.Popen("{}".format(cmd), shell=True)
    filter.wait()

if __name__ == "__main__":
    # sudo tshark -r /tmp/throughput-test.pcap -w /tmp/throughput-test-filtered.pcap -Y "ip.addr == 10.40.18.2"

    parser = argparse.ArgumentParser()

    parser.add_argument('indir', help='Specify directory of unfiltered core logs/pcaps.',
                        default='../logs/measurements/VarParams/download')
    parser.add_argument('outdir', help='Specify directory for filtered core logs/pcaps.',
                        default='../logs/measurements/VarParams/download-filtered')
    args = parser.parse_args()

    measurements_dir = os.path.abspath(args.indir) + "/"
    filtered_measurements_dir = os.path.abspath(args.outdir) + "/"

    create_log_dir(filtered_measurements_dir)

    all_files = []

    for (dirpath, dirnames, filenames) in os.walk(measurements_dir):
        all_files.extend(sorted(filenames))
        break

    files = [file for file in all_files if ".core." in file]
    filespath = [measurements_dir + file for file in files]
    filtered_filespath = [filtered_measurements_dir + file for file in files]

    # print(files)

    jobs = []
    with Pool() as pool:
        for i, file in enumerate(filespath):
            jobs.append(pool.apply_async(filter_job, args=[file, filtered_filespath[i]]))

        for job in jobs:
            job.get()
