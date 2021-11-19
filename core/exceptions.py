class SoftAbort(Exception):
    """ sutable for situations that logging is not neccecery of debug level suffices."""
    pass

class HardAbort(Exception):
    """ sutable for situations that log level shoudl flags as error or critical."""
    pass
