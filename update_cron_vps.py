import pty
import os

def run_cmd(cmd, password):
    pid, fd = pty.fork()
    if pid == 0:
        os.execvp(cmd[0], cmd)
    else:
        while True:
            try:
                output = os.read(fd, 1024).decode()
                print(output, end='')
                if 'yes/no' in output.lower():
                    os.write(fd, b'yes\n')
                elif 'password:' in output.lower():
                    os.write(fd, (password + '\n').encode())
            except OSError:
                break
        _, status = os.waitpid(pid, 0)
        return status

if __name__ == "__main__":
    pwd = "ciao2112"
    ip = "65.108.208.5"
    user = "root"

    setup_script = """
    echo "Updating Cron Job (Runs every Sunday at 02:00 AM)..."
    (crontab -l 2>/dev/null | grep -v "/root/scraper/daily_job.sh"; echo "0 2 * * 0 /root/scraper/daily_job.sh") | crontab -
    echo "Cron updated successfully."
    """
    
    print("Executing remote setup via SSH...")
    cmd_ssh = ["ssh", "-o", "StrictHostKeyChecking=no", f"{user}@{ip}", setup_script]
    run_cmd(cmd_ssh, pwd)

    print("All done successfully.")
