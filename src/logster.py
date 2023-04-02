"""Generic Logging class

    Returns:
        object: Configured logging object
"""
import logging


class Logster:
    """Common logging"""

    def __init__(self: object, log_level: str, logger_name: str):
        """init the class

        Set the log level and logger name

        Acceptable Log Levels:

            DEBUG: the messages written in this level provide
                detailed insights about the application.

            INFO: in this level, the messages are used to confirm
                that the application is running smoothly.

            WARNING: the messages written in this level provide
                insights that indicate something unusual is going on.

            ERROR: as suggested by the name, the messages in this
                level suggest that the application is not working correctly.

            CRITICAL: the highest level. The application will stop
                running soon and will no longer produce an output.

        Args:
            self (object): Class self
            log_level (str): Log level
            logger_name (str): Name of the module or class logging
        """
        self.log_level = logging.getLevelName(log_level)
        self.logger_name = logger_name

    def get_logger(self: object) -> object:
        """Setup Logger

        Configure the file and console loggers

        Args:
            self (object): Class self

        Returns:
            object: Logger object with formatting
        """
        # Setup file format and name
        file_formatter = logging.Formatter(
            "%(asctime)s~%(levelname)s~ \
                %(message)s~module:%(module)s~ \
                    function:%(module)s"
        )
        file_handler = logging.FileHandler("logfile.log")
        file_handler.setLevel(self.log_level)
        file_handler.setFormatter(file_formatter)

        # Setup console format
        console_formatter = logging.Formatter("%(levelname)s -- %(message)s")
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.log_level)
        console_handler.setFormatter(console_formatter)

        # wizbang out outputs
        logger = logging.getLogger(self.logger_name)
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        logger.setLevel(self.log_level)

        return logger
