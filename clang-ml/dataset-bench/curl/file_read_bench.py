import subprocess
import os

url = f"file://{os.getcwd()}/test.txt"
for _ in range(1000):
    subprocess.run(["./curl", "-s", url], stdout=subprocess.DEVNULL)
