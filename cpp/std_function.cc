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

// outerFunction 是一個 function 回傳一個 void function，
std::function<std::function<void()>()> outerFunction = []() -> std::function<void()> {
    return []() {
        std::cout << "Hello, World!" << std::endl;
    };
};

int main() {
    auto add = getAdditionFunction();
    std::cout << "3 + 4 = " << add(3, 4) << std::endl; // 7

    auto echo = getEchoFunction();
    std::cout << "echo(1) = " << echo(1) << std::endl; // 1

    std::function<void()> innerFunction = outerFunction();
    innerFunction();

    return 0;
}
