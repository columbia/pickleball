import pickle

from pickleassem import PickleAssembler


class TestClass:
    def foo(self):
        print("Hello from foo")


if __name__ == "__main__":

    pa = PickleAssembler(proto=4)

    pa.push_short_binunicode("__main__")
    pa.push_short_binunicode("TestClass")
    pa.build_stack_global()
    pa.push_mark()
    pa.push_none()
    pa.push_empty_dict()
    pa.push_binstring("foo")
    pa.push_short_binunicode("importme")
    pa.push_short_binunicode("import_this")
    pa.build_stack_global()
    pa.build_setitem()
    pa.build_tuple()
    pa.build_build()

    payload = pa.assemble()

    pickle.loads(payload)

    TestClass().foo()
