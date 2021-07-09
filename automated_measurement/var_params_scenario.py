import subprocess
import os
import time

class VarParams:
    def __init__(self, log_dir, txport, rxport, core, gw_mac, src_ip, dst_ip, ue_ip, temp_dir):

        self.moongen = os.path.expanduser("~/MoonGen/build/MoonGen ")
        self.moongen_app = os.path.expanduser(
            "~/MoonGen/examples/timestamping-tests/timestamps-software-tx-capture.lua ")
        print("Moongen app: {}".format(self.moongen_app))
        self.log_dir = log_dir
        self.txport = txport
        self.rxport = rxport
        self.gw_mac = gw_mac
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.ue_ip = ue_ip
        self.core = core
        self.temp_dir = temp_dir

    def run(self, print_only=False):

        pkt_sizes = [128, 256, 512, 1024, 1280]
        pkt_rates = [10, 100, 1000, 10000, 100000]
        # pkt_sizes = [128]
        # pkt_rates = [10]

        duration = 1000

        print("pkt_sizes: ", pkt_sizes)
        print("pkt_rates: ", pkt_rates)

        if self.temp_dir:
            log_dir = self.temp_dir
        else:
            log_dir = self.log_dir

        for pkt_size in pkt_sizes:
            for pkt_rate in pkt_rates:
                print("Measurement: PktSize: {} PktRate: {}".format(pkt_size, pkt_rate))
                logfile_name = log_dir + "{}.{}.pcap".format(pkt_size, pkt_rate)
                num_pkts = pkt_rate * duration

                if self.core:
                    logfile_name_core = log_dir + "{}.{}.core.pcap".format(pkt_size, pkt_rate)
                    mg_command = self.moongen + self.moongen_app + "{} {} {} {} {} --file {} --gw-mac {} --src-ip {} --dst-ip {} --ue-ip {} --corePort {} --cfile {}".format(
                        self.txport,
                        self.rxport,
                        num_pkts,
                        pkt_rate,
                        pkt_size,
                        logfile_name, self.gw_mac, self.src_ip, self.dst_ip, self.ue_ip, self.core, logfile_name_core)
                else:
                    mg_command = self.moongen + self.moongen_app + "{} {} {} {} {} --file {} --gw-mac {} --src-ip {} --dst-ip {} --ue-ip {}".format(
                        self.txport,
                        self.rxport,
                        num_pkts,
                        pkt_rate,
                        pkt_size,
                        logfile_name, self.gw_mac, self.src_ip, self.dst_ip, self.ue_ip)
                print("Logfile: {}".format(logfile_name))
                print("Moongen command: sudo {}".format(mg_command))
                if not print_only:
                    tg = subprocess.Popen("sudo {}".format(mg_command), shell=True)
                    tg.wait()
                    time.sleep(2)

                    if self.temp_dir:
                        if self.core:
                            src = logfile_name_core
                            dst = self.log_dir + "{}.{}.core.pcap".format(pkt_size, pkt_rate)
                            copy_command = "sudo mv {} {}".format(src, dst)
                            copy_operation = subprocess.Popen(copy_command, shell=True)
                            # copy_operations.append(copy_operation)
                            copy_operation.wait()

                        src = logfile_name
                        dst = self.log_dir + "{}.{}.pcap".format(pkt_size, pkt_rate)
                        copy_command = "sudo mv {} {}".format(src, dst)
                        copy_operation = subprocess.Popen(copy_command, shell=True)
                        # copy_operations.append(copy_operation)
                        copy_operation.wait()

        for file in os.listdir(self.log_dir):
            print(file)