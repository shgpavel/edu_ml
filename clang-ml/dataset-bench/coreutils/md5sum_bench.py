import subprocess

for _ in range(100):
    subprocess.run(["./md5sum", "medium.bin"], stdout=subprocess.DEVNULL)
