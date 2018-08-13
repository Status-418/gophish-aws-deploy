# Gophish AWS Deploy
This script makes it possible to deploy a fully functioning Gophish instance to an AWS EC2 instance with one cammand. The script will create the required Security Groups, Key Pairs, Roles & Profiles as well as create an instance to run Gophish and install the binary.

# Requirements
## Authentication
In order for this script to be able to perform the above tasks the user needs to provide an AWS API Key and Secret with appropriate privileges. The API details need to be configured with one of the <a href="https://boto3.readthedocs.io/en/latest/guide/configuration.html" target="_blank">following </a>methodes. 

## Dependancies
This script requires the following two python libraries:
- Boto3
- Requests

# Setup
Clone this repository to where you want to run it from by issueing the following command:
```
git clone https://github.com/Status-418/gophish-aws-deploy.git
```
Install the required dependancies:
```
pip install requirements.txt
```

# Basic Usage

The below command shows all valid arguments available:
```
#python goPhish-AWS-Deploy.py -h

usage: goPhish-AWS-Deploy.py [-h] --InstanceName INSTANCENAME
                             [--Region REGION] [--InstanceType INSTANCETYPE]
                             [--ImageId IMAGEID] [--AdminContact ADMINCONTACT]

optional arguments:
  -h, --help                    show this help message and exit
  --InstanceName INSTANCENAME   Provide the name of the instance you want to stand up
  --Region REGION               Provide the Region to be used (Default: us-west-1)
  --InstanceType INSTANCETYPE   Provide the type of the instance you want to stand up (Default: t2.micro)
  --ImageId IMAGEID             Provide the ImageID for the image you want to deploy (Default: ami-4aa04129)
  --AdminContact ADMINCONTACT   Provide the project admin account email address
```
The only mandatory argument is the InstanceName. 

All other arguments have a default value that can be over ruled by providing an appropriate alternative argument.

Below is what the execution of the script will look like:
```
python goPhish-AWS-Deploy.py --InstanceName Gophish

[*] A new Key Pair named "GophishKey" was created
[*] Key Fingerpring: 
a9:ff:fd:ea:28:8a:......
[*] Key Material: 
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCA...
...
...
...
-----END RSA PRIVATE KEY-----
[*] A new Security Group named "GophishGroup" was creased. Admin access granted from X.X.X.X/32
[*] A new Instance Profile named "GophishInstanceProfile" was created
[*] A new Role named "GophishRole" was created
[*] Added Role: "GophishRole" to the Instance Profile: "GophishInstanceProfile"
[*] A new EC2 Instance is being spun up
[*] The instance is up and running. Waiting for checks to complete.
[*] Added the required permissions to allow SSM
[*] Waiting for the instance to finish starting start up
[*] The new Instance (i-XXXXXXXXXXXXXXXX) is now ready to go
[*] Preparing to install Gophish
[*] The Gophish installation has started
[*] The Gophish installation has completed
[*] The setup of Gophish is complete please try connecting to the admin pannel: https://x.x.x.x.:3333
```

# Resources Created
The following AWS resources are created as part of the setup script:

## Key Pair
If there is not already an existing Key Pair with the name \<InstanveName\>Key a new Key Pair is created. The Key Fingerprint and Key Material are printed to standard out once. Be sure to safe the details in a secure location.

A KeyPair of your choice can be assigned to the EC2 instance after the setup completes and the just created Key Pair can be deleted if no longer required.

## Security Group
If there is not already an existing Security Group with the name \<InstanceName\>Group a new Secutiy Group is created.
  
By defaul the public IP address from where the script was run will be given admin access on port 3333 and 22.

This default configuration can be changed at any time in the AWS console.

## Permissions

### Role
A new Role called \<InstanceName\>Role is created and the following policy is assigned to it:
  - AmazonSSMFullAccess

This Policy is needed so AWS Systems Manager can be used to install Gophish

### Instance Profile
A new Instance Policy is created named \<InstanceName\>InstanceProfile and the previously created Role is assigned to this Instance Profile
 
