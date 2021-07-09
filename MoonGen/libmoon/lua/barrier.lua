--- Barriers to synchronize execution of different tasks
local mod = {}

local ffi = require "ffi"


ffi.cdef [[
    struct barrier { };
    struct barrier* make_barrier(size_t n);
    void barrier_wait(struct barrier* barrier);
	void barrier_reinit(struct barrier* barrier, size_t n);
]]

local C = ffi.C

local barrier = {}
barrier.__index = barrier

--- @param n number of tasks
function mod:new(n)
    return C.make_barrier(n)
end

function barrier:wait()
    C.barrier_wait(self)
end

--- Can only be called if no tasks are waiting, i.e., after wait() returned
--- @param n number of tasks
function barrier:reinit(n)
    C.barrier_reinit(self, n)
end

ffi.metatype("struct barrier", barrier)

return mod
