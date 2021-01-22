import os
from flask import Flask, request, redirect, url_for
from azure.storage.blob import BlockBlobService
import string, random, requests
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from googletrans import Translator
from array import array
import os
from PIL import Image
import sys
import time

translator = Translator()
subscription_key = "Azure CV Subscription Key"
endpoint = "Azure CV Endpoint"

computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

app = Flask(__name__, instance_relative_config=True)

account = 'Storage Account Name'  # Azure account name
key = 'Key'  # Azure Storage account access key
container = 'Container'  # Container name

blob_service = BlockBlobService(account_name=account, account_key=key)


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        file = request.files['file']
        filename = file.filename
        fileextension = filename.rsplit('.', 1)[1]
        filename = filename
        try:
            blob_service.create_blob_from_stream(container, filename, file)
        except Exception:
            print('Exception=' + Exception)
            pass
        ref = 'https://' + account + '.blob.core.windows.net/' + container + '/' + filename
        recognize_handw_results = computervision_client.read(ref,  raw=True)
        operation_location_remote = recognize_handw_results.headers["Operation-Location"]
        operation_id = operation_location_remote.split("/")[-1]
        while True:
            get_handw_text_results = computervision_client.get_read_result(operation_id)
            if get_handw_text_results.status not in ['notStarted', 'running']:
                break
            time.sleep(1)

        lines = []
        # Print the detected text, line by line
        if get_handw_text_results.status == OperationStatusCodes.succeeded:
            for text_result in get_handw_text_results.analyze_result.read_results:
                for line in text_result.lines:
                    lines.append(line.text)
        newtext = ''
        translations = translator.translate(lines, dest='en')
        for translation in translations:
            print(translation.origin, ' -> ', translation.text)
            newtext = newtext + '\n' + translation.text

        return '''
        <!doctype html>
        <title>Translation</title>
        <h1>Translation to english</h1>
        <p>''' + newtext + '''</p>
        '''
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form action="" method=post enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''


if __name__ == '__main__':
    app.run(debug=True)
