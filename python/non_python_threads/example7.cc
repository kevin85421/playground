#include <Python.h>
#include <stdio.h>
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

int main(int argc, char *argv[]) {
    // Initialize Python interpreter
    Py_Initialize();

    printf("[C++][%s] Before PyGILState_Ensure()\n", get_current_time().c_str());
    
    // Ensure GIL
    PyGILState_STATE gstate = PyGILState_Ensure();

    // Run some Python code
    std::string py_code = 
        "print(f'[Python] Hello from main thread!')";
    PyRun_SimpleString(py_code.c_str());

    printf("[C++][%s] Before PyGILState_Release()\n", get_current_time().c_str());
    
    // Release GIL
    PyGILState_Release(gstate);

    printf("[C++][%s] After PyGILState_Release()\n", get_current_time().c_str());

    // Second PyGILState_Release() will cause segfault.
    printf("[C++][%s] Before PyGILState_Release()\n", get_current_time().c_str());
    PyGILState_Release(gstate);
    printf("[C++][%s] After PyGILState_Release()\n", get_current_time().c_str());

    Py_Finalize();
    return 0;
}
