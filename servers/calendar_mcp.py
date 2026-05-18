from fastmcp import FastMCP
import datetime
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
CREDENTIALS_FILE = "config/gc_client.json"
TOKEN_FILE = "config/token.json"

mcp = FastMCP("calendar")

def get_calendar_service():
    """Authenticate and return a Google Calendar service instance."""
    creds = None

    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)

@mcp.tool()
async def get_todays_events() -> str:
    """Get all events from Google Calendar for today."""

    service = get_calendar_service()

    now = datetime.datetime.utcnow()
    start_of_day = now.replace(hour=0, minute=0, second=0).isoformat() + "Z"
    end_of_day = now.replace(hour=23, minute=59, second=59).isoformat() + "Z"

    events_result = service.events().list(
        calendarId="primary",
        timeMin=start_of_day,
        timeMax=end_of_day,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = events_result.get("items", [])

    if not events:
        return "No events scheduled for today."

    lines = ["Your events today:\n"]
    for e in events:
        start = e["start"].get("dateTime", e["start"].get("date", ""))
        if "T" in start:
            time = start[11:16]
        else:
            time = "All day"
        title = e.get("summary", "No title")
        lines.append(f"- {time} {title}")

    return "\n".join(lines)

if __name__ == "__main__":
    mcp.run()
