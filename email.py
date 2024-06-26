import requests

def send_email_via_postmark(subject, body, recipient):
    url = "https://api.postmarkapp.com/email"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Postmark-Server-Token": "b4458825-787c-48b7-8a80-2ee3405d60a0"
    }
    data = {
        "From": "mashood@altventures.co",  # This must be a verified sender signature in Postmark
        "To": "mashood@altventures.co", #recipient
        "Subject": subject,
        "TextBody": body
    }
    response = requests.post(url, headers=headers, json=data)
    return response.status_code, response.text
