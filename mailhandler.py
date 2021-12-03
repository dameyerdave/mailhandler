#!/usr/bin/env python3

from modules.queues import MailForwardQueue, MailDeleteQueue
import traceback
from os.path import join, realpath, dirname
from pprint import pprint
from sys import exit, stdout

from envparse import env
from friendlylog import colored_logger as log

from modules.bookkeeper import BookKeeper
from modules.configuration import Configuration, ParseError
from modules.imap import Imap
from modules.smtp import Smtp
from modules.processor import MailProcessor, AttachmentProcessor, LinkProcessor, RawProcessor


def parse_arguments():
    import argparse
    parser = argparse.ArgumentParser(description='Process mailbox by rules')

    parser.add_argument('-d', '--disable-bookkeeping', action='store_true', dest='disable_bookkeeping',
                        help='Disable bookkeeping')

    return parser.parse_args()


def main():
    options = parse_arguments()

    configuration = Configuration(
        join(dirname(realpath(__file__)), 'mailhandler.yml'))
    try:
        configuration.parse()
    except ParseError as pe:
        log.error(pe)
        traceback.print_exc(file=stdout)
        exit(1)

    try:
        env.read_envfile()
        temp_folder = env('TEMP_FOLDER')

        bookKeeper = BookKeeper('bookkeeping.db')

        imap = Imap(env('IMAP_HOST'), env.int('IMAP_PORT'), env(
            'IMAP_USER'), env('IMAP_PASSWORD'), env.bool('IMAP_SSL'))
        imap.connect()
        imap.select()

        smtp = Smtp(env('SMTP_HOST'), env.int('SMTP_PORT'), env(
            'SMTP_USER'), env('SMTP_PASSWORD'), env.bool('SMTP_SSL'))
        smtp.connect()

        if configuration.has_rules():
            for rule in configuration.rules():
                log.info(f"Applying rule '{rule.name}'...")
                stats = {
                    'rule': rule.name,
                    'processed': 0,
                }
                for msg in imap.filter(rule.filter):
                    mailid = int(msg.get('id'))
                    stats['processed'] += 1
                    if options.disable_bookkeeping or not bookKeeper.is_tracked(mailid):
                        log.info(
                            f"Handling message {mailid} | {msg.get('subject')} | {msg.get('from')}...")
                        if 'process' in rule:
                            mailProcessor = MailProcessor(
                                rule.process, imap, msg, temp_folder)
                            mailProcessor.process()

                        if 'raw' in rule:
                            if 'process' in rule.raw:
                                mailProcessor = RawProcessor(
                                    rule.raw.process, imap, msg, temp_folder)
                                mailProcessor.process()

                        if 'attachments' in rule:
                            if 'handle' in rule.attachments and rule.attachments.handle:
                                if 'process' in rule.attachments:
                                    attachments = msg.get('attachments')
                                    attachmentProcessor = AttachmentProcessor(
                                        rule.attachments.process, imap, msg, attachments, temp_folder)
                                    attachmentProcessor.process()

                        if 'links' in rule:
                            if 'handle' in rule.links and rule.links.handle:
                                if 'process' in rule.links:
                                    links = msg.get('links')
                                    linkProcessor = LinkProcessor(
                                        rule.links.process, imap, msg, links, temp_folder)
                                    linkProcessor.process()

                        if not options.disable_bookkeeping:
                            bookKeeper.track(mailid, msg.get(
                                'subject'), msg.get('from'), msg.get('to'))
                    else:
                        log.warning(
                            f"Message already handled: {mailid} | {msg.get('subject')} | {msg.get('from')}")
                fwd_ret = MailForwardQueue.forwardAll(imap, smtp)
                del_ret = MailDeleteQueue.deleteAll(imap)
                pprint(stats)
                pprint(fwd_ret)
                pprint(del_ret)
        else:
            imap.listMailboxes()

        imap.destroy()
        smtp.destroy()

    except Exception as ex:
        log.error(ex)
        traceback.print_exc(file=stdout)


if __name__ == '__main__':
    main()
