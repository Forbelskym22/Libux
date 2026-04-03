import shutil

def is_service_installed(service_name):
    """
    function used to check if the service is installed on our device.
    """
    return shutil.which(service_name) is not None