obj/arch_specific.o: highwayhash/arch_specific.cc \
 highwayhash/arch_specific.h highwayhash/compiler_specific.h
obj/benchmark.o: highwayhash/benchmark.cc highwayhash/arch_specific.h \
 highwayhash/compiler_specific.h highwayhash/instruction_sets.h \
 highwayhash/nanobenchmark.h highwayhash/robust_statistics.h \
 highwayhash/highwayhash_test_target.h highwayhash/hh_types.h \
 highwayhash/highwayhash.h highwayhash/iaca.h highwayhash/hh_portable.h \
 highwayhash/endianess.h highwayhash/load3.h
obj/c_bindings.o: highwayhash/c_bindings.cc highwayhash/c_bindings.h \
 highwayhash/hh_types.h highwayhash/highwayhash_target.h \
 highwayhash/arch_specific.h highwayhash/compiler_specific.h \
 highwayhash/hh_types.h highwayhash/instruction_sets.h
obj/example.o: highwayhash/example.cc highwayhash/highwayhash.h \
 highwayhash/arch_specific.h highwayhash/compiler_specific.h \
 highwayhash/hh_types.h highwayhash/iaca.h highwayhash/hh_portable.h \
 highwayhash/endianess.h highwayhash/load3.h
obj/hh_avx2.o: highwayhash/hh_avx2.cc highwayhash/highwayhash_target.cc \
 highwayhash/highwayhash_target.h highwayhash/arch_specific.h \
 highwayhash/compiler_specific.h highwayhash/hh_types.h \
 highwayhash/highwayhash.h highwayhash/iaca.h highwayhash/hh_avx2.h \
 highwayhash/hh_buffer.h highwayhash/vector128.h highwayhash/load3.h \
 highwayhash/endianess.h highwayhash/vector256.h
obj/hh_portable.o: highwayhash/hh_portable.cc \
 highwayhash/highwayhash_target.cc highwayhash/highwayhash_target.h \
 highwayhash/arch_specific.h highwayhash/compiler_specific.h \
 highwayhash/hh_types.h highwayhash/highwayhash.h highwayhash/iaca.h \
 highwayhash/hh_portable.h highwayhash/endianess.h highwayhash/load3.h
obj/hh_sse41.o: highwayhash/hh_sse41.cc highwayhash/highwayhash_target.cc \
 highwayhash/highwayhash_target.h highwayhash/arch_specific.h \
 highwayhash/compiler_specific.h highwayhash/hh_types.h \
 highwayhash/highwayhash.h highwayhash/iaca.h highwayhash/hh_sse41.h \
 highwayhash/hh_buffer.h highwayhash/vector128.h highwayhash/load3.h \
 highwayhash/endianess.h
obj/hh_vsx.o: highwayhash/hh_vsx.cc
obj/highwayhash_test.o: highwayhash/highwayhash_test.cc \
 highwayhash/highwayhash_test_target.h highwayhash/arch_specific.h \
 highwayhash/compiler_specific.h highwayhash/hh_types.h \
 highwayhash/highwayhash.h highwayhash/iaca.h highwayhash/hh_portable.h \
 highwayhash/endianess.h highwayhash/load3.h highwayhash/nanobenchmark.h \
 highwayhash/data_parallel.h highwayhash/highwayhash_target.h \
 highwayhash/instruction_sets.h
obj/highwayhash_test_avx2.o: highwayhash/highwayhash_test_avx2.cc \
 highwayhash/highwayhash_test_target.cc \
 highwayhash/highwayhash_test_target.h highwayhash/arch_specific.h \
 highwayhash/compiler_specific.h highwayhash/hh_types.h \
 highwayhash/highwayhash.h highwayhash/iaca.h highwayhash/hh_avx2.h \
 highwayhash/hh_buffer.h highwayhash/vector128.h highwayhash/load3.h \
 highwayhash/endianess.h highwayhash/vector256.h \
 highwayhash/nanobenchmark.h
obj/highwayhash_test_portable.o: highwayhash/highwayhash_test_portable.cc \
 highwayhash/highwayhash_test_target.cc \
 highwayhash/highwayhash_test_target.h highwayhash/arch_specific.h \
 highwayhash/compiler_specific.h highwayhash/hh_types.h \
 highwayhash/highwayhash.h highwayhash/iaca.h highwayhash/hh_portable.h \
 highwayhash/endianess.h highwayhash/load3.h highwayhash/nanobenchmark.h
obj/highwayhash_test_sse41.o: highwayhash/highwayhash_test_sse41.cc \
 highwayhash/highwayhash_test_target.cc \
 highwayhash/highwayhash_test_target.h highwayhash/arch_specific.h \
 highwayhash/compiler_specific.h highwayhash/hh_types.h \
 highwayhash/highwayhash.h highwayhash/iaca.h highwayhash/hh_sse41.h \
 highwayhash/hh_buffer.h highwayhash/vector128.h highwayhash/load3.h \
 highwayhash/endianess.h highwayhash/nanobenchmark.h
obj/highwayhash_test_target.o: highwayhash/highwayhash_test_target.cc \
 highwayhash/highwayhash_test_target.h highwayhash/arch_specific.h \
 highwayhash/compiler_specific.h highwayhash/hh_types.h \
 highwayhash/highwayhash.h highwayhash/iaca.h highwayhash/hh_portable.h \
 highwayhash/endianess.h highwayhash/load3.h highwayhash/nanobenchmark.h
obj/highwayhash_test_vsx.o: highwayhash/highwayhash_test_vsx.cc
obj/instruction_sets.o: highwayhash/instruction_sets.cc \
 highwayhash/instruction_sets.h highwayhash/arch_specific.h \
 highwayhash/compiler_specific.h
obj/nanobenchmark.o: highwayhash/nanobenchmark.cc \
 highwayhash/nanobenchmark.h highwayhash/arch_specific.h \
 highwayhash/compiler_specific.h highwayhash/os_specific.h \
 highwayhash/robust_statistics.h highwayhash/tsc_timer.h
obj/nanobenchmark_example.o: highwayhash/nanobenchmark_example.cc \
 highwayhash/nanobenchmark.h highwayhash/arch_specific.h \
 highwayhash/compiler_specific.h highwayhash/os_specific.h
obj/os_specific.o: highwayhash/os_specific.cc highwayhash/os_specific.h \
 highwayhash/arch_specific.h highwayhash/compiler_specific.h
obj/profiler_example.o: highwayhash/profiler_example.cc \
 highwayhash/os_specific.h highwayhash/profiler.h \
 highwayhash/arch_specific.h highwayhash/compiler_specific.h \
 highwayhash/robust_statistics.h highwayhash/tsc_timer.h
obj/scalar_sip_tree_hash.o: highwayhash/scalar_sip_tree_hash.cc \
 highwayhash/scalar_sip_tree_hash.h highwayhash/state_helpers.h \
 highwayhash/compiler_specific.h highwayhash/sip_hash.h \
 highwayhash/arch_specific.h highwayhash/endianess.h
obj/sip_hash.o: highwayhash/sip_hash.cc highwayhash/sip_hash.h \
 highwayhash/arch_specific.h highwayhash/compiler_specific.h \
 highwayhash/endianess.h highwayhash/state_helpers.h
obj/sip_hash_test.o: highwayhash/sip_hash_test.cc highwayhash/sip_hash.h \
 highwayhash/arch_specific.h highwayhash/compiler_specific.h \
 highwayhash/endianess.h highwayhash/state_helpers.h \
 highwayhash/scalar_sip_tree_hash.h highwayhash/sip_tree_hash.h
obj/sip_tree_hash.o: highwayhash/sip_tree_hash.cc \
 highwayhash/sip_tree_hash.h highwayhash/state_helpers.h \
 highwayhash/compiler_specific.h highwayhash/arch_specific.h \
 highwayhash/sip_hash.h highwayhash/endianess.h
obj/vector_test.o: highwayhash/vector_test.cc \
 highwayhash/instruction_sets.h highwayhash/arch_specific.h \
 highwayhash/compiler_specific.h highwayhash/vector_test_target.h \
 highwayhash/hh_types.h
obj/vector_test_avx2.o: highwayhash/vector_test_avx2.cc \
 highwayhash/vector_test_target.cc highwayhash/vector_test_target.h \
 highwayhash/arch_specific.h highwayhash/compiler_specific.h \
 highwayhash/hh_types.h
obj/vector_test_portable.o: highwayhash/vector_test_portable.cc \
 highwayhash/vector_test_target.cc highwayhash/vector_test_target.h \
 highwayhash/arch_specific.h highwayhash/compiler_specific.h \
 highwayhash/hh_types.h
obj/vector_test_sse41.o: highwayhash/vector_test_sse41.cc \
 highwayhash/vector_test_target.cc highwayhash/vector_test_target.h \
 highwayhash/arch_specific.h highwayhash/compiler_specific.h \
 highwayhash/hh_types.h
obj/vector_test_target.o: highwayhash/vector_test_target.cc \
 highwayhash/vector_test_target.h highwayhash/arch_specific.h \
 highwayhash/compiler_specific.h highwayhash/hh_types.h
