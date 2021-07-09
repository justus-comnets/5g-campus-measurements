#include <cstdint>
#include <string>
#include <cstring>
#include <unordered_map>
#include <tuple>
#include <mutex>
#include <iostream>
#include <atomic>

static std::unordered_map<uint64_t, std::string> results;
static std::mutex results_mutex;
static std::atomic<uint64_t> task_id_ctr(1);

extern "C" {

uint64_t task_generate_id() {
	return task_id_ctr.fetch_add(1);
}

void task_store_result(uint64_t task_id, char* result) {
	std::lock_guard<std::mutex> lock(results_mutex);
	results.emplace(task_id, result);
}

char* task_get_result(uint64_t task_id) {
	std::lock_guard<std::mutex> lock(results_mutex);
	auto result = results.find(task_id);
	if (result != results.end()) {
		auto string = result->second;
		char* buf = (char*) malloc(string.length() + 1);
		std::strcpy(buf, string.c_str());
		results.erase(task_id);
		return buf;
	}
	return nullptr;
}

}
