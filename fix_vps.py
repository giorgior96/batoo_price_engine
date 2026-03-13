import paramiko
import time

host = '65.108.208.5'
user = 'root'
password = 'ciao2112'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(host, username=user, password=password)
    
    print("--- INSTALLING MISSING DEPENDENCIES ---")
    commands = [
        "cd /root/scraper && venv/bin/pip install thefuzz python-Levenshtein pyarrow",
        "cd /root/scraper && venv/bin/python normalize_data.py",
        "cd /root/scraper && export GOOGLE_APPLICATION_CREDENTIALS='/root/bq_credentials.json' && venv/bin/python upload_to_bq.py"
    ]
    
    for cmd in commands:
        print(f"Executing: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        
        # Wait for the command to finish and print output
        exit_status = stdout.channel.recv_exit_status() 
        print(f"Exit status: {exit_status}")
        
        out = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        
        if out:
            print(f"STDOUT:\n{out}")
        if err:
            print(f"STDERR:\n{err}")
        print("-" * 40)
        
except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
