#include <memory>

int main() {
    // 建立一個 unique_ptr 管理一個 new 出來的 int
    std::unique_ptr<int> ptr(new int(42));

    // 釋放 unique_ptr 的管理，但不刪除記憶體
    int* raw_ptr = ptr.release();

    // 此時 raw_ptr 指向的記憶體不再被任何智能指標管理，
    // 如果不手動 delete，就會造成記憶體洩漏
    // delete raw_ptr;  // 正確做法：在適當時機釋放記憶體

    return 0;
}
