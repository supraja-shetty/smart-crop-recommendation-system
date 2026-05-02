import smtplib
from email.message import EmailMessage
from config import Config
import os

def send_email(to_email, crop, top3, pdf):
    print("📧 MOCK EMAIL SENT")
    print("To:", to_email)
    print("Crop:", crop)
    print("Top3:", top3)
    print("PDF:", pdf)