#include <iostream>
#include <memory>
#include <absl/container/flat_hash_map.h>

int main() {
    // 使用 shared_ptr 存儲字符串
    absl::flat_hash_map<int, std::shared_ptr<std::string>> map;
    
    // 插入一些元素
    for (int i = 0; i < 10; ++i) {
        map[i] = std::make_shared<std::string>("value" + std::to_string(i));
    }

    // 記錄 key=0 的 value 的 shared_ptr
    auto it = map.find(0);
    std::shared_ptr<std::string> old_ptr = it->second;
    std::cout << "Before rehash, value: " << *old_ptr << std::endl;
    std::cout << "Before rehash, address: " << old_ptr.get() << std::endl;
    std::cout << "Before rehash, use count: " << old_ptr.use_count() << std::endl;
    
    // 強制 rehash，讓 map 擴容
    map.rehash(100);

    // 重新尋找 key=0 的 value
    it = map.find(0);
    std::shared_ptr<std::string> new_ptr = it->second;
    std::cout << "After rehash, value: " << *new_ptr << std::endl;
    std::cout << "After rehash, address: " << new_ptr.get() << std::endl;
    std::cout << "After rehash, use count: " << new_ptr.use_count() << std::endl;

    // 更新透過舊指標的值
    *old_ptr = "updated value";
    std::cout << "\nAfter updating via old_ptr:" << std::endl;
    std::cout << "Value via old_ptr: " << *old_ptr << std::endl;
    std::cout << "Value via new_ptr: " << *new_ptr << std::endl;
    std::cout << "Value via map[0]: " << *map[0] << std::endl;

    // 證明 old_ptr 和 new_ptr 指向同一對象
    if (old_ptr.get() == new_ptr.get()) {
        std::cout << "\nSame object! Both pointers refer to the same memory." << std::endl;
    } else {
        std::cout << "\nDifferent objects! The pointers refer to different memory locations." << std::endl;
    }
    
    return 0;
} 