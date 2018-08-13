import argparse
import boto3
import requests
import time

MinCount = 1
MaxCount =1


def _create_instance_proflie(client, instance_profile_name):
    try:
        profiles = client.list_instance_profiles()

        for profile in profiles['InstanceProfiles']:
            if instance_profile_name in profile['InstanceProfileName']:
                print('[*] Using existing Instance Profile: {}'.format(profile['InstanceProfileName']))
                return True

        instance_profile = client.create_instance_profile(InstanceProfileName=instance_profile_name)

        if instance_profile['ResponseMetadata']['HTTPStatusCode'] is 200:
            print('[*] A new Instance Profile named "{}" was created'.format(instance_profile_name))
            return True
        else:
            print('[*] Failed to create a new Instance Profile: {}'.format(instance_profile))
            return False

    except Exception as e:
        print('[***] Failed to create a Instance Profile: {}'.format(e))
        return False


def _create_role(client, role_name):
    try:
        roles = client.list_roles()

        for role in roles['Roles']:
            if role_name in role['RoleName']:
                print('[*] Using existing Role: {}'.format(role['RoleName']))
                return True

        role = client.create_role(RoleName=role_name, AssumeRolePolicyDocument='{"Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"Service": "ec2.amazonaws.com"}, "Action": "sts:AssumeRole"}]}', Description='A role to allows SSM access to the {} instance for provisioning'.format(role_name))

        if role['ResponseMetadata']['HTTPStatusCode'] is 200:
            print('[*] A new Role named "{}" was created'.format(role_name))
            return True
        else:
            print('[***] Failed to created a new Role: {}'.format(role))
            return False

    except Exception as e:
        print('[***] Failed to create a new Role: {}'.format(e))
        return False


def _attach_policy_to_role(client, role_name):
    try:
        response = client.attach_role_policy(
            PolicyArn='arn:aws:iam::aws:policy/AmazonSSMFullAccess',
            RoleName=role_name,
        )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            print('[***] Failed to attach a Policy to Role: {}'.format(response))
            return False

    except Exception as e:
        print('[***] Failed to attach a Policy to Role: {}'.format(e))
        return False


def _add_role_to_profile(client, instance_profile_name, role_name):
    try:
        profile = client.get_instance_profile(InstanceProfileName=instance_profile_name)

        if len(profile['InstanceProfile']['Roles']) > 0:
            for role in profile['InstanceProfile']['Roles']:
                if role['RoleName'] in role_name:
                    print('[*] The Profile: "{}" already has a Role: "{}" associated'.format(instance_profile_name, role_name))
                    return True
                else:
                    print('[***] The Profile "{}" has an incorrect Role "{}" associated'.format(instance_profile_name, role_name))
                    return False

        else:
            add_role = client.add_role_to_instance_profile(InstanceProfileName=instance_profile_name, RoleName=role_name)

            if add_role['ResponseMetadata']['HTTPStatusCode'] is 200:
                print('[*] Added Role: "{}" to the Instance Profile: "{}"'.format(role_name, instance_profile_name))
                return True
            else:
                print('[*] Failed to add the Role: "()" to the Profiel: {}'.format(role_name, instance_profile_name))
                return False

    except Exception as e:
        print('[***] Failed to create a Instance Profile: {}'.format(e))
        return False


def _check_command_status(client, command_id):
    try:
        response = client.list_command_invocations(CommandId=command_id)

        if response['CommandInvocations'][0]['Status'] == 'Success':
            return 200
        else:
            time.sleep(5)
            _check_command_status(client, command_id)

    except Exception as e:
        print('[***] Failed to check the SSM command status: {}'.format(e))
        return False


def create_key_pairs(client, key_name):
    try:
        key_pairs = client.describe_key_pairs()

        for key_pair in key_pairs['KeyPairs']:
            if key_pair['KeyName'] == key_name:
                print('[*] Using existing Key Pair: {}'.format(key_name))
                return True

        response = client.create_key_pair(KeyName=key_name)

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print('[*] A new Key Pair named "{}" was created\n[*] Key Fingerpring: \n{}\n[*] Key Material: \n{}\n'.format(response['KeyName'], response['KeyFingerprint'], response['KeyMaterial']))
            return True
        else:
            print('[***] Failed to create a Key Pair: {}'.format(response))
            return False

    except Exception as e:
        print('[***] Failed to create Key Pair: {}'.format(e))
        return False


def create_secutiry_groups(client, group_name, instance_name):
    try:
        security_groups = client.describe_security_groups()

        for security_group in security_groups['SecurityGroups']:
            if group_name in security_group['GroupName']:
                print('[*] Using existing Security Group: {}'.format(group_name))
                return True

        response = client.create_security_group(GroupName=group_name, Description='A security group that provides access to the {} instance'.format(instance_name))

        src_ip = '{}/32'.format(requests.get('http://jsonip.com').json()['ip'])

        client.authorize_security_group_ingress(GroupId=response['GroupId'], IpProtocol="tcp", CidrIp=src_ip, FromPort=22, ToPort=22)
        client.authorize_security_group_ingress(GroupId=response['GroupId'], IpProtocol="tcp", CidrIp='0.0.0.0/32', FromPort=443, ToPort=443)
        client.authorize_security_group_ingress(GroupId=response['GroupId'], IpProtocol="tcp", CidrIp=src_ip, FromPort=3333, ToPort=3333)

        print('[*] A new Security Group named "{}" was creased. Admin access granted from {}'.format(group_name, src_ip))
        return True

    except Exception as e:
        print('[***] Failed to create Security Group: {}'.format(e))
        return False


def create_iam_profile(client, instance_name):
    InstanceProfileName = '{}InstanceProfile'.format(instance_name)
    RoleName = '{}Role'.format(instance_name)

    if _create_instance_proflie(client, InstanceProfileName):
        if _create_role(client, RoleName):
            if _attach_policy_to_role(client, RoleName):
                if _add_role_to_profile(client, InstanceProfileName, RoleName):
                    return True
                else:
                    return False


def create_instance(client, ec2, instance_name, image_id, key_name, instance_type, security_group, admin_contact):
    try:
        running_instances = client.describe_instances()

        if len(running_instances['Reservations']) > 0:
            for reservations in running_instances['Reservations']:
                for ec2_instance in reservations['Instances']:
                    if ec2_instance['State']['Name'] == 'running':
                        for tag in ec2_instance['Tags']:
                            if 'Name' in tag['Key'] and instance_name == tag['Value']:
                                print('[***] An instance named {} already exists. Stopping the deployment of Gophish. \n      Rename the existing instance or provide the a differnat InsstanceName argument.'.format(instance_name))
                                return False

        if admin_contact is None:
            admin_contact = 'No Admin Contact Provided'

        instance = ec2.create_instances(
            ImageId=image_id,
            MinCount=MinCount,
            MaxCount=MaxCount,
            KeyName=key_name,
            InstanceType=instance_type,
            SecurityGroups=[security_group],
            TagSpecifications=[
                {'ResourceType': 'instance',
                                  'Tags': [
                                      {'Key': 'Name', 'Value': instance_name},
                                      {'Key': 'admin_contact', 'Value': admin_contact},
                                      {'Key': 'service_id', 'Value': instance_name},
                                      {'Key': 'service_data', 'Value': 'env=Dev'}
                                  ]
                }])[0]

        print('[*] A new EC2 Instance is being spun up')
        new_instance = ec2.Instance(instance.id)
        new_instance.wait_until_running()
        print('[*] The instance is up and running. Waiting for checks to complete.')

        client.associate_iam_instance_profile(
            IamInstanceProfile = {'Arn': 'arn:aws:iam::054732315499:instance-profile/{}InstanceProfile'.format(instance_name),
                                  'Name': '{}Role'.format(instance_name)},
            InstanceId=instance.id)
        print('[*] Added the required permissions to allow SSM')

        print('[*] Waiting for the instance to finish starting up')
        waiter = client.get_waiter('instance_status_ok')
        waiter.wait(InstanceIds=[new_instance.id])
        print('[*] The new Instance ({}) is now ready to go'.format(instance.id))

        return instance.id

    except Exception as e:
        if 'InvalidKeyPair.NotFound' in str(e):
            print('[***]No Key Pair named {} was found. Please create this Key Pair first and store the keys safely.'.format(key_name))
            return False
        else:
            print('[***] Failed to create Instance: {}'.format(e))
            return False


def execute_commands_on_instance(client, Commands, Instance):
    try:
        print('[*] Preparing to install Gophish')
        response = client.send_command(
            DocumentName="AWS-RunShellScript",
            Parameters={'commands': Commands},
            InstanceIds=Instance,
            )

        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            print('[*] The Gophish installation has started')
        else:
            print('[***] Failed to install Gophish: {}'.format(command))
            return False

        if _check_command_status(client, response['Command']['CommandId']) == None:
            print('[*] The Gophish installation has completed')
            return True
        else:
            return False


    except Exception as e:
        print('[***] Failed to execute commands: {}'.format(e))
        return False


def main(args):
    client_ec2 = boto3.client('ec2', region_name=args.Region)
    client_iam = boto3.client('iam', region_name=args.Region)
    client_ssm = boto3.client('ssm', region_name=args.Region)
    ec2 = boto3.resource('ec2', region_name=args.Region)

    SecurityGroup = '{}Group'.format(args.InstanceName)
    KeyName = '{}Key'.format(args.InstanceName)

    if create_key_pairs(client_ec2, KeyName):
        if create_secutiry_groups(client_ec2, SecurityGroup, args.InstanceName):
            if create_iam_profile(client_iam, args.InstanceName):
                instance = create_instance(client_ec2, ec2, args.InstanceName, args.ImageId, KeyName, args.InstanceType, SecurityGroup, args.AdminContact)
                if instance:
                    instance = instance.split(',')
                    if execute_commands_on_instance(client_ssm,
                                                           ['git clone https://github.com/Status-418/gophish-aws-deploy.git',
                                                            'cd gophish-aws-deploy/tools',
                                                            'sudo bash install.sh'
                                                           ],
                                                           instance):
                        public_ip = client_ec2.describe_instances(InstanceIds=instance)['Reservations'][0]['Instances'][0]['PublicIpAddress']
                        print('[*] The setup of Gophish is complete please try connecting to the admin pannel: https://{}:3333'.format(public_ip))


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--InstanceName', required=True, help='Provide the name of the instance you want to stand up')
    parser.add_argument('--Region', default='us-west-1', help='Provide the Region to be used (Default: us-west-1)')
    parser.add_argument('--InstanceType', default='t2.micro', help='Provide the type of the instance you want to stand up (Default: t2.micro)')
    parser.add_argument('--ImageId', default='ami-4aa04129', help='Provide the ImageID for the image you want to deploy (Default: ami-4aa04129)')
    parser.add_argument('--AdminContact', help='Provide the project admin account email address')
    args = parser.parse_args()

    main(args)

