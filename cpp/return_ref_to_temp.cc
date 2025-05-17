#include <string>
#include <iostream>

// Return a reference to a temporary object
// Solution: `const std::string&` -> `const std::string`
const std::string& GetMessage() {
    return std::string("hello world");
}

int main() {
    const std::string& msg = GetMessage();
    std::cout << msg << std::endl;
    return 0;
}
