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
    
    print("Uploading updated scripts to VPS...")
    # Using the local file 'prepare_navisnet.py' which exists in the previous local folder path
    cmd_scp1 = ["scp", "-o", "StrictHostKeyChecking=no", "/home/giorgio/Scrivania/base_database_scraping/prepare_navisnet.py", f"{user}@{ip}:/root/scraper/"]
    run_cmd(cmd_scp1, pwd)

    cmd_scp2 = ["scp", "-o", "StrictHostKeyChecking=no", "new_run_all.py", f"{user}@{ip}:/root/scraper/run_all.py"]
    run_cmd(cmd_scp2, pwd)

    cmd_scp3 = ["scp", "-o", "StrictHostKeyChecking=no", "new_normalize_data.py", f"{user}@{ip}:/root/scraper/normalize_data.py"]
    run_cmd(cmd_scp3, pwd)

    # Visto che prepare_navisnet.py usa requests, assicuriamoci che sia installato anche quello (anche se l'avevamo aggiunto prima)
    setup_script = """
    cd /root/scraper
    source venv/bin/activate
    pip install requests pandas > /dev/null
    """
    cmd_ssh = ["ssh", "-o", "StrictHostKeyChecking=no", f"{user}@{ip}", setup_script]
    run_cmd(cmd_ssh, pwd)

    print("Navisnet integration done!")
