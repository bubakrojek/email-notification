import email
import imaplib
import time
from email.header import decode_header
from email.utils import  parseaddr
from dotenv import load_dotenv
import os

from winotify import Notification

import json

load_dotenv()

def load_history():

    path=os.environ.get('mail_list')

    if os.path.exists(path):
        with open(path,'r') as f:
            try:
                return set(json.load(f))
            except json.JSONDecodeError:
                return set()
    return set()

def save_history(id_set):
    path = os.environ.get('mail_list')

    with open(path, 'w') as f:
        json.dump(list(id_set),f)



def get_emails():
    with imaplib.IMAP4_SSL('poczta.o2.pl',993) as server:

        server.login(os.environ.get('email'),os.environ.get('password'))
        server.select("INBOX")

        status, messages = server.uid('search',None,"ALL")
        ids=messages[0].split()

        messages=[]
        current_ids=load_history()
        if ids:
            for latest_id in reversed(ids[-10:]):
                if latest_id.decode() not in current_ids:
                    status, data = server.uid('fetch',latest_id,"(RFC822)")

                    for response_part in data:
                        if isinstance(response_part,tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject =decode_header(msg["Subject"])[0][0]
                            if isinstance(subject,bytes):
                                subject = subject.decode()

                            messages.append({
                                'sender':parseaddr(msg.get("From"))[0],
                                'subject':subject
                            })
            save_history([coded_id.decode() for coded_id in ids])

        server.logout()
        return messages if messages else None

def show_notifications():
    emails = get_emails()
    if emails:

        concatenated_emails=[f'{email.get("sender")}: {email.get("subject")}' for email in emails]
        joined_emails="\n".join(concatenated_emails)

        for email in emails[:5]:
            print(email)
            toast=Notification(
                app_id="Notifier",
                title=email.get("sender"),
                msg=email.get("subject"),
                duration="long"
            )
            toast.show()
            time.sleep(2)


if __name__=="__main__":
    show_notifications()