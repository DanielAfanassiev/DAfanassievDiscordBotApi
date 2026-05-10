from helpers import *
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from get_keys import get_key, get_api_key_dir

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_service():
    creds = None

    if os.path.exists(f'{get_api_key_dir()}/token.json'):
        creds = Credentials.from_authorized_user_file(f'{get_api_key_dir()}/token.json', SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    elif not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(
            f'{get_api_key_dir()}/client_secret_{get_key("googlecalci")}.json', SCOPES)
        creds = flow.run_local_server(port=0)

        with open(f'{get_api_key_dir()}/token.json', 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

def add_event(name, start_time, description, end_time = None):
    service = get_service()

    if end_time == None:
        end_time = start_time



    event = {
        'summary': name,
        'colorId': '7',
        'start': start_time,
        'end': end_time,
        'visibility': 'private',
        'transparency': 'transparent',
        'description': description
    }

    if not does_event_exist(event):
        event['start'] = {
            'dateTime': timestamp_to_iso(start_time),
            'timeZone': 'America/Toronto',
        },
        event['end'] = {
            'dateTime': timestamp_to_iso(end_time),
            'timeZone': 'America/Toronto',
        }

        log(f"Adding cs2 match {name} {start_time} {description}")
        
        created_event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()
        log("Event created:" + created_event.get('htmlLink'))

    else:
        log(f"Match {name} on {datetime.datetime.fromtimestamp(start_time).strftime("%d/%m/%Y %H:%M:%S")} already exists in calendar")

def get_events():
    service = get_service()

    current_time = datetime.datetime.now(datetime.timezone.utc)
    one_day_ago = current_time - datetime.timedelta(days=1)

    events_result = service.events().list(
        calendarId='primary',
        timeMin = one_day_ago.isoformat(),
        orderBy = 'startTime',
        singleEvents = True,
        eventTypes = "default"
    ).execute()

    return events_result['items']

def filter_events(events):
    events_to_remove = []
    events_to_return = []
    for event in events:
        if 'eventType' in event and event['eventType'] == 'workingLocation':
            events_to_remove.append(event)

        if event['status'] == 'cancelled':
            events_to_remove.append(event)

    for event in events:
        if not event in events_to_remove:
            events_to_return.append(event)

    return events_to_return

def does_event_exist(event_to_add):
    existing_events = get_events() # Gets all events after 24 hours ago
    for event in existing_events:
        try:
            dt = datetime.datetime.fromisoformat(event['start']['dateTime'])
            timestamp = int(dt.timestamp())
            summary_same = event_to_add['summary'] == event['summary']
            description_same = event_to_add['description'] == event['description']
            time_start_same = timestamp == event_to_add['start']

            if summary_same and description_same and time_start_same:
                return True
        except:
            pass
    return False

def to_utc(dt_str):
    return datetime.datetime.fromisoformat(dt_str).astimezone(datetime.timezone.utc)

def timestamp_to_iso(timestamp):
    return datetime.datetime.fromtimestamp(timestamp).isoformat()