cmd_cxgbe_ethdev.o = gcc -Wp,-MD,./.cxgbe_ethdev.o.d.tmp  -m64 -pthread  -march=native -DRTE_MACHINE_CPUFLAG_SSE -DRTE_MACHINE_CPUFLAG_SSE2 -DRTE_MACHINE_CPUFLAG_SSE3 -DRTE_MACHINE_CPUFLAG_SSSE3 -DRTE_MACHINE_CPUFLAG_SSE4_1 -DRTE_MACHINE_CPUFLAG_SSE4_2 -DRTE_MACHINE_CPUFLAG_AES -DRTE_MACHINE_CPUFLAG_PCLMULQDQ -DRTE_MACHINE_CPUFLAG_AVX -DRTE_MACHINE_CPUFLAG_RDRAND -DRTE_MACHINE_CPUFLAG_FSGSBASE -DRTE_MACHINE_CPUFLAG_F16C -DRTE_MACHINE_CPUFLAG_AVX2  -I/home/justus/work/porsche/porsche/RTPanalyzer/MoonGen/libmoon/deps/dpdk/mybuild/include -include /home/justus/work/porsche/porsche/RTPanalyzer/MoonGen/libmoon/deps/dpdk/mybuild/include/rte_config.h -I/home/justus/work/porsche/porsche/RTPanalyzer/MoonGen/libmoon/deps/dpdk/drivers/net/cxgbe/base/ -I/home/justus/work/porsche/porsche/RTPanalyzer/MoonGen/libmoon/deps/dpdk/drivers/net/cxgbe -O3 -W -Wall -Wstrict-prototypes -Wmissing-prototypes -Wmissing-declarations -Wold-style-definition -Wpointer-arith -Wcast-align -Wnested-externs -Wcast-qual -Wformat-nonliteral -Wformat-security -Wundef -Wwrite-strings  -Wimplicit-fallthrough=0 -Wno-format-truncation -Wno-deprecated    -o cxgbe_ethdev.o -c /home/justus/work/porsche/porsche/RTPanalyzer/MoonGen/libmoon/deps/dpdk/drivers/net/cxgbe/cxgbe_ethdev.c 
