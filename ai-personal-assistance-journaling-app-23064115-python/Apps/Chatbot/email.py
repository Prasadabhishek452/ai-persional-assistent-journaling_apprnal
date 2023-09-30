import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
from .models import MyUser
import random

from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

def send_otp_email(email, otp, user_name):
    subject = "Mobiloitte Journal A.I - Password Reset OTP"
    template_path = 'email-verify-otp.html'

    try:
        message = render_to_string(template_path, {'otp': otp,'user_name':user_name })
        msg = EmailMultiAlternatives(subject, '', settings.EMAIL_HOST_USER, [email])
        msg.attach_alternative(message, "text/html")
        msg.send()
    except Exception as e:
        print("Error: unable to send email:", e)
        return False
    
    return True


def send_otp_reset_password(email, otp, user_name):
    subject = "Mobiloitte Journal A.I - Password Reset OTP"
    template_path = 'forget-password-otp.html'

    try:
        message = render_to_string(template_path, {'otp': otp,'user_name':user_name })
        msg = EmailMultiAlternatives(subject, '', settings.EMAIL_HOST_USER, [email])
        msg.attach_alternative(message, "text/html")
        msg.send()
    except Exception as e:
        print("Error: unable to send email:", e)
        return False
    
    return True