from pathlib import Path

PLACEHOLDER_FILE_PATH = Path("/root/.loader_used")


def verify_loader_was_used() -> bool:
    if PLACEHOLDER_FILE_PATH.is_file():
        PLACEHOLDER_FILE_PATH.unlink()
        return True
    else:
        # raise Exception("PICKLEBALL loader was not used to load the model!")
        return False


def collect_attr_stats(_pklball_instance):

    print()
    # allattrs = set(
    #     list(_pklball_instance.__dict__.keys())
    #     + list(_pklball_instance.__class__.__dict__.keys())
    # )
    allattrs = set(dir(_pklball_instance))
    allattrs.remove("_pklball_accessed_attrs")
    print(f"Attributes for {_pklball_instance}: {allattrs} ({len(allattrs)})")
    accessed_attrs = _pklball_instance._pklball_accessed_attrs
    print(
        f"Accessed attributes for {_pklball_instance}: {accessed_attrs} ({len(accessed_attrs)})"
    )
    for attr in accessed_attrs:
        if attr not in allattrs:
            raise Exception(f"{attr} was accessed but not found in all attrs")
    print(f"{100.0*len(accessed_attrs)/len(allattrs)}%")
