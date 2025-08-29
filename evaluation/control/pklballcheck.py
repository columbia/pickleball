import inspect
from pathlib import Path
#from pickle import StubObject

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
    pass

#     print()
#     print(
#         f"{_pklball_instance.__class__} defined at {inspect.getfile(_pklball_instance.__class__)}"
#     )
#     allattrs = set(dir(_pklball_instance))
#     print(f"Attributes for {_pklball_instance.__class__}: {allattrs} ({len(allattrs)})")
#     print(
#         f"Accessed attributes for {_pklball_instance.__class__}: {_pklball_accessed_attrs} ({len(_pklball_accessed_attrs)})"
#     )
#     for attr in _pklball_accessed_attrs.copy():
#         if attr not in allattrs:
#             # raise Exception(f"{attr} was accessed but not found in all attrs")
#             _pklball_accessed_attrs.remove(attr)
#     print(
#         f"Total attrs accessed compared to all attrs: {100.0*len(_pklball_accessed_attrs)/len(allattrs)}%"
#     )

#     # XXX This needs to run after the previous part has finished because we need
#     # access every attribute in the instance
#     total_stubs = 0
#     for attrname in dir(_pklball_instance):
#         attr = getattr(_pklball_instance, attrname)
#         if isinstance(attr, StubObject):
#             print(f"Stub object found for {attrname}: {attr}")
#             total_stubs += 1

#     print(
#         f"Total stub objects compared to all attrs: {100.0*total_stubs/len(allattrs)}%"
#     )
