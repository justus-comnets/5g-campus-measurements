import subprocess
import os
import time


class UdpPing:
    def __init__(self, log_dir, txport, rxport, core, gw_mac, src_ip, dst_ip, ue_ip, temp_dir):
        # measurement_dict = {pktSize: pktRates: numPkts}

        self.moongen = os.path.expanduser("~/MoonGen/build/MoonGen ")
        self.moongen_app = os.path.expanduser(
            "~/MoonGen/examples/timestamping-tests/udpping.lua ")
        print("Moongen app: {}".format(self.moongen_app))
        self.log_dir = log_dir
        self.txport = txport
        self.rxport = rxport
        self.gw_mac = gw_mac
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.ue_ip = ue_ip
        self.temp_dir = temp_dir

        if self.ue_ip == self.dst_ip:
            self.upload = True
        else:
            self.upload = False

    def run(self, print_only=False):

        pkt_sizes = [128, 256, 512, 1024, 1280]
        pkt_rates = [10, 100, 1000, 10000, 10000]
        # pkt_sizes = [128]
        # pkt_rates = [1000]

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
                rpl_logfile_name = log_dir + "rpl.{}.{}.pcap".format(pkt_size, pkt_rate)
                req_logfile_name = log_dir + "req.{}.{}.pcap".format(pkt_size, pkt_rate)
                num_pkts = pkt_rate * duration

                mg_command = self.moongen + self.moongen_app + "{} {} {} {} --file {} --gw-mac {} --src-ip {} --dst-ip {} --reply {} --rfile {} --poisson".format(
                    self.txport,
                    num_pkts,
                    pkt_rate,
                    pkt_size,
                    rpl_logfile_name, self.gw_mac, self.src_ip, self.dst_ip, self.rxport, req_logfile_name)
                if self.upload:
                    mg_command += " --upload"

                print(f"Logfiles:\n{rpl_logfile_name}\n{req_logfile_name}")
                print("Moongen command: sudo {}".format(mg_command))
                if not print_only:
                    tg = subprocess.Popen("sudo {}".format(mg_command), shell=True)
                    tg.wait()
                    time.sleep(2)

                    if self.temp_dir:
                        src = rpl_logfile_name
                        dst = self.log_dir + "rpl.{}.{}.pcap".format(pkt_size, pkt_rate)
                        copy_command = "sudo mv {} {}".format(src, dst)
                        copy_operation = subprocess.Popen(copy_command, shell=True)
                        copy_operation.wait()

                        src = req_logfile_name
                        dst = self.log_dir + "req.{}.{}.pcap".format(pkt_size, pkt_rate)
                        copy_command = "sudo mv {} {}".format(src, dst)
                        copy_operation = subprocess.Popen(copy_command, shell=True)
                        copy_operation.wait()

        for file in os.listdir(self.log_dir):
            print(file)