#include <boost/asio/thread_pool.hpp>
#include <boost/asio/post.hpp>
#include <iostream>
#include <chrono>
#include <thread>
#include <ctime>
#include <iomanip>

// 取得目前時間字串 (格式：HH:MM:SS)
std::string current_time() {
    auto now = std::chrono::system_clock::now();
    std::time_t now_time = std::chrono::system_clock::to_time_t(now);
    std::tm* ptm = std::localtime(&now_time);
    char buffer[32];
    std::strftime(buffer, sizeof(buffer), "%H:%M:%S", ptm);
    return std::string(buffer);
}

void task(int id) {
    std::cout << "[" << current_time() << "] Task " << id << " started." << std::endl;
    // 模擬任務執行 3 秒
    std::this_thread::sleep_for(std::chrono::seconds(3));
    std::cout << "[" << current_time() << "] Task " << id << " finished." << std::endl;
}

int main() {
    // 建立一個有 2 個工作線程的 thread_pool
    boost::asio::thread_pool pool(2);

    // 提交 5 個任務
    for (int i = 0; i < 5; ++i) {
        boost::asio::post(pool, [i] { task(i); });
    }

    // 稍微等待一下，確保部分任務已開始執行
    std::this_thread::sleep_for(std::chrono::seconds(1));
    std::cout << "[" << current_time() << "] Calling pool.stop()..." << std::endl;
    
    // 呼叫 stop()：僅停止尚未開始的任務，已開始的任務仍會完成
    pool.stop();

    // 等待所有執行中的任務完成並關閉線程池
    pool.join();
    std::cout << "[" << current_time() << "] Thread pool terminated." << std::endl;

    return 0;
}
