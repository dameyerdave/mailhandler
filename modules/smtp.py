import smtplib


class Smtp():
    def __init__(self, host, port, user, password):
        self.host = host
        self.port = port
        self.user = user
        self.password = password

    def connect(self):
        try:
            self.smtp_server = smtplib.SMTP(self.host, self.port)
            self.smtp_server.starttls()
            self.smtp_server.login(self.user, self.password)
        except Exception as ex:
            raise ex

    @property
    def server(self):
        return self.smtp_server

    def destroy(self):
        self.smtp_server.quit()
