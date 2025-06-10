#include <iostream>

// Fix: 將 int& 改成 const int&
void foo(int& x) {
    std::cout << x << '\n';
}

int main() {
    foo(42);
    return 0;
}
