# Demo App – DevOps Bootcamp Training (TechWorld with Nana)
This repository is part of the DevOps Bootcamp from TechWorld with Nana.

# monitor_nginx_website.py

## Overview

This script is a **demo project** created as part of DevOps Bootcamp Training (TechWorld with Nana).
It demonstrates how to monitor the availability of multiple Nginx-based websites running in Docker containers on AWS EC2 instances, and how to automate recovery actions and notifications.

**Key Features:**
- Monitors multiple EC2 instances and their associated Docker containers/websites.
- Automatically restarts containers via SSH if a website is down.
- Reboots or starts EC2 instances via AWS API if needed.
- Sends email notifications for website downtime, recovery actions, and when the monitoring program exits.
- Graceful shutdown with notification on program exit.

## How It Works

- The script loops through a list of EC2 instance/container pairs.
- For each, it checks if the website is up (HTTP 200).
- If down, it attempts to SSH in and restart the Docker container.
- If the container restart fails 3 times, it reboots the EC2 instance.
- If the instance is stopped, it starts it and waits for it to become available.
- All actions and failures trigger email notifications.
- If the monitoring script is stopped (Ctrl+C or SIGTERM), it sends a notification email.

## Configuration

### Environment Variables

MONITOR_INSTANCES=i-04cc5fdaed56889ab:compassionate_shockley,i-05985ff6ec74ae8ca:adoring_black
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
TO_EMAIL=recipient@example.com
PEM_FILE_PATH=/path/to/debian-key.pem
REMOTE_USER=admin
AWS_REGION=eu-west-2
CHECK_INTERVAL_SECONDS=300

```

### How to Set Environment Variables in PyCharm and VS Code

#### PyCharm
1. Open your project in PyCharm.
2. Go to `Run` > `Edit Configurations...`.
3. Select your script (e.g., `monitor_nginx_website.py`) or create a new configuration.
4. In the configuration window, find the `Environment variables` field.
5. Click the icon to the right (or enter directly) and add each variable in the format `KEY=VALUE`, separated by semicolons (Windows) or colons (macOS/Linux).
   - Example: `EMAIL_ADDRESS=your_email@gmail.com;EMAIL_PASSWORD=your_app_password;AWS_REGION=eu-west-2`
6. Click OK to save.

#### VS Code
1. Open your project in VS Code.
2. If you use the built-in debugger, create or edit a `.env` file in your project root.
3. Add each environment variable on a new line in the format `KEY=VALUE`.
   - Example:
     ```
     EMAIL_ADDRESS=your_email@gmail.com
     EMAIL_PASSWORD=your_app_password
     AWS_REGION=eu-west-2
     ```
4. In your `launch.json` (for debugging), add or ensure the following:
   ```json
   "envFile": "${workspaceFolder}/.env"
   ```
5. Save the files. VS Code will load these variables when running or debugging your script.

### How to Create an App Password for Gmail

If you use Gmail for sending notification emails, you need to generate an app password (not your regular Gmail password) and add it to your environment variables.

#### Steps to Create an App Password:
1. Go to your Google Account at https://myaccount.google.com/
2. Navigate to `Security`.
3. Under `Signing in to Google`, ensure 2-Step Verification is enabled. If not, enable it first.
4. Once 2-Step Verification is enabled, you will see the `App passwords` option. Click on it.
5. Sign in again if prompted.
6. Under `Select app`, choose `Mail` (or `Other` and name it as you like).
7. Under `Select device`, choose your device or enter a custom name.
8. Click `Generate`.
9. Copy the 16-character app password shown. You will not see it again!

#### Add the App Password to Your Editor's Environment Variables
- Use the generated app password as the value for `EMAIL_PASSWORD` in your environment variables, as described in the previous section for PyCharm or VS Code.
- Example:
  - `EMAIL_PASSWORD=your_generated_app_password`

## Testing and Prerequisites

This demo leverages AWS resources. You will need an AWS account with sufficient permissions to create EC2 instances, key pairs, and security groups. Charges may apply for AWS usage.

### Prerequisites
- AWS account credentials configured (e.g., via environment variables or AWS CLI)
- Python dependencies installed (`boto3`, `paramiko`, `requests`)
- Environment variables set as described above

### Step-by-Step Instructions

**Step 1: Create an AWS Key Pair**
- Run the following script to create a new AWS key pair for SSH access:
  ```bash
  python create_aws_keypair.py
  ```
- This will generate a PEM file for connecting to your EC2 instances.

**Step 2: Launch an Nginx Server on a Debian EC2 Instance**
- Run the following script to launch a Debian EC2 instance with Docker and Nginx:
  ```bash
  python ec2_nginx_webserver.py
  ```
- This will start an EC2 instance, install Docker, and run an Nginx container.
- Note the instance ID and public IP for use in your monitoring configuration.

**Step 3: Test the Monitoring Script**
- With your environment variables set and the EC2 instance running, start the monitoring script:
  ```bash
  python monitor_nginx_website.py
  ```
- The script will check the status of your Nginx website and perform automated recovery actions if needed.

### Final Steps: Cleanup AWS Resources

To avoid unnecessary AWS charges, terminate your EC2 instances after completing the demo.

**Terminate EC2 Instances**
- For each EC2 instance you created, run the following script:
  ```bash
  python terminate_ec2_instance.py
  ```
- Run the script once for each instance (e.g., if you created 3 instances, run it 3 times), providing the appropriate instance ID each time.
- Ensure each instance is successfully terminated before proceeding to the next.

## Usage

1. Install dependencies:
   ```bash
   pip install boto3 paramiko requests
```

2. Set your environment variables (see above).
3. Run the script:
   ```bash
   python monitor_nginx_website.py
   ```

## What Happens on Exit?

If you stop the script (Ctrl+C or kill), it will:

- Send an email notification stating that the monitoring program has stopped and is no longer running.
- Exit gracefully.

## Customization & Extension

- You can monitor any number of EC2/container pairs by editing `MONITOR_INSTANCES`.
- The script can be extended to support other types of web servers or recovery actions.
- Email notifications can be customized for your team or alerting system.

## Example Output

```
[i-04cc5fdaed56889ab] Website http://13.42.37.128:8080 is UP.
[i-05985ff6ec74ae8ca] Website http://13.41.22.111:8080 is DOWN. Sending notification email and attempting to restart container.
...
Received termination signal. Shutting down monitoring program gracefully...
Notification email sent. Exiting now.
```

License

Copyright © Techworld with Nana. All rights reserved.

This project is provided for personal training and educational purposes only. No part of this project may be reproduced, distributed, or transmitted in any form or by any means, including photocopying, recording, or other electronic or mechanical methods, without the prior written permission of the copyright owner, except in the case of brief quotations embodied in critical reviews and certain other noncommercial uses permitted by copyright law
---

**This script is a demonstration project from the DevOps Bootcamp from TechWorld with Nana
It has been enhanced to support multi-instance monitoring, container restarts, EC2 recovery, and robust notification handling.**

```


```
