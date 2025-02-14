#include <Python.h>
#include <pthread.h>
#include <stdio.h>
#include <unistd.h>

// 長時間運行的線程函數
void* py_long_running_thread(void* arg) {
    // 確保當前線程獲得 GIL
    PyGILState_STATE gstate = PyGILState_Ensure();

    // 這個線程會持續運行，每隔 5 秒執行一次 Python 指令
    while (1) {
        // 例如，使用 PyRun_SimpleString 呼叫 Python 代碼
        PyRun_SimpleString("print('Hello from the long running python thread!')");
        sleep(5);
    }

    // 如果跳出循環（實際上這裡不會到達），釋放 GIL
    PyGILState_Release(gstate);
    return NULL;
}

void* cpp_long_running_thread(void* arg) {
    while (1) {
        printf("Hello from the long running cpp thread!\n");
        sleep(5);
    }
    return NULL;
}

int main(int argc, char *argv[]) {
    // 初始化 Python 解釋器
    Py_Initialize();

    // 釋放 GIL，允許其他線程運行
    PyThreadState *_save = PyEval_SaveThread();

    pthread_t py_thread;
    if (pthread_create(&py_thread, NULL, py_long_running_thread, NULL) != 0) {
        fprintf(stderr, "Error creating thread\n");
        return 1;
    }

    pthread_t cpp_thread;
    if (pthread_create(&cpp_thread, NULL, cpp_long_running_thread, NULL) != 0) {
        fprintf(stderr, "Error creating thread2\n");
        return 1;
    }

    pthread_join(py_thread, NULL);
    pthread_join(cpp_thread, NULL);

    // 如果沒有 RestoreThread 就呼叫 Finalize 會造成 segfault
    PyEval_RestoreThread(_save);
    // 結束前清理 Python 解釋器（通常不會執行到這裡）
    Py_Finalize();
    return 0;
}

