"""A script to get the status of USCIS using receipt number"""

import smtplib
from dataclasses import dataclass
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path
from typing import Tuple

import requests
from lxml import html


@dataclass
class UscisData:
    id: str     # Uscis receipt number
    email: str  # Receiving email


@dataclass
class Credential:
    email: str
    password: str


@dataclass
class Email:
    subject: str
    content: str
    to_email: str
    from_email: str


DATA = {
    "charles": UscisData("WACXXXXXXXXXX", "your_email@email.com"),
}


def read_cred(path: Path) -> Credential:
    """Read email and password from given text file location"""
    data = path.read_text().split("\n")
    return Credential(*data)


def extract_status(url: str) -> Tuple[str, str]:
    """Scrape status and its description from USCIS site"""
    r = requests.get(url)
    tree = html.fromstring(r.content)
    status = tree.find_class("current-status-sec")[0].text_content().strip().split("\n\t")
    status = [s.strip() for s in status][1]

    desc = tree.find_class("rows text-center")[0].text_content().strip().split("\n\t")
    desc = [d.strip() for d in desc][1]
    return status, desc


def create_msg(email: Email) -> EmailMessage:
    """Creates email message"""
    msg = EmailMessage()
    msg["Subject"] = email.subject
    msg["From"] = email.from_email
    msg["To"] = email.to_email

    msg.set_content(email.content)
    return msg


def send_email(msg: EmailMessage, creds: Credential) -> None:
    """Send email using smtp
    Future scope: Create smtp server on Raspberry Pi
    """
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(creds.email, creds.password)
        smtp.send_message(msg)


def main(email: bool = False) -> None:
    """Main
    Example: https://egov.uscis.gov/casestatus/mycasestatus.do?appReceiptNum=WACXXXXXXXXXX
    """

    for name, data in DATA.items():
        url = f"https://egov.uscis.gov/casestatus/mycasestatus.do" \
              f"?appReceiptNum={data.id}"

        status, desc = extract_status(url)
        print(name.title(), data.id, status, desc)

        if email:
            creds = read_cred(Path(".variables"))
            msg = create_msg(Email(f"USCIS Status: {status}", desc, data.email, creds.email))
            send_email(msg, creds)
            print(f"Status: {status} | Email sent successfully on {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}")


if __name__ == '__main__':
    main(email=False)
