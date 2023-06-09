import datetime
import dateparser
import spacy
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

nlp = spacy.load("en_core_web_sm")

def get_date_info(question):
    today = datetime.date.today()

    doc = nlp(question)
    date_detected = False
    relative_date_detected = False

    # Dictionary for relative date phrases
    relative_date_phrases = {
        "yesterday": -1,
        "tomorrow": 1,
        "last week": -7,
        "next week": 7,
        "next month": "next_month",
        "last month": "last_month",
    }

    for ent in doc.ents:
        if ent.label_ == "DATE":
            parsed_date = dateparser.parse(ent.text)
            if parsed_date is not None:
                target_date = parsed_date.date()
                date_detected = True
                break

    if not date_detected:
        for phrase, value in relative_date_phrases.items():
            if phrase in question.lower():
                relative_date_detected = True
                if isinstance(value, int):
                    target_date = today + datetime.timedelta(days=value)
                elif value == "next_month":
                    year = today.year
                    month = today.month + 1
                    if month == 13:
                        month = 1
                        year += 1
                    target_date = datetime.date(year, month, today.day)
                elif value == "last_month":
                    year = today.year
                    month = today.month - 1
                    if month == 0:
                        month = 12
                        year -= 1
                    target_date = datetime.date(year, month, today.day)
                break

    if not date_detected and not relative_date_detected:
        print("No Date Info")
        return None

    return f"{target_date.strftime('%A, %B %d, %Y')}."


    # if target_date == today:
    #     return f"Today is {today.strftime('%A, %B %d')}."
    # elif target_date == today + datetime.timedelta(days=1):
    #     return f"Tomorrow is {target_date.strftime('%A, %B %d')}."
    # elif target_date > today and target_date < today + datetime.timedelta(days=7):
    #     return f"{target_date.strftime('%A')} is {target_date.strftime('%B %d')}."
    # elif target_date.month == today.month and target_date.year == today.year:
    #     days_left = (target_date - today).days
    #     return f"There are {days_left} days left until {target_date.strftime('%A, %B %d')}."
    # elif target_date.year == today.year:
    #     return f"{target_date.strftime('%A, %B %d')} is in {target_date.month - today.month} months."
    # else:
    #     return f"{target_date.strftime('%A, %B %d, %Y')} is in {target_date.year - today.year} years."
    
    
def get_calendar_service():
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    SERVICE_ACCOUNT_FILE = 'C:\\Users\\Zeebra\\code\\Key\\speech-381402-70b45c1e2474.json'

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, SCOPES)

    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def create_reminder(title, start_time, calendar_id='primary'):
    service = get_calendar_service()
    if service is None:
        return "Failed to set reminder. Please check your credentials."

    event = {
        'summary': title,
        'start': {
            'dateTime': start_time.isoformat(),
            'timeZone': 'UTC',  # Change this to the appropriate timezone
        },
        'end': {
            'dateTime': (start_time + datetime.timedelta(minutes=15)).isoformat(),
            'timeZone': 'UTC',  # Change this to the appropriate timezone
        },
        'reminders': {
            'useDefault': True
        },
    }

    try:
        event = service.events().insert(calendarId=calendar_id, body=event).execute()
        return f'Reminder created: {event["summary"]} on {event["start"]["dateTime"]}'
    except HttpError as error:
        print(f'An error occurred: {error}')
        return "Failed to set reminder."