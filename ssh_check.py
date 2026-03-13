import paramiko

host = '65.108.208.5'
user = 'root'
password = 'ciao2112'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    client.connect(host, username=user, password=password)
    
    print("--- daily_job.sh ---")
    stdin, stdout, stderr = client.exec_command('cat /root/scraper/daily_job.sh')
    print(stdout.read().decode())
    
    print("--- ls -la /root/scraper ---")
    stdin, stdout, stderr = client.exec_command('ls -la /root/scraper')
    print(stdout.read().decode())
    
    print("--- TAIL OF POTENTIAL LOGS ---")
    stdin, stdout, stderr = client.exec_command('tail -n 50 /root/scraper/*.log')
    print(stdout.read().decode())
    
except Exception as e:
    print(f"Error: {e}")
finally:
    client.close()
