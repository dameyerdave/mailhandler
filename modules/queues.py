import email
from email import policy


class BaseQueue():
    __queue = {}

    @classmethod
    def enqueue(cls, msg_id):
        if cls.__name__ not in cls.__queue:
            cls.__queue[cls.__name__] = []
        cls.__queue[cls.__name__].append(msg_id)

    @classmethod
    def getQueue(cls):
        if cls.__name__ not in cls.__queue:
            return []
        return cls.__queue[cls.__name__]

    @classmethod
    def initQueue(cls):
        cls.__queue[cls.__name__] = []


class MailForwardQueue(BaseQueue):
    @classmethod
    def forwardAll(cls, imap, smtp):
        length = len(cls.getQueue())
        count = 0
        for item in cls.getQueue():
            message = item['message']
            destination = item['destination']
            status, data = imap.server.fetch(message.get('id'), "(RFC822)")
            if status == 'OK':
                msg = email.message_from_bytes(
                    data[0][1], policy=policy.default)

                msg.replace_header("From", message.get('to'))
                msg.replace_header("To", destination)

                smtp.server.sendmail(message.get('to'),
                                     destination, msg.as_string())
                count += 1
        return {'forwarded': count, 'mails_in_queue': length}


class MailDeleteQueue(BaseQueue):
    @classmethod
    def deleteAll(cls, imap):
        length = len(cls.getQueue())
        count = 0
        for mail_id in cls.getQueue():
            ret, data = imap.server.store(
                mail_id, '+FLAGS', '\\Deleted')
            if ret == 'OK':
                count += 1
        imap.server.expunge()
        cls.initQueue()
        return {'deleted': count, 'mails_in_queue': length}
