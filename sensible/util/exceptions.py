class ParseError(Exception):
    """Raised when an incoming packet is unable to be read.
    """
    def __init__(self, message, errors):
        super(ParseError, self).__init__(message)
