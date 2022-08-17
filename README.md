[5G Campus Networks: A First Measurement Study](https://dx.doi.org/10.1109/ACCESS.2021.3108423)
---
This repository contains the source code used for measurements, data analysis, and plot generation for the papers [5G Campus Networks: A First Measurement Study](https://dx.doi.org/10.1109/ACCESS.2021.3108423) [1] and [Empirical Study of 5G Downlink & Uplink Scheduling and its Effects on Latency](https://doi.org/10.1109/WoWMoM54355.2022.00017) [2].

The corresponding data set can be found at [IEEE Dataport](https://dx.doi.org/10.21227/xe3c-e968) [3].

## Content
* [automated_measurement](automated_measurement/) contains scripts to automatically perform measurements using MooGen
* [MoonGen](MoonGen/) contains a copy of the original [MoonGen Repository](https://github.com/emmericp/MoonGen) 
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
## 

# References
[1] J. Rischke, P. Sossalla, S. Itting, F. H. P. Fitzek and M. Reisslein, "5G Campus Networks: A First Measurement Study," in IEEE Access, vol. 9, pp. 121786-121803, 2021, doi: 10.1109/ACCESS.2021.3108423. [Available online](https://dx.doi.org/10.1109/ACCESS.2021.3108423).
```
@article{9524600,
title = {5G Campus Networks: A First Measurement Study},
author = {Justus {Rischke} and Peter {Sossalla} and Sebastian A. W. {Itting} and Frank H. P. {Fitzek} and Martin {Reisslein}},
doi = {10.1109/ACCESS.2021.3108423},
year = {2021},
date = {2021-01-01},
urldate = {2021-01-01},
journal = {IEEE Access},
volume = {9},
pages = {121786-121803},
keywords = {},
pubstate = {published},
tppubtype = {article}}
```

[2] J. Rischke, C. Vielhaus, P. Sossalla, S. Itting, G. T. Nguyen and F. H. P. Fitzek, "Empirical Study of 5G Downlink & Uplink Scheduling and its Effects on Latency," 2022 IEEE 23rd International Symposium on a World of Wireless, Mobile and Multimedia Networks (WoWMoM), 2022, pp. 11-19, doi: 10.1109/WoWMoM54355.2022.00017. [Available online](https://doi.org/10.1109/WoWMoM54355.2022.00017).
```
@INPROCEEDINGS{9842810,
author={Rischke, Justus and Vielhaus, Christian and Sossalla, Peter and Itting, Sebastian and Nguyen, Giang T. and Fitzek, Frank H. P.},
booktitle={2022 IEEE 23rd International Symposium on a World of Wireless, Mobile and Multimedia Networks (WoWMoM)}, 
title={Empirical Study of 5G Downlink & Uplink Scheduling and its Effects on Latency}, 
year={2022},
volume={},
number={},
pages={11-19},
doi={10.1109/WoWMoM54355.2022.00017}}
```

[3] Justus Rischke, July 8, 2021, "5G Campus Networks: Measurement Traces", IEEE Dataport, doi: https://dx.doi.org/10.21227/xe3c-e968.  [Available online](https://dx.doi.org/10.21227/xe3c-e968).
```
@data{xe3c-e968-21,
doi = {10.21227/xe3c-e968},
url = {https://dx.doi.org/10.21227/xe3c-e968},
author = {Rischke, Justus},
publisher = {IEEE Dataport},
title = {5G Campus Networks: Measurement Traces},
year = {2021}} 
```