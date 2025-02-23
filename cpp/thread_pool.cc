#include <boost/asio.hpp>
#include <iostream>

int main() {
    // 從環境變數讀取線程池大小，默認為系統線程數
    const char* thread_count_str = std::getenv("THREAD_POOL_SIZE");
    unsigned int thread_count = thread_count_str ? 
        std::stoul(thread_count_str) : 
        std::thread::hardware_concurrency();
    std::cout << "Thread pool size: " << thread_count << std::endl;
    
    // 建立指定大小的 thread_pool
    boost::asio::thread_pool pool(thread_count);

    // 向 thread_pool 中提交一個簡單的任務
    boost::asio::post(pool, [](){
        std::cout << "This task will be executed because there are threads in the thread pool." << std::endl;
    });

    // 等待所有線程完成工作（由於沒有線程，join() 會立即返回）
    pool.join();

    std::cout << "Program execution finished." << std::endl;
    return 0;
}
