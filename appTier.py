import boto3
import time
import os
import subprocess
import base64,json

sqs_client = boto3.client('sqs', region_name='us-east-1')
s3_client = boto3.client('s3')
response_queue_url = 'https://sqs.us-east-1.amazonaws.com/830292860456/1230531746-resp-queue'
request_queue_url = 'https://sqs.us-east-1.amazonaws.com/830292860456/1230531746-req-queue'

input_bucket_name = '1230531746-in-bucket'
output_bucket_name = '1230531746-out-bucket'

#func to calssify face rec
def call_face_recognition_script(image_path):
    script_path = os.path.join('model', 'face_recognition.py')

    # start classifying
    command = ["python3", script_path, image_path]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode == 0:
        matched_name = result.stdout.strip()
        print(matched_name)
        return matched_name
    else:
        error_message = result.stderr.strip()
        print(f"Error in face recognition script: {error_message}") 
        return "Error"

#main func
def process_requests():
    image_folder_path = "face_images_1000/face_images_1000"
    while True:
        messages = sqs_client.receive_message(
            QueueUrl=request_queue_url,
            MaxNumberOfMessages=3,
            WaitTimeSeconds=20,
            VisibilityTimeout=30
        )

        if 'Messages' in messages:
            
            for message in messages['Messages']:
                body = json.loads(message['Body'])
                image_name = body['filename']
                encoded_content = body['content']

                # decode image content
                image_data = base64.b64decode(encoded_content)
                image_path = os.path.join(image_folder_path, image_name)

                s3_client.put_object(Bucket=input_bucket_name, Key=image_name, Body=image_data)

                # call script to classify
                image_path = os.path.join(image_folder_path, image_name)
                matched_name = call_face_recognition_script(image_path)

                s3_client.put_object(Bucket=output_bucket_name, Key=f"{image_name}_result.txt", Body=matched_name)

                response_message = f"{image_name}:{matched_name}"
                print(response_message)
                sqs_client.send_message(QueueUrl=response_queue_url, MessageBody=response_message)

                # delete from req queue
                sqs_client.delete_message(
                    QueueUrl=request_queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
        time.sleep(1)

if __name__ == "__main__":
    process_requests()
