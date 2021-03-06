import os
import logging
import logging.config

from windnode_kwum.tools import config


def setup_logger(log_dir=None, loglevel=logging.DEBUG):
    """
    Instantiate logger

    Parameters
    ----------
    log_dir : str
        Directory to save log, default: <package_dir>/../../logs/
    loglevel : ?
        Loglevel

    Returns
    -------
    instance of logger
    """

    if log_dir is None:
        log_dir = os.path.join(config.get_data_root_dir(), config.get('user_dirs', 'log_dir'))

    logger = logging.getLogger('windnode_kwum') # use filename as name in log
    logger.setLevel(loglevel)

    # create a file handler
    handler = logging.FileHandler(os.path.join(log_dir, 'windnode_kwum.log'))
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s-%(levelname)s-%(funcName)s: %(message)s')
    handler.setFormatter(formatter)

    # create a stream handler (print to prompt)
    stream = logging.StreamHandler()
    stream.setLevel(logging.INFO)
    stream_formatter = logging.Formatter(
        '%(asctime)s-%(levelname)s: %(message)s',
        '%H:%M:%S')
    stream.setFormatter(stream_formatter)

    # add the handlers to the logger
    logger.addHandler(handler)
    logger.addHandler(stream)

    logger.propagate = False

    logger.debug('*********************************************************')
    logging.info('Path for logging: %s' % log_dir)

    return logger