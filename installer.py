import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

FLUIDSYNTH_URL = "https://github.com/FluidSynth/fluidsynth/releases/download/v2.3.4/fluidsynth-2.3.4-win10-x64.zip"
FLUIDSYNTH_DIR = Path("C:/Program Files/fluidsynth")  # fluidsynth will live here


def install_requirements():
    """install all libraries in the requirements.txt file"""
    print("Installing Python dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
    print("Done.")


def install_fluidsynth():
    """install fluidsynth from the FLUIDSYNTH_URL and put it in the FLUIDSYNTH_DIR"""
    if FLUIDSYNTH_DIR.exists():
        print("FluidSynth already installed, skipping.")
        return

    print("Downloading FluidSynth...")
    zip_path = Path("fluidsynth.zip")
    urllib.request.urlretrieve(FLUIDSYNTH_URL, zip_path)

    print("Extracting FluidSynth...")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(FLUIDSYNTH_DIR)
    zip_path.unlink()

    print("Adding FluidSynth to PATH...")
    subprocess.run(f'setx PATH "%PATH%;{FLUIDSYNTH_DIR / "bin"}"', shell=True, check=True)
    print("Done.")


def main():
    print("SongSmith Installer")
    print("===================")
    install_requirements()
    install_fluidsynth()
    print("===================")
    print("Installation complete! Run 'python run.py' to start SongSmith.")


if __name__ == "__main__":
    main()
