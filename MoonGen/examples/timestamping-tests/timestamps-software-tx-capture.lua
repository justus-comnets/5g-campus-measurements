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
require "utils"
local pcap   = require "pcap"
local eth    = require "proto.ethernet"
local ip4    = require "proto.ip4"
local udp    = require "proto.udp"
local gtp    = require "proto.gtp"




--local PKT_SIZE = 150

--local NUM_PKTS = 10^7

-- set addresses here
--local GW_DST_MAC		= nil -- resolved via ARP on GW_IP or DST_IP, can be overriden with a string here
--local SRC_IP		= "10.40.18.2" -- actual address will be SRC_IP_BASE + random(0, flows)
--local DST_IP		= "10.40.15.4"
--local SRC_PORT		= 1234
local SRC_PORT_TS	= 1337
local GTP_PORT		= 2152
local DST_PORT		= 65001

-- used to resolve GW_DST_MAC
--local GW_IP		= "10.40.18.1"
-- used as source IP to resolve GW_IP to GW_DST_MAC
--local ARP_IP	= SRC_IP

function configure(parser)
	parser:description("Generates onedirectional CBR traffic with software rate control, timestamps and captures it at second port.")
	parser:argument("txPort", "Device to transmit from."):convert(tonumber)
	parser:argument("rxPort", "Device to receive from."):convert(tonumber)
	parser:argument("numPkts", "Number of packets which are sent in total."):convert(tonumber)
	parser:argument("pktRate", "Packet rate in Pps."):convert(tonumber)
	parser:argument("pktSize", "Size of packets."):convert(tonumber)
	parser:option("-f --file", "Filename of the pcap."):default("/tmp/timestamp.pcap")
--	https://github.com/libmoon/libmoon/blob/fba09041b635d719b0190fab427f638b02e4612b/lua/proto/arp.lua#L570
	parser:option("--gw-mac", "Gateway MAC."):default("3c:fd:fe:b9:24:68")
	parser:option("--src-ip", "SRC IP."):default("10.40.16.19")
	parser:option("--dst-ip", "DST IP."):default("10.40.17.1")
	parser:option("--ue-ip", "UE IP."):default("192.168.1.102")

	parser:option("--corePort", "Device to capture traffic from core."):convert(tonumber)
	parser:option("-cf --cfile", "Filename of the pcap."):default("/tmp/core.pcap")
end

function master(args)

    local SRC_IP = args.src_ip
	local DST_IP = args.dst_ip
	local UE_IP = args.ue_ip
	local GW_MAC = args.gw_mac
    log:info("Setting GW MAC to %s", GW_MAC)

	local coreDev
	if args.corePort and args.cfile then
		coreDev = device.config{port = args.corePort, rxQueues = 1, rxDescs = 4096, dropEnable = false }
		coreDev:enableRxTimestampsAllPackets(coreDev:getRxQueue(0))
		coreDev:clearTimestamps()
	end

	local txDev = device.config{port = args.txPort, txQueues = 1 }
	local rxDev = device.config{port = args.rxPort, rxQueues = 1, txQueues = 1, rxDescs = 4096, dropEnable = false }
	device.waitForLinks()
    device.waitForLinks()

--	if args.corePort and args.cfile then
--		stats.startStatsTask{txDevices = {txDev}, rxDevices = {rxDev, coreDev} }
--	else
--		stats.startStatsTask{txDevices = {txDev}, rxDevices = {rxDev} }
--	end

--	arp.startArpTask{{ rxQueue = txDev:getRxQueue(0), txQueue = txDev:getTxQueue(0), ips = SRC_IP }}
	arp.startArpTask{{txQueue = rxDev:getTxQueue(0), ips = UE_IP}}
	arp.waitForStartup()

	mg.startTask("dumper", rxDev:getRxQueue(0), args.file)

	if args.corePort and args.cfile then
		mg.startTask("coreDumper", coreDev:getRxQueue(0), args.cfile)
	end

	mg.startTask("txTimestamper", txDev:getTxQueue(0), args.numPkts, args.pktRate, args.pktSize, SRC_IP, DST_IP, GW_MAC)


	mg.waitForTasks()
end

local function testConnection(queue, pktSize, SRC_IP, DST_IP, DST_MAC)
	log:info("Test connection")
	local mem = memory.createMemPool(function(buf)
		buf:getUdpPacket():fill{
			ethSrc = queue,
			ethDst = DST_MAC,
			ip4Src = SRC_IP,
			ip4Dst = DST_IP,
			udpSrc = SRC_PORT_TS,
			udpDst = 42069,
			pktLength = pktSize
		}
	end)
	local bufs = mem:bufArray(1)
	local rateLimit = timer:new(1 / 5) -- timestamped packets
	local i = 0
	while i < 50 do
		bufs:alloc(pktSize - 8)
		bufs:offloadUdpChecksums()
		queue:send(bufs)
		rateLimit:wait()
		rateLimit:reset()
		i = i + 1
	end
	return
end

function txTimestamper(queue, numPkts, pktRate, pktSize, SRC_IP, DST_IP, DST_MAC)
	testConnection(queue, pktSize, SRC_IP, DST_IP, DST_MAC)
	local mem = memory.createMemPool(function(buf)
		-- just to use the default filter here
		-- you can use whatever packet type you want
		buf:getUdpPacket():fill{
			ethSrc = queue,
			ethDst = DST_MAC,
			ip4Src = SRC_IP,
			ip4Dst = DST_IP,
			udpSrc = SRC_PORT_TS,
			udpDst = DST_PORT,
			pktLength = pktSize
		}
	end)
	mg.sleepMillis(1000)
	local bufs = mem:bufArray(1)
--	TODO: Make flag for HW vs SW rate control
	local rateLimit = timer:new(1 / pktRate) -- timestamped packets
--    queue:setRate(pktRate * (pktSize + 4) * 8)
--	queue:setRate(pktRate)
--	queue:setRateMpps(pktRate, pktSize)
	log:info("Start packet generation")
	local i = 0
	while i < numPkts and mg.running() do
		bufs:alloc(pktSize - 8)
		bufs:offloadUdpChecksums()
		queue:sendWithTimestampSeqno(bufs, 40, i)
		rateLimit:wait()
		rateLimit:reset()
		i = i + 1
	end
	mg.sleepMillis(1000)
	mg.stop()
end

function dumper(queue, file)
--    queue.dev:enableRxTimestampsAllPackets(queue)
	-- default: show everything
	local writer
	local captureCtr, filterCtr
	local tv_sec, tv_nsec
    -- set the relative starting timestamp to 0
    writer = pcap:newWriterNS(file, 0)
    captureCtr = stats:newPktRxCounter("Capture, thread recv" )
	local bufs = memory.bufArray()
	local drainQueue = timer:new(5)
	while drainQueue:running() do
		local rx = queue:tryRecv(bufs, 100)
		for i = 1, rx do
			tv_sec, tv_nsec = getRealtimeTimestamp()
			if filter(bufs[i]) then
				writer:writeBufNano(tv_sec, tv_nsec, bufs[i], 160)
				captureCtr:countPacket(bufs[i])
			end
			if bufs[i]:getEthernetPacket().eth:getType() == eth.TYPE_ARP then
				-- inject arp packets to the ARP task
				-- this is done this way instead of using filters to also dump ARP packets here
				arp.handlePacket(bufs[i])
			else
				-- do not free packets handlet by the ARP task, this is done by the arp task
				bufs[i]:free()
			end
		end

		captureCtr:update()

		if mg.running() then
			drainQueue:reset()
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
		return pkt.udp:getDstPort() == DST_PORT
	end
end

function coreDumper(queue, file)
--    queue.dev:enableRxTimestampsAllPackets(queue)
	-- default: show everything
	local writer_core
	local captureCtr
	local tv_sec, tv_nsec
    -- set the relative starting timestamp to 0
    writer_core = pcap:newWriterNS(file, 0)
    captureCtr = stats:newPktRxCounter("Capture, thread core" )
	local bufs = memory.bufArray()
	local drainQueue = timer:new(5)
	while drainQueue:running() do
		local rx = queue:tryRecv(bufs, 100)
		for i = 1, rx do
			tv_sec, tv_nsec = bufs[i]:getTimestampTS(queue.dev)
--            if true then
--			if coreFilter(bufs[i]) then
			if filter(bufs[i]) then
				captureCtr:countPacket(bufs[i])
			end
			writer_core:writeBufNano(tv_sec, tv_nsec, bufs[i], 160)
		end
		bufs:freeAll()
		captureCtr:update()
		if mg.running() then
			drainQueue:reset()
		end
	end
	captureCtr:finalize()
	log:info("Flushing buffers, this can take a while...")
	writer_core:close()
end

function coreFilter(buf)
	local pkt = buf:getUdpPacket()
	if pkt.eth.type == bswap16(eth.TYPE_IP) and pkt.ip4.protocol == ip4.PROTO_UDP then
		local port = pkt.udp:getDstPort()
		if port == DST_PORT or port == GTP_PORT then
			return true
		else
			return false
		end
	end
end