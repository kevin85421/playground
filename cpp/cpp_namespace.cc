#include <iostream>

namespace A {
    void hello() {
        std::cout << "Hello from A\n";
    }
}

namespace B {
    void hello() {
        std::cout << "Hello from B\n";
    }
}

void hello() {
    std::cout << "Hello from global\n";
}

int main() {
    A::hello();  // 輸出: Hello from A
    B::hello();  // 輸出: Hello from B
    ::hello();  // 輸出: Hello from global
}
