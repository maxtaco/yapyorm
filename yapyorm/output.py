import sys
import math

##-----------------------------------------------------------------------

def notimpl ():
    raise NotImplementedError, "pure virtual called"

##-----------------------------------------------------------------------

class Row:
    def __init__ (self): pass
    def minwidth (self, seplen): notimpl ()
    def n_columns (self): notimpl ()
    def output (self, colwidths, pagewidth, aligns, fh): notimpl ()
    def colwidths (self): notimpl ()

##-----------------------------------------------------------------------

def mystr (s):
    if s is None: s = ""
    return str (s)

##-----------------------------------------------------------------------

def moneyfmt (i):
    return "%0.2f" % i

##-----------------------------------------------------------------------

def pctfmt (i):
    return "%0.3f%%" % (100 * i)


##-----------------------------------------------------------------------

class DataRow (Row):

    ##-----------------------------------------

    def make_aligns (self, s, n):
        ret = [ str.rjust for i in range (n) ]
        d = { 'c' : str.center,
              'l' : str.ljust,
              'r' : str.rjust }
        if s:
            for (i,c) in enumerate (s.lower ()):
                try: ret[i] = d[c]
                except KeyError, e: pass
        return ret
            
    ##-----------------------------------------

    def __init__ (self, r):
        self._row = [ mystr (c) for c in r ]

    ##-----------------------------------------

    def colwidths (self):
        return [ len (r) for r in self._row ]
        
    ##-----------------------------------------

    def data_width (self):
        ret = 0
        for r in self._row:
            ret += len (r)
        return ret

    ##-----------------------------------------

    def minwidth (self, seplen):
        # need 1 space (at least) between all rows
        return self.data_width() + seplen * (len(self._row) - 1)

    ##-----------------------------------------

    def n_columns (self):
        return len (self._row)

    ##-----------------------------------------

    def output (self, colwidths, pagewidth, seplen, aligns, fh):
        sep = ' ' * seplen
        alignfns = self.make_aligns (aligns, len (colwidths) )
        fh.write ( sep.join ([ alignfns[i] (s, colwidths[i]) 
                               for (i,s) in enumerate (self._row) ]) + "\n") 

##-----------------------------------------------------------------------

class HeadingRow (DataRow):

    def __init (self, r):
        DataRow.__init__ (self, r)

##-----------------------------------------------------------------------

class Divider (Row):

    def __init__ (self, char):
        Row.__init__ (self)
        self._char = char

    def minwidth (self, colsep):
        return 1

    def n_columns (self):
        return 0

    def colwidths (self): return []

    def output (self, colwidth, pagewidth, seplen, aligns, fh):
        fh.write (self._char * pagewidth + "\n")

##-----------------------------------------------------------------------

class Table:

    ##----------------------------------------

    def __init__ (self):
        self._rows = []
        self._col_sep = 4;
        self._aligns = None

    ##----------------------------------------

    def addrow (self, r):
        self._rows += [ r ]

    ##----------------------------------------

    def divider (self, char = '-'):
        self.addrow ( Divider (char = char) )

    ##----------------------------------------

    def data_row (self, r):
        self.addrow ( DataRow (r) )
        
    ##----------------------------------------

    def headings (self, h):
        self.addrow ( HeadingRow (h) )

    ##---------------------------------------

    def minwidth (self):
        minw = 0
        for r in self._rows:
            w = r.minwidth (self._col_sep)
            if w > minw:
                minw = w
        return minw
            
    ##---------------------------------------

    def colwidths (self):
        """Find the maximal cell in each column (by width)."""
        cws = [ r.colwidths () for r in self._rows ]
        ret = []
        for i in range (self.n_columns ()):
            mx = 0
            for c in cws:
                try:
                    if c[i] > mx: mx = c[i]
                except IndexError, e:
                    pass
            ret += [ mx ]

        return ret 

    ##---------------------------------------

    def n_columns (self):
        cols = 0
        for r in self._rows:
            c = r.n_columns ()
            if c > cols:
                cols = c
        return cols
                
    ##---------------------------------------

    def set_colsep (self, s):
        self._col_sep = s

    ##---------------------------------------
        
    def set_alignment (self, s):
        self._aligns = s

    ##---------------------------------------

    def output (self, fh = sys.stdout):
        cw = self.colwidths ()

        # total width of the page
        tot = self._col_sep * (self.n_columns () - 1)
        for c in cw: tot += c

        for r in self._rows:
            r.output (cw, tot, self._col_sep, self._aligns, fh)

##-----------------------------------------------------------------------

if False:
    t = Table ()
    t.data_row ([None, "dog", "cat", "biririririd"])
    t.divider ()
    t.data_row ([1,4,3,4])
    t.data_row ([55500,44444,3333333333,111])
    t.output ()

        
