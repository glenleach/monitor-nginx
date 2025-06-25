import boto3
from botocore.exceptions import ClientError

REGION = 'eu-west-2'
KEY_NAME = 'debian-key'  # Should match the key used to launch the instance
SECURITY_GROUP_NAME = 'debian-nginx-sg'  # Should match the security group used

# Initialize EC2 resource and client
ec2 = boto3.resource('ec2', region_name=REGION)
ec2_client = boto3.client('ec2', region_name=REGION)

def find_instance():
    # Filter for running instances with the correct key and security group
    filters = [
        {'Name': 'instance-state-name', 'Values': ['pending', 'running', 'stopping', 'stopped']},
        {'Name': 'key-name', 'Values': [KEY_NAME]},
        {'Name': 'instance.group-name', 'Values': [SECURITY_GROUP_NAME]},
    ]
    instances = list(ec2.instances.filter(Filters=filters))
    if not instances:
        print('No matching EC2 instances found.')
        return None
    # Return the most recently launched instance
    latest_instance = max(instances, key=lambda i: i.launch_time)
    return latest_instance

def terminate_instance(instance):
    print(f'Terminating instance: {instance.id}')
    instance.terminate()
    instance.wait_until_terminated()
    print(f'Instance {instance.id} terminated.')

def delete_security_group():
    try:
        # Find the security group by name
        response = ec2_client.describe_security_groups(GroupNames=[SECURITY_GROUP_NAME])
        sg_id = response['SecurityGroups'][0]['GroupId']
        try:
            ec2_client.delete_security_group(GroupId=sg_id)
            print(f"Security group '{SECURITY_GROUP_NAME}' deleted.")
        except ClientError as e:
            if e.response['Error']['Code'] == 'DependencyViolation':
                print(f"Security group '{SECURITY_GROUP_NAME}' is still in use by another instance. Skipping deletion.")
            else:
                print(f"Could not delete security group '{SECURITY_GROUP_NAME}': {e}")
    except Exception as e:
        print(f"Could not find security group '{SECURITY_GROUP_NAME}': {e}")

def main():
    instance = find_instance()
    if instance:
        terminate_instance(instance)
    # After instance is terminated, try to delete the security group
    delete_security_group()

if __name__ == '__main__':
    main()