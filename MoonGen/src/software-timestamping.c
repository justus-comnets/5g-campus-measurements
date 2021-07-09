#include <stdint.h>

#include <rte_config.h>
#include <rte_ethdev.h> 
#include <rte_mempool.h>
#include <rte_mbuf.h>
#include <rte_cycles.h>

#include "rdtsc.h"
#include "lifecycle.h"
#include "time.h"
#include <netinet/in.h>

//https://man7.org/linux/man-pages/man2/clock_gettime.2.html
/*
#define CLOCKFD 3
#define FD_TO_CLOCKID(fd)   ((~(clockid_t) (fd) << 3) | CLOCKFD)
#define CLOCKID_TO_FD(clk)  ((unsigned int) ~((clk) >> 3))

struct timeval tv;
clockid_t clkid;
int fd;

fd = open("/dev/ptp0", O_RDWR);
clkid = FD_TO_CLOCKID(fd);
clock_gettime(clkid, &tv);
*/



// software timestamping
void moongen_send_packet_with_timestamp(uint8_t port_id, uint16_t queue_id, struct rte_mbuf* pkt, uint16_t offs) {
	while (is_running(0)) {
		rte_pktmbuf_mtod_offset(pkt, uint64_t*, 0)[offs] = read_rdtsc();
		if (rte_eth_tx_burst(port_id, queue_id, &pkt, 1) == 1) {
			return;
		}
	}
}

void moongen_send_packet_with_timestamp_seqno(uint8_t port_id, uint16_t queue_id, struct rte_mbuf* pkt, uint16_t offs, uint64_t seqno) {
	struct timespec ts;
	while (is_running(0)) {
	    clock_gettime(CLOCK_REALTIME, &ts);
        rte_pktmbuf_mtod_offset(pkt, time_t*, 2)[offs] = htobe64(ts.tv_sec);
        rte_pktmbuf_mtod_offset(pkt, uint64_t*, 10)[offs] = htobe64(ts.tv_nsec);
		rte_pktmbuf_mtod_offset(pkt, uint64_t*, 18)[offs] = htobe64(seqno);
		if (rte_eth_tx_burst(port_id, queue_id, &pkt, 1) == 1) {
			return;
		}
	}
}

