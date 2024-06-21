from flask import Flask, request
import boto3
import time
import threading
import base64,json

app = Flask(__name__)

sqs_client = boto3.client('sqs', region_name='us-east-1')
ec2_client = boto3.client('ec2', region_name='us-east-1')


request_queue_url = 'https://sqs.us-east-1.amazonaws.com/830292860456/1230531746-req-queue'
response_queue_url = 'https://sqs.us-east-1.amazonaws.com/830292860456/1230531746-resp-queue'
ami_id = 'ami-0109e86258c36cf6c' 
instance_type = 't2.micro' 
security_group_ids = ['sg-0db7e1ae935e44d7c']  
key_name = 'my_key_pair'  
user_data_script = """#!/bin/bash
cd /home/ubuntu
sudo pip3 install boto3
sudo -u ubuntu python3 /home/ubuntu/appTier.py""" 

max_instances = 20  
cooldown_period = 10  
instances_needed = 0
active_instance_ids = []
check=[]
instance_counter=0
request_counter = 0  
response_counter = 0
c=0

#scaleup logic
def scale_up():
    global active_instance_ids
    global instance_counter
    global check

    instance_counter += 1
    instance_name = f"app-tier-instance-{instance_counter}"

    instance = ec2_client.run_instances(
        ImageId=ami_id,
        InstanceType=instance_type,
        KeyName=key_name,
        SecurityGroupIds=security_group_ids,
        MinCount=1,
        MaxCount=1,
        UserData=user_data_script,
        IamInstanceProfile={
        'Arn': 'arn:aws:iam::830292860456:instance-profile/Project1Part2'
            },
        TagSpecifications=[{
            'ResourceType': 'instance',
            'Tags': [{'Key': 'Name', 'Value': instance_name}],
        }]
    )
    instance_id = instance['Instances'][0]['InstanceId']
    active_instance_ids.append(instance_id)
    # print(f"Launched new app tier instance: {instance_id} with name {instance_name}")
    instance_id = instance_counter
    check.append(instance_id)

#running as background thread checking every 5 sec
def autoscaling_controller():
    global instance_counter
    global check
    global request_counter, response_counter, results_dict
    while True:

        global instances_needed
        length=len(check)

        #making sure max 20 instances launched, and any extra if needed when req messages take time to show
        instances_needed = min(request_counter, max_instances) - len(check)
        # print(f"Instances needed are {instances_needed}")
        # print(f"total running instances are {length}")
        # print(f"messages sent {request_counter}")
        # print(f"messages received {response_counter}")

        if response_counter==0 and instances_needed > 0:
            for  _ in range(instances_needed):
                scale_up()

        if response_counter==request_counter:
            # print(f"instances terminated")
            terminate_all_instances()
            #reset evrything for next requests
            check=[]
            instance_counter=0
            response_counter=0
            request_counter=0
            results_dict={}

        time.sleep(5)  

#terminates all instances
def terminate_all_instances():
    global active_instance_ids
    global c
    if active_instance_ids:
        # print(f"Terminating instances: {active_instance_ids}")
        ec2_client.terminate_instances(InstanceIds=active_instance_ids)
        active_instance_ids.clear()  # Clear the list after terminating
        # print("All instances have been terminated.")

    else:
        print("No active instances to terminate.")

#run autoscaling controller as background thread
threading.Thread(target=autoscaling_controller, daemon=True).start()
request_counter = 0
results_dict={}

@app.route('/', methods=['POST'])
def upload_image():
    global request_counter, response_counter
    if 'inputFile' not in request.files:
        return "Missing inputFile", 400
    file = request.files['inputFile']
    if file.filename == '':
        return "No selected file", 400
    file_content = file.read()
    encoded_content = base64.b64encode(file_content).decode('utf-8')
    
    # Construct message with filename and encoded content
    message = json.dumps({
        'filename': file.filename,
        'content': encoded_content
    })
    #message sent to apptier
    request_counter+=1
    sqs_client.send_message(QueueUrl=request_queue_url, MessageBody=message)
    #background thread to check for messages from apptier
    threading.Thread(target=get_messages, daemon=True).start()
    result=lookup_dict(file.filename)
    #message received from apptier
    response_counter+=1
    return f"{file.filename}: {result}", 200

#lookup filename in dict
def lookup_dict(filename):
    global results_dict
    while True:
        if filename in results_dict.keys():
            return results_dict[filename]
        else:
            time.sleep(0.1)

#run as background thread
def get_messages():
    global results_dict
    while True:
        response = sqs_client.receive_message(
            QueueUrl=response_queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=5,  
            VisibilityTimeout=15
        )
        
        if 'Messages' in response:
            for message in response['Messages']:
                filename, result = message['Body'].split(':')
                results_dict[filename] = result
                if filename in results_dict:
                    result = results_dict[filename]
                    sqs_client.delete_message(
                        QueueUrl=response_queue_url,
                        ReceiptHandle=message['ReceiptHandle']
                        )
                    
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8000)
