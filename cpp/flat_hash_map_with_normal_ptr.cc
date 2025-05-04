#include <iostream>
#include <absl/container/flat_hash_map.h>

int main() {
    absl::flat_hash_map<int, std::string> map;
    // 插入一些元素
    for (int i = 0; i < 10; ++i) {
        map[i] = "value" + std::to_string(i);
    }

    // 記錄 key=0 的 value address
    auto it = map.find(0);
    std::string* old_addr = &(it->second);
    std::cout << "Before rehash, address: " << old_addr << std::endl;
    // 強制 rehash，讓 map 擴容
    map.rehash(100);

    // 重新尋找 key=0 的 value address
    it = map.find(0);


    // Update the value that old_addr points to
    *old_addr = "updated value";
    std::cout << "Updated value at old address: " << *old_addr << std::endl;

    std::string* new_addr = &(it->second);
    std::cout << "After rehash, address:  " << new_addr << std::endl;
    std::cout << "Value from new address: " << *new_addr << std::endl;

    assert(old_addr != new_addr);
    assert(*old_addr != *new_addr);

    std::cout << "Address changed after rehash!" << std::endl;
    std::cout << "The value at the old address updated after rehash doesn't affect the value at the new address." << std::endl;
}
