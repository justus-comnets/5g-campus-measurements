#! /usr/bin/python3

import dpkt
import argparse
import struct
import os
import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import array
import pickle
import subprocess
import decimal
import logging
import operator
import itertools

decimal.getcontext().prec = 19

from bisect import bisect_left

import sys
import gc
from multiprocessing import Pool

# https://stackoverflow.com/questions/47776486/python-struct-error-i-format-requires-2147483648-number-2147483647/47776649#47776649
assert sys.version_info >= (3, 8), "Python 3.8 or higher is required."


# NOTE: python script with HW timestamping places sent_ts in next packet. MoonGen however puts it directly in the packet

class PCAPParser:
    def __init__(self, file=None, cfile=None, trgenerator="MoonGen", loglevel=logging.ERROR):
        assert file is None or cfile is None

        if file:
            # self.logger = logging.getLogger(".".join(file.split("/")[-1].split(".")[:-1]))
            self.logger = logging.getLogger(file)
        else:
            # self.logger = logging.getLogger(".".join(cfile.split("/")[-1].split(".")[:-1]))
            self.logger = logging.getLogger(cfile)

        self.logger.setLevel(loglevel)
        ch = logging.StreamHandler()
        ch.setLevel(loglevel)
        formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        self.logger.debug("Open file: {}".format(file))
        self.file = file

        self.trgenerator = trgenerator

        self.logger.debug("Open core file: {}".format(cfile))
        self.cfile = cfile

        assert self.file or self.cfile, "No file specified."

    def analyze(self, pcap_file, save_pickle=False, load_pickle=False, save_pickle_dir=None):
        if save_pickle_dir:
            assert save_pickle

        # see https://docs.python.org/3/library/array.html
        data_seq_no = array.array("Q", [])
        data_sent_ts = array.array("d", [])
        data_recv_ts_sec = array.array("L", [])
        data_recv_ts_nsec = array.array("d", [])

        if load_pickle:
            data_seq_no, data_sent_ts, data_recv_ts_sec, data_recv_ts_nsec = self.load_pickle_files(pcap_file)

        else:

            self.logger.info("Analyze PCAP ", pcap_file)

            command = "capinfos {} -E".format(pcap_file)
            output = subprocess.run([command], shell=True, capture_output=True)

            fo = open(pcap_file, 'rb')
            # if "pcapng" in file:
            #     self.pcaps.append(dpkt.pcapng.Reader(fo))
            # else:
            pcap = dpkt.pcap.Reader(fo)

            p_no = 0
            try:
                for recv_ts, buf in pcap:
                    try:
                        if "Ethernet" in str(output.stdout).split("File encapsulation: ")[1]:
                            eth = dpkt.ethernet.Ethernet(buf)
                            ip = eth.data
                        elif "Raw IP" in str(output.stdout).split("File encapsulation: ")[1]:
                            ip = dpkt.ip.IP(buf)
                        else:
                            self.logger.error("Specify encapsulation type: RAWIP or Ethernet. Default Ethernet")
                            eth = dpkt.ethernet.Ethernet(buf)
                            ip = eth.data

                        udp = ip.data

                        sec, nsec, seq_no = struct.unpack('>qqq', udp.data[0:24])

                    except Exception as e:
                        print("Error: {} \n in file: {}".format(e, pcap_file))
                        continue

                    sent_ts = sec + (int(nsec / 1000) * 10 ** -6)  # sent_ts is for the preceeding packet

                    if self.trgenerator == "MoonGen":
                        # data_dict[p_no]["sent_ts"] = sent_ts
                        data_sent_ts.append(sent_ts)
                    elif self.trgenerator == "Python":
                        if not p_no == 0:
                            # data_dict[p_no - 1]["sent_ts"] = sent_ts
                            data_sent_ts.append(sent_ts)
                    else:
                        self.logger.error("Specify used generator.")
                        return

                    data_seq_no.append(seq_no)
                    recv_ts_sec, recv_ts_nsec = decimal_to_sec_nsec(recv_ts)
                    data_recv_ts_sec.append(recv_ts_sec)
                    data_recv_ts_nsec.append(recv_ts_nsec)
                    p_no += 1
            except Exception as e:
                self.logger.error("Error: {} \n in file: {}".format(e, pcap_file))

            fo.close()

        self.logger.info("Data size: ",
                         get_obj_size(data_seq_no) + get_obj_size(data_sent_ts) + get_obj_size(data_recv_ts_sec),
                         + get_obj_size(data_recv_ts_nsec))
        self.logger.info("Lengths: ", len(data_seq_no), len(data_sent_ts), len(data_recv_ts_sec),
                         len(data_recv_ts_nsec))

        if save_pickle:
            self.save_pickle_files(pcap_file, data_seq_no, data_sent_ts, data_recv_ts_sec, data_recv_ts_nsec,
                                   save_pickle_dir=save_pickle_dir)

        return data_seq_no, data_sent_ts, zip(data_recv_ts_sec, data_recv_ts_nsec)

    def analyze_core(self, cpcap_file, save_pickle=False, load_pickle=False, core_type="Open5GS", save_pickle_dir=None,
                     upload=False, sanity_check=False):
        assert "Open5GS" in core_type or "Nokia" in core_type
        if save_pickle_dir:
            assert save_pickle, "save_pickle must be true for save_pickle_dir"

        # see https://docs.python.org/3/library/array.html
        data_seq_no = array.array("Q", [])
        data_seq_no_pre = array.array("Q", [])
        data_sent_ts = array.array("d", [])
        data_recv_ts_sec = array.array("L", [])
        data_recv_ts_nsec = array.array("d", [])

        if load_pickle:
            data_seq_no, data_seq_no_pre, data_sent_ts, data_recv_ts_sec, data_recv_ts_nsec = self.load_pickle_files(
                cpcap_file, core=True)
        else:

            self.logger.info("Analyze Core PCAP.")
            fo = open(cpcap_file, 'rb')
            # if "pcapng" in file:
            #     self.pcaps.append(dpkt.pcapng.Reader(fo))
            # else:
            cpcap = dpkt.pcap.Reader(fo)

            # TODO: Nokia and Open5GS GTP header structure is not the same (different extension header)
            if "Nokia" in core_type:
                gtp_offs = 36
            elif "Open5GS" in core_type:
                gtp_offs = 44
            else:
                self.logger.error("Wrong core type.")
                raise Exception

            # TODO: Apparently MoonGen(Generator/Capturing???) has some lags (no packets for a short time)

            last_seq_no = None
            for ts, buf in cpcap:
                eth = dpkt.ethernet.Ethernet(buf)
                ip = eth.data
                udp = ip.data
                if not upload:
                    if udp.dport == 2152:  # GTP packet
                        recv_ts_sec, recv_ts_nsec = decimal_to_sec_nsec(ts)
                        data_recv_ts_sec.append(recv_ts_sec)
                        data_recv_ts_nsec.append(recv_ts_nsec)
                        sec, nsec, seq_no = struct.unpack('>qqq', udp.data[gtp_offs:gtp_offs + 24])
                        data_seq_no.append(seq_no)
                    else:
                        data_sent_ts.append(ts)
                        sec, nsec, seq_no = struct.unpack('>qqq', udp.data[0:24])
                        data_seq_no_pre.append(seq_no)
                else:
                    if udp.dport == 2152:  # GTP packet
                        data_sent_ts.append(ts)
                        sec, nsec, seq_no = struct.unpack('>qqq', udp.data[gtp_offs:gtp_offs + 24])
                        data_seq_no_pre.append(seq_no)
                    else:
                        sec, nsec, seq_no = struct.unpack('>qqq', udp.data[0:24])
                        # NOTE: Weird bug in the Nokia core. During Upload (GTP->UDP) there are duplicated UDP packets.
                        if seq_no == last_seq_no:
                            continue
                        recv_ts_sec, recv_ts_nsec = decimal_to_sec_nsec(ts)
                        data_recv_ts_sec.append(recv_ts_sec)
                        data_recv_ts_nsec.append(recv_ts_nsec)
                        data_seq_no.append(seq_no)
                        last_seq_no = seq_no

            fo.close()

        if sanity_check:
            data_seq_no, data_sent_ts, data_recv_ts_sec, data_recv_ts_nsec, data_seq_no_pre = self.sanity_check_core(
                data_seq_no, data_sent_ts, data_recv_ts_sec, data_recv_ts_nsec, data_seq_no_pre)

        self.logger.info("Data size: ", get_obj_size(data_seq_no) + get_obj_size(data_seq_no_pre) + get_obj_size(
            data_sent_ts) + get_obj_size(data_recv_ts_sec),
                         + get_obj_size(data_recv_ts_nsec))
        self.logger.info("Lengths: ", len(data_seq_no), len(data_seq_no_pre), len(data_sent_ts), len(data_recv_ts_sec),
                         len(data_recv_ts_nsec))

        if save_pickle:
            self.save_pickle_files(cpcap_file, data_seq_no, data_sent_ts, data_recv_ts_sec, data_recv_ts_nsec,
                                   data_seq_no_pre=data_seq_no_pre, save_pickle_dir=save_pickle_dir)

        return data_seq_no, data_sent_ts, zip(data_recv_ts_sec, data_recv_ts_nsec), data_seq_no_pre

    def load_pickle_files(self, pcap_file, core=False):
        self.logger.info("Load pickle files.")
        pfile_base = ".".join(pcap_file.split(".")[:-1])
        data_seq_no_file = open(pfile_base + ".data_seq_no.obj", "rb")
        data_sent_ts_file = open(pfile_base + ".data_sent_ts.obj", "rb")
        data_recv_ts_sec_file = open(pfile_base + ".data_recv_ts_sec.obj", "rb")
        data_recv_ts_nsec_file = open(pfile_base + ".data_recv_ts_nsec.obj", "rb")

        data_seq_no = pickle.load(data_seq_no_file)

        data_sent_ts = pickle.load(data_sent_ts_file)
        data_recv_ts_sec = pickle.load(data_recv_ts_sec_file)
        data_recv_ts_nsec = pickle.load(data_recv_ts_nsec_file)

        data_seq_no_file.close()
        data_sent_ts_file.close()
        data_recv_ts_sec_file.close()
        data_recv_ts_nsec_file.close()

        self.logger.info("Size of data_seq_no: ", get_obj_size(data_seq_no))
        self.logger.info("Size of data_sent_ts: ", get_obj_size(data_sent_ts))
        self.logger.info("Size of data_recv_ts_sec: ", get_obj_size(data_recv_ts_sec))
        self.logger.info("Size of data_recv_ts_nsec: ", get_obj_size(data_recv_ts_nsec))

        if not core:
            return data_seq_no, data_sent_ts, data_recv_ts_sec, data_recv_ts_nsec
        else:
            data_seq_no_pre_file = open(pfile_base + ".data_seq_no_pre.obj", "rb")
            data_seq_no_pre = pickle.load(data_seq_no_pre_file)
            data_seq_no_pre_file.close()
            self.logger.info("Size of data_seq_no_pre: ", get_obj_size(data_seq_no_pre))
            return data_seq_no, data_seq_no_pre, data_sent_ts, data_recv_ts_sec, data_recv_ts_nsec

    def save_pickle_files(self, pcap_file, data_seq_no, data_sent_ts, data_recv_ts_sec, data_recv_ts_nsec,
                          data_seq_no_pre=None, save_pickle_dir=None):
        pfile_base = ".".join(pcap_file.split(".")[:-1])
        pfile_name = pfile_base.split("/")[-1]
        if save_pickle_dir:
            if save_pickle_dir[-1] == "/":
                pfile_dir = save_pickle_dir
            else:
                pfile_dir = save_pickle_dir + "/"
        else:
            pfile_dir = "/".join(pfile_base.split("/")[:-1])
            if pfile_dir:
                pfile_dir += "/"

        pfile = pfile_dir + pfile_name

        data_seq_no_file = open(pfile + ".data_seq_no.obj", "w+b")
        data_sent_ts_file = open(pfile + ".data_sent_ts.obj", "w+b")
        data_recv_ts_sec_file = open(pfile + ".data_recv_ts_sec.obj", "w+b")
        data_recv_ts_nsec_file = open(pfile + ".data_recv_ts_nsec.obj", "w+b")

        pickle.dump(data_seq_no, data_seq_no_file)
        pickle.dump(data_sent_ts, data_sent_ts_file)
        pickle.dump(data_recv_ts_sec, data_recv_ts_sec_file)
        pickle.dump(data_recv_ts_nsec, data_recv_ts_nsec_file)

        data_seq_no_file.close()
        data_sent_ts_file.close()
        data_recv_ts_sec_file.close()
        data_recv_ts_nsec_file.close()

        if data_seq_no_pre:
            data_seq_no_pre_file = open(pfile + ".data_seq_no_pre.obj", "w+b")
            pickle.dump(data_seq_no_pre, data_seq_no_pre_file)
            data_seq_no_pre_file.close()

    def sanity_check_core(self, data_seq_no, data_sent_ts, data_recv_ts_sec, data_recv_ts_nsec, data_seq_no_pre):
        self.logger.info(
            "data_seq_no_pre sorted: {} data_seq_no sorted: {}".format(issorted(data_seq_no_pre),
                                                                       issorted(data_seq_no)))
        overhang = np.setdiff1d(data_seq_no, data_seq_no_pre, assume_unique=True)
        sanity_check = False if len(overhang) else True
        self.logger.info("Sanity check: {}  Error length: {}".format(sanity_check, len(overhang)))

        filtered_data_seq_no = array.array("Q", [])
        filtered_data_recv_ts_sec = array.array("L", [])
        filtered_data_recv_ts_nsec = array.array("d", [])

        for (seq_no, recv_ts_sec, recv_ts_nsec) in zip(data_seq_no, data_recv_ts_sec, data_recv_ts_nsec):
            if seq_no in overhang:
                continue
            else:
                filtered_data_seq_no.append(seq_no)
                filtered_data_recv_ts_sec.append(recv_ts_sec)
                filtered_data_recv_ts_nsec.append(recv_ts_nsec)

        return filtered_data_seq_no, data_sent_ts, filtered_data_recv_ts_sec, filtered_data_recv_ts_nsec, data_seq_no_pre

    # TODO: replace this with wrapper and make parsing dependent on len(args):
    def owdelay(self, data_seq_no, data_sent_ts, data_recv_ts, *args):
        delta_t_list = []

        if not len(args):
            for (sent_ts, recv_ts) in zip(data_sent_ts, data_recv_ts):
                recv_ts = sum(recv_ts)  # Note: This decreases the accuracy
                delta_t_list.append(recv_ts - sent_ts)
        else:
            # Note: dumb new hack to analyze core captures correctly.
            data_seq_no_pre = args[0]

            pre_indices = np.where(np.in1d(data_seq_no_pre, data_seq_no, assume_unique=True))[0]
            for (recv_ts, pre_index) in zip(data_recv_ts, pre_indices):
                recv_ts = sum(recv_ts)
                delta_t_list.append(recv_ts - data_sent_ts[pre_index])

        self.logger.info("Length data_seq_no: {}  delta_t_list: {}".format(len(data_seq_no), len(delta_t_list)))

        return delta_t_list

    def ipdv(self, data_seq_no, data_sent_ts, data_recv_ts, *args):
        ipdv_list = []

        if not len(args):
            lost_packets = max(data_seq_no) + 1 - len(data_seq_no)
            # self.logger.info(
            #     "IPDV:  Max seq_no {}  Len data_seq_no {}  Lost packets {}".format(max(data_seq_no), len(data_seq_no),
            #                                                                        lost_packets))
            delta_t_last = None
            last_seq_no = -2
            # Note: Assumption is in order delivery of packets
            for (seq_no, sent_ts, recv_ts) in zip(data_seq_no, data_sent_ts, data_recv_ts):
                recv_ts = sum(recv_ts)  # TODO: This decreases the accuracy
                delta_t = recv_ts - sent_ts
                if not seq_no == last_seq_no + 1:
                    delta_t_last = None
                else:
                    if delta_t_last:
                        ipdv_list.append(delta_t - delta_t_last)
                    delta_t_last = delta_t
                last_seq_no = seq_no
        else:
            # Note: dumb new hack to analyze core captures correctly.
            data_seq_no_pre = args[0]
            pre_indices = np.where(np.in1d(data_seq_no_pre, data_seq_no, assume_unique=True))[0]

            delta_t_last = None
            last_seq_no = -2
            for (seq_no, recv_ts, pre_index) in zip(data_seq_no, data_recv_ts, pre_indices):
                recv_ts = sum(recv_ts)
                delta_t = recv_ts - data_sent_ts[pre_index]
                if not seq_no == last_seq_no + 1:
                    delta_t_last = None
                else:
                    if delta_t_last:
                        ipdv_list.append(delta_t - delta_t_last)
                    delta_t_last = delta_t
                last_seq_no = seq_no
        self.logger.info("IPDV:  Len data_seq_no {}  Len ipdv_list {}".format(len(data_seq_no), len(ipdv_list)))

        return ipdv_list

    def pdv(self, data_seq_no, data_sent_ts, data_recv_ts, *args):
        delta_t_list = self.owdelay(data_seq_no, data_sent_ts, data_recv_ts, *args)
        min_delta_t = min(delta_t_list)
        pdv_list = [delta_t - min_delta_t for delta_t in delta_t_list]

        return pdv_list

    def throughput(self, data_seq_no, data_sent_ts, data_recv_ts, *args, pkt_size=150):
        interval_length = 1  # second
        throughput = []

        count = 0
        start = None
        for recv_ts in data_recv_ts:
            recv_ts_dec = sec_nsec_to_decimal(*recv_ts)
            if not start:
                start = recv_ts_dec
            if recv_ts_dec - start > 1:
                throughput.append(count)
                count = 0
                start = recv_ts_dec
            else:
                count += 1

        return throughput

    def throughput_test(self, data_seq_no, data_sent_ts, data_recv_ts, *args, pkt_size=150, pause_time=1):
        # pause_time = 1  # second
        throughput = []
        throughput.append([])

        burst_index = 0
        prev_recv_ts = None
        for recv_ts in data_recv_ts:
            recv_ts_dec = sec_nsec_to_decimal(*recv_ts)
            if prev_recv_ts:
                gap = recv_ts_dec - prev_recv_ts
                if gap > pause_time:
                    burst_index += 1
                    throughput.append([])
                    prev_recv_ts = None
                    continue
                throughput[burst_index].append(float(pkt_size / gap))
            prev_recv_ts = recv_ts_dec

        return throughput

    def downtime(self, data_seq_no, data_sent_ts, data_recv_ts, *args, threshold=0.01):
        # NOTE: lost packets are  not considered
        first_ts = None
        first_seq_no = None
        consecutive = None
        downtimes = []
        consecutives = []

        if not len(args):
            for (seq_no, sent_ts, recv_ts) in zip(data_seq_no, data_sent_ts, data_recv_ts):
                recv_ts = sum(recv_ts)  # TODO: This decreases the accuracy
                delta_t = recv_ts - sent_ts
                if delta_t >= threshold:
                    if not first_ts:
                        first_ts = sent_ts
                        first_seq_no = seq_no
                else:
                    if first_ts:
                        downtimes.append(sent_ts - first_ts)
                        consecutives.append(seq_no - first_seq_no)
                        first_ts = None
                        first_seq_no = None
        else:
            # Note: dumb new hack to analyze core captures correctly.
            data_seq_no_pre = args[0]
            pre_indices = np.where(np.in1d(data_seq_no_pre, data_seq_no, assume_unique=True))[0]
            for (seq_no, recv_ts, pre_index) in zip(data_seq_no, data_recv_ts, pre_indices):
                sent_ts = data_sent_ts[pre_index]
                recv_ts = sum(recv_ts)
                delta_t = recv_ts - sent_ts
                if delta_t >= threshold:
                    if not first_ts:
                        first_ts = sent_ts
                        first_seq_no = seq_no
                else:
                    if first_ts:
                        downtimes.append(sent_ts - first_ts)
                        consecutives.append(seq_no - first_seq_no)
                        first_ts = None
                        first_seq_no = None
        # self.logger.error("first_ts: {} first_seq_no: {}".format(first_ts, first_seq_no))
        self.logger.info("Length Downtimes: {} Consecutives: {}".format(len(downtimes), len(consecutives)))
        return downtimes, consecutives

    def losses(self, data_seq_no, data_sent_ts, data_recv_ts, *args, duration=1000):
        losses = []

        if not len(args):
            if self.file:
                packet_rate = int(self.file.split(".")[-2])
                total = packet_rate * duration
            elif self.cfile:
                packet_rate = int(self.cfile.split(".")[-2])
                total = packet_rate * duration
            else:
                total = max(data_seq_no) + 1

            diff = np.setdiff1d(list(range(0, total)), data_seq_no, assume_unique=True)
            for k, g in itertools.groupby(enumerate(diff), lambda x: x[1] - x[0]):
                losses.append(len(list(map(operator.itemgetter(1), g))))

        else:
            # TODO: Implementation for core
            data_seq_no_pre = args[0]

            diff = np.setdiff1d(data_seq_no_pre, data_seq_no, assume_unique=True)
            # https://docs.python.org/2.6/library/itertools.html#examples
            # https://stackoverflow.com/questions/35181413/using-a-tuple-as-a-parameter-of-lambda-throws-an-error-about-a-missing-required
            for k, g in itertools.groupby(enumerate(diff), lambda x: x[1] - x[0]):
                losses.append(len(list(map(operator.itemgetter(1), g))))

            total = len(data_seq_no_pre)

        return losses, total


def show_owdelay(delta_t_lists, files, save=False):
    fig = plt.figure(tight_layout=True)
    # fig.suptitle('Will be multiple plots later', fontsize=12)
    ax = fig.add_subplot(221)
    ax.set_xscale('log')
    # ax.set_yscale('log')
    ax.set_title(r"One-way Delay Distribution (ECDF)")
    ax.set_ylabel(r'ECDF')
    ax.set_xlabel(r'One-way delay (s)')
    ax.grid(True)

    ax_hist = fig.add_subplot(222)
    ax_hist.set_xscale('log')
    ax_hist.set_title(r"One-way Delay Histogram")
    ax_hist.set_ylabel(r'Probability')
    ax_hist.set_xlabel(r'One-way delay (s)')
    ax_hist.grid(True)

    ax_cont = fig.add_subplot(212)
    ax_cont.set_title(r"One-way Delay over Time")
    ax_cont.set_ylabel(r'Delay (s)')
    ax_cont.set_xlabel(r'Packet number')
    ax_cont.grid(True)

    for i, delta_t_list in enumerate(delta_t_lists):
        name = "".join(files[i].split(".")[:-1])

        ecdf = sm.distributions.empirical_distribution.ECDF(delta_t_list)
        x = np.linspace(min(delta_t_list), max(delta_t_list), num=1000)
        y = ecdf(x)
        ax.step(x, y, label=name)

        ax_hist.hist(delta_t_list, weights=np.ones(len(delta_t_list)) / len(delta_t_list), label=name)

        ax_cont.plot(range(len(delta_t_list)), delta_t_list, label=name)

        ax_hist.legend()
        ax_cont.legend()
        ax.legend()

    plt.show()

    if save:
        pass


def show_ipdv(ipdv_lists, files, save=False):
    fig = plt.figure(tight_layout=True)
    # fig.suptitle('Will be multiple plots later', fontsize=12)
    ax = fig.add_subplot(221)
    # ax.set_xscale('log')
    ax.set_title(r"Inter-Packet Delay Variation (ECDF)")
    ax.set_ylabel(r'ECDF')
    ax.set_xlabel(r'IPDV (s)')
    ax.grid(True)

    ax_hist = fig.add_subplot(222)
    # ax_hist.set_xscale('log')
    ax_hist.set_title(r"Inter-Packet Delay Variation Histogram")
    ax_hist.set_ylabel(r'Probability')
    ax_hist.set_xlabel(r'IPDV (s)')
    ax_hist.grid(True)

    ax_cont = fig.add_subplot(212)
    ax_cont.set_title(r"Inter-Packet Delay Variation over Time")
    ax_cont.set_ylabel(r'IPDV (s)')
    ax_cont.set_xlabel(r'Packet number')
    ax_cont.grid(True)

    for i, ipdv_list in enumerate(ipdv_lists):
        name = "".join(files[i].split(".")[:-1])
        ecdf = sm.distributions.empirical_distribution.ECDF(ipdv_list)
        x = np.linspace(min(ipdv_list), max(ipdv_list), num=1000)
        y = ecdf(x)

        ax.step(x, y, label=name)

        ax_hist.hist(ipdv_list, bins=100, weights=np.ones(len(ipdv_list)) / len(ipdv_list), label=name)

        ax_cont.plot(range(len(ipdv_list)), ipdv_list, label=name)

        ax.legend()
        ax_hist.legend()
        ax_cont.legend()

    plt.show()

    if save:
        pass


def show_throughput(throughput_list, files, pkt_size=150, save=False):
    fig = plt.figure(tight_layout=True)
    ax = fig.add_subplot(221)
    # ax.set_xscale('log')
    ax.set_title(r"Packets per second ECDF")
    ax.set_ylabel(r'ECDF')
    ax.set_xlabel(r'Packets per second (pps)')
    ax.grid(True)

    ax_hist = fig.add_subplot(222)
    # ax_hist.set_xscale('log')
    ax_hist.set_title(r"Packets per second Histogram")
    ax_hist.set_ylabel(r'Probability')
    ax_hist.set_xlabel(r'Packets per second (pps)')
    ax_hist.grid(True)

    ax_cont = fig.add_subplot(212)

    ax_cont.set_title(r"Packets per second over Time")
    ax_cont.set_ylabel(r'Packets per second (pps)')
    ax_cont.set_xlabel(r'Time (s)')
    ax_cont.grid(True)
    ax_cont_bytes = ax_cont.secondary_yaxis('right', functions=(lambda x: x * pkt_size, lambda x: x / pkt_size))
    ax_cont_bytes.set_ylabel(r'Bytes per second (Bps)')

    for i, throughput in enumerate(throughput_list):
        name = "".join(files[i].split(".")[:-1])

        ecdf = sm.distributions.empirical_distribution.ECDF(throughput)
        x = np.linspace(min(throughput), max(throughput), num=1000)
        y = ecdf(x)

        ax.step(x, y, label=name)

        ax_hist.hist(throughput, bins=100, weights=np.ones(len(throughput)) / len(throughput), label=name)

        ax_cont.plot(range(len(throughput)), throughput, label=name)

        ax.legend()
        ax_hist.legend()
        ax_cont.legend()

    plt.show()

    if save:
        pass


def decimal_to_sec_nsec(ts):
    ts_tuple = ts.as_tuple()
    sec = sum([v * 10 ** i for i, v in enumerate(reversed(ts_tuple.digits[:ts_tuple.exponent]))])
    nsec = sum([v * 10 ** -i for i, v in enumerate(ts_tuple.digits[ts_tuple.exponent:], 1)])
    return sec, nsec


def sec_nsec_to_decimal(sec, nsec):
    return sec + decimal.Decimal(nsec)


# https://stackoverflow.com/questions/16974047/efficient-way-to-find-missing-elements-in-an-integer-sequence
def missing_elements(L):
    start, end = L[0], L[-1]
    return sorted(set(range(start, end + 1)).difference(L))


# https://stackoverflow.com/questions/3755136/pythonic-way-to-check-if-a-list-is-sorted-or-not
def issorted(l):
    """Check if l is sorted"""
    # return (np.diff(l) >= 0).all()  # is diff between all consecutive entries >= 0
    return all(l[i] <= l[i+1] for i in range(len(l)-1))

def check_unique(x):
    if len(x) > len(set(x)):
        return False
    else:
        return True



# https://stackoverflow.com/questions/13530762/how-to-know-bytes-size-of-python-object-like-arrays-and-dictionaries-the-simp
def get_obj_size(obj):
    marked = {id(obj)}
    obj_q = [obj]
    sz = 0

    while obj_q:
        sz += sum(map(sys.getsizeof, obj_q))

        # Lookup all the object referred to by the object in obj_q.
        # See: https://docs.python.org/3.7/library/gc.html#gc.get_referents
        all_refr = ((id(o), o) for o in gc.get_referents(*obj_q))

        # Filter object that are already marked.
        # Using dict notation will prevent repeated objects.
        new_refr = {o_id: o for o_id, o in all_refr if o_id not in marked and not isinstance(o, type)}

        # The new obj_q will be the ones that were not marked,
        # and we will update marked with their ids so we will
        # not traverse them again.
        obj_q = new_refr.values()
        marked.update(new_refr.keys())

    return sz


def find_obj_files(logdir, core=False):
    if logdir[-1] == "/":
        dir = logdir
    else:
        dir = logdir + "/"
    all_objs = []

    for (dirpath, dirnames, filenames) in os.walk(dir):
        all_objs.extend(sorted(filenames))
        break

    if core:
        core_objs = [dir + file for file in all_objs if ".core." in file and ".obj" in file]
        return core_objs
    else:
        objs = [dir + file for file in all_objs if ".core." not in file and ".obj" in file]
        return objs


def pseudo_pcap_files(objs, core=False):
    pcaps = []
    for obj in objs:
        pcap = ".".join(obj.split(".")[:-2]) + ".pcap"
        if pcap in pcaps:
            continue
        else:
            pcaps.append(pcap)
    return pcaps


def find_pcap_files(logdir, core=False):
    if logdir[-1] == "/":
        dir = logdir
    else:
        dir = logdir + "/"
    all_pcaps = []

    for (dirpath, dirnames, filenames) in os.walk(dir):
        all_pcaps.extend(sorted(filenames))
        break
    core_pcaps = [dir + file for file in all_pcaps if "core.pcap" in file]
    pcaps = [dir + file for file in all_pcaps if "pcap" in file and not ".core." in file]

    if core:
        return core_pcaps
    else:
        return pcaps


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--files', help='Specify pcap files (can be multiple)', nargs='*')
    parser.add_argument('--show', help='Show plot', action='store_true')
    parser.add_argument('--save', help='Save plot', action='store_true')
    parser.add_argument('--gen', help='Specify used traffic generator (\'MoonGen\' or \'Python\')', default='MoonGen')
    parser.add_argument('--save-pickle', help='Save analysed pcap metadata objects with pickle', action='store_true')
    parser.add_argument('--load-pickle', help='Load analysed pcap metadata objects with pickle', action='store_true')
    parser.add_argument('--type', help='Specify type of analysis / plot (\'owdelay\', \'ipdv\', \'throughput\')',
                        default='owdelay')
    parser.add_argument('--pkt-size',
                        help='Specify used packet size. Will be used for throughput calculation. Default: 150bytes ',
                        default=150)
    parser.add_argument('--save-pickle-dir',
                        help='Specify the directory where the pcap metadata pickle files will be saved.')
    parser.add_argument('--core',
                        help='Process core pcaps of specified core type (Nokia or Open5GS). Note: --upload or --download is needed')
    parser.add_argument('--upload', help='Upload core measurement.', action='store_true')
    parser.add_argument('--download', help='Download core measurement.', action='store_true')
    args = parser.parse_args()

    if args.core:
        # NOTE: better to explicitly specify if it is upload or download and not use default argument
        assert args.upload or args.download, "--upload or --download is needed, if core pcap is analyzed."
        assert args.upload != args.download, "--upload and --download cannot be simultaneously chosen."

    pp_dict = {}
    results_dict = {}
    cresults_dict = {}

    with Pool() as pool:
        workers_dict = {}
        if args.core:
            opts = {"save_pickle": args.save_pickle, "load_pickle": args.load_pickle, "save_pickle_dir": args.save_pickle_dir,
                    "core_type": args.core, "upload": args.upload}
            for cfile in args.files:
                pp_dict[cfile] = PCAPParser(cfile=cfile)
                workers_dict[cfile] = pool.apply_async(pp_dict[cfile].analyze_core, args=[cfile], kwds=opts)
        else:
            opts = {"save_pickle": args.save_pickle, "load_pickle": args.load_pickle,
                    "save_pickle_dir": args.save_pickle_dir}
            for file in args.files:
                pp_dict[file] = PCAPParser(file=file)
                workers_dict[file] = pool.apply_async(pp_dict[file].analyze, args=[file], kwds=opts)

        for worker in workers_dict.keys():
            results_dict[worker] = workers_dict[worker].get()
    print("Analyzed PCAPs.")
    # TODO: scenario analysis does not use multiprocessing yet
    if args.show:
        if args.type == "owdelay":
            delta_t_lists = [pp_dict[key].owdelay(*results_dict[key]) for key in results_dict.keys()]
            show_owdelay(delta_t_lists, args.files, save=args.save)
        elif args.type == "ipdv":
            ipdv_lists = [pp_dict[key].ipdv(*results_dict[key]) for key in results_dict.keys()]
            show_ipdv(ipdv_lists, args.files, save=args.save)
        elif args.type == "throughput":
            throughputs = [pp_dict[key].throughput(*results_dict[key]) for key in results_dict.keys()]
            show_throughput(throughputs, args.files, pkt_size=args.pkt_size, save=args.save)
        elif args.type == "downtime":
            downtimes = [pp_dict[key].downtime(*results_dict[key]) for key in results_dict.keys()]
        elif args.type == "losses":
            downtimes = [pp_dict[key].losses(*results_dict[key]) for key in results_dict.keys()]
        else:
            print("Wrong plot type specified.")
