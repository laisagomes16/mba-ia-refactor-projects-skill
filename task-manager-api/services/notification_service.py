"""Serviço de notificação por e-mail — sem credenciais no código.

SMTP é opcional: se `SMTP_USER`/`SMTP_PASSWORD` não estiverem no ambiente, o
envio é ignorado (log de aviso) em vez de falhar ou expor segredos.
"""
import logging
import smtplib
from email.message import EmailMessage

from flask import current_app

logger = logging.getLogger(__name__)


class NotificationService:
    @staticmethod
    def _smtp_config():
        return {
            'host': current_app.config.get('SMTP_HOST'),
            'port': current_app.config.get('SMTP_PORT'),
            'user': current_app.config.get('SMTP_USER'),
            'password': current_app.config.get('SMTP_PASSWORD'),
        }

    @staticmethod
    def is_configured():
        config = NotificationService._smtp_config()
        return bool(config['host'] and config['user'] and config['password'])

    @staticmethod
    def send_email(to, subject, body):
        if not NotificationService.is_configured():
            logger.warning('SMTP não configurado: e-mail para %s ignorado', to)
            return False

        config = NotificationService._smtp_config()
        message = EmailMessage()
        message['From'] = config['user']
        message['To'] = to
        message['Subject'] = subject
        message.set_content(body)

        try:
            with smtplib.SMTP(config['host'], config['port'], timeout=10) as smtp:
                smtp.starttls()
                smtp.login(config['user'], config['password'])
                smtp.send_message(message)
            return True
        except (smtplib.SMTPException, OSError) as exc:
            # Log sem segredos.
            logger.error('Falha ao enviar e-mail: %s', exc)
            return False

    @staticmethod
    def notify_task_assigned(user, task):
        if not user or not user.email:
            return False
        subject = 'Nova task atribuída: {}'.format(task.title)
        body = 'Olá {},\n\nA task "{}" foi atribuída a você.'.format(user.name, task.title)
        return NotificationService.send_email(user.email, subject, body)

    @staticmethod
    def notify_task_overdue(user, task):
        if not user or not user.email:
            return False
        subject = 'Task atrasada: {}'.format(task.title)
        body = 'Olá {},\n\nA task "{}" está atrasada.'.format(user.name, task.title)
        return NotificationService.send_email(user.email, subject, body)

