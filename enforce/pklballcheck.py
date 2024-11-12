from pathlib import Path

PLACEHOLDER_FILE_PATH = Path("/root/.loader_used")


def verify_loader_was_used():
    if PLACEHOLDER_FILE_PATH.is_file():
        PLACEHOLDER_FILE_PATH.unlink()
    else:
        raise Exception("PICKLEBALL loader was not used to load the model!")
