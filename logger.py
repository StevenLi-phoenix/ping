import logging
import logging.handlers
import os
import os.path as osp
import platform

import CONFIG


def file(filename):
    os.makedirs(osp.dirname(filename), exist_ok=True)
    return filename


def create_default_logger(name="", level=CONFIG.LEVEL, filename=osp.join(CONFIG.LogDirectionary, __name__+".log"),
                          buffer=1024) -> logging.Logger:
    log = logging.getLogger(name)
    log.setLevel(level)
    formatter = logging.Formatter('[%(asctime)s][%(levelname)s]: %(message)s')

    # set up logging to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    log.addHandler(console_handler)

    # set up logging to file
    file_handler = logging.FileHandler(filename=file(filename))
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    memoryhandler = logging.handlers.MemoryHandler(buffer, level, file_handler, flushOnClose=True)
    log.addHandler(memoryhandler)

    log.debug(platform.uname())

    return log


def test(logger: logging.Logger):
    logger.debug("test")
    logger.info("test")
    logger.warning("test")
    logger.error("test")
    logger.critical("test")


if __name__ == '__main__':
    log = create_default_logger(level=CONFIG.LEVEL, name="")
    test(log)
