import subprocess

for _ in range(50):
    subprocess.run(["./sort", "numbers.txt"], stdout=subprocess.DEVNULL)
