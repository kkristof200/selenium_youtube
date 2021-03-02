# --------------------------------------------------------------- Imports ---------------------------------------------------------------- #

# System
from enum import Enum

# Pip
from selenium_firefox.firefox import Firefox

# ---------------------------------------------------------------------------------------------------------------------------------------- #



# --------------------------------------------------------- class: UploadStatus ---------------------------------------------------------- #

class UploadStatus(Enum):
    UNIDENTIFIED                = -1
    UPLOADING                   = 0
    PROCESSING_SD               = 1
    PROCESSED_SD_PROCESSING_HD  = 2
    PROCESSED_ALL               = 3

    # ------------------------------------------------------------- Init ------------------------------------------------------------- #

    @classmethod
    def get_status(
        cls,
        ff: Firefox,
        element
    ):
        attriutes = ff.get_attributes(element)

        uploading = 'uploading' in attriutes and attriutes['uploading'] == ''
        processing = 'processing' in attriutes and attriutes['processing'] == ''
        processed = 'checks-can-start' in attriutes and attriutes['checks-can-start'] == ''

        if uploading:
            return UploadStatus.UPLOADING
        elif processing and processed:
            return UploadStatus.PROCESSED_SD_PROCESSING_HD
        elif processing:
            return UploadStatus.PROCESSING_SD
        elif processed:
            return UploadStatus.PROCESSED_ALL

        return UploadStatus.UNIDENTIFIED


# ---------------------------------------------------------------------------------------------------------------------------------------- #