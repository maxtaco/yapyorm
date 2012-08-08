
##-----------------------------------------------------------------------

def seq_scan (vec, date):
    """Scan a sequence of sorted items (vec) to find the one closest
    to the given date."""

    mid = len(vec) / 2
    q = vec[mid]
    if q.date () == date or mid == 0:
        return (q, mid)
    elif q.date () > date:
        return seq_scan (vec[0:mid], date)
    else:
        return seq_scan (vec[mid+1:], date)

##-----------------------------------------------------------------------

def pure_virtual ():
    raise NotImplementedError, "pure virtual called"

##-----------------------------------------------------------------------
