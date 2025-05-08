#include <boost/thread/latch.hpp>
#include <boost/thread/thread.hpp>
#include <iostream>
#include <vector>
#include <functional>

void worker(boost::latch& completion_latch, int id) {
    // Simulate some work
    std::cout << "Worker " << id << " is doing some work..." << std::endl;
    
    // Sleep for a random amount of time (1-3 seconds)
    boost::this_thread::sleep_for(boost::chrono::milliseconds(1000 + (id * 500)));
    
    std::cout << "Worker " << id << " has completed its task." << std::endl;
    
    // Count down the latch when the work is done
    completion_latch.count_down();
}

int main() {
    const int num_workers = 5;
    
    // Create a latch with a count equal to the number of workers
    boost::latch completion_latch(num_workers);
    
    std::vector<boost::thread> threads;
    
    // Launch worker threads
    for (int i = 0; i < num_workers; ++i) {
        threads.emplace_back(worker, std::ref(completion_latch), i);
    }
    
    std::cout << "Main thread waiting for all workers to complete..." << std::endl;
    
    // Wait for all workers to complete their tasks
    completion_latch.wait();
    
    std::cout << "All workers have completed their tasks!" << std::endl;
    
    // Join all threads
    for (auto& thread : threads) {
        thread.join();
    }
    
    return 0;
}
