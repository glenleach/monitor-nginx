import boto3
import time
import paramiko
import contextlib
import os

# --- Configuration ---
REGION = 'eu-west-2'
INSTANCE_TYPE = 't2.micro'
KEY_NAME = 'debian-key'  # Replace with your EC2 key pair name
PRIVATE_KEY_PATH = 'debian-key.pem'  # Replace with your .pem file path
SECURITY_GROUP_NAME = 'debian-nginx-sg'
SSH_USERNAME = 'admin'  # Default for Debian AMI

# --- AWS Clients ---
ec2 = boto3.resource('ec2', region_name=REGION)
ec2_client = boto3.client('ec2', region_name=REGION)
ssm = boto3.client('ssm', region_name=REGION)

# --- Get Latest Debian AMI from SSM ---
ami_param = '/aws/service/debian/release/bookworm/latest/amd64'
ami_id = ssm.get_parameter(Name=ami_param)['Parameter']['Value']
print(f"✅ Latest Debian AMI ID: {ami_id}")

# --- Create Security Group ---
try:
    sg_response = ec2_client.create_security_group(
        GroupName=SECURITY_GROUP_NAME,
        Description='Allow SSH, HTTP, and port 8080'
    )
    sg_id = sg_response['GroupId']
    ec2_client.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp', 'FromPort': 8080, 'ToPort': 8080, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
        ]
    )
    print(f"✅ Created security group: {SECURITY_GROUP_NAME}")
except ec2_client.exceptions.ClientError as e:
    if 'InvalidGroup.Duplicate' in str(e):
        sg = list(ec2.security_groups.filter(Filters=[{'Name': 'group-name', 'Values': [SECURITY_GROUP_NAME]}]))[0]
        sg_id = sg.group_id
        print(f"ℹ️ Security group already exists: {SECURITY_GROUP_NAME}")
    else:
        raise

# --- Launch EC2 Instance ---
print("🚀 Launching EC2 instance...")
instance = ec2.create_instances(
    ImageId=ami_id,
    InstanceType=INSTANCE_TYPE,
    MinCount=1,
    MaxCount=1,
    KeyName=KEY_NAME,
    SecurityGroupIds=[sg_id],
)[0]

instance.wait_until_running()
instance.reload()
public_ip = instance.public_ip_address
print(f"✅ Instance running at: http://{public_ip}:8080")

# --- Wait for EC2 Boot & SSH ---
print("⏳ Waiting for instance to initialize (60 seconds)...")
time.sleep(60)

# --- SSH Configuration ---
print("🔐 Setting up SSH connection configuration...")
if not os.path.exists(PRIVATE_KEY_PATH):
    raise FileNotFoundError(f"Private key file not found: {PRIVATE_KEY_PATH}")

key = paramiko.RSAKey.from_private_key_file(PRIVATE_KEY_PATH)
ssh_client = paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

def exec_command_and_close(ssh, command):
    """Executes a command and ensures the channel is closed."""
    stdin, stdout, stderr = ssh.exec_command(command)
    try:
        out = stdout.read().decode()
        err = stderr.read().decode()
        return out, err
    finally:
        # Explicitly close the channel to avoid Paramiko destructor errors
        stdout.channel.close()
        stderr.channel.close()

# --- Connect via SSH and Setup Docker + NGINX ---
print(f"🔐 Connecting to {public_ip} as '{SSH_USERNAME}' using key '{PRIVATE_KEY_PATH}'...")
with contextlib.closing(ssh_client) as ssh:
    try:
        ssh.connect(hostname=public_ip, username=SSH_USERNAME, pkey=key)
        print("✅ SSH connection established.")

        commands = [
            "sudo apt-get update && sudo apt-get install -y docker.io",
            "sudo systemctl start docker",
            "sudo docker run -d -p 8080:80 nginx"
        ]

        for cmd in commands:
            print(f"💻 Executing: {cmd}")
            out, err = exec_command_and_close(ssh, cmd)
            print(out)
            print(err)

        # --- Print running Docker container names ---
        print("🔎 Fetching running Docker container names...")
        out, err = exec_command_and_close(ssh, "sudo docker ps --format '{{.Names}}'")
        container_names = out.splitlines()
        if container_names:
            print("🚢 Running Docker container names:")
            for name in container_names:
                print(f"  - {name}")
        else:
            print("⚠️ No running Docker containers found.")

        print("🔒 SSH connection closed.")
    except Exception as e:
        print(f"❌ SSH connection or command failed: {e}")

print(f"🌐 Your NGINX website is live at: http://{public_ip}:8080")