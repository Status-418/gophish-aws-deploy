import argparse
import boto3
import json

MinCount = 1
MaxCount =1


def _check_instance_proflie(client, InstanceProfileName):
    try:
        profiles = client.list_instance_profiles()
        for profile in profiles['InstanceProfiles']:
            if InstanceProfileName in profile['InstanceProfileName']:
                print('[*] Using existing Instance Profile: {}'.format(profile['InstanceProfileName']))
                return True

        instance_profile = client.create_instance_profile(InstanceProfileName=InstanceProfileName)
        if instance_profile['ResponseMetadata']['HTTPStatusCode'] is 200:
            print('[*] A new Instance Profile named "{}" was created'.format(InstanceProfileName))
            return True
        else:
            print('[*] Failed to create a new Instance Profile: {}'.format(instance_profile))
            return False
    except Exception as e:
        print('[***] Failed to create a Instance Profile: {}'.format(e))


def _check_role(client, RoleName):

    try:
        roles = client.list_roles()
        for role in roles['Roles']:
            if RoleName in role['RoleName']:
                print('[*] Using existing Role: {}'.format(role['RoleName']))
                return True

        role = client.create_role(RoleName=RoleName, AssumeRolePolicyDocument='{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"}, "Action": "sts:AssumeRole"}]}', Description='A role to allows SSM access to the {} instance for provisioning'.format(RoleName))
        if role['ResponseMetadata']['HTTPStatusCode'] is 200:
            print('[*] A new Role called "{}" was created'.format(RoleName))
            return True
        else:
            print('[***] Failed to created a new Role: {}'.format(role))
            return False
    except Exception as e:
        print('[***] Failed to create a Instance Profile: {}'.format(e))


def _attach_policy_to_role(clien, PolicyName, RoleName):
    response = client.attach_role_policy(
        PolicyArn='arn:aws:iam::aws:policy/AmazonSSMFullAccess',
        RoleName=RoleName,
    )
    print(response)

    return False


def _add_role_to_profile(client, InstanceProfileName, RoleName):
    try:
        profile = client.get_instance_profile(InstanceProfileName=InstanceProfileName)
        if len(profile['InstanceProfile']['Roles']) > 0:
            for role in profile['InstanceProfile']['Roles']:
                if role['RoleName'] in RoleName:
                    print('[*] The Profile: "{}" already has a Role: "{}" associated'.format(InstanceProfileName, RoleName))
                    return True
                else:
                    print('[***] The Profile "{}" has an incorrect Role "{}" associated'.format(InstanceProfileName, RoleName))
                    return False
        else:
            add_role = client.add_role_to_instance_profile(InstanceProfileName=InstanceProfileName, RoleName=RoleName)
            if add_role['ResponseMetadata']['HTTPStatusCode'] is 200:
                print('[*] Added Role: "{}" to the Instance Profile: "{}"'.format(RoleName, InstanceProfileName))
                return True
            else:
                print('[*] Failed to add the Role: "()" to the Profiel: {}'.format(RoleName, InstanceProfileName))
                return False
    except Exception as e:
        print('[***] Failed to create a Instance Profile: {}'.format(e))


def check_key_pairs(client, KeyName):
    key_pairs = client.describe_key_pairs()

    for key_pair in key_pairs['KeyPairs']:
        if KeyName in key_pair['KeyName']:
            print('[*] Using existing Key Pair: {}'.format(KeyName))
            return True

    try:
        response = client.create_key_pair(KeyName=KeyName)
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print('[*] A new Key Pair named "{}" was created\n[*] Key Fingerpring: \n{}\n[*] Key Material: \n{}\n'.format(response['KeyName'], response['KeyFingerprint'], response['KeyMaterial']))
            return True
        else:
            print(json.dumps(response, indent=4))
            return False


    except Exception as e:
        print('[***] Failed to create Key Pair: {}'.format(e))
        return False


def check_secutiry_groups(client, GroupName, InstanceName, src_ips):

    security_groups = client.describe_security_groups()

    for security_group in security_groups['SecurityGroups']:
        if GroupName in security_group['GroupName']:
            print('[*] Using existing Security Group: {}'.format(GroupName))
            return True

    try:
        response = client.create_security_group(GroupName=GroupName, Description='A security group that provides access to the {} instance'.format(InstanceName))

        for src_ip in src_ips:
            client.authorize_security_group_ingress(GroupId=response['GroupId'], IpProtocol="tcp", CidrIp=src_ip, FromPort=22, ToPort=22)
            client.authorize_security_group_ingress(GroupId=response['GroupId'], IpProtocol="tcp", CidrIp='0.0.0.0/32', FromPort=443, ToPort=443)
            client.authorize_security_group_ingress(GroupId=response['GroupId'], IpProtocol="tcp", CidrIp=src_ip, FromPort=3333, ToPort=3333)

        print('[*] A new Security Group named "{}" was creased'.format(GroupName))
        return True

    except Exception as e:
        print('[***] Failed to create Security Group: {}'.format(e))
        return False


def check_iam_profile(client, InstanceName):
    InstanceProfileName = '{}InstanceProfile'.format(InstanceName)
    RoleName = '{}Role'.format(InstanceName)

    if _check_instance_proflie(client, InstanceProfileName):
        if _check_role(client, RoleName):
            if _attach_policy_to_role:
                if _add_role_to_profile(client, InstanceProfileName, RoleName):
                    return True
                else:
                    return False


def create_instance(client, ec2, InstanceName, ImageId, KeyName, InstanceType, SecurityGroup, AdminContact):

    running_instances = client.describe_instances()

    if len(running_instances['Reservations']) > 0:
        for reservations in running_instances['Reservations']:
            for ec2_instance in reservations['Instances']:
                if ec2_instance['State']['Name'] == 'running':
                    for tag in ec2_instance['Tags']:
                        if 'Name' in tag['Key'] and InstanceName == tag['Value']:
                            print('[***] An instance named {} already exists. Stopping the deployment of goPhish. \n      Rename the existing instance or provide the a differnat InsstanceName argument.'.format(InstanceName))
                            return False
    if AdminContact is '':
        AdminContact = 'No Admin Contact Provided'

    try:
        instance = ec2.create_instances(
            ImageId=ImageId,
            MinCount=MinCount,
            MaxCount=MaxCount,
            KeyName=KeyName,
            InstanceType=InstanceType,
            SecurityGroups=[SecurityGroup],
            TagSpecifications=[
                {'ResourceType': 'instance',
                                  'Tags': [
                                      {'Key': 'Name', 'Value': InstanceName},
                                      {'Key': 'admin_contact', 'Value': AdminContact},
                                      {'Key': 'service_id', 'Value': InstanceName},
                                      {'Key': 'service_data', 'Value': 'env=Dev'}
                                  ]
                }])[0]

        print('[*] A new EC2 Instance is being spun up for you. Please hold tight!')
        new_instance = ec2.Instance(instance.id)
        new_instance.wait_until_running()
        print('[*] The instance is up and running. Just waiting for a few checks to complete')

        client.associate_iam_instance_profile(
            IamInstanceProfile = {'Arn': 'arn:aws:iam::054732315499:instance-profile/goPhishInstanceProfile',
                                  'Name': 'goPhishRole'},
            InstanceId=instance.id)
        print('[*] Added the required roles to allow SSM')

        print('[*] Waiting for the instance to spin up fully')
        waiter = client.get_waiter('instance_status_ok')
        waiter.wait(InstanceIds=[new_instance.id])
        print('[*] The new Instance ({}) is now ready to go'.format(instance.id))

        return instance.id

    except Exception as e:
        if 'InvalidKeyPair.NotFound' in str(e):
            print('[***]No Key Pair named {} was found. Please create this Key Pair first and store the keys safely.'.format(args.KeyName))
            return False
        else:
            print('[***] {}'.format(e))
            return False


def execute_commands_on_instance(client, Commands, Instance):

    print('[*] Starting the Installation of goPhish')
    response = client.send_command(
        DocumentName="AWS-RunShellScript",
        Parameters={'commands': Commands},
        InstanceIds=Instance,
        )
    return response


def main(args):
    client_ec2 = boto3.client('ec2', region_name=args.Region)
    client_iam = boto3.client('iam', region_name=args.Region)
    client_ssm = boto3.client('ssm', region_name=args.Region)
    ec2 = boto3.resource('ec2', region_name=args.Region)

    SecurityGroup = '{}Group'.format(args.InstanceName)
    KeyName = '{}Key'.format(args.InstanceName)

    if check_key_pairs(client_ec2, KeyName):
        if check_secutiry_groups(client_ec2, SecurityGroup, args.InstanceName, args.src_ip):
            if check_iam_profile(client_iam, args.InstanceName):
                instance = create_instance(client_ec2, ec2, args.InstanceName, args.ImageId, KeyName, args.InstanceType, SecurityGroup, args.AdminContact)
                if instance:
                    instance = instance.split(',')
                    command = execute_commands_on_instance(client_ssm,
                                                           ['git clone https://github.com/Status-418/gophish-aws-deploy.git',
                                                            'cd gophish-aws-deploy/tools',
                                                            'sudo bash install.sh'
                                                           ],
                                                           instance)
                    if command['ResponseMetadata']['HTTPStatusCode'] == 200:
                        public_ip = client_ec2.describe_instances(InstanceIds=instance)['Reservations'][0]['Instances'][0]['PublicIpAddress']
                        print('[*] The installation of goPhish is complete please try connecting on port https://{}:3333'.format(public_ip))
                    else:
                        print('[***] Failed to install goPhish: {}'.format(command))

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--InstanceName', required=True, help='Provide the name of the instance you want to stand up')
    parser.add_argument('--src_ip', required=True, help='Provide a coma seperated list of IPs that are to have access to the admin interface.')
    parser.add_argument('--Region', default='us-west-1', help='Provide the Region to be used (Default: us-west-1')
    parser.add_argument('--InstanceType', default='t2.micro', help='Provide the type of the instance you want to stand up (Default: t2.micro)')
    parser.add_argument('--ImageId', default='ami-4aa04129', help='Provide the ImageID for the image you want to deploy (Default: ami-4aa04129')
    parser.add_argument('--AdminContact', help='Provide the project admin account email address')
    args = parser.parse_args()

    if isinstance(args.src_ip, str):
        args.src_ip = args.src_ip.split(',')

    main(args)

