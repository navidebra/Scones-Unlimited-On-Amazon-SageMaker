"""
Lambda Function 1: serialize Image Data

A Lambda function that retrieves an object from S3, encodes it in base64, and returns the serialized data as image_data within an event to the step function.
"""

import json
import boto3
import base64

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """A function to serialize target data from S3"""

    # Get the s3 address from the Step Function event input
    key = event['s3_key']
    bucket = event['s3_bucket']

    # Download the data from s3 to /tmp/image.png
    s3.download_file(bucket, key, "/tmp/image.png")

    # We read the data from a file
    with open("/tmp/image.png", "rb") as f:
        image_data = base64.b64encode(f.read())

    # Pass the data back to the Step Function
    print("Event:", event.keys())
    return {
        'statusCode': 200,
        'body': {
            "image_data": image_data,
            "s3_bucket": bucket,
            "s3_key": key,
            "inferences": []
        }
    }

"""
Lambda Function 2: Image Classification

A Lambda function responsible for the classification task. It takes the image output from the first Lambda function, decodes it, and then returns the inferences back to the Step Function.
"""

import json
import sagemaker
import base64
from sagemaker.serializers import IdentitySerializer

runtime_client = boto3.client('sagemaker-runtime')

# Fill this in with the name of your deployed model
ENDPOINT = "image-classification-2024-08-11-12-33-27-056"

def lambda_handler(event, context):

    # Decode the image data
    image = base64.b64decode(event['image_data'])

    # Instantiate a Predictor
    predictor = runtime_client.invoke_endpoint(
                                        EndpointName=ENDPOINT,    # Endpoint Name
                                        Body=image,               # Decoded Image Data as Input (class:'Bytes') Image Data
                                        ContentType='image/png'   # Type of inference input data - Content type (Eliminates the need of serializer)
                                    )

    # For this model the IdentitySerializer needs to be "image/png"
    predictor.serializer = IdentitySerializer("image/png")

    # Make a prediction:
    inferences = json.loads(response['Body'].read().decode('utf-8'))

    # We return the data back to the Step Function    
    event["inferences"] = inferences.decode('utf-8')
    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }

"""
Lambda Function 3: Low Confidence Filter Inferences

A Lambda function that filters the inferences from the output of the second Lambda function, retaining only those with confidence levels above a specified threshold, indicating success.
"""

import json


THRESHOLD = .9


def lambda_handler(event, context):
    
    # Grab the inferences from the event
    inferences = event['inferences']
    
    # Check if any values in our inferences are above THRESHOLD
    meets_threshold = max(inferences) > THRESHOLD
    
    # If our threshold is met, pass our data back out of the
    # Step Function, else, end the Step Function with an error
    if meets_threshold:
        pass
    else:
        raise("THRESHOLD_CONFIDENCE_NOT_MET")

    return {
        'statusCode': 200,
        'body': json.dumps(event)
    }