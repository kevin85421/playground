#include <Python.h>
#include <boost/asio/thread_pool.hpp>
#include <boost/asio/post.hpp>
#include <stdio.h>
#include <unistd.h>

// 長時間運行的線程函數
PyGILState_STATE init_python_thread() {
    // 確保當前線程獲得 GIL
    PyGILState_STATE gstate = PyGILState_Ensure();
    PyRun_SimpleString("print('Hello from the init_python_thread!')");

    // 不在這裡釋放 GIL，而是回傳 gstate
    return gstate;
}

void release_gstate(PyGILState_STATE gstate) {
    PyRun_SimpleString("print('Hello from the release_gstate!')");
    PyGILState_Release(gstate);
}

int main(int argc, char *argv[]) {
    // 初始化 Python 解釋器
    Py_Initialize();

    // 釋放 GIL，允許其他線程運行
    PyThreadState *_save = PyEval_SaveThread();

    boost::asio::thread_pool pool(1);

    PyGILState_STATE gstate;
    boost::asio::post(pool, [&gstate]() {
        gstate = init_python_thread();
    });

    // 等待 60 秒，此時用 py-spy 查看，應該還是要有兩個 Python threads
    printf("Sleep 60 seconds\n");
    sleep(60);

    boost::asio::post(pool, [&gstate]() {
        release_gstate(gstate);
    });

    pool.join();

    PyEval_RestoreThread(_save);
    Py_Finalize();
    return 0;
}
