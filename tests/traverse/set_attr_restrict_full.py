"""Set a member (function) of a module to another with unpicklers that
restrict both the module and the name (replacement belongs to the same module)
--- Doesn't work with either type of unpicklers"""

import io
import os
import pickle
import pickletools
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


# Pain pickle paper calls this "single-level acquisition" (i.e., directly calling
# getattr without any additional parsing of the module/name)
class RestrictedUnpicklerSingle(pickle.Unpickler):

    def find_class(self, module, name):
        if module == "os" and name == "getcwd":
            return getattr(os, name)
        raise pickle.UnpicklingError("global '%s.%s' is forbidden" % (module, name))


if __name__ == "__main__":

    pa = PickleAssembler(proto=4)

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

    # Both fail
    # RestrictedUnpicklerSingle(f).load()
    RestrictedUnpicklerRecursive(f).load()

    print(os.environ.items())
