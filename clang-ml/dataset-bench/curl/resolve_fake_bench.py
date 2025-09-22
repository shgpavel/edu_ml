import subprocess

for _ in range(100):
    subprocess.run(
        ["./curl", "-s", "--resolve", "fake.local:80:127.0.0.1", "http://fake.local"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
