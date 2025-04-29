// IoContextThreadPool: Using boost::asio::io_context as a task queue
// Coarse-grained task execution model

#include <boost/asio.hpp>
#include <vector>
#include <thread>
#include <functional>
#include <memory>
#include <iostream>

class IoContextThreadPool {
public:
    explicit IoContextThreadPool(std::size_t numThreads)
        : ioContext_(std::make_shared<boost::asio::io_context>()),
          workGuard_(boost::asio::make_work_guard(*ioContext_))
    {
        // Start threads that run the io_context event loop
        for (std::size_t i = 0; i < numThreads; ++i) {
            threads_.emplace_back([ctx = ioContext_] {
                ctx->run();
            });
        }
    }

    ~IoContextThreadPool() {
        // workGuard_ 是一個 executor_work_guard 物件，它的作用是防止 io_context 在沒有任務時自動結束
        // 當 io_context 中沒有任何待處理的任務時，io_context::run() 方法通常會立即返回
        // 但有了 work_guard，即使沒有任務，run() 也會繼續阻塞並等待新任務
        // 
        // Graceful shutdown: stop accepting new work and let run() return
        workGuard_.reset();     // 釋放 work guard，允許 io_context 在任務完成後自然退出
        ioContext_->stop();     // 強制停止 io_context，中斷所有待處理的任務

        // Join all threads
        for (auto &t : threads_) {
            if (t.joinable()) {
                t.join();
            }
        }
    }

    // Post a task into the io_context
    template<typename F>
    void post(F&& task) {
        boost::asio::post(*ioContext_, std::forward<F>(task));
    }

private:
    std::shared_ptr<boost::asio::io_context> ioContext_;
    boost::asio::executor_work_guard<boost::asio::io_context::executor_type> workGuard_;
    std::vector<std::thread> threads_;
};

// Example usage:
int main() {
    IoContextThreadPool pool(4);
    for (int i = 0; i < 100; ++i) {
        pool.post([i]{
            auto now = std::chrono::system_clock::now();
            auto now_time_t = std::chrono::system_clock::to_time_t(now);
            std::cout << "Timestamp: " << std::ctime(&now_time_t);
            std::cout << "Thread ID: " << std::this_thread::get_id() << " - ";
            std::cout << "Hello, World! " << i << std::endl;
            std::this_thread::sleep_for(std::chrono::seconds(1));
        });
    }
    // Pool destructor will wait for tasks to finish and threads to join
    // Wait for all tasks to complete
    std::cout << "Waiting for all tasks to complete..." << std::endl;
    std::this_thread::sleep_for(std::chrono::seconds(60));
    return 0;
}
