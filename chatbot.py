from flask import Flask, request
import re
from twilio.twiml.messaging_response import MessagingResponse, Message
from twilio.rest import Client
import urllib

import yaml

with open("config.yaml", 'r') as stream:
    try:
        config = yaml.load(stream)
    except yaml.YAMLError as exc:
        print(exc)

account_sid = config['twilio']['account_sid']
auth_token = config['twilio']['auth_token']
from_number = config['numbers']['from']
phone_number = config['numbers']['to']
doctor_phone_number = config['numbers']['doctor']
client = Client(account_sid, auth_token)
app = Flask(__name__)

class Patient:
    def __init__(self, age, name, cancer_type, day_of_treatment):
        self.day_of_treatment = day_of_treatment
        self.name = name
        self.age = age
        self.cancer_type = cancer_type

patient = Patient(config['sample_patient']['age'],
                  config['sample_patient']['name'],
                  config['sample_patient']['cancer_type'],
                  config['sample_patient']['day_of_treatment'])

print(f'Patient data: {patient.name}, {patient.age} y/o, {patient.cancer_type}')
# Initial greeting
client.messages.create(body=config['messages']['day_1_greeting'],
                       from_=from_number,
                       to=phone_number)
print('Initial greeting sent')

@app.route('/sms', methods=['POST'])
def inbound_sms():
    answer = urllib.parse.quote(request.form['Body'])
    print(f'day: {patient.day_of_treatment} received: {answer}')
    response = MessagingResponse()

    if patient.day_of_treatment == 1:
        if (re.match(r'^[1-5]$', answer) and int(answer) == 5):
            response.message(config['messages']['day_1_answers'][0])
        elif re.match(r"\d+\.\d+", answer): # Match float (temp)
            response.message(config['messages']['day_1_answers'][1])
            patient.day_of_treatment = patient.day_of_treatment + 1
    elif patient.day_of_treatment == 2:
        if (re.match(r'^[1-5]$', answer) and int(answer) == 2):
            response.message(config['messages']['day_2_answers'][0])
        elif re.match(r"\d+\.\d+", answer): # Match float (temp)
            response.message(config['messages']['day_2_answers'][1])
        else:
            # Send message to doctor
            client.messages.create(body=f'{patient.name}, {patient.age} y/o, ' \
               f'with a {patient.cancer_type} has a MASCC score below threshold',
                                   from_=from_number,
                                   to=doctor_phone_number)
            response.message(config['messages']['day_2_answers'][2])

    print('replied %s ' % str(response))
    return str(response)
