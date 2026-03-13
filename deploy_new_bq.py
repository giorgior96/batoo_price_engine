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
    
    print("Uploading new BigQuery script to VPS...")
    cmd_scp = ["scp", "-o", "StrictHostKeyChecking=no", "new_upload_to_bq.py", f"{user}@{ip}:/root/scraper/upload_to_bq.py"]
    run_cmd(cmd_scp, pwd)

    print("Done!")
