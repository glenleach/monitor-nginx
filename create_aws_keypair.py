import boto3

REGION = 'eu-west-2'
KEY_PAIR_NAME = 'debian-key'  # change as needed
PEM_FILE = f'{KEY_PAIR_NAME}.pem'

ec2_client = boto3.client('ec2', region_name=REGION)

# Create key pair
response = ec2_client.create_key_pair(KeyName=KEY_PAIR_NAME)
private_key = response['KeyMaterial']

# Save private key to a .pem file
with open(PEM_FILE, 'w') as pem_file:
    pem_file.write(private_key)

# Set secure permissions on the file (Unix only)
import os
os.chmod(PEM_FILE, 0o400)

print(f"Key pair created and saved to {PEM_FILE}")
