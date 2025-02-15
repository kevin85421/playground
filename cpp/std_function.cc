#include <functional>
#include <iostream>

// 回傳一個可呼叫對象，該對象接受兩個 int 並返回 int
std::function<int(int, int)> getAdditionFunction() {
    return [](int a, int b) -> int {
        return a + b;
    };
}

std::function<int(int)> getEchoFunction() {
    return [](int a) -> int {
        return a;
    };
}

int main() {
    auto add = getAdditionFunction();
    std::cout << "3 + 4 = " << add(3, 4) << std::endl; // 7

    auto echo = getEchoFunction();
    std::cout << "echo(1) = " << echo(1) << std::endl; // 1

    return 0;
}
