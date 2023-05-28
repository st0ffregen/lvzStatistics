import logging
from datetime import datetime

class Logger:

    def __init__(self, path_to_logs: str, file_name: str, log_level: str):
        """
        Provides a logger to be accessed from logger variable.

        :param path_to_logs: path to logs folder.
        :param file_name: name of log file.
        :param log_level: log level.
        """

        self.logger = logging.getLogger(__name__)

        if log_level == "INFO":
            self.logger.setLevel(logging.INFO)
        elif log_level == "WARN":
            self.logger.setLevel(logging.WARN)

        formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

        file_handler = logging.FileHandler(f'{path_to_logs}{file_name}_{str(int(datetime.utcnow().timestamp()))}.log')
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

    def get_logger(self) -> logging.Logger:
        """
        Makes logger accessible.

        :return: logger instance.
        """
        return self.logger
