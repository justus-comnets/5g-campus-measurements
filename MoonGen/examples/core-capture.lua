--- Software timestamping precision test.
--- (Used for an evaluation for a paper)
local mg     = require "moongen"
local ts     = require "timestamping"
local device = require "device"
local hist   = require "histogram"
local memory = require "memory"
local stats  = require "stats"
local timer  = require "timer"
local ffi    = require "ffi"
local arp	 = require "proto.arp"
local log    = require "log"
local arp	 = require "proto.arp"
local ip	 = require "proto.ip4"

local pcap   = require "pcap"
local eth    = require "proto.ethernet"
local ip4    = require "proto.ip4"

--local PKT_SIZE = 150

--local NUM_PKTS = 10^7

-- set addresses here
local DST_MAC		= nil -- resolved via ARP on GW_IP or DST_IP, can be overriden with a string here
--local SRC_IP		= "10.40.18.2" -- actual address will be SRC_IP_BASE + random(0, flows)
--local DST_IP		= "10.40.17.1"
--local SRC_PORT		= 1234
local GTP_PORT	= 2152
local DST_PORT		= 65001


function configure(parser)
	parser:description("Captures all packets one port. Filters for packets processed by 5G core.")
	parser:argument("rxPort", "Device to receive from."):convert(tonumber)
	parser:option("-f --file", "Filename of the pcap."):default("/tmp/core.pcap")
end


function master(args)
	local rxDev = device.config{port = args.rxPort, rxQueues = 1}
	device.waitForLinks()
	device.waitForLinks()
	rxDev:enableRxTimestampsAllPackets(rxDev:getRxQueue(0))
	mg.startSharedTask("dumper", rxDev:getRxQueue(0), args.file)
	stats.startStatsTask{rxDevices = {rxDev} }
	mg.waitForTasks()
end



function dumper(queue, file)
    queue.dev:enableRxTimestampsAllPackets(queue)
	-- default: show everything
	local writer
	local captureCtr, filterCtr
    -- set the relative starting timestamp to 0
    writer = pcap:newWriterNS(file, 0)
    captureCtr = stats:newPktRxCounter("Capture, thread #" )
	local bufs = memory.bufArray()
	while mg.running() do
		local rx = queue:tryRecv(bufs, 100)
--        log:info("batchTime: " .. batchTime)
		for i = 1, rx do
            local tv_sec, tv_nsec = bufs[i]:getTimestampTS(queue.dev)
--            log:info("tv_sec: " .. tv_sec .. " tv_nsec: " .. tv_nsec)
			local buf = bufs[i]
			if filter(buf) then
				if writer then
--					writer:writeBuf(tv_sec, buf)
					writer:writeBufNano(tv_sec, tv_nsec, buf)
					captureCtr:countPacket(buf)
				else
					buf:dump()
				end
			end
			buf:free()
		end
		if writer then
			captureCtr:update()
		end
	end
	if writer then
		captureCtr:finalize()
		log:info("Flushing buffers, this can take a while...")
		writer:close()
	end
end

function filter(buf)
	local pkt = buf:getUdpPacket()
	if pkt.eth.type == bswap16(eth.TYPE_IP) and pkt.ip4.protocol == ip4.PROTO_UDP then
		local port = pkt.udp:getDstPort()
		if port == DST_PORT then
			return true
		else
			if port == GTP_PORT then
				local gtpPkt = buf:getGtpUdpPacket()
				if gtpPkt.nestedUdp:getDstPort() == DST_PORT then
					return true
				else
					return false
				end
			else
				return false
			end
		end
	end
end

