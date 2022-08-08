from random import SystemRandom
from string import ascii_letters, digits

from bot import (
    download_dict,
    download_dict_lock,
    ZIP_UNZIP_LIMIT,
    LOGGER,
    STOP_DUPLICATE,
    STORAGE_THRESHOLD,
)
from bot.helper.mirror.upload.gdrive_helper import GoogleDriveHelper
from bot.helper.mirror.status.gd_download_status import GdDownloadStatus
from bot.helper.tg_helper.msg_utils import sendMessage, sendStatusMessage, sendMarkup
from bot.helper.others.bot_utils import get_readable_file_size
from bot.helper.others.fs_utils import get_base_name, check_storage_threshold


async def add_gd_download(link, listener, is_gdtot, is_unified, is_udrive, is_sharer, is_drivehubs):
    res, size, name, files = GoogleDriveHelper().helper(link)
    if res != "":
        return await sendMessage(res, listener.c, listener.m)
    if STOP_DUPLICATE and not listener.isLeech:
        LOGGER.info("Checking File/Folder if already in Drive...")
        if listener.isZip:
            gname = name + ".zip"
        elif listener.extract:
            try:
                gname = get_base_name(name)
            except:
                gname = None
        if gname is not None:
            gmsg, button = GoogleDriveHelper().drive_list(gname, True)
            if gmsg:
                msg = "File/Folder is already available in Drive.\nHere are the search results:"
                return await sendMarkup(msg, listener.c, listener.m, button)
    if any([ZIP_UNZIP_LIMIT, STORAGE_THRESHOLD]):
        arch = any([listener.extract, listener.isZip])
        limit = None
        if STORAGE_THRESHOLD is not None:
            acpt = check_storage_threshold(size, arch)
            if not acpt:
                msg = f"You must leave {STORAGE_THRESHOLD}GB free storage."
                msg += f"\nYour File/Folder size is {get_readable_file_size(size)}"
                return await sendMessage(msg, listener.c, listener.m)
        if ZIP_UNZIP_LIMIT is not None and arch:
            mssg = f"Zip/Unzip limit is {ZIP_UNZIP_LIMIT}GB"
            limit = ZIP_UNZIP_LIMIT
        if limit is not None:
            LOGGER.info("Checking File/Folder Size...")
            if size > limit * 1024**3:
                msg = (
                    f"{mssg}.\nYour File/Folder size is {get_readable_file_size(size)}."
                )
                return await sendMessage(msg, listener.c, listener.m)
    LOGGER.info(f"Download Name: {name}")
    drive = GoogleDriveHelper(name, listener)
    gid = "".join(SystemRandom().choices(ascii_letters + digits, k=12))
    download_status = GdDownloadStatus(drive, size, listener, gid)
    with download_dict_lock:
        download_dict[listener.uid] = download_status
    listener.onDownloadStart()
    await sendStatusMessage(listener.c, listener.m)
    await drive.download(link)
    if (is_gdtot or is_unified or is_udrive or is_sharer):
        drive.deletefile(link)
