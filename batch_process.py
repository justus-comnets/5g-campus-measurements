import os
import subprocess
import argparse
from multiprocessing import Pool


# TODO: remove harcoded paths and replace with default argument
def process_tasks(task):
    if task == "SA-up":
        cmds = [
            "python3.8 process_pcaps.py /media/justus/2TBSA/SA/VarParams/upload /media/justus/1TB/SA/VarParams/upload",
            "python3 filter.py /media/justus/2TBSA/SA/VarParams/upload /media/justus/1TB/SA/VarParams/upload",
            "python3.8 process_pcaps.py /media/justus/1TB/SA/VarParams/upload /media/justus/1TB/SA/VarParams/upload --core Open5GS --upload",
            "rm /media/justus/1TB/SA/VarParams/upload/*.core.pcap"]


    elif task == "SA-down":
        cmds = [
            "python3.8 process_pcaps.py /media/justus/2TBSA/SA/VarParams/download /media/justus/1TB/SA/VarParams/download",
            "python3 filter.py /media/justus/2TBSA/SA/VarParams/download /media/justus/1TB/SA/VarParams/download",
            "python3.8 process_pcaps.py /media/justus/1TB/SA/VarParams/download /media/justus/1TB/SA/VarParams/download --core Open5GS --download",
            "rm /media/justus/1TB/SA/VarParams/download/*.core.pcap"]

    elif task == "NSA-up":
        cmds = [
            "python3.8 process_pcaps.py /media/justus/2TBNSA/NSA/VarParams/upload /media/justus/1TB/NSA/VarParams/upload",
            "python3 filter.py /media/justus/2TBNSA/NSA/VarParams/upload /media/justus/1TB/NSA/VarParams/upload",
            "python3.8 process_pcaps.py /media/justus/1TB/NSA/VarParams/upload /media/justus/1TB/NSA/VarParams/upload --core Nokia --upload",
            "rm /media/justus/1TB/NSA/VarParams/upload/*.core.pcap"]

    elif task == "NSA-down":
        cmds = [
            "python3.8 process_pcaps.py /media/justus/2TBNSA/NSA/VarParams/download /media/justus/1TB/NSA/VarParams/download",
            "python3 filter.py /media/justus/2TBNSA/NSA/VarParams/download /media/justus/1TB/NSA/VarParams/download",
            "python3.8 process_pcaps.py /media/justus/1TB/NSA/VarParams/download /media/justus/1TB/NSA/VarParams/download --core Nokia --download",
            "rm /media/justus/1TB/NSA/VarParams/download/*.core.pcap"]
    else:
        print("Task not found (SA-up, SA-down, NSA-up, NSA-down).")
        return

    for cmd in cmds:
        print(cmd)
        job = subprocess.Popen("{}".format(cmd), shell=True)
        job.wait()


def process_files(files):
    # TODO: use multiprocessing
    # /media/justus/2TBNSA/NSA/VarParams/upload/128.100000.pcap
    jobs = []
    with Pool() as pool:
        for file in files:
            jobs.append(pool.apply_async(process_file, args=[file]))
        for job in jobs:
            job.get()


def process_file(file):
    meta = file.split("/")
    name = meta[-1]
    direction = meta[-2]
    tech = meta[-4]
    if tech == "NSA":
        core_type = "Nokia"
    else:
        core_type = "Open5GS"
    short_path = "/".join(file.split("/")[-4:-1])
    core = ".".join(name.split(".")[:-1]) + ".core.pcap"

    cmd = "tshark -r /media/justus/2TB{}/{}/{} -w /media/justus/1TB/{}/{} -Y 'udp.dstport == 65001' -F nsecpcap".format(
        tech, short_path, core, short_path, core)
    print(cmd)
    job = subprocess.Popen("{}".format(cmd), shell=True)
    job.wait()

    cmd = "python3.8 pcap_parser.py --save-pickle --type owdelay --files /media/justus/1TB/{}/{} --core {} --{}".format(
        short_path, core, core_type, direction)
    print(cmd)
    job = subprocess.Popen("{}".format(cmd), shell=True)
    job.wait()

    cmd = "rm /media/justus/1TB/{}/{}".format(short_path, core)
    print(cmd)
    job = subprocess.Popen("{}".format(cmd), shell=True)
    job.wait()

    cmd = "python3.8 pcap_parser.py --save-pickle --type owdelay --files /media/justus/2TB{}/{}/{} --save-pickle-dir /media/justus/1TB/{}".format(
        tech, short_path, name, short_path)
    print(cmd)
    job = subprocess.Popen("{}".format(cmd), shell=True)
    job.wait()

    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--tasks',
                        help='Specify categories as list to be processed (SA-up, SA-down, NSA-up, NSA-down).',
                        nargs='*')
    parser.add_argument('--files',
                        help='Specify files with path as list to be processed (/tmp/128.10.pcap) with .core.pcap.',
                        nargs='*')
    args = parser.parse_args()
    assert args.tasks or args.files, "Specify either whole category or multiple single files (128.10.pcap without core.pcap)."

    if args.tasks:
        for task in args.tasks:
            process_tasks(task)
    elif args.files:
        process_files(args.files)
