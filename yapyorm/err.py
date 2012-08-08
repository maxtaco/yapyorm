

class Error (Exception):

    def __init__ (self, s):
        self._s = s
    def __str__ (self):
        return repr (self._s)


class Internal (Error):
    pass
class DB (Error):
    pass
class Data (Error):
    pass
class Corruption (Error):
    pass
class NotFound (Error):
    pass
class Index (Error):
    pass
class TypeError (Error):
    pass
class Schema (Error):
    pass
class NotUnique (Error):
    pass
class Inheritance (Error):
    pass
class Dotfile(Error):
    pass
class InsufficientData(Error):
    pass
class TooMuchData (Error):
    pass
class UnknownType (Error):
    pass
class BadTickerData (Error):
    pass
class HarvestError (Error):
    pass
class NoData (Error):
    pass
class BadAccount (Error):
    pass
class Order (Error):
    pass
class TxFilename (Error):
    pass
class Date (Error):
    pass
