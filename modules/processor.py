from modules.action import DeleteAction, ForwardAction, MoveAction, StoreAction, VisitAction
import textract
import re
from os.path import join, isfile, splitext
from os import remove
from friendlylog import colored_logger as log


class ProcessorBase():
    def __init__(self, process_config, imap, message, temp_folder):
        self.__process_config = process_config
        self.imap = imap
        self.message = message
        self.temp_folder = temp_folder

    def __execute_actions(self, actions, **kwargs):
        log.debug("Processing actions")
        for action in actions:
            action_config = action.copy()
            action_config.update({
                'imap': self.imap,
                'message': self.message,
                'temp_folder': self.temp_folder
            })
            action_config.update(kwargs)
            if 'forward' in action:
                ForwardAction(action_config).execute()
            if 'store' in action:
                StoreAction(action_config).execute()
            if 'move' in action:
                MoveAction(action_config).execute()
            if 'delete' in action:
                DeleteAction(action_config).execute()
            if 'visit' in action:
                VisitAction(action_config).execute()

    def process_rules(self, content, **kwargs):
        for process in self.__process_config:
            if 'if_content' in process:
                if 'actions' in process:
                    log.info(
                        "Processing 'if_content' actions...")
                    if content:
                        regex = process['if_content']
                        if re.search(regex, content):
                            log.debug(
                                f"Pattern '{regex}' found in content")
                            self.__execute_actions(
                                process.actions, **kwargs)
                        else:
                            log.debug(
                                f"Pattern '{regex}' not found in content")
                    else:
                        log.debug("Content is None")
            if 'always' in process:
                if 'actions' in process:
                    log.info(
                        "Processing 'always' actions...")
                    self.__execute_actions(
                        process.actions, **kwargs)

    def process(self):
        raise NotImplementedError('process is not implemented')


class MailProcessor(ProcessorBase):
    def __init__(self, process_config, imap, message, temp_folder):
        super().__init__(
            process_config, imap, message, temp_folder)

    def process(self):
        log.debug(f"Processing {self.__class__.__name__}...")
        if self.message:
            content = self.message.get('payload')
            self.process_rules(content)


class RawProcessor(ProcessorBase):
    def __init__(self, process_config, imap, message, temp_folder):
        super().__init__(
            process_config, imap, message, temp_folder)

    def process(self):
        log.debug(f"Processing {self.__class__.__name__}...")
        if self.message:
            content = self.message.get('raw')
            self.process_rules(content)


class LinkProcessor(ProcessorBase):
    def __init__(self, process_config, imap, message, links, temp_folder):
        self.links = links
        super().__init__(
            process_config, imap, message, temp_folder)

    def process(self):
        log.debug(f"Processing {self.__class__.__name__}...")
        if self.links:
            for link in self.links:
                if link:
                    match = re.search(r'.*(?P<link>http(s)?:\/\/.+)', link)
                    if match:
                        link = match.group('link')
                        log.info(f"Handling link '{link}''...")
                        self.process_rules(
                            link, link=link)


class AttachmentProcessor(ProcessorBase):
    RE_ATT_POSTFIX = r' \([0-9]+\)\.'
    supported_extensions = [
        '.csv', '.doc', '.docx', '.eml', '.epub', '.gif', '.htm', '.html', '.jpeg', '.jpg', '.json', '.log',
        '.mp3', '.msg', '.odt', '.ogg', '.pdf', '.png', '.pptx', '.ps', '.psv', '.rtf', '.tff', '.tif', '.tiff',
        '.tsv', '.txt', '.wav', '.xls', '.xlsx']

    def __init__(self, process_config, imap, message, attachments, temp_folder):
        self.attachments = attachments
        super().__init__(
            process_config, imap, message, temp_folder)

    def __store_attachment(self, attachment):
        downloaded_file = join(self.temp_folder, attachment)
        num = 1
        while isfile(downloaded_file):
            filename, extension = splitext(
                downloaded_file)
            if re.search(self.RE_ATT_POSTFIX, downloaded_file):
                downloaded_file = re.sub(
                    self.RE_ATT_POSTFIX, '.', downloaded_file)
                filename, extension = splitext(
                    downloaded_file)

            downloaded_file = join(self.temp_folder,
                                   f"{filename} ({num}){extension}")
            num += 1
        with open(downloaded_file, 'wb') as f:
            f.write(self.attachments[attachment])
            f.close()
        return downloaded_file

    def process(self):
        log.debug(f"Processing {self.__class__.__name__}...")
        if self.attachments:
            for attachment in self.attachments.keys():
                log.info(f"Handling attachment '{attachment}''...")
                downloaded_file = self.__store_attachment(attachment)
                _, extension = splitext(
                    attachment)
                if extension in AttachmentProcessor.supported_extensions:
                    log.debug(
                        f"Extracting content of attachment '{attachment}''...")
                    content = textract.process(
                        downloaded_file).decode("utf-8", errors='ignore')
                    self.process_rules(
                        content, attachment=attachment)
                else:
                    log.debug(
                        f"Extension '{extension}' not supported to extract content from attachment '{attachment}'")
                log.debug(
                    f"Removing temporary stored attachment: {downloaded_file}")
                remove(downloaded_file)
