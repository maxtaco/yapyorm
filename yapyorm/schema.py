
import yapyorm.db as db
import yapyorm.err as err
import copy
import re
import datetime
import time

##-----------------------------------------------------------------------

def escape (s, d):

    def re_escape (s):
        if s == '\\':
            return '\\\\'
        else:
            return s

    rxx = re.compile ("([" + 
                      ''.join ([ re_escape (c) for c in d.keys ()]) 
                      + "])")
    def fn (i, s):
        if i % 2 == 0:
            return s
        else:
            return d[s]
    return ''.join ([ fn (*p) for p in enumerate (rxx.split (s)) ])
   
##-----------------------------------------------------------------------

def sql_escape (s):
    return escape (s, { "\\": "\\\\", "'" : "\\'" })

##-----------------------------------------------------------------------

def is_quoted (x):
    return (x[0] == "'" and x[-1] == "'") or \
        (x[0] == '"' and x[-1] == '"')

##-----------------------------------------------------------------------

def string_it (x):
    t = type (x)
    if x is None:
        return "NULL"
    elif t is int or t is long:
        return str(x)
    else:
        return "'%s'" % sql_escape (str(x))

##-----------------------------------------------------------------------

def remove_nones (x):
    out = []
    for i in x:
        if i is not None:
            out.append (i)
    return out

##-----------------------------------------------------------------------

def make_query (*lst):
    return " ".join (remove_nones (list (lst)))

##-----------------------------------------------------------------------

dkx = re.compile ('([a-zA-Z0-9_]+)__(lt|le|ge|gt|eq|ne)')
dk_map = { 'lt' : '<' ,
           'le' : '<=' ,
           'ge' : '>=' ,
           'gt' : '>' ,
           'eq' : '=',
           'ne' : '!=' }

def dict_key_to_rel (k):
    m = dkx.match (k)
    rel = '='
    if m is not None:
        rel = dk_map[m.group (2)]
        k = m.group (1)

    return (k, rel)

##=======================================================================
##-----------------------------------------------------------------------

class DbObj:

    def __init__ (self):
        pass

    def name (self):
        return self._nm

##-----------------------------------------------------------------------

class Field (DbObj):

    def __init__ (self, nm):
        self._nm = nm

    def is_mutable (self):
        return True

    def to_value (self, v):
        return v

    def from_value (self, v):
        return v

    def is_primary_key (self):
        return False

    def is_orderer (self):
        return False

    def is_key (self):
        return False

    def to_sql_value (self, v):
        return string_it (self.to_value (v))

    def resolve (self, base_obj_klass, dict):
        pass

##-----------------------------------------------------------------------

class Key (Field):

    def __init__ (self, nm):
        Field.__init__ (self, nm)

    def is_key (self):
        return True

##-----------------------------------------------------------------------

class PrimaryKey (Field):

    def is_primary_key (self):
        return True

##-----------------------------------------------------------------------

class AIPK (PrimaryKey):

    def is_mutable (self):
        return False

##-----------------------------------------------------------------------

class Bool (Field):

    def to_sql_value (self, v):
        return int (v)

    def from_value (self, v):
        return (v != 0)

##-----------------------------------------------------------------------

class ForeignKey (Key):

    def __init__ (self, nm, robj):
        Field.__init__ (self, nm)
        if type (robj) is str:
            self._robj_unresolved = robj
        else:
            self._robj_unresolved = None
            self._robj = robj
            if not issubclass (robj, BaseObj):
                raise err.TypeError, "reference object not of right type!"

    #-----------

    def resolve (self, base_obj_klass, dct):
        k = self._robj_unresolved
        if k is not None:
            try:
                self._robj = dct[k]
                self._robj_unresolved = None
            except KeyError:
                raise err.TypeError, "cannot resolve class: %s" % k
        self._robj.db_def.add_child (self, base_obj_klass)

    #---------------

    def to_value (self, v):
        if isinstance (v, BaseObj):
            v = v.pkv ()
        return v
    
    #---------------

    def from_value (self, v):
        r = v
        if not isinstance (v, BaseObj):
            r = self._robj.create_from_pkv (v)
        return r

    #---------------
       
##-----------------------------------------------------------------------

class DateTime (Field):

    fmt = "%Y-%m-%d %H:%M:%S"

    def __init__ (self, nm):
        Field.__init__ (self, nm)

    def to_value (self, v):
        t = type (v)
        if v is None: pass
        elif t is str: pass
        elif t is datetime.datetime: v = v.strftime (self.fmt)
        elif t is time.struct_time: v = v.strftime (self.fmt)
        else: 
            raise err.TypeError, \
                "cannot convert to date string: %s (type=%s)" % (v, type (v))
        return v

    def from_value (self, v):
        if v is not None:
            if type (v) is str:
                v = time.strptime (v, self.fmt)
            if type (v) is time.struct_time:
                v = datetime.datetime ( month = v.tm_mon,
                    year =  v.tm_year,
                    day = v.tm_mday,
                    minute = v.tm_min,
                    second = v.tm_second,
                    hour = v.tm_hour )
            if type (v) is not datetime.datetime:
                raise err.TypeError, "cannot convert to date: %s" % v
        return v
        
##-----------------------------------------------------------------------

class Date (Field):

    fmt = "%Y-%m-%d"

    def __init__ (self, nm):
        Field.__init__ (self, nm)

    def to_value (self, v):
        t = type (v)
        if v is None: pass
        elif t is str: pass
        elif t is datetime.date: v = v.strftime (self.fmt)
        elif t is time.struct_time: v = v.strftime (self.fmt)
        else: 
            raise err.TypeError, \
                "cannot convert to date string: %s (type=%s)" % (v, type (v))
        return v

    def from_value (self, v):
        if v is not None:
            if type (v) is str:
                v = time.strptime (v, self.fmt)
            if type (v) is time.struct_time:
                v = datetime.date ( month = v.tm_mon,
                                    year =  v.tm_year,
                                    day = v.tm_mday)
            if type (v) is not datetime.date:
                raise err.TypeError, "cannot convert to date: %s" % v
        return v

##-----------------------------------------------------------------------

class Sorter (Key):

    ASC = 0
    DESC = 1

    def __init__ (self, nm, order):
        Field.__init__ (self, nm)
        self._order = order

    def is_orderer (self):
        return True

    def order (self):
        if self._order == self.ASC:
            dir = "ASC"
        else:
            dir = "DESC"
        return "ORDER by %s %s" % (self.name (), dir)

    @classmethod
    def ord_to_str (klass, i):
        if i == klass.ASC: return "ASC"
        elif i == klass.DESC: return "DESC"
        else: raise err.Order, \
                "order param must be either Sorter.ASC or Sorter.DESC"
 
##-----------------------------------------------------------------------

class DateSorter (Date, Sorter):

    def __init__ (self, nm, order):
        Date.__init__ (self, nm)
        self._order = order

 
##-----------------------------------------------------------------------

class DateTimeSorter (DateTime, Sorter):

    def __init__ (self, nm, order):
        DateTime.__init__ (self, nm)
        self._order = order

##-----------------------------------------------------------------------

def toField (x):
    if type(x) is str:
        return Field (x)
    return x

##-----------------------------------------------------------------------

class DbDef (DbObj):

    def __init__ (self):
        self._table = None
        self._fields = []
        self._wc_extra = None
        self._children = {}
        self._primary_key = None
        self._keys = []
        self._orderer = None
        self._abstract = False
        self._unique_indices = []

    #---------------

    def set_abstract (self, a):
        self._abstract = a

    #---------------

    def add (self, table = None, fields = None, wc_extra = None, 
             classname = None, abstract = None,
             unique_indices = None):
        if table is not None:
            self._table = table
        if fields is not None:
            self._fields += [ toField(f) for f in fields ]
        if wc_extra is not None:
            self._wc_extra = wc_extra
        if classname is not None:
            self._classname = classname
        if unique_indices is not None:
            self._unique_indices = unique_indices
        return self

    #---------------

    def toDict (self):
        d = {}
        for i in [ '_table' , '_fields', '_wc_extra' ]:
            d[i] = getattr (self, i)
        return d
            
    #---------------

    def materialize (self, base_obj_klass, objs):
        self._nm = base_obj_klass.__name__

        if self._abstract:
            return

        self._fnames = [ f.name () for f in self._fields ]
        for f in self._fields:
            f.resolve (base_obj_klass, objs)
            if f.is_primary_key ():
                if self._primary_key:
                    raise err.Schema, "duplicate primary key!"
                self._primary_key = f
            if f.is_orderer ():
                self._orderer = f
            if f.is_key ():
                self._keys += [ f ]

    #---------------

    def pk (self):
        n = self._primary_key
        if not n:
            raise err.Index, "no primary key on object specified"
        return n

    #---------------

    def finalize (self):

        if self._abstract:
            return

        lst = [ (f.name (), f) for f in self._fields ]
        lst += [ (k, v[1].db_def) for (k,v) in self._children.items () ]
        self._dict = dict (lst)

    #---------------

    #
    # Imagine two tables.  A parent 'Holding' and a child 'Quote'.
    # Then this function will be called with the foreign key in Quote.db_def
    # that points back to a Holding object. The base_obj_klass will
    # be the klass 'Quote'.  The self object will be the db_def in the
    # Holding klass.
    #
    def add_child (self, fk, base_obj_klass):
        self._children[base_obj_klass.to_seq_name ()] = (fk, base_obj_klass)

    #---------------

    def get_child (self, k):
        return self._children[k]

    #---------------

    def obj_init (self, bo):
        for f in self._fields:
            bo.create_db_field (f.name (), f.is_mutable ())
        for k in self._children:
            bo.create_db_child (k)

    #---------------

    def where_clause (self, dct, limit):
        clauses = []
        limit_sql = None
        all_items = []
        if dct: all_items += dct.items ()
        if self._wc_extra: all_items += self._wc_extra
        order = None

        order_rxx = re.compile ("([a-zA-Z0-9_]+)__order")

        for (k,v) in all_items:
            if k == 'limit':
                limit_sql = " LIMIT %d" % v
            else:
                m = order_rxx.match (k)
                if m:
                    k = m.group (1)
                    if self._dict.get (k) is None:
                        raise err.Index, \
                            "order by field is not an index (%s)" % k
                    order = " ORDER BY %s %s" % (k, Sorter.ord_to_str (v))
                else:
                    try:
                        (k, rel) = dict_key_to_rel (k)
                        f = self._dict[k]
                        clauses += [ (k, f.to_sql_value (v), rel) ]
                    except KeyError:
                        raise err.Index, "not an index: %s" % k

        if len(clauses) == 0 and limit:
            raise err.Index, "no index values given!"

        if len (clauses):
            wc = ' AND '.join ([ p[2].join ([ p[0], p[1] ]) for p in clauses ])
            wc = "WHERE %s" % wc
        else:
            wc = ''

        return (wc, limit_sql, order)

    #---------------

    def order (self, order_in):
        r = ''
        if order_in:
            r = order_in
        elif self._orderer:
            r = self._orderer.order ()
        return r

    #---------------

    def select_qry (self, dct, limit):

        (wc, lim_sql, order) = self.where_clause (dct = dct, limit = limit)

        q = make_query ("SELECT",
                        ','.join (self._fnames),
                        "FROM",
                        self._table,
                        wc,
                        self.order (order),
                        lim_sql)

        db.DBH().debug (q)
        return q

    #---------------

    def table (self):
        return self._table

    #--------------------

    def fields (self):
        return self._fields

    #--------------------

    def unique_indices (self):
        return self._unique_indices

    #--------------------

    def classname (self):
        return self._classname

    #--------------------

    def lookup (self, f):
        try:
            r = self._dict[f]
            return r
        except KeyError:
            raise err.Schema, "cannot find field value %s" % f

    #--------------------
        

##=======================================================================
##-----------------------------------------------------------------------

def init (locals_dict):

    lst = []
    for (k,v) in locals_dict.items ():
        if k != '__builtins__' and type(v) is type(BaseObj) and \
                issubclass (v, BaseObj):
            lst += [ v ]

    objs = dict ([ (k.__name__, k) for k in lst ])
    for k in lst:
        k.db_def.materialize (k, objs)
    for k in lst:
        k.db_def.finalize ()

##=======================================================================
##-----------------------------------------------------------------------

class MetaBaseObj (type):

    def __new__ (cls, classname, bases, classdict):

        d = {}
        nd = classdict.copy ()
        for k in nd:
            if k.startswith ('db_'):
                d[k[3:]] = nd[k]
        d['classname'] = classname

        if len(bases) != 1:
            raise err.Inheritance, "wrong number of base classes for DB obj"
        
        if bases[0] is object:
            dbd = DbDef ()
        else:
            dbd = copy.deepcopy (bases[0].db_def).add (**d)

        a = False
        try:
            if d['abstract']:
                a = True
        except KeyError:
            pass
        dbd.set_abstract (a)

        nd['db_def'] = dbd
        x = type.__new__ (cls, classname, bases, nd)
        return x

##=======================================================================
##-----------------------------------------------------------------------

class BaseObj (object):

    #--------------------

    __metaclass__ = MetaBaseObj

    #--------------------

    def _fset (self, n, v):
        setattr (self, "_%s" % n, v)
    def _fget (self, n):
        return getattr (self, "_%s" % n)

    #--------------------

    def _mk_getter (self, n):
        def getter ():
            return self._fget_db (n)
        return getter

    #--------------------

    def _mk_clearer (self, n, v):
        def clearer ():
            self._fset (n, v)
        return clearer

    #--------------------

    def _mk_setter (self, n):
        def setter (v):
            self._fset (n, v)
        return setter

    #--------------------

    def _mk_ch_getter (self, n):
        def ch_getter ():
            return self._fget_ch_db (n)
        return ch_getter

    #--------------------

    def __str__ (self):
        d = dict ([(f.name (),self._fget (f.name ())) 
                   for f in self.db_def.fields () ])
        return self.db_def.classname () + ":" + str (d)

    #--------------------

    def create_db_field (self, f, mutable):
        self._fset (f, None)
        setattr (self, f, self._mk_getter (f))
        if mutable:
            setattr (self, "set_%s" % f, self._mk_setter (f))
        else:
            setattr (self, "clear_%s" % f, self._mk_clearer (f, None))

    #--------------------

    def create_db_child (self, k):
        self._fset (k, None)
        setattr (self, k, self._mk_ch_getter (k))

    #--------------------

    def load_from_dict (self, dct):
        
        for (k,v) in dct.items ():
            try:
                f = self.db_def.lookup (k)
                self._fset (k, f.from_value (v))
            except AttributeError:
                raise err.Schema, "unknown data model field: %s -> %s" % p 
        
    #--------------------

    def __init__ (self, dct = {}, _loaded = False, **kwargs):
        d2 = dct.copy ()
        self._loaded = _loaded
        self.db_def.obj_init (self)
        for k in kwargs.keys ():
            d2[k] = kwargs[k]
        self.load_from_dict (d2)

    #--------------------

    def make_unique_index (self, ifields):
        """Given a set of fields that comprise a unique index, see
        if all of those fields are set.  If so, construct an index
        for the row out of those fields."""
        d = {}
        for n in ifields:
            v = self._fget (n)
            if v is None: return None
            d[n] = v
        return d

    #--------------------

    def to_key_dict (self):

        for ui in self.db_def.unique_indices ():
            d = self.make_unique_index (ui)
            if d: return d

        d = {}
        for f in self.db_def.fields ():
            n = f.name ()
            v = self._fget (n)
            if v is not None:
                d[n] = v
        return d

    #--------------------

    def to_prikey_dict (self):
        v = self.pkv_noload ()
        if v:
            d = { self.pkn () : v }
        else:
            d = self.to_key_dict ()
        return d

    #--------------------

    @classmethod
    def to_seq_name (klass):
        return klass.__name__.lower () + "s"

    #--------------------

    @classmethod
    def purge (klass, **kwargs):

        (wc,lim_sql,order) = klass.db_def.where_clause (kwargs, limit = False)

        q = make_query ("DELETE",
                        "FROM",
                        klass.db_def.table (), 
                        wc,
                        lim_sql)
        db.DBH ().do (q)
        klass.commit ()

    #--------------------

    @classmethod
    def load_cursor (klass, dct):

        q = klass.db_def.select_qry (dct = dct, limit = False)
        cursor = db.DBH ().dictCursor ()
        cursor.execute (q)
        return cursor
    
    #--------------------

    @classmethod
    def load (klass, **kwargs):

        c = klass.load_cursor (dct = kwargs)
        res = [ klass (dct=r, _loaded=True) for r in c.fetchall () ]
        c.close ()
        return res

    #--------------------

    @classmethod
    def iterate (klass, **kwargs):
        return Iterator (klass, klass.load_cursor (dct = kwargs))

    #--------------------

    @classmethod
    def load1 (klass, **kwargs):
        o = klass (dct=kwargs, _loaded=False)
        o.self_load ()
        return o

    #--------------------

    @classmethod
    def pkn (klass):
        return klass.db_def.pk ().name ()

    #--------------------

    def pkv (self):
        """Fetch the primary key value for this object."""
        return self._fget_db (self.db_def.pk().name())

    #--------------------

    def pkv_noload (self):
        return self._fget (self.db_def.pk().name())

    #--------------------

    def pkd (self):
        return { self.pkn () : self.pkv () }

    #--------------------

    def remove (self):
        d = self.to_prikey_dict ()
        self.purge (**d)

    #--------------------

    def self_load (self):

        if self._loaded:
            return self

        d = self.to_key_dict ()
        c = self.load_cursor (d)
        rs = c.fetchall ()
        c.close ()
        if len(rs) == 0:
            raise err.NotFound, "object not found"
        elif len(rs) == 1:
            self.load_from_dict (rs[0])
        else:
            raise err.NotUnique, "many objects found; expected one"

        self._loaded = True
        return self

    #--------------------

    def load_or_create (self):
        try:
            self.self_load ()
        except err.NotFound:
            self.store ()
        return self

    #--------------------

    def store (self):
        if self._loaded:
            self.update ()
        else:
            self.insert ()

    #--------------------

    @classmethod
    def commit (self):
        db.DBH().do ("COMMIT")

    #--------------------

    def insert (self):
        self.insert_or_replace ("INSERT")

    #--------------------

    def replace (self):
        self.insert_or_replace ("REPLACE")

    #--------------------

    def insert_or_replace (self, cmd):

        fields = []
        values = []

        for f in self.db_def.fields ():
            n = f.name ()
            v = self._fget (n)
            if v is not None:
                v = f.to_sql_value (v)
                fields += [ n ]
                values += [ v ]

        q = "%s INTO %s (%s) VALUES(%s)" % \
            ( cmd, self.db_def.table (), ",".join (fields), ",".join (values)) 

        db.DBH().do (q)
        return self.commit ()

    #--------------------

    def update (self):
        
        d = self.to_prikey_dict ()
        (wc, lim_sql,order) = self.db_def.where_clause (dct = d , limit = True)
        up_set = []
        for f in self.db_def.fields ():
            if f.is_mutable ():
                n = f.name ()
                v = f.to_sql_value (self._fget (n))
                up_set += [ (n, v) ]
        up_s = ', '.join ([ "%s=%s" % p for p in up_set ])

        q = make_query ( "UPDATE",
                         self.db_def.table (),
                         "SET",
                         up_s,
                         wc,
                         lim_sql )

        db.DBH().do (q)
        self.commit ()
        
    #--------------------

    def _fget_db (self, n):
        v = self._fget (n)
        if v is None:
            self.self_load ()
            v = self._fget (n)
        return v

    #--------------------

    def _fget_ch_db (self, n):
        v = self._fget (n)
        if v is None:
            (fk, klass) = self.db_def.get_child (n)
            d = { fk.name () : self }
            self._fset (n, klass.load (**d))
        return self._fget (n)

    #--------------------

    @classmethod
    def create_from_pkv (klass, v):
        d = { klass.pkn () : v }
        return klass (dct = d)

    #--------------------

    def equals (self, x):
        v = 0
        if type (x) is int or type(x) is long:
            v = x
        else:
            v = x.pkv ()
        return self.pkv () == v

    #--------------------

    def __eq__ (self, x):
        return self.equals (x)

    #--------------------

    def __neq__ (self, x):
        return not self.equals (x)

##-----------------------------------------------------------------------

class Iterator:

    def __init__ (self, k, c):
        self._cursor = c
        self._klass = k

    def next (self):
        r = self._cursor.fetchone ()
        if r is None:
            self._cursor.close ()
            raise StopIteration
        return self._klass (dct = r, _loaded = True) 

    def __iter__ (self):
        return self
