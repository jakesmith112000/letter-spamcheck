#!/usr/bin/env python3
"""
Super Simple Email Sender with SMTP Rotation
"""

import json
import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

class SimpleEmailSender:
    def __init__(self):
        self.load_config()
        self.current_smtp_index = 0
        
    def load_config(self):
        """Load all configuration files with proper encoding"""
        try:
            # Load main config
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # Load SMTP accounts
            with open('smtp_accounts.json', 'r', encoding='utf-8') as f:
                self.smtp_accounts = json.load(f)
            
            # Load email list
            with open('email_list.txt', 'r', encoding='utf-8') as f:
                self.recipients = [line.strip() for line in f if line.strip()]
            
            # Load email content with proper encoding handling
            if self.config['email_type'] == 'html':
                # Try multiple encodings for the HTML file
                encodings = ['utf-8', 'latin-1', 'cp1252']
                for encoding in encodings:
                    try:
                        with open('template.html', 'r', encoding=encoding) as f:
                            self.body = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    # If all encodings fail, read as binary and decode with errors ignored
                    with open('template.html', 'rb') as f:
                        self.body = f.read().decode('utf-8', errors='ignore')
            else:
                with open('plain_text.txt', 'r', encoding='utf-8') as f:
                    self.body = f.read()
                    
        except FileNotFoundError as e:
            print(f"❌ Missing file: {e.filename}")
            raise
        except Exception as e:
            print(f"❌ Error loading configuration: {str(e)}")
            raise
    
    def get_next_smtp(self):
        """Get next SMTP account for rotation"""
        smtp = self.smtp_accounts[self.current_smtp_index]
        self.current_smtp_index = (self.current_smtp_index + 1) % len(self.smtp_accounts)
        return smtp
    
    def get_attachments(self):
        """Get PDF files from attachments folder"""
        attachments = []
        if self.config.get('use_attachments') and os.path.exists('attachments'):
            for file in os.listdir('attachments'):
                if file.lower().endswith('.pdf'):
                    attachments.append(os.path.join('attachments', file))
        return attachments
    
    def send_single_email(self, recipient, smtp_account):
        """Send email to one recipient"""
        try:
            # Create message
            if self.config['email_type'] == 'html':
                message = MIMEMultipart()
                # Use utf-8 encoding for HTML content
                message.attach(MIMEText(self.body, 'html', 'utf-8'))
            else:
                message = MIMEText(self.body, 'plain', 'utf-8')
                message = MIMEMultipart()  # Still use multipart for attachments
                message.attach(MIMEText(self.body, 'plain', 'utf-8'))
            
            # Use custom from email if specified, otherwise use SMTP account email
            from_email = self.config.get('from_email', smtp_account['email'])
            from_name = self.config.get('from_name', 'AOL')
            
            # Format: "Name <email@domain.com>"
            formatted_from = f"{from_name} <{from_email}>"
            message['From'] = formatted_from
            message['To'] = recipient
            message['Subject'] = self.config['subject']
            
            # Add Reply-To header if specified
            if self.config.get('reply_to'):
                message['Reply-To'] = self.config['reply_to']
            
            # Add attachments
            attachments = self.get_attachments()
            for file_path in attachments:
                with open(file_path, 'rb') as file:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(file.read())
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename={os.path.basename(file_path)}'
                )
                message.attach(part)
            
            # Send email
            with smtplib.SMTP(smtp_account['server'], smtp_account['port']) as server:
                server.starttls()
                server.login(smtp_account['email'], smtp_account['password'])
                server.send_message(message)
            
            print(f"✅ Sent to: {recipient} (via {smtp_account['name']}, From: {from_email})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send to {recipient} via {smtp_account['name']}: {str(e)}")
            return False
    
    def send_all_emails(self):
        """Send to all recipients with SMTP rotation"""
        print("🚀 Starting email campaign...")
        print(f"📧 Recipients: {len(self.recipients)}")
        print(f"🎨 Email type: {self.config['email_type']}")
        print(f"📎 Attachments: {'Yes' if self.config.get('use_attachments') else 'No'}")
        print(f"🔄 SMTP Accounts: {len(self.smtp_accounts)} (Auto-rotation)")
        print(f"📨 From Address: {self.config.get('from_email', 'Using SMTP account email')}")
        print("-" * 50)
        
        success_count = 0
        
        for i, recipient in enumerate(self.recipients):
            smtp_account = self.get_next_smtp()
            
            if self.send_single_email(recipient, smtp_account):
                success_count += 1
            
            # Add delay between emails
            delay = self.config.get('delay_between_emails', 2)
            if delay > 0 and i < len(self.recipients) - 1:
                time.sleep(delay)
        
        print("-" * 50)
        print(f"📊 Results: {success_count}/{len(self.recipients)} emails sent successfully!")
    
    def show_config(self):
        """Show current configuration"""
        print("\n📋 CURRENT CONFIGURATION:")
        print(f"   Email Type: {self.config['email_type']}")
        print(f"   Subject: {self.config['subject']}")
        print(f"   From Email: {self.config.get('from_email', 'Using SMTP account email')}")
        print(f"   From Name: {self.config.get('from_name', 'AOL')}")
        if self.config.get('reply_to'):
            print(f"   Reply-To: {self.config['reply_to']}")
        print(f"   Attachments: {'Yes' if self.config.get('use_attachments') else 'No'}")
        print(f"   Delay between emails: {self.config.get('delay_between_emails', 2)} seconds")
        print(f"   SMTP Accounts: {len(self.smtp_accounts)}")
        print(f"   Recipients: {len(self.recipients)}")
        
        attachments = self.get_attachments()
        if attachments:
            print(f"   PDF Files: {len(attachments)}")
            for att in attachments:
                print(f"     - {os.path.basename(att)}")
        
        print("\n🔄 SMTP Rotation Order:")
        for i, smtp in enumerate(self.smtp_accounts):
            print(f"   {i+1}. {smtp['name']} ({smtp['email']})")

def main():
    print("""
╔══════════════════════════════════════╗
║    SIMPLE EMAIL SENDER + SMTP ROTATION
╚══════════════════════════════════════╝
    """)
    
    try:
        sender = SimpleEmailSender()
        sender.show_config()
        
        confirm = input("\nStart sending? (y/n): ").lower()
        if confirm == 'y':
            sender.send_all_emails()
        else:
            print("Cancelled.")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\nPlease check your configuration files!")

if __name__ == "__main__":
    main()