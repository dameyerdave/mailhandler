import email
from email import policy
import imaplib
import traceback
from bs4 import BeautifulSoup
from friendlylog import colored_logger as log
from sys import stdout


class Imap():
    def __init__(self, host, port, user, password, ssl=True):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.ssl = ssl

    def connect(self):
        try:
            if self.ssl:
                self.imap_server = imaplib.IMAP4_SSL(host=self.host, port=self.port)
            else:
                self.imap_server = imaplib.IMAP4(host=self.host, port=self.port)
            self.imap_server.login(self.user, self.password)
        except Exception as ex:
            raise ex

    @property
    def server(self):
        return self.imap_server

    def select(self, mailbox='INBOX'):
        self.imap_server.select(mailbox)

    def listMailboxes(self):
        response_code, folders = self.imap_server.list()
        if response_code == 'OK':
            print('Mailboxes:')
            for folder_details_raw in folders:
                folder_details = folder_details_raw.decode(
                    'utf-8', errors='ignore').split()
                print(f'- {folder_details[-1]}')
        else:
            raise Exception('Response code is {response_code}')

    def filter(self, filter):
        _, message_numbers_raw = self.imap_server.search(None, filter)
        for message_number in message_numbers_raw[0].split():
            #_, msg = self.imap_server.fetch(message_number, '(RFC822)')
            _, msg = self.imap_server.fetch(message_number, '(BODY.PEEK[])')

            message = email.message_from_bytes(
                msg[0][1], policy=policy.default)

            # Hanling payload
            def extract_payload(msg):
                if msg.is_multipart():
                    _pl = ''
                    for part in msg.get_payload():
                        _pl += extract_payload(part)
                    return _pl
                else:
                    content_type = msg.get_content_type()
                    if content_type == 'text/plain' or content_type == 'text/html':
                        return msg.get_payload()
                    else:
                        return ''

            payload = extract_payload(message)
            links = []
            try:
                soup = BeautifulSoup(payload, features='html.parser')
                for script in soup(["script", "style"]):
                    script.extract()
                payload = soup.get_text()
                for link in soup.findAll('a'):
                    links.append(link.get('href'))
            except Exception as ex:
                log.warning(f"HTML parse error: {ex}")
                pass

            ret_msg = {}
            for key in message.keys():
                try:
                    ret_msg[key.lower()] = message.get(key)
                except Exception as ex:
                    log.error(ex)
                    ret_msg[key.lower()] = 'Unknown'
            ret_msg['id'] = message_number
            ret_msg['payload'] = payload
            ret_msg['links'] = links
            try:
                ret_msg['raw'] = msg[0][1].decode('utf-8', errors='ignore')
            except Exception as ex:
                log.error(ex)
                traceback.print_exc(file=stdout)
                ret_msg['raw'] = ''

            # Handling attachments
            for part in message.walk():
                # this part comes from the snipped I don't understand yet...
                if part.get_content_maintype() == 'multipart':
                    continue
                if part.get('Content-Disposition') is None:
                    continue
                filename = part.get_filename()
                if bool(filename):
                    if 'attachments' not in ret_msg:
                        ret_msg['attachments'] = {}
                    ret_msg['attachments'][filename] = part.get_payload(
                        decode=True)

            yield ret_msg

    def destroy(self):
        self.imap_server.close()
        self.imap_server.logout()
