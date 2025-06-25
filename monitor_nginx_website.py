import os
import time
import requests
import paramiko
import signal
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import boto3

# --- Configuration ---
CHECK_INTERVAL_SECONDS = int(os.environ.get('CHECK_INTERVAL_SECONDS', 300))  # Default: 5 minutes

# Comma-separated list of instance IDs and container names (format: i-xxxx:containername)
INSTANCES = os.environ.get('MONITOR_INSTANCES', 'i-04cc5fdaed56889ab:nginx,i-05985ff6ec74ae8ca:nginx1,i-088631c87f7087d03:nginx2')
# Example: 'i-1234567890abcdef0:nginx,i-0987654321fedcba0:nginx1'

# Email settings
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
EMAIL_ADDRESS = os.environ.get('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.environ.get('EMAIL_PASSWORD')
TO_EMAIL = os.environ.get('TO_EMAIL', 'your_emailaddress@yourdomain.com')

# SSH settings
REMOTE_USER = os.environ.get('REMOTE_USER', 'admin')  # Debian default user
PEM_FILE_PATH = os.environ.get('PEM_FILE_PATH', 'debian-key.pem')

# AWS EC2 settings
AWS_REGION = os.environ.get('AWS_REGION', 'eu-west-2')

def parse_instances(instances_str):
    """
    Parse the MONITOR_INSTANCES string into a list of dicts.
    """
    result = []
    for entry in instances_str.split(','):
        parts = entry.strip().split(':')
        if len(parts) == 2:
            result.append({'instance_id': parts[0], 'container_name': parts[1]})
    return result

def get_instance_public_ip(instance_id, region):
    ec2 = boto3.resource('ec2', region_name=region)
    instance = ec2.Instance(instance_id)
    return instance.public_ip_address

def check_website_status(url):
    try:
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except Exception:
        return False

def send_email(subject, body, to_email):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
    except Exception as e:
        print(f"Failed to send email: {e}")

def restart_container_via_ssh(host, username, pem_file_path, container_name):
    key = paramiko.RSAKey.from_private_key_file(pem_file_path)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(hostname=host, username=username, pkey=key)
        stdin, stdout, stderr = ssh.exec_command(f"sudo docker restart {container_name}")
        output = stdout.read().decode()
        error = stderr.read().decode()
        if error:
            print(f"Error restarting container: {error}")
        else:
            print(f"Container '{container_name}' restarted successfully: {output}")
    except Exception as e:
        print(f"SSH connection or command failed: {e}")
    finally:
        ssh.close()

def reboot_server(instance_id):
    print(f"Rebooting AWS EC2 instance {instance_id}...")
    try:
        ec2 = boto3.client('ec2', region_name=AWS_REGION)
        ec2.reboot_instances(InstanceIds=[instance_id])
        print(f"Reboot command sent to EC2 instance {instance_id}.")
    except Exception as e:
        print(f"Failed to reboot EC2 instance: {e}")

def start_server(instance_id):
    print(f"Starting AWS EC2 instance {instance_id}...")
    try:
        ec2 = boto3.client('ec2', region_name=AWS_REGION)
        ec2.start_instances(InstanceIds=[instance_id])
        print(f"Start command sent to EC2 instance {instance_id}.")
    except Exception as e:
        print(f"Failed to start EC2 instance: {e}")

def graceful_exit(signum, frame):
    print("\nReceived termination signal. Shutting down monitoring program gracefully...")
    subject = "Nginx Multi-Instance Monitoring Program Stopped"
    body = (
        "Your Nginx multi-instance monitoring program has been stopped and is no longer running.\n"
        "No further monitoring or automated recovery actions will be performed until it is restarted."
    )
    send_email(subject, body, TO_EMAIL)
    print("Notification email sent. Exiting now.")
    sys.exit(0)

def main():
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, graceful_exit)
    signal.signal(signal.SIGTERM, graceful_exit)

    instances = parse_instances(INSTANCES)
    failure_counts = {inst['instance_id']: 0 for inst in instances}

    while True:
        for inst in instances:
            instance_id = inst['instance_id']
            container_name = inst['container_name']
            public_ip = get_instance_public_ip(instance_id, AWS_REGION)
            if not public_ip:
                print(f"[{instance_id}] Could not retrieve EC2 public IP. Attempting to start the instance.")
                start_server(instance_id)
                # Wait for the instance to start and get a public IP
                for _ in range(30):  # Wait up to 5 minutes (30 * 10s)
                    time.sleep(10)
                    public_ip = get_instance_public_ip(instance_id, AWS_REGION)
                    if public_ip:
                        print(f"[{instance_id}] Instance started. New public IP: {public_ip}")
                        break
                else:
                    print(f"[{instance_id}] Instance did not start in time. Skipping this check.")
                    continue

            website_url = f"http://{public_ip}:8080"

            if check_website_status(website_url):
                print(f"[{instance_id}] Website {website_url} is UP.")
                failure_counts[instance_id] = 0
            else:
                print(f"[{instance_id}] Website {website_url} is DOWN. Sending notification email and attempting to restart container.")
                subject = f"ALERT: Website {website_url} is DOWN"
                body = f"The monitored Nginx website {website_url} (instance {instance_id}) appears to be DOWN. Attempting to restart the container '{container_name}'."
                send_email(subject, body, TO_EMAIL)
                restart_container_via_ssh(public_ip, REMOTE_USER, PEM_FILE_PATH, container_name)
                failure_counts[instance_id] += 1
                if failure_counts[instance_id] >= 3:
                    subject = f"CRITICAL: Website {website_url} is STILL DOWN after container restart"
                    body = f"The monitored Nginx website {website_url} (instance {instance_id}) is still DOWN after {failure_counts[instance_id]} attempts. Rebooting the EC2 instance."
                    send_email(subject, body, TO_EMAIL)
                    reboot_server(instance_id)
                    failure_counts[instance_id] = 0  # Reset after reboot attempt
        time.sleep(CHECK_INTERVAL_SECONDS)

if __name__ == "__main__":
    main()