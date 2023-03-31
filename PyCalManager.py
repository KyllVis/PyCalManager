import base64
import os.path
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
import pytz
from datetime import datetime, time, timedelta

#PROVIDE details about the account that will run the program from
#Email , #timezone (For specific timezone format see https://stackoverflow.com/questions/22526635/list-of-acceptable-google-calendar-api-time-zones
#Timezone shortened format, standard
my_email = "kyll.hutchens@gmail.com"
timezone = 'Australia/Sydney'
timezonesymb = 'AEDT'


# Set up scopes and credentials for Gmail API

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
creds = None
# Load or refresh credentials

if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
email_body = []
to_email = ""
from_email = ""

# Read the latest email sent to the specified email address
try:
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', maxResults=1, q=f"to:{my_email}").execute()
    messages = results.get('messages', [])
    # Parse email contents
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        payload = msg['payload']
        headers = payload['headers']
        if 'data' in payload['body']:
            body = payload['body']['data']
        else:
            parts = payload['parts']
            body = None
            for part in parts:
                if 'mime' in part and part['mime'] == 'text/plain':
                    body = part['body']['data']
                    break
                elif 'mime' in part and part['mime'] == 'text/html':
                    body = part['body']['data']
                    break
            if not body:
                for part in parts:
                    if 'body' in part and 'data' in part['body']:
                        body = part['body']['data']
                        break

        for header in headers:
            if header['name'] == 'To':
                to_email = header['value']
            elif header['name'] == 'From':
                from_email = header['value']
        if body:
            body = base64.urlsafe_b64decode(body).decode()
            email_body = body
        else:
            print("No body found")


except HttpError as error:
    print(f'An error occurred: {error}')

# Extract appointment details from the email
email = body

# Extract name of client
name = re.search(r'Name:\s*(\w+)', email).group(1)

# Extract new client status
new_client = re.search(r'New Client:\s*(\w+)', email).group(1)

# Extract date of appointment
date = re.search(r'Date of Appointment:\s*(\d{1,2}/\d{1,2}/\d{4})', email).group(1)

# Extract time of appointment
time = re.search(r'Time of Appointment:\s*([^\n]+)', email).group(1)

type = re.search(r'Appointment Type:\s*(\w+)', email).group(1)
client_email = re.search(r'[\w\.-]+@[\w\.-]+', from_email).group(0)

day = date.split("/")[0]
month = date.split("/")[1]
year = date.split("/")[2]
day = int(day)
month = int(month)
year = int(year)

# Fix up the date and time structures

try:
    time = time.strip()
    if time[-2] in ['A', 'P']:
        time = time[:-2] + ' ' + time[-2:]
    print(time)
    time_obj = datetime.strptime(time, "%I:%M %p")
    time_obj = time_obj.strftime('%H:%M')
    print(time_obj)
except:
    time_obj = datetime.strptime(time, "%H:%M")
    time_obj = datetime.strftime(time_obj, '%H:%M')

timezonesymb = pytz.timezone('Australia/Sydney')  # Create a timezone object for AEDT

#THIS SESSION TIME IS A FIXED VALUE. Consider uploading a table of types of appointments and allocated session times.
session_time = 1

new_time_obj = datetime.strptime(time_obj, "%H:%M") + timedelta(hours = session_time)
new_time_str = new_time_obj.time()


# Set up scopes and credentials for Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
creds2 = None

if os.path.exists('token2.json'):
    creds2 = Credentials.from_authorized_user_file('token2.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
if not creds2 or not creds2.valid:
    if creds2 and creds2.expired and creds2.refresh_token:
        creds2.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds2 = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token2.json', 'w') as token:
        token.write(creds2.to_json())
# If the timeslot is available, create the event in the calendar
service_cal = build('calendar', 'v3', credentials=creds2)
start_time = datetime(year,month,day, int(time_obj.split(':')[0]), int(time_obj.split(':')[1]), tzinfo=timezonesymb)
end_time = datetime(year,month,day, new_time_str.hour, new_time_str.minute, tzinfo=timezonesymb)

str_start_time = datetime(year,month,day, int(time_obj.split(':')[0]), int(time_obj.split(':')[1]))
str_end_time = datetime(year,month,day, new_time_str.hour, new_time_str.minute)
events_result = service_cal.events().list(calendarId='primary', timeMin=start_time.isoformat(), timeMax=end_time.isoformat(), singleEvents=True, orderBy='startTime').execute()
events = events_result.get('items', [])
timeslot_available = []

for event in events:
    start = event['start'].get('dateTime', event['start'].get('date'))
    end = event['end'].get('dateTime', event['end'].get('date'))
    event_start = datetime.fromisoformat(start).astimezone(timezonesymb)
    event_end = datetime.fromisoformat(end).astimezone(timezonesymb)
    if 'summary' in event:
        summary = event['summary']
    else:
        summary = 'No title'
    if event_start <= end_time and start_time <= event_end:
        timeslot_available = False
        print(
            f"Time slot not available: {summary} at {event_start.strftime('%d-%m-%Y %H:%M:%S %Z')} to {event_end.strftime('%d-%m-%Y %H:%M:%S %Z')}")
        break
else:
    print("Time slot is available")
    timeslot_available = True
cal_event = {
        'summary': type,
        'location': "Local Office",
        'description': type,
        'start': {
            'dateTime':(str_start_time + timedelta(hours=0)).isoformat(),
            'timeZone' : timezone,
        },
        'end': {
            'dateTime': (str_start_time + timedelta(hours=1)).isoformat(),
            'timeZone': timezone,
        },
        'reminders': {
            'useDefault':True
        }

    }

if timeslot_available == True:
    event = service_cal.events().insert(calendarId='primary', body=cal_event).execute()
    print('Event created: %s' % (event.get('htmlLink')))

    # Set up scopes and credentials for sending emails
    # If the appointment is created successfully, send a confirmation email

    message = MIMEText(f'Dear {name} \n \n Your appointment for {type} has been created successfully for {date} at {time}. \n we look forward to seeing you then')
    message['to'] = client_email
    message['subject'] = f'Confirmation regarding your appointment for {type}'
    create_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    SCOPES = ['https://www.googleapis.com/auth/gmail.compose']
    creds = None
    if os.path.exists('token3.json'):
        creds = Credentials.from_authorized_user_file('token3.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token3.json', 'w') as token:
            token.write(creds.to_json())

    service3 = build('gmail', 'v1', credentials=creds)
    message = (service3.users().messages().send(userId='me', body=create_message).execute())
    print(F'The message was sent to {name}, APPOINTMENT CREATION SUCCESSFUL')



# If the appointment is not created, send an unsuccessful email
else:

    SCOPES = ['https://www.googleapis.com/auth/gmail.compose']
    creds = None
    if os.path.exists('token4.json'):
        creds = Credentials.from_authorized_user_file('token4.json', SCOPES)
        # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token4.json', 'w') as token:
            token.write(creds.to_json())

    message = MIMEText(
        f'Dear {name} \n \n Your appointment for {type} was unable to be created. Please contact our administration team to create an appointment')
    message['to'] = client_email
    message['subject'] = f'{type} appointment unsuccessfully created'
    create_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}
    service4 = build('gmail', 'v1', credentials=creds)
    message = (service4.users().messages().send(userId='me', body=create_message).execute())
    print(F'The message was sent to {name} APPOINTMENT NOT CREATED')