#include <boost/asio/thread_pool.hpp>
#include <boost/asio/post.hpp>
#include <iostream>
#include <chrono>
#include <thread>
#include <boost/version.hpp>

void task(int id) {
    std::cout << "Task " << id << " started." << std::endl;
    std::this_thread::sleep_for(std::chrono::seconds(1));
    std::cout << "Task " << id << " finished." << std::endl;
}

int main() {
    std::cout << "Boost version: " << BOOST_VERSION << std::endl;
    // 建立一個有 2 個執行緒的 thread_pool
    boost::asio::thread_pool pool(2);
    boost::asio::thread_pool pool2(2);

    // 提交初始的任務
    std::cout << "[thread_pool.wait() example]" << std::endl;
    for (int i = 0; i < 3; ++i) {
        boost::asio::post(pool, [i] { task(i); });
    }

    std::cout << "Waiting for initial tasks to complete..." << std::endl;
    // wait() 等待初始任務完成
    pool.wait();
    std::cout << "Initial tasks completed." << std::endl;

    // 在第一次 wait() 後提交額外任務
    std::cout << "[thread_pool.join() example]" << std::endl;
    for (int i = 3; i < 6; ++i) {
        boost::asio::post(pool2, [i] { task(i); });
    }

    // 再次呼叫 wait() 等待新提交的任務完成
    std::cout << "Waiting for additional tasks to complete..." << std::endl;
    pool2.join();
    std::cout << "Additional tasks completed." << std::endl;

    return 0;
}
