import tnglib


def register_sp(url, username=None, password=None):
    """
    Register the SP
    Has to be run before every interaction
    """
    tnglib.set_sp_path(url)
    if not tnglib.sp_health_check():
        raise ConnectionError
