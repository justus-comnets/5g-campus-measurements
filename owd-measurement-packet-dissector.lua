--
-- One-Way Delay Measurement Protocol  - Wireshark dissector
--
-- Writen by: Justus Rischke
--


owdmeasurement_protocol = Proto("owd", "OWD measurement protocol dissector")

local fields = owdmeasurement_protocol.fields
fields.ts_sec = ProtoField.uint64("owd.ts_sec", "TS Seconds", base.DEC)
fields.ts_nsec = ProtoField.uint64("owd.ts_nsec", "TS Nano Seconds", base.DEC)
fields.seq_no = ProtoField.uint64("owd.seq_no", "Sequence Number", base.DEC)


function owdmeasurement_protocol.dissector (buffer, pinfo, tree)
    pinfo.cols.protocol = "One-Way Delay Proto"
    local subtree = tree:add(owdmeasurement_protocol,buffer(),"OWD Measurement Protocol Data")
    subtree:add(fields.ts_sec, buffer(0,8))
    subtree:add(fields.ts_nsec, buffer(8,8))
    subtree:add(fields.seq_no, buffer(16,8))
end

local udp_table = DissectorTable.get("udp.port")
udp_table:add(65001,owdmeasurement_protocol)
