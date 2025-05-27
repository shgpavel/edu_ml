import subprocess

for _ in range(10000):
    subprocess.run(["./echo", "hello", "world"], stdout=subprocess.DEVNULL)
