import MySQLdb
import yapyorm.err as err
import os
import re
import sys

##-----------------------------------------------------------------------

class DBH:
    
    #--------------------

    loaded_db_info = False

    host = "10.0.0.1"
    username = "my-user-name"
    password = "my-pw"
    database = "my-db"
    _dbh = None
    querydebug = False

    #--------------------

    @classmethod
    def read_db_info (klass):

        if klass.loaded_db_info:
            return

        rx = re.compile ('\\s*=\\s*')
        fn = os.getenv ('HOME') + '/.yapyorm'
        
        try:
            fh = open (fn, "r")
            lineno = 0
            for line in fh:
                lineno += 1

                # Strip out any comments
                v = line.split ('#')
                if len (v) > 1:
                    line = v[0]

                v = rx.split (line)
                if len(v) != 2:
                    raise err.Dotfile, \
                        "%s:%d: bad line" % (fn, lineno)
                setattr (klass, v[0], v[1].strip ())
        except IOError:
            pass

        klass.loaded_db_info = True

    #--------------------

    @classmethod
    def connect (klass):
        klass.read_db_info ()
        try:
            return MySQLdb.connect (host = klass.host,
                                    user = klass.username,
                                    passwd = klass.password,
                                    db = klass.database)
        except MySQLdb.Error, e:
            s = "Error %d: %s" % (e.args[0], e.args[1])
            raise err.DB, e

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
