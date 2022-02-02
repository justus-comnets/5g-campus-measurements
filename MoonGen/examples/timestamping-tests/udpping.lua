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
local random, ln = math.random, math.log



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

local CLOCK_REALTIME = 0
local CLOCK_MONOTONIC = 1


-- used to resolve GW_DST_MAC
--local GW_IP		= "10.40.18.1"
-- used as source IP to resolve GW_IP to GW_DST_MAC
--local ARP_IP	= SRC_IP

function configure(parser)
	parser:description("Generates onedirectional CBR traffic with software rate control, timestamps and captures it at second port.")
	parser:argument("port", "Device to transmit from."):convert(tonumber)
	parser:argument("numPkts", "Number of packets which are sent in total."):convert(tonumber)
	parser:argument("pktRate", "Packet rate in Pps."):convert(tonumber)
	parser:argument("pktSize", "Size of packets."):convert(tonumber)
	parser:option("-f --file", "Filename of the pcap."):default("/tmp/timestamp.pcap")
--	https://github.com/libmoon/libmoon/blob/fba09041b635d719b0190fab427f638b02e4612b/lua/proto/arp.lua#L570
	parser:option("--gw-mac", "Gateway MAC."):default("3c:fd:fe:b9:24:68")
	parser:option("--src-ip", "SRC IP."):default("10.40.16.19")
	parser:option("--dst-ip", "DST IP."):default("10.40.24.104")
	parser:option("--upload", "ARP task will run on rpldev and reply with DST IP."):args("?")
	parser:option("--poisson", "Poisson distribution will be used for packet generation."):args("?")


	parser:option("--reply", "Work in echo reply mode."):convert(tonumber)
	parser:option("-rf --rfile", "Filename of the replier pcap.")

end

function master(args)

    local SRC_IP = args.src_ip
	local DST_IP = args.dst_ip
	local UE_IP = args.ue_ip
	local GW_MAC = args.gw_mac
    log:info("Setting GW MAC to %s", GW_MAC)

	if not args.reply then
		local dev = device.config{port = args.port, txQueues = 1, rxQueues = 1}
		device.waitForLinks(100)
		mg.startTask("dumper", dev:getRxQueue(0), args.file)
		mg.startTask("txTimestamper", dev:getTxQueue(0), args.numPkts, args.pktRate, args.pktSize, SRC_IP, DST_IP, GW_MAC)
		arp.startArpTask{{txQueue = dev:getTxQueue(0), ips = SRC_IP}}

	end
	if args.reply and args.reply ~= args.port then
		local dev = device.config{port = args.port, txQueues = 1, rxQueues = 1}
		local rplDev = device.config{port = args.reply, txQueues = 1, rxQueues = 1}
		device.waitForLinks(100)
		mg.startTask("echoReply", rplDev, args.rfile)
		mg.startTask("dumper", dev:getRxQueue(0), args.file)
		mg.startTask("txTimestamper", dev:getTxQueue(0), args.numPkts, args.pktRate, args.pktSize, SRC_IP, DST_IP, GW_MAC, args.poisson)
		if args.upload then
			arp.startArpTask{{txQueue = rplDev:getTxQueue(0), ips = DST_IP} }
		else
			arp.startArpTask{{txQueue = dev:getTxQueue(0), ips = SRC_IP} }
		end

	end
	if args.reply == args.port then
		log:error("Not yet tested.")
--		local dev = device.config{port = args.port, txQueues = 1, rxQueues = 1 }
--		device.waitForLinks(100)
--		mg.startTask("echoReply", dev, args.file)
--		arp.startArpTask{{txQueue = dev:getTxQueue(0), ips = SRC_IP}}
	end

	arp.waitForStartup()
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
	local rateLimit = timer:new(1 / 10) -- timestamped packets
	local i = 0
	while i < 350 do
		bufs:alloc(pktSize)
		bufs:offloadUdpChecksums()
		queue:send(bufs)
		rateLimit:wait()
		rateLimit:reset()
		i = i + 1
	end
	return
end

function txTimestamper(queue, numPkts, pktRate, pktSize, SRC_IP, DST_IP, DST_MAC, poisson)
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
	log:info("Start packet generation")
	local i = 0
	while i < numPkts and mg.running() do
		bufs:alloc(pktSize)
		bufs:offloadUdpChecksums()
		queue:sendWithClkTimestampSeqno(bufs, CLOCK_REALTIME, 40, i)
		rateLimit:wait()
		if poisson then
			poissonDelay = -ln(1 - random()) / pktRate 
			rateLimit:reset(poissonDelay)
		else
			rateLimit:reset()
		end
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
	local bufs = memory.bufArray(1)
	local drainQueue = timer:new(3)
	while drainQueue:running() do
		local rx = queue:recvWithTimestampsClk(bufs, CLOCK_REALTIME)
		for i = 1, rx do
            tv_sec, tv_nsec = splitTimestamp(bufs[i].udata64)
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

function echoReply(dev, file)
	local devMac = dev:getMac(true)
	local rxQueue = dev:getRxQueue(0)
	local txQueue = dev:getTxQueue(0)
	local writer
	local captureCtr, filterCtr
	local tv_sec, tv_nsec
    -- set the relative starting timestamp to 0
    writer = pcap:newWriterNS(file, 0)
    captureCtr = stats:newPktRxCounter("Capture, thread echo reply " )
--	local mem = memory.createMemPool()
	local bufs = memory.bufArray(1)
	local drainQueue = timer:new(5)
	while drainQueue:running() do
		local rx = rxQueue:recvWithTimestampsClk(bufs, CLOCK_REALTIME)
		if rx > 0 then
			if filter(bufs[1]) then
				tv_sec, tv_nsec = splitTimestamp(bufs[1].udata64)
				writer:writeBufNano(tv_sec, tv_nsec, bufs[1], 160)
				local pkt = bufs[1]:getIP4Packet()
				local ip4src = pkt.ip4.src:get()
				pkt.eth.dst:set(pkt.eth.src:get())
				pkt.eth.src:set(devMac)
				pkt.ip4.src:set(pkt.ip4.dst:get())
				pkt.ip4.dst:set(ip4src)
				-- the bufs are free'd implicitly by this function
				txQueue:sendWithClkTimestamp(bufs, CLOCK_REALTIME, 40)
				captureCtr:countPacket(bufs[1])
				goto continue
			end
			if bufs[1]:getEthernetPacket().eth:getType() == eth.TYPE_ARP then
				-- inject arp packets to the ARP task
				-- this is done this way instead of using filters to also dump ARP packets here
--				log:info("Got ARP packet from " .. bufs[1]:getEthernetPacket().eth:getSrcString())
				arp.handlePacket(bufs[1])
			else
				-- do not free packets handlet by the ARP task, this is done by the arp task
				bufs[1]:free()
			end
		end
		::continue::

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
