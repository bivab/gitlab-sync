import logging
from termcolor import colored

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'WARNING': 'yellow',
        'INFO': 'green', # ignored
        'DEBUG': 'blue',
        'CRITICAL': 'yellow',
        'ERROR': 'red',
    }
    def format(self, record):
        levelname = record.levelname
        if levelname != 'INFO':
            record.msg = colored(record.msg, self.COLORS[levelname])
        record.levelname = colored(record.levelname, self.COLORS[levelname])
        return logging.Formatter.format(self, record)


def getLogger():
    logger = logging.getLogger('gitlab-sync')
    logger.setLevel(logging.DEBUG)
    # create file handler which logs even debug messages
    fh = logging.FileHandler('gitlab.log')
    fh.setLevel(logging.DEBUG)
    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    f2 = ColoredFormatter("[%(levelname)s] %(message)s")

    fh.setFormatter(formatter)
    ch.setFormatter(f2)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger
