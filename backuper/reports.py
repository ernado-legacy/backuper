# coding=utf-8
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import Encoders
import smtplib
import os

import errors
import log


def _add_files(files, message, logger):
    logger.info('Attaching files')

    for f in files:
        logger.info('Attaching file: %s' % f)
        part = MIMEBase('application', "octet-stream")
        part.set_payload(open(f, "rb").read())
        Encoders.encode_base64(part)
        part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(f))
        message.attach(part)
    return message


def _format_message(subject, text, files, logger, cfg):
    logger.info('Generation report message')

    msg = MIMEMultipart()
    msg['From'] = cfg.get('email', 'from')
    msg['To'] = COMMASPACE.join(cfg.get('email', 'to'))
    msg['Date'] = formatdate(localtime=True)
    msg['Subject'] = subject
    msg.attach(MIMEText(text))

    msg = _add_files(files, msg, logger)
    return msg


def send(subject, text, files=None, cfg=None):
    """
    Sends mail
    @type text: str
    @param subject: subject of the report
    @param text: text of the report
    @param files: attached files
    @param cfg: ParseConfig object
    @type subject: str
    """
    logger = log.get(__name__)

    if files is None:
        files = []
    assert type(files) == list

    logger.debug('Processing report, subject: %s, text length: %s, files: %s' % (subject, len(text), len(files)))

    if cfg is None:
        from config import get_config
        cfg = get_config()

    message = _format_message(subject, text, files, logger, cfg)

    try:
        logger.info('Starting smtp connection')
        smtp = smtplib.SMTP(cfg.get('email', 'host'))
        logger.info('Loggin in mail server')
        smtp.starttls()
        smtp.login(cfg.get('email', 'from'), cfg.get('email', 'password'))
        logger.info('Sending message...')
        smtp.sendmail(cfg.get('email', 'from'), cfg.get('email', 'to'), message.as_string())
        logger.info('Message sent')
        smtp.close()
    except (smtplib.SMTPException, smtplib.SMTPResponseException), e:
        logger.error('Unable to send message: %s' % e)
        raise errors.BackupException('Failed to send report')
    logger.info('Report ')

