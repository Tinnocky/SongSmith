import subprocess
import sys
import time
from pathlib import Path


def main():
    print("Starting SongSmith...")

    # start server in background
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "server.main:app"],
        cwd=Path(__file__).parent
    )

    # wait for server to start
    time.sleep(2)

    # start client
    subprocess.run(
        [sys.executable, "Client/main.py"],
        cwd=Path(__file__).parent
    )

    # when client closes, shut down server
    server.terminate()
    print("SongSmith closed.")


if __name__ == "__main__":
    main()
