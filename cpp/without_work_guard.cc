#include <boost/asio.hpp>
#include <iostream>

int main() {
    boost::asio::io_context io;

    std::thread t([&io]() {
        std::cout << "before io_context run\n";
        io.run();
        std::cout << "after io_context run\n";
    });

    // 主執行緒稍作延遲
    std::cout << "before sleep 5 seconds\n";
    std::this_thread::sleep_for(std::chrono::seconds(5));
    std::cout << "after sleep 5 seconds\n";

    t.join();
    return 0;
}
