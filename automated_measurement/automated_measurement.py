import subprocess
import os
import argparse

scenarios = {"VarParams": "var_params_scenario",
             "ThroughputTest": "throughput_test_scenario",
             "ThroughputTestEval": "throughput_test_eval"}


class AutomatedMeasurement:
    def __init__(self, dpdk_tx_port=1, dpdk_rx_port=2, dpdk_core_port=None, log_dir="/tmp/measurements", temp_dir=None):
        self.dpdk_tx_port = dpdk_tx_port
        self.dpdk_rx_port = dpdk_rx_port
        self.dpdk_core_port = dpdk_core_port
        self.log_dir = log_dir
        self.temp_dir = temp_dir

        command = "python3 ~/MoonGen/libmoon/deps/dpdk/usertools/dpdk-devbind.py --status | grep -A 5 \"Network devices using DPDK-compatible driver\""
        result = subprocess.check_output(command, shell=True)
        print("DPDK devices: \n" + result.decode("utf8"))
        print("Tx port: {}".format(self.dpdk_tx_port))
        print("Rx port: {}".format(self.dpdk_rx_port))
        if self.dpdk_core_port:
            print("Capturing core traffic on port: {}".format(self.dpdk_core_port))

    def run_measurement(self, scenario="VarParams", gw_mac="3c:fd:fe:b9:24:68", src_ip="10.40.18.2", dst_ip="10.40.17.1",
                        ue_ip="192.168.1.102", upload=False, print_only=False):
        print("Run scenario: " + scenario + " Upload: {} ".format(upload) + "GW MAC: {}".format(gw_mac))

        scenario_module = __import__(scenarios[scenario])
        temp_scenario_dir = None
        if not upload:
            scenario_dir = self.log_dir + "/{}/download/".format(scenario)
            create_log_dir(scenario_dir)
            tx_port = self.dpdk_tx_port
            rx_port = self.dpdk_rx_port
            if self.temp_dir:
                temp_scenario_dir = self.temp_dir + "/{}/download/".format(scenario)
                create_log_dir(temp_scenario_dir)

        else:
            scenario_dir = self.log_dir + "/{}/upload/".format(scenario)
            create_log_dir(scenario_dir)
            tx_port = self.dpdk_rx_port
            rx_port = self.dpdk_tx_port
            if self.temp_dir:
                temp_scenario_dir = self.temp_dir + "/{}/upload/".format(scenario)
                create_log_dir(temp_scenario_dir)

        scenario_class = getattr(scenario_module, scenario)(scenario_dir, tx_port, rx_port, self.dpdk_core_port, gw_mac, src_ip, dst_ip, ue_ip, temp_scenario_dir)
        scenario_class.run(print_only=print_only)
        print("Finished measurements.")


def create_log_dir(log_dir="/tmp/measurements"):
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
    parser.add_argument('--scenario', help='Specify scenario ("VarParams", "ThroughputTest")', default='VarParams')
    parser.add_argument('--logdir', help='Specify directory for logs/pcaps', default='/tmp/measurements')
    parser.add_argument('--tempdir',
                        help='Specify temporal directory for logs/pcaps used to buffer results first before copying it to logdir (Used for slow external hard drives).')
    parser.add_argument('--txport', help='Specify txport', default="1")
    parser.add_argument('--rxport', help='Specify rxport', default="2")
    parser.add_argument('--core', help='Specify port for core capture.')
    parser.add_argument('--upload', help='Make upload measurement.', action='store_true')
    parser.add_argument('--gw-mac', help='GW MAC.', default='3c:fd:fe:b9:24:68')
    parser.add_argument('--src-ip', help='SRC IP.', default='10.40.18.2')
    parser.add_argument('--dst-ip', help='DST IP.', default='10.40.17.1')
    parser.add_argument('--ue-ip', help='UE IP.', default='192.168.1.102')
    parser.add_argument('--print-only', help='Print only commands and do nothing else.', action='store_true')

    args = parser.parse_args()

    am = AutomatedMeasurement(log_dir=args.logdir, dpdk_tx_port=args.txport, dpdk_rx_port=args.rxport,
                              dpdk_core_port=args.core, temp_dir=args.tempdir)
    am.run_measurement(scenario=args.scenario, upload=args.upload, gw_mac=args.gw_mac, src_ip=args.src_ip,
                       dst_ip=args.dst_ip, ue_ip=args.ue_ip, print_only=args.print_only)
