import datetime
import re
import sys

##-----------------------------------------------------------------------

lit = re.compile ("(?P<num>\\d+)\\s+(?P<inc>day|month|year)s?\\s+ago", 
                  re.IGNORECASE)
lit_map = { "day" : 1, "month" : 30, "year" : 365 }

machine = re.compile ("(?P<year>\\d{4})(?P<mon>\\d{2})(?P<day>\\d{2})")
mysql = re.compile ("(?P<year>\\d{4})-(?P<mon>\\d{1,2})-(?P<day>\\d{1,2})")
us =  re.compile ("(?P<mon>\\d{1,2})/(?P<day>\\d{1,2})/(?P<year>\\d{4})")
unix = re.compile ("-((?P<mon>\\d+)m|(?P<day>\\d+)d|(?P<year>\\d+)y)",
                   re.IGNORECASE)

##-----------------------------------------------------------------------

def _match_one (s):
    d = None
    for r in (machine, mysql, us):
        x = r.match (s)
        if x:
            return x.groupdict ()
    return None

##-----------------------------------------------------------------------

def parse_lit (s):
    ret = None
    x = lit.match (s)
    if x:
        d = x.groupdict ()
        today = datetime.date.today ()
        n = int (d["num"]) * lit_map[d["inc"]]
        ret = datetime.date.today () - datetime.timedelta (n)
    return ret

##-----------------------------------------------------------------------

def parse_unix (s):
    x = unix.match (s)
    days = None
    ret = None
    if x:
        d = x.groupdict ()
        for p in ( ( "day", 1 ), ("mon", 30), ("year", 365.25) ):
            try : 
                days = int (int (d[p[0]]) * p[1])
                if days: break
            except KeyError, e: pass
            except ValueError, e: pass
            except TypeError, e: pass
    if days:
        ret = datetime.date.today () - \
            datetime.timedelta (days)
    return ret

##-----------------------------------------------------------------------

def parse_std (s):
    ret = None
    d = _match_one (s)
    if d:
        ret = datetime.date (day = int (d["day"]),
                             month = int (d["mon"]),
                             year = int (d["year"]))
    return ret

##-----------------------------------------------------------------------

def parse (s):
    ret = None
    for parser in [ parse_lit, parse_unix, parse_std ]:
        ret = parser (s)
        if ret is not None:
            return ret
    return ret
        

##-----------------------------------------------------------------------
