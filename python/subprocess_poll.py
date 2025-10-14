import subprocess
import time

# Start a long-running process
process = subprocess.Popen(['sleep', '5'])

# Check if the process is still running using poll()
while True:
    return_code = process.poll()
    
    if return_code is None:
        # Process is still running
        print("Process is still running...", time.ctime())
        time.sleep(1)
    else:
        # Process has finished
        print(f"Process has finished with return code: {return_code}", time.ctime())
        break
