import subprocess

for _ in range(500):
    subprocess.run(["./head", "-n", "10", "large.txt"], stdout=subprocess.DEVNULL)
