# --------------------------------------------------------------- Imports ---------------------------------------------------------------- #

# System
from enum import Enum

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
        element
    ) -> cls:
        try:
            uploading = element.get_attribute('uploading') == ''
        except:
            uploading = False

        try:
            processing = element.get_attribute('processing') == ''
        except:
            processing = False

        try:
            processed = element.get_attribute('checks-can-start') == ''
        except:
            processed = False

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