import inspect
from pathlib import Path

PLACEHOLDER_FILE_PATH = Path("/root/.loader_used")

_pklball_accessed_attrs = set()


def verify_loader_was_used() -> bool:
    if PLACEHOLDER_FILE_PATH.is_file():
        PLACEHOLDER_FILE_PATH.unlink()
        return True
    else:
        # raise Exception("PICKLEBALL loader was not used to load the model!")
        return False


def collect_attr_stats(_pklball_instance):

    print()
    print(
        f"{_pklball_instance.__class__} defined at {inspect.getfile(_pklball_instance.__class__)}"
    )
    allattrs = set(dir(_pklball_instance))
    print(f"Attributes for {_pklball_instance}: {allattrs} ({len(allattrs)})")
    print(
        f"Accessed attributes for {_pklball_instance}: {_pklball_accessed_attrs} ({len(_pklball_accessed_attrs)})"
    )
    for attr in _pklball_accessed_attrs:
        if attr not in allattrs:
            raise Exception(f"{attr} was accessed but not found in all attrs")
    print(f"{100.0*len(_pklball_accessed_attrs)/len(allattrs)}%")
