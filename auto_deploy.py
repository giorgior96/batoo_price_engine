import pty
import os
import sys

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

    # 1. Compress the directory
    print("Compressing scraper directory...")
    os.system("tar -czf /tmp/scraper_deploy.tar.gz -C /home/giorgio/Scrivania/base_database_scraping .")

    # 2. SCP the file
    print("Uploading scraper to VPS...")
    cmd_scp = ["scp", "-o", "StrictHostKeyChecking=no", "/tmp/scraper_deploy.tar.gz", f"{user}@{ip}:/tmp/"]
    run_cmd(cmd_scp, pwd)

    # 3. SCP Google Cloud Credentials
    print("Uploading Google Cloud Credentials...")
    gcp_creds = "/home/giorgio/.config/gcloud/application_default_credentials.json"
    if os.path.exists(gcp_creds):
        cmd_scp_creds = ["scp", "-o", "StrictHostKeyChecking=no", gcp_creds, f"{user}@{ip}:/root/bq_credentials.json"]
        run_cmd(cmd_scp_creds, pwd)
    else:
        print("Warning: Google Cloud Credentials not found locally.")

    # 4. SSH into VPS and setup everything
    setup_script = """
    mkdir -p /root/scraper
    tar -xzf /tmp/scraper_deploy.tar.gz -C /root/scraper
    cd /root/scraper

    echo "Installing system dependencies..."
    apt-get update -y > /dev/null
    apt-get install -y python3 python3-venv python3-pip cron > /dev/null

    echo "Setting up Python virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    echo "Installing Python requirements..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    fi
    pip install pandas google-cloud-bigquery bs4 requests httpx tqdm > /dev/null

    echo "Creating daily job script..."
    cat << 'EOF' > /root/scraper/daily_job.sh
#!/bin/bash
cd /root/scraper
source venv/bin/activate

# Use the explicitly copied credentials for Google Cloud
export GOOGLE_APPLICATION_CREDENTIALS="/root/bq_credentials.json"

echo "Running scrapers at $(date)" >> /root/scraper/cron.log
python run_all.py >> /root/scraper/cron.log 2>&1
echo "Uploading to BigQuery at $(date)" >> /root/scraper/cron.log
python upload_to_bq.py >> /root/scraper/cron.log 2>&1
echo "Job finished at $(date)" >> /root/scraper/cron.log
EOF

    chmod +x /root/scraper/daily_job.sh

    echo "Setting up Cron Job (Runs every day at 02:00 AM)..."
    (crontab -l 2>/dev/null | grep -v "/root/scraper/daily_job.sh"; echo "0 2 * * * /root/scraper/daily_job.sh") | crontab -

    echo "VPS Setup Complete!"
    """
    
    print("Executing remote setup via SSH...")
    cmd_ssh = ["ssh", "-o", "StrictHostKeyChecking=no", f"{user}@{ip}", setup_script]
    run_cmd(cmd_ssh, pwd)

    print("All done successfully.")
