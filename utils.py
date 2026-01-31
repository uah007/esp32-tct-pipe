import subprocess

def kill_chrome_process(pid):
    try:
        subprocess.run(f"taskkill /F /PID {pid}", shell=True, check=True)
    except subprocess.CalledProcessError:
        pass

def check_if_chrome_is_running(profile_dir):
    try:
        result = subprocess.check_output(
            f'tasklist /FI "IMAGENAME eq chrome.exe" /FI "WINDOWTITLE eq {profile_dir}"',
            shell=True,
            text=True
        )
        return "chrome.exe" in result
    except subprocess.CalledProcessError:
        return False
