"""Check if we can call os.environ.items() with a single-acquisition and a
recursive unpickler that restrict the module to 'os' and name to 'getcwd'
--- Both types of unpicklers block it"""

import io
import os
import pickle
import sys

from pickleassem import PickleAssembler


class RestrictedUnpicklerRecursive(pickle.Unpickler):

    def find_class(self, module, name):

        if module != "os" or name != "getcwd":
            raise pickle.UnpicklingError("global %s.%s is forbidden" % (module, name))
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


class RestrictedUnpicklerSingle(pickle.Unpickler):

    def find_class(self, module, name):
        if module == "os" and name == "getcwd":
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

    # Both fail
    # print(RestrictedUnpicklerSingle(f).load())
    print(RestrictedUnpicklerRecursive(f).load())
