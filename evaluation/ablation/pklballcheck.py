from pathlib import Path

PLACEHOLDER_FILE_PATH = Path("/root/.loader_used")


def verify_loader_was_used() -> bool:
    if PLACEHOLDER_FILE_PATH.is_file():
        PLACEHOLDER_FILE_PATH.unlink()
        return True
    else:
        #raise Exception("PICKLEBALL loader was not used to load the model!")
        return False
