'''
sudo apt install python3-pip
pip3 install imap_tools
pip3 install genanki
'''

from imap_tools import MailBox, AND
import random
import time
import sys
import genanki
from datetime import date
today = date.today()

import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders

DIR = "./decks/"

class parseMessage:
    def __init__(self):
        self.email = sys.argv[1]
        self.password = sys.argv[2]
        
        self.my_model = genanki.Model(
            1607392319,
            'Simple Model',
            fields=[
                {'name': 'Question'},
                {'name': 'Answer'},
            ],
            templates=[
                {
                    'name': 'Card 1',
                    'qfmt': '{{Question}}',
                    'afmt': '{{FrontSide}}<hr id="answer">{{Answer}}',
                },
            ])
       
        mailbox = MailBox('imap.gmail.com')
        mailbox.login(self.email, self.password, initial_folder='INBOX')  # or mailbox.folder.set instead 3d arg
        msgs = [msg for msg in mailbox.fetch(AND(seen=False))]
        decks = []
        for msg in msgs:
            if "`anki`" in msg.subject:
                decks.append(self.parse_deck(msg))
            if "`youtube`" in msg.subject:
                import json
                with open('study_list.json', 'r') as f:
                    json_data = json.load(f)
                    json_data[msg.subject.strip("`youtube`")] = {'date':today.strftime("%m-%d-%y"), 't':msg.text.strip("\r\n")}

                with open('study_list.json', 'w') as f:
                    f.write(json.dumps(json_data))

        mailbox.logout()
        print(decks)
        if len(decks) > 0 and decks[0][2] > 0:
            for n in range(len(decks)):
                self.send_mail(self.email, decks[n][1].from_, decks[n][1].subject, decks[n][0], self.email, self.password, files=[DIR+decks[n][0]])

    def parse_deck(self,msg):
        split_deck = msg.text.replace('\r','\n').split('\n')
        formatted_deck = genanki.Deck(random.randrange(1 << 30, 1 << 31), msg.subject)

        for sd in split_deck:
            if ':::' in sd:
                formatted_deck.add_note(genanki.Note(model=self.my_model,fields=(sd.split(':::'))))

        name = today.strftime("%m-%d-%y")+"-"+msg.subject+'.apkg'
        num_notes = len(formatted_deck.notes)
        print('created new deck: {} with {} cards'.format(name, num_notes))
        if num_notes > 0:
            genanki.Package(formatted_deck).write_to_file(DIR+name)

        return([name,msg,num_notes])
        #genanki.Package(formatted_deck).write_to_file(msg.subject+'.apkg')

        #return(formatted_deck)


    def send_mail(self, send_from, send_to, subject, message, username, password, files=[],server="smtp.gmail.com", port=587,  use_tls=True):
        """Compose and send email with provided info and attachments.
   
        Args:
            send_from (str): from name
            send_to (list[str]): to name(s)
            subject (str): message title
            message (str): message body
            files (list[str]): list of file paths to be attached to email
            server (str): mail server host name
            port (int): port number
            username (str): server auth username
            password (str): server auth password
            use_tls (bool): use TLS mode
        """
        msg = MIMEMultipart()
        msg['From'] = send_from
        msg['To'] = send_to #COMMASPACE.join(send_to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject
   
        msg.attach(MIMEText(message))
   
        for path in files:
            part = MIMEBase('application', "octet-stream")
            print(path)
            with open(path, 'rb') as file:
                part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                            'attachment; filename={}'.format(Path(path).name))
            msg.attach(part)
   
        smtp = smtplib.SMTP(server, port)
        if use_tls:
            smtp.starttls()
        smtp.login(username, password)
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.quit()


if __name__ == '__main__':
    #while True:
    p = parseMessage()
    #time.sleep(20)
