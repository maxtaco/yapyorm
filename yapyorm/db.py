import MySQLdb
import yapyorm.err as err
import os
import re
import sys

##-----------------------------------------------------------------------

class DBH:
    
    #--------------------

    loaded_db_info = False

    _dbh = None
    _config = None
    querydebug = False

    #--------------------

    @classmethod
    def set_config (klass, cfg):
        klass._config = cfg
        
    #--------------------

    @classmethod
    def connect (klass):
        cfg = klass._config
        if not cfg:
            raise err.DB, "must call DBH.set_config before attempting connect"
        try:
            return MySQLdb.connect (host = cfg.host,
                                    user = cfg.username,
                                    passwd = cfg.password,
                                    db = cfg.database)
        except MySQLdb.Error, e:
            s = "Error %d: %s" % (e.args[0], e.args[1])
            raise err.DB, s

    #--------------------

    @classmethod 
    def getdb (klass):
        if klass._dbh is None:
            klass._dbh = klass.connect()
        if klass._dbh is None:
            raise err.DB, "Cannot make db handle"

    #--------------------

    def __init__ (self):
        self.getdb ()

    #--------------------

    def dictCursor (self):
        return self._dbh.cursor (MySQLdb.cursors.DictCursor)
                               
    #--------------------

    def cursor (self):
        return self._dbh.cursor ()

    #--------------------

    def debug (self, q):
        if self.querydebug:
            sys.stderr.write ("QRY: " + q + "\n")
            sys.stderr.flush ()

    #--------------------

    def do (self, q):
        c = self._dbh.cursor ()
        self.debug (q)
        r = c.execute (q)
        c.close ()

    #--------------------

##-----------------------------------------------------------------------
