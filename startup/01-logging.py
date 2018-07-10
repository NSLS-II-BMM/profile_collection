import logging

BMM_logger = logging.getLogger('BMM_logger')
BMM_logger.handlers = []

BMM_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s\n%(message)s')
BMM_log_master = logging.FileHandler('/home/bravel/BMM_Data/BMM_master.log')
BMM_log_master.setFormatter(BMM_formatter)
BMM_logger.addHandler(BMM_log_master)
BMM_logger.setLevel(logging.INFO)

BMM_log_user = None

def user_log(filename):
    BMM_log_user = logging.FileHandler(filename)
    BMM_log_user.setFormatter(formatter)
    BMM_logger.addHandler(BMM_log_user)

def BMM_log_info(message):
    entry = ''
    for line in message.split('\n'):
        entry += '    ' + line + '\n'
    BMM_logger.info(entry)
