local device = require "device"
local ffi    = require "ffi"
local pkt    = require "packet"
require "dpdkc" -- struct definitions

local txQueue = device.__txQueuePrototype
local C = ffi.C
local uint64Ptr = ffi.typeof("uint64_t*")

ffi.cdef[[
	void moongen_send_packet_with_timestamp(uint8_t port_id, uint16_t queue_id, struct rte_mbuf* pkt, uint16_t offs);
]]

ffi.cdef[[
	void moongen_send_packet_with_seqno(uint8_t port_id, uint16_t queue_id, struct rte_mbuf* pkt, uint16_t offs, uint64_t seqno);
]]

ffi.cdef[[
	void moongen_send_packet_with_clk_timestamp_seqno(uint8_t port_id, uint16_t queue_id, struct rte_mbuf* pkt, clockid_t clk_id, uint16_t offs, uint64_t seqno);
]]

ffi.cdef[[
	void moongen_send_packet_with_clk_timestamp(uint8_t port_id, uint16_t queue_id, struct rte_mbuf* pkt, clockid_t clk_id, uint16_t offs);
]]

ffi.cdef[[
	void moongen_send_packet_with_hw_timestamp_seqno(uint8_t port_id, uint16_t queue_id, struct rte_mbuf* pkt, uint16_t offs, uint32_t tx_high, uint32_t tx_low, uint64_t seqno);
]]

ffi.cdef[[
	struct timespec split_uint64_timestamp(uint64_t timestamp);
]]

--- Send a single timestamped packet
-- @param bufs bufArray, only the first packet in it will be sent
-- @param offs offset in the packet at which the timestamp will be written. will be aligned to a uint64_t
function txQueue:sendWithTimestamp(bufs, offs)
	self.used = true
	offs = offs and offs / 8 or 6 -- first 8-byte aligned value in UDP payload
	C.moongen_send_packet_with_timestamp(self.id, self.qid, bufs.array[0], offs)
end

--- Send a single packet with sequence number
-- @param bufs bufArray, only the first packet in it will be sent
-- @param offs offset in the packet at which the timestamp will be written. will be aligned to a uint64_t
-- @param seqno seqno, which will be written after the timestamp.

function txQueue:sendWithSeqno(bufs, offs, seqno)
	self.used = true
	offs = offs and offs / 8 or 6 -- first 8-byte aligned value in UDP payload
	C.moongen_send_packet_with_seqno(self.id, self.qid, bufs.array[0], offs, seqno)
end

--- Send a single timestamped packet with sequence number
-- @param bufs bufArray, only the first packet in it will be sent
-- @param offs offset in the packet at which the timestamp will be written. will be aligned to a uint64_t
-- @param seqno seqno, which will be written after the timestamp.
-- @param clk_id clk_id, clock used to get timestamp (REALTIME, MONOTONIC etc.).

function txQueue:sendWithClkTimestampSeqno(bufs, clk_id, offs, seqno)
	self.used = true
	offs = offs and offs / 8 or 6 -- first 8-byte aligned value in UDP payload
	C.moongen_send_packet_with_clk_timestamp_seqno(self.id, self.qid, bufs.array[0], clk_id, offs, seqno)
end

--- Send a single timestamped packet (sequence number is not added or modified)
-- @param bufs bufArray, only the first packet in it will be sent
-- @param offs offset in the packet at which the timestamp will be written. will be aligned to a uint64_t
-- @param clk_id clk_id, clock used to get timestamp (REALTIME, MONOTONIC etc.).

function txQueue:sendWithClkTimestamp(bufs, clk_id, offs)
	self.used = true
	offs = offs and offs / 8 or 6 -- first 8-byte aligned value in UDP payload
	C.moongen_send_packet_with_clk_timestamp(self.id, self.qid, bufs.array[0], clk_id, offs)
end


function txQueue:sendWithHwTimestampSeqno(bufs, offs, tx_high, tx_low, seqno)
	self.used = true
	offs = offs and offs / 8 or 6 -- first 8-byte aligned value in UDP payload
	C.moongen_send_packet_with_hw_timestamp_seqno(self.id, self.qid, bufs.array[0], offs, tx_high, tx_low, seqno)
end

function pkt:getSoftwareTxTimestamp(offs)
	local offs = offs and offs / 8 or 6 -- default from sendWithTimestamp
	return uint64Ptr(self:getData())[offs]
end

function splitTimestamp(timestamp)
	local ts = C.split_uint64_timestamp(timestamp)
	return ts.tv_sec, ts.tv_nsec
end
