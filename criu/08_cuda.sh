#!/usr/bin/env bash
# 08 — GPU processes: cuda-checkpoint moves GPU state into host memory, then
# CRIU can dump the (now CPU-only) process. On restore we also move the
# process to a DIFFERENT GPU with --device-map.
source "$(dirname "$0")/common.sh"
init 08_cuda
CLEANUP_PATTERNS=("./gpu_counter")
command -v cuda-checkpoint >/dev/null || { echo "cuda-checkpoint not installed"; exit 1; }

cat > gpu_counter.cu <<'EOF'
#include <cstdio>
#include <unistd.h>
// The counter lives in GPU memory; only the kernel changes it.
__global__ void inc(int *c) { (*c)++; }
int main() {
  int *d, h = 0, dev;
  cudaMalloc(&d, sizeof(int)); cudaMemset(d, 0, sizeof(int));
  for (;;) {
    inc<<<1, 1>>>(d);
    cudaMemcpy(&h, d, sizeof(int), cudaMemcpyDeviceToHost);
    cudaGetDevice(&dev);
    char bus[32]; cudaDeviceGetPCIBusId(bus, sizeof bus, dev);
    printf("gpu counter=%d  (running on PCI %s)\n", h, bus); fflush(stdout);
    sleep(1);
  }
}
EOF
run "nvcc -o gpu_counter gpu_counter.cu 2>&1 | grep -v warning || true"

setsid ./gpu_counter > out.log 2>&1 < /dev/null &
PID=$(wait_pid "./gpu_counter")
sleep 3
run "tail -n 1 out.log"
run "nvidia-smi --query-compute-apps=pid,gpu_bus_id,used_memory --format=csv"

step "cuda-checkpoint, step by step (--toggle does lock+checkpoint or restore+unlock in one go)"
run "cuda-checkpoint --get-state --pid $PID"
note "lock: wait for in-flight CUDA work to finish and block new CUDA API calls"
run "cuda-checkpoint --action lock --pid $PID"
run "cuda-checkpoint --get-state --pid $PID"
note "checkpoint: copy device memory to host memory and release the GPU"
run "cuda-checkpoint --action checkpoint --pid $PID"
run "cuda-checkpoint --get-state --pid $PID"
run "nvidia-smi --query-compute-apps=pid,gpu_bus_id,used_memory --format=csv"
note "the process no longer holds any GPU: to CRIU it is an ordinary CPU process now"

step "CRIU dump and restore, exactly as for a CPU process"
mkdir img
run "criu dump -t $PID -D img -o dump.log"
run "du -sh img"
run "criu restore -D img -d -o restore.log"
run "cuda-checkpoint --get-state --pid $PID"
note "after criu restore the process is back, but its CUDA state is still 'checkpointed'"

step "Restore CUDA state onto ANOTHER GPU: swap GPU 0 and GPU 1"
mapfile -t UUIDS < <(nvidia-smi --query-gpu=uuid --format=csv,noheader)
MAP="${UUIDS[0]}=${UUIDS[1]},${UUIDS[1]}=${UUIDS[0]}"
for u in "${UUIDS[@]:2}"; do MAP+=",$u=$u"; done
note "the map must cover every GPU the process can see, so the other GPUs map to themselves"
run "cuda-checkpoint --action restore --pid $PID --device-map '$MAP'"
run "cuda-checkpoint --action unlock --pid $PID"
run "cuda-checkpoint --get-state --pid $PID"
sleep 3
run "tail -n 4 out.log"
run "nvidia-smi --query-compute-apps=pid,gpu_bus_id,used_memory --format=csv"
note "the counter continued from GPU memory. nvidia-smi shows a different physical GPU,"
note "but the program still prints the OLD bus id: the remap is invisible to the process,"
note "which still thinks it is on 'device 0' as it was before the checkpoint"
