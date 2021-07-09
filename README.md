5G Campus Networks: A First Measurement Study
---

Source code used for measurements, data analysis and plot generation.

## Content
* [automated_measurement](automated_measurement/) contains scripts to automatically perform measurements using MooGen
* [MoonGen](MonGen/) contains a copy of the original [MoonGen Repository](https://github.com/emmericp/MoonGen) 
by Paul Emmerich ([Commit b11da03](https://github.com/emmericp/MoonGen/commit/b11da03004ab08e1c12fe3c2b51d6417553b9fbc))
with some modifications. TODO: Replace with fork.
* [plots](plots/) contains a generalized plot script.
  * [paper](plots/paper/) contains plot scripts for paper. Some plots need adaption of value ranges etc.
  * [README](plots/README.md) a README describing the structure of the measurement data.

## How to
### Measurement
Either execute the MoonGen script directly with 
```
$ sudo ./MoonGen/build/MoonGen ./MoonGen/examples/timestamping-tests/timestamps-software-tx-capture.lua 2 3 100000000 
100000 128 --file /tmp/128.100000.pcap --gw-mac 0c:42:a1:0a:42:f6 --src-ip 10.40.16.19 --dst-ip 10.40.17.2 
--ue-ip 192.168.1.102 --corePort 0 --cfile /tmp/128.100000.core.pcap
```
or use the automation script with
```
$ python3 ./automated_measurement/automated_measurement.py --scenario VarParams --gw-mac 0c:42:a1:0a:42:f6 --src-ip 10.40.16.19 
--dst-ip 10.40.17.2 --ue-ip 192.168.1.102 --logdir /tmp/ --core 0 --txport 2 --rxport 3
```

For PCAP evaluation using Wireshark, a dissector is provided [owd-measurement-packet-dissector.lua](owd-measurement-packet-dissector.lua)

### PCAP processing

For processing the PCAPs multiple scripts are provided:
* [pcap_parser.py](pcap_parser.py) which implements the basic pcap parsing
```
$ python3.8 pcap_parser.py --type owdelay --files /tmp/128.10000.core.pcap --show --save-pickle
```
* [process_pcaps.py](process_pcaps.py) processes multiple pcaps at once using multiprocessing
```
$ python3.8 process_pcaps.py /tmp/NSA/VarParams/download /tmp/NSAproc/VarParams/download
```
other helper scripts such as:
* [batch_process.py](batch_process.py) to evaluate multipe scenarios (SA-up, SA-down, NSA-up, NSA-down)
* [filter.py](filter.py) to filter out any packets which are not related to the measurement

### Plot generation

Plots can be generated with [plot.py](plots/plot.py)
```
$ python3.8 plot.py --scenario VarParams --logdirs /tmp/SA/VarParams/download /tmp/NSA/VarParams/download --labels SA NSA
 --plot-type multiplecdf-owd --paper --show
```

