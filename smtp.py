# -*- coding: utf-8 -*-


### Libraries

# For JSON operations
import json

# For logging
import logging

# For performing datetime operations
from datetime import datetime
import time

# For adding the system path
import os
import sys

# For SMTP operations
import smtplib

# For performing email operations
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

# For API operations
import requests

# For performing file operations
import glob
import base64

# For suppressing warnings
import warnings
warnings.filterwarnings("ignore")

# Add the parent directory containing the "bin" directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

class SMTP:
    def __init__(self):
        """
        Initializes the SMTP object with configuration from a dictionary.

        This method reads SMTP server details such as server address, port, 
        user credentials, API key and API endpoints from a dictionary. It 
        also sets up logging for SMTP activities.
        
        Returns
        -------
        None
        """
        # Load the required configurations
        self.load_configs()
    
    def load_configs(self):
        """
        Load essential configurations including server address, port, 
        user credentials, API key, API endpoints and log folder from a dictionary.
        
        Attributes:
        ----------
        smtp_server : str
            The SMTP server address.
        smtp_port : int
            The port number to connect to the SMTP server.
        smtp_user : str
            The username to log in to the SMTP server.
        smtp_password : str
            The password to log in to the SMTP server.
        api_key : str
            The key for the Netcore Web API.
        api_endpoint : str
            The API endpoint for sending mails via Netcore Web API.
        max_retries : int
            The maximum attempts for sending a mail.
        retry_delay : int
            The delay in seconds, before re-attempting to send a mail.
        attachment_folder: str
            The folder path where attachments will be stored.
        log_folder : str
            The folder path where log files will be stored.
        logging : logging.Logger
            Configured logging instance for tracking mails.

        Returns
        -------
        None
        """
        # Read the JSON file
        with open(r"../configs/smtp_configs.JSON", "r") as file:
            smtp_configs = json.load(file)
        
        # Load TCP configurations
        self.smtp_server = smtp_configs["smtp_server"]
        self.smtp_port = smtp_configs["smtp_port"]
        self.smtp_user = smtp_configs["smtp_user"]
        self.smtp_password = smtp_configs["smtp_password"]
        
        # Load Web API configurations
        self.api_key = smtp_configs["api_key"]
        self.api_endpoint = smtp_configs["api_endpoint"]
        self.max_retries = smtp_configs["max_retries"]
        self.retry_delay = smtp_configs["retry_delay_in_seconds"]
        self.attachment_folder = smtp_configs["attachment_folder"]
        
        # Load logging configurations 
        self.log_folder = smtp_configs["log_folder"]
        self.configure_logging()
        
        return
    
    def configure_logging(self):
        """
        Set up a logging system to monitor mail operations.

        Returns
        -------
        None
        """
        # Create a logger for the SMTP class
        self.logging = logging.getLogger("SMTPLogging")
        self.logging.setLevel(logging.INFO)
        
        # Create a file handler to log messages to a file
        file_handler = logging.FileHandler(f"{self.log_folder}/log_SMTP_{datetime.now().date()}.log")
        formatter = logging.Formatter("%(asctime)s-%(levelname)s-%(message)s")
        file_handler.setFormatter(formatter)
        self.logging.addHandler(file_handler)
        
        return
    
    def send_email_via_tcp(self, sender_email, sender_name, receiver_emails, cc_emails, subject, body=None, attachments=None):
        """
        Sends an email via TCP to a list of recipients with optional HTML content and attachments.
        
        Parameters
        ----------
        sender_email : str
            The email address of the sender.
        sender_name : str
            The name of the sender.
        receiver_emails : list of dict
            List of recipient details, each as a dictionary with "email" and optionally "name".
        cc_emails: list of dict
            List of cc'd recipient details, each as a dictionary with "email".
        subject : str
            The subject of the email.
        body : str
            The HTML content of the email.
        attachments : list of dict, optional
            List of attachments, each as a dictionary with "name" and "path".
        -------
        None
        """
        try:
            # Create a multipart message
            msg = MIMEMultipart()
            msg["From"] = f"{sender_name} <{sender_email}>"
            msg["Subject"] = subject

            # Prepare the 'To' and 'Cc' email addresses
            to_addresses = [r["email"] for r in receiver_emails] if receiver_emails else []
            cc_addresses = [cc["email"] for cc in cc_emails] if cc_emails else []
            msg["To"] = ", ".join(to_addresses)
            msg["Cc"] = ", ".join(cc_addresses)

            # Attach the HTML content in the body
            if body:
                msg.attach(MIMEText(body, "html"))

            # Attach files if provided
            if attachments:
                for attachment in attachments:
                    if "path" in attachment and os.path.exists(attachment["path"]):
                        try:
                            # Open the file in binary mode
                            with open(attachment["path"], "rb") as attachment_file:
                                part = MIMEBase("application", "octet-stream")
                                part.set_payload(attachment_file.read())

                            # Encode the file to be safe for email transfer
                            encoders.encode_base64(part)
                            part.add_header(
                                "Content-Disposition",
                                f"attachment; filename={attachment['name']}",
                            )

                            # Attach the file to the message
                            msg.attach(part)
                        except Exception as e:
                            self.logging.error(f"Could not attach file {attachment['path']}: {e}")

            # Connect to the SMTP server
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Secure the connection
                server.login(self.smtp_user, self.smtp_password)  # Log in to the server
                server.sendmail(
                    sender_email, 
                    to_addresses + cc_addresses, 
                    msg.as_string()
                )  # Send the email to all recipients
                self.logging.info(f"OrderLogs Email sent successfully from {sender_email} to {', '.join(to_addresses)} with CC to {', '.join(cc_addresses)}. (via TCP) ")

        except smtplib.SMTPException as e:
            self.logging.error(f"SMTP error occurred while sending orderlogs email: {e}")

        except Exception as e:
            self.logging.error(f"Error occurred while sending orderlogs email: {e}")

        finally:
            self.logging.info("SMTP process completed.")


            
    def send_email_via_api(self, sender_email, sender_name, receiver_emails, cc_emails, subject, body, attachments=None):
        """
        Sends an email using Netcore API with provided sender, receiver, 
        and content details.

        Parameters
        ----------
        sender_email : str
            The email address of the sender.
        sender_name : str
            The name of the sender.
        receiver_emails : list of dict
            List of recipient details, each as a dictionary with "email" and optionally "name".
        cc_emails: list of dict
            List of cc'd recipient details, each as a dictionary with "email".
        subject : str
            The subject of the email.
        body : str
            The HTML content of the email.
        attachments : list of dict, optional
            List of attachments, each as a dictionary with "name" and "path".

        Returns
        -------
        dict
            API response as a JSON dictionary.
        """
        # Create email content structure
        data = {
            "from": {"email": sender_email, "name": sender_name},
            "subject": subject,
            "content": [{"type": "html", "value": body}],
            "personalizations": [
                {
                    "to": receiver_emails,
                    "cc": cc_emails
                }
            ]
        }

        # Add attachments if provided
        if attachments:
            data["attachments"] = []
            for attachment in attachments:
                if os.path.exists(attachment["path"]):
                    self.logging.info(f"Found attachment {attachment['path']}.")
                    try:
                        with open(attachment["path"], "rb") as f:
                            file_content = f.read()
                            encoded_content = base64.b64encode(file_content).decode("utf-8")
                            self.logging.info(f"Encoded content length for {attachment['name']} is {len(encoded_content)}.")
                        data["attachments"].append({
                            "name": attachment["name"],
                            "content": encoded_content
                        })
                    except Exception as e:
                        self.logging.error(f"Error reading or encoding attachment {attachment['path']}: {e}")

        # Create the authentication header
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "api_key": self.api_key
        }

        # Send email request with retries
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    self.api_endpoint,
                    headers=headers,
                    json=data,
                    verify=False,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
                
                # After successful delivery of email delete attachments 
                if result.get("status") == "success":
                    # Remove temp files
                    temp_files = glob.glob(os.path.join(self.attachment_folder, "*"))
                    for temp_file in temp_files:
                        try:
                            os.remove(temp_file)
                            self.logging.info(f"Removed attached file: {temp_file}")
                        
                        except Exception as e:
                            self.logging.error(f"Error removing attached file {temp_file}: {e}")
                
                self.logging.info(f"Orderlogs Email sent successfully, response: {result}")
                return result
            
            except requests.exceptions.RequestException as e:
                self.logging.error(f"Attempt {attempt} failed to send email: {e}")
                if attempt < self.max_retries:
                    self.logging.info(f"Retrying in {self.retry_delay} seconds.")
                    time.sleep(self.retry_delay)
                    
            self.logging.info("SMTP process completed.")
            
        return {"status": "error", "message": f"Failed to send orderlogs email after maximum {self.max_retries} attempts."}