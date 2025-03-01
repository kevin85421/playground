#include <Python.h>
#include <boost/asio/thread_pool.hpp>
#include <boost/asio/post.hpp>
#include <stdio.h>
#include <unistd.h>
#include <string>
#include <chrono>
#include <iomanip>
#include <sstream>
#include <functional>
#include <vector>
#include <future>
#include <memory>

std::string get_current_time() {
    auto now = std::chrono::system_clock::now();
    auto now_time_t = std::chrono::system_clock::to_time_t(now);
    auto now_ms = std::chrono::duration_cast<std::chrono::milliseconds>(
        now.time_since_epoch()) % 1000;
    
    std::stringstream ss;
    ss << std::put_time(std::localtime(&now_time_t), "%H:%M:%S")
       << '.' << std::setfill('0') << std::setw(3) << now_ms.count();
    return ss.str();
}

std::function<void()> init_python_thread(std::string pool_name) {
    PyGILState_STATE gstate = PyGILState_Ensure();
    printf("[C++][%s] Hello from the %s in init_python_thread\n",
        get_current_time().c_str(), pool_name.c_str());

    std::string py_code =
                        "current_time = datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]\n"
                        "print(f'[Python][{current_time}] Hello from " + pool_name + "!')";
    PyRun_SimpleString(py_code.c_str());

    return [gstate]() {
        printf("[C++] PyGILState_Release()\n");
        PyGILState_Release(gstate);
    };
}

int main(int argc, char *argv[]) {
    Py_Initialize();
    PyRun_SimpleString("import datetime");
    PyThreadState *_save = PyEval_SaveThread();

    boost::asio::thread_pool default_pool(1);
    boost::asio::thread_pool custom_pool(1);

    auto default_callback = std::make_shared<std::function<void()>>();
    auto custom_callback = std::make_shared<std::function<void()>>();

    // PyGILState_Ensure()
    boost::asio::post(default_pool, [callback = default_callback]() {
        printf("[C++][%s] First post in default_pool\n", get_current_time().c_str());
        *callback = init_python_thread("default_pool");
    });

    boost::asio::post(custom_pool, [callback = custom_callback]() {
        printf("[C++][%s] First post in custom_pool\n", get_current_time().c_str());
        *callback = init_python_thread("custom_pool");
    });

    // PyGILState_Release()
    boost::asio::post(default_pool, [callback = default_callback]() {
        printf("[C++][%s] Second post in default_pool\n", get_current_time().c_str());
        if (*callback) (*callback)();
    });

    boost::asio::post(custom_pool, [callback = custom_callback]() {
        printf("[C++][%s] Second post in custom_pool\n", get_current_time().c_str());
        if (*callback) (*callback)();
    });

    default_pool.join();
    custom_pool.join();

    PyEval_RestoreThread(_save);
    Py_Finalize();
    return 0;
}
