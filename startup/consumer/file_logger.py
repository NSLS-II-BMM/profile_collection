import logging, os


def add_handler(this, logger):
    this.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s\n%(message)s\n')
    this.setFormatter(formatter)
    logger.addHandler(this)


def clear_logger(logger):
    '''Reset the logger to have only the stream handler.  

    Copy log to central storage as a permanent part of the record of
    the experiment.

    '''
    logger.handlers.clear()
    logger = logging.getLogger('BMM file manager logger')
    logger.setLevel(logging.INFO)
    sh = logging.StreamHandler()
    add_handler(sh, logger)
    ## copy it....
    
def establish_logger(logger, folder=None):
    if folder is None:
        print('No folder provided for experiment log')
        return
        
    log_master_file = os.path.join(folder, 'file_manager.log')
    fh = logging.FileHandler(log_master_file)
    add_handler(fh, logger)
    logger.info(f'established a logging file handler for experiment in {folder}')
