------------------------------------------------------------------------
--- @file gtp.lua
--- @brief (gtp) utility.
--- Utility functions for the gtp_header structs 
--- Includes:
--- - gtp constants
--- - gtp header utility
--- - Definition of gtp packets
------------------------------------------------------------------------

--[[
-- Use this file as template when implementing a new gtpcol (to implement all mandatory stuff)
-- Replace all occurrences of gtp with your gtpcol (e.g. sctp)
-- Remove unnecessary comments in this file (comments inbetween [[...]]
-- Necessary changes to other files:
-- - packet.lua: if the header has a length member, adapt packetSetLength; 
-- 				 if the packet has a checksum, adapt createStack (loop at end of function) and packetCalculateChecksums
-- - gtp/gtp.lua: add gtp.lua to the list so it gets loaded
--]]
local ffi = require "ffi"

require "utils"
require "proto.template"
local initHeader = initHeader

local ntoh, hton = ntoh, hton
local ntoh16, hton16 = ntoh16, hton16
local bswap = bit.bswap


---------------------------------------------------------------------------
---- GTP constants
---------------------------------------------------------------------------

--- GTP gtpcol constants
local gtp = {}


---------------------------------------------------------------------------
---- GTP header
---------------------------------------------------------------------------
-- TODO: Extension header is not well catched
gtp.headerFormat = [[
	uint8_t flags;
	uint8_t message;
	uint16_t length;
	uint32_t teid;
	uint8_t empty;
	uint16_t padding;
	uint8_t NextExtHeaderLen;
	uint32_t ExtHeader;
]]

--- Variable sized member
gtp.headerVariableMember = nil

--- Module for gtp_address struct
local gtpHeader = initHeader()
gtpHeader.__index = gtpHeader

--[[ for all members of the header with non-standard data type: set, get, getString 
-- for set also specify a suitable default value
--]]
----- Set the XYZ.
----- @param int XYZ of the gtp header as A bit integer.
--function gtpHeader:setXYZ(int)
--	int = int or 0
--end

--- Retrieve flags.
--- @return Length as 8 bit integer.
function gtpHeader:getFlags()
	return bswap(self.flags)
end

--- Retrieve message.
--- @return Message as 8 bit integer.
function gtpHeader:getMessage()
	return bswap(self.message)
end

--- Retrieve the length of the GTP payload.
--- @return Length as 16 bit integer.
function gtpHeader:getLength()
	return ntoh16(self.length)
end


--- Retrieve the Tunnel Endpoint Identifier (TEID).
--- @return TEID as 32 bit integer.
function gtpHeader:getTEID()
	return ntoh(self.teid)
end


--- Set all members of the gtp header.
--- Per default, all members are set to default values specified in the respective set function.
--- Optional named arguments can be used to set a member to a user-provided value.
--- @param args Table of named arguments. Available arguments: gtpXYZ
--- @param pre prefix for namedArgs. Default 'gtp'.
--- @code
--- fill() -- only default values
--- fill{ gtpXYZ=1 } -- all members are set to default values with the exception of gtpXYZ, ...
--- @endcode
--function gtpHeader:fill(args, pre)
--	args = args or {}
--	pre = pre or "gtp"
--
--	self:setXYZ(args[pre .. "gtpXYZ"])
--end

--- Retrieve the values of all members.
--- @param pre prefix for namedArgs. Default 'gtp'.
--- @return Table of named arguments. For a list of arguments see "See also".
--- @see gtpHeader:fill
function gtpHeader:get(pre)
	pre = pre or "gtp"

	local args = {}
	args[pre .. "Flags"] = self:getFlags()
	args[pre .. "Message"] = self:getMessage()
	args[pre .. "Length"] = self:getLength()
	args[pre .. "TEID"] = self:getTEID()

	return args
end

--- Retrieve the values of all members.
--- @return Values in string format.
function gtpHeader:getString()
	local retStr = "GTP "
	retStr = retStr .. "Flags " .. self:getFlags()
	retStr = retStr .. "Message " .. self:getMessage()
	retStr = retStr .. "Length" .. self:getLength()
	retStr = retStr .. "TEID " .. self:getTEID()

	return retStr
end

----- Resolve which header comes after this one (in a packet)
----- For instance: in tcp/udp based on the ports
----- This function must exist and is only used when get/dump is executed on
----- an unknown (mbuf not yet casted to e.g. tcpv6 packet) packet (mbuf)
----- @return String next header (e.g. 'eth', 'ip4', nil)
--function gtpHeader:resolveNextHeader()
--	local proto = self:getNextHeader()
--	for name, _proto in pairs(mapNameProto) do
--		if proto == _proto then
--			return name
--		end
--	end
--	return nil
--end

--- Change the default values for namedArguments (for fill/get)
--- This can be used to for instance calculate a length value based on the total packet length
--- See gtp/ip4.setDefaultNamedArgs as an example
--- This function must exist and is only used by packet.fill
--- @param pre The prefix used for the namedArgs, e.g. 'gtp'
--- @param namedArgs Table of named arguments (see See more)
--- @param nextHeader The header following after this header in a packet
--- @param accumulatedLength The so far accumulated length for previous headers in a packet
--- @return Table of namedArgs
--- @see gtpHeader:fill
function gtpHeader:setDefaultNamedArgs(pre, namedArgs, nextHeader, accumulatedLength)
	return namedArgs
end


------------------------------------------------------------------------
---- Metatypes
------------------------------------------------------------------------

gtp.metatype = gtpHeader


return gtp
