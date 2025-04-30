#include <boost/asio.hpp>
#include <iostream>

int main() {
    boost::asio::io_context io;

    // 創建 work_guard，阻止 io_context 自動停止
    auto work_guard = boost::asio::make_work_guard(io);

    std::thread t([&io]() {
        std::cout << "before io_context run\n";
        io.run();
        std::cout << "after io_context run\n";
    });

    // 主執行緒稍作延遲
    std::cout << "before sleep 5 seconds\n";
    std::this_thread::sleep_for(std::chrono::seconds(5));
    std::cout << "after sleep 5 seconds\n";

    // 只能在 work_guard.reset() 之後，`io.run()` 才會返回
    std::cout << "reset work_guard so that io_context.run() will return.\n";
    work_guard.reset();

    t.join();
    return 0;
}
