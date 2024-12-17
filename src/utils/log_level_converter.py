import logging as log


def convert_string_to_logger_level(log_level_str):
    """
    Convert the string log level to the actual log level
    """
    log_level_map = {
        "DEBUG": log.DEBUG,
        "INFO": log.INFO,
        "WARNING": log.WARNING,
        "ERROR": log.ERROR,
        "CRITICAL": log.CRITICAL
    }
    return log_level_map.get(log_level_str.upper(), log.NOTSET)
