import subprocess
for _ in range(500):
    subprocess.run([
        "./curl", "-s",
        "data:text/plain;base64,aGVsbG8gd29ybGQK"
    ], stdout=subprocess.DEVNULL)
