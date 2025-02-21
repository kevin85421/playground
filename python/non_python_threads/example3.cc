#include <Python.h>
#include <boost/asio/thread_pool.hpp>
#include <boost/asio/post.hpp>
#include <stdio.h>
#include <unistd.h>
#include <string>
#include <chrono>
#include <iomanip>
#include <sstream>

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

// 長時間運行的線程函數
PyGILState_STATE init_python_thread(std::string pool_name) {
    // 確保當前線程獲得 GIL
    PyGILState_STATE gstate = PyGILState_Ensure();
    printf("[C++][%s] Hello from the %s in init_python_thread\n", 
           get_current_time().c_str(), pool_name.c_str());
    std::string py_code = "thread_local.name = '" + pool_name + "'\n"
                         "print(f'Hello from {thread_local.name}!')";
    PyRun_SimpleString(py_code.c_str());

    // 不在這裡釋放 GIL，而是回傳 gstate
    return gstate;
}

void release_gstate(PyGILState_STATE gstate, std::string pool_name) {
    printf("[C++][%s] Hello from the %s in release_gstate\n", 
           get_current_time().c_str(), pool_name.c_str());
    PyRun_SimpleString("print(f'Hello from {thread_local.name} in release_gstate!')");

    // 釋放 GIL
    PyGILState_Release(gstate);
}

int main(int argc, char *argv[]) {
    // 初始化 Python 解釋器
    Py_Initialize();
    PyRun_SimpleString("import threading; thread_local = threading.local()");

    // 釋放 GIL，允許其他線程運行
    PyThreadState *_save = PyEval_SaveThread();

    boost::asio::thread_pool default_pool(1);
    boost::asio::thread_pool custom_pool(1);

    PyGILState_STATE default_gstate;
    PyGILState_STATE custom_gstate;
    boost::asio::post(default_pool, [&default_gstate]() {
        default_gstate = init_python_thread("default_pool");
    });

    boost::asio::post(custom_pool, [&custom_gstate]() {
        // 此 thread 會先執行 init_python_thread，直到 C++ log 印出，但是 Python log 並不會印出
        // 直到 default_pool 呼叫 release_gstate 後，GIL 被釋放，Python log 才會印出。
        custom_gstate = init_python_thread("custom_pool");
    });

    // 等待 10 秒，custom_pool 應該要在 sleep 10 秒結束前就執行完 init_python_thread
    // 確認不需要等到 default_pool 呼叫 release_gstate 後，custom_pool 才會執行。
    printf("[C++][%s] Sleep 10 seconds\n", get_current_time().c_str());
    sleep(10);

    boost::asio::post(default_pool, [&default_gstate]() {
        release_gstate(default_gstate, "default_pool");
    });

    boost::asio::post(custom_pool, [&custom_gstate]() {
        release_gstate(custom_gstate, "custom_pool");
    });

    // Release 後 py-spy 就看不到該 Python threads
    printf("[C++][%s] Sleep 60 seconds\n", get_current_time().c_str());
    sleep(60);

    default_pool.join();
    custom_pool.join();

    PyEval_RestoreThread(_save);
    Py_Finalize();
    return 0;
}
