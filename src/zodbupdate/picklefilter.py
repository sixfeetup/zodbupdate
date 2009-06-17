##############################################################################
#
# Copyright (c) 2009 Zope Corporation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""Tools for filtering a pickle opcode stream (as generated by
pickletools.genops) and reassemblying the pickle.
"""

import ZODB
import sys
import struct
import pickle
import pickletools
import StringIO

# The following functions were created on the basis of the code found in
# pickle.py. They reflect all opcodes that pickle knows about and how they get
# written to the output stream under the knowledge how pickletools.genops
# parses the opcode arguments.

packi = lambda arg:struct.pack('<i', arg)
reprn = lambda arg:repr(arg)+'\n'
strn = lambda arg:str(arg)+'\n'
fact_ref = lambda arg:arg.replace(' ','\n')+'\n'
arg_len = lambda arg:packi(len(arg))+arg
unicode_escape = lambda arg:arg.replace('\\', '\\u005c').replace('\n', '\\u000a').encode('raw-unicode-escape')+'\n'

noargs = [pickle.EMPTY_TUPLE,
          pickle.MARK,
          pickle.STOP,
          pickle.NONE,
          pickle.BINPERSID,
          pickle.REDUCE,
          pickle.EMPTY_LIST,
          pickle.APPEND,
          pickle.BUILD,
          pickle.DICT,
          pickle.APPENDS,
          pickle.OBJ,
          pickle.SETITEM,
          pickle.TUPLE,
          pickle.SETITEMS,
          pickle.EMPTY_DICT,
          pickle.LIST,
          pickle.POP,
          pickle.POP_MARK,
          pickle.DUP,
          pickle.NEWOBJ,
          pickle.TUPLE1,
          pickle.TUPLE2,
          pickle.TUPLE3,
          pickle.NEWTRUE,
          pickle.NEWFALSE]

def _pickle_int(arg):
    if type(arg) is int:
        return reprn(arg)
    else:
        return '0%s\n' % int(arg)
        
generators = {
    pickle.BINFLOAT: lambda arg:struct.pack('>d', arg),
    pickle.FLOAT: reprn,
    pickle.INT: _pickle_int,
    pickle.BININT: packi,
    pickle.BININT1: chr,
    pickle.LONG: reprn,
    pickle.BININT2: lambda arg:"%c%c" % (arg&0xff, arg>>8),
    pickle.STRING: reprn,
    pickle.BINSTRING: arg_len,
    pickle.SHORT_BINSTRING: lambda arg:chr(len(arg)) + arg,
    pickle.BINUNICODE: lambda arg:arg_len(arg.encode('utf-8')),
    pickle.GLOBAL: fact_ref,
    pickle.INST: fact_ref,
    pickle.BINGET: chr,
    pickle.LONG_BINGET: packi,
    pickle.PUT: reprn,
    pickle.GET: reprn,
    pickle.BINPUT: chr,
    pickle.LONG_BINPUT: packi,
    pickle.PERSID: strn,
    pickle.UNICODE: unicode_escape,
    pickle.PROTO: chr,
    pickle.EXT1: chr,
    pickle.EXT2: lambda arg:"%c%c" % (arg&0xff, arg>>8),
    pickle.EXT4: packi,
    pickle.LONG1: lambda arg:chr(len(pickle.encode_long(arg)))+pickle.encode_long(arg),
    pickle.LONG4: lambda arg:arg_len(pickle.encode_long(arg)),
}


def to_pickle_chunk(opcode, arg):
    """Transform an operation and its argument into pickle format."""
    chunk = opcode
    if opcode in noargs:
        pass
    elif opcode in generators:
        generated = generators[opcode](arg)
        chunk += generated
    else:
        raise ValueError('Unknown opcode: %s' % (opcode,))
    return chunk


def filter(f, pickle_data):
    """Apply filter function to each opcode of a pickle, return new pickle.

    Calls function for each opcode with the arguments (code, arg) as created
    by the pickletools.genops function. 

    The filter function is expected to return a new (code, arg) tuple or None
    which causes the old (code, arg) tuple to be placed into the stream again.

    """
    new = StringIO.StringIO()
    for op, arg, pos in pickletools.genops(pickle_data):
        op = op.code
        result = f(op, arg)
        if result is not None:
            op, arg = result
        new.write(to_pickle_chunk(op, arg))
    return new.getvalue()
