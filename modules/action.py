from friendlylog import colored_logger as log
import shutil
from os.path import join
from modules.queues import MailDeleteQueue, MailForwardQueue


class ActionBase():
    def __init__(self, action_config):
        self.action_config = action_config

    def execute(self):
        raise NotImplementedError('execute is not implemented')


class MoveAction(ActionBase):
    def __init__(self, action_config):
        super().__init__(action_config)

    def execute(self):
        if 'move' in self.action_config:
            imap = self.action_config['imap']
            message = self.action_config['message']
            destination = self.action_config['move']
            imap.server.create(destination)
            log.info(
                f"Moveing message '{int(message.get('id'))}' to '{destination}'...")
            result = imap.server.copy(message.get('id'), destination)
            if result[0] == 'OK':
                MailDeleteQueue.enqueue(message.get('id'))


class DeleteAction(ActionBase):
    def __init__(self, action_config):
        super().__init__(action_config)

    def execute(self):
        if 'delete' in self.action_config:
            message = self.action_config['message']
            delete = self.action_config['delete']
            log.info(f"Deleteing message '{int(message.get('id'))}'...")
            if delete:
                MailDeleteQueue.enqueue(message.get('id'))


class ForwardAction(ActionBase):
    def __init__(self, action_config):
        super().__init__(action_config)

    def execute(self):
        if 'forward' in self.action_config:
            message = self.action_config['message']
            destination = self.action_config['forward']
            log.info(
                f"Forwarding message '{int(message.get('id'))}' to '{destination}'...")
            MailForwardQueue.enqueue(
                {'message': message, 'destination': destination})


class StoreAction(ActionBase):
    def __init__(self, action_config):
        super().__init__(action_config)

    def execute(self):
        if 'store' in self.action_config:
            temp_folder = self.action_config['temp_folder']
            attachment = self.action_config['attachment']
            download_folder = self.action_config['store']
            log.info(
                f"Storeing attachment '{attachment}'' to '{download_folder}'...")
            shutil.copy(join(temp_folder, attachment),
                        join(download_folder, attachment))
