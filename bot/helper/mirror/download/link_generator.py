from bot import CRYPT
from bot.helper.others.exceptions import DirectDownloadLinkException
from re import (
    findall as re_findall,
    sub as re_sub,
    match as re_match,
    search as re_search,
)
from base64 import b64decode
from requests import get as rget, head as rhead, post as rpost, Session as rsession


def gdtot(url: str) -> str:
    """Gdtot google drive link generator
    By https://github.com/xcscxr"""

    if CRYPT is None:
        raise DirectDownloadLinkException("ERROR: CRYPT cookie not provided")

    match = re_findall(r"https?://(.+)\.gdtot\.(.+)\/\S+\/\S+", url)[0]

    with rsession() as client:
        client.cookies.update({"crypt": CRYPT})
        res = client.get(url)
        res = client.get(
            f"https://{match[0]}.gdtot.{match[1]}/dld?id={url.split('/')[-1]}"
        )
    matches = re_findall("gd=(.*?)&", res.text)
    try:
        decoded_id = b64decode(str(matches[0])).decode("utf-8")
    except:
        raise DirectDownloadLinkException(
            "ERROR: Try in your broswer, mostly file not found or user limit exceeded!"
        )
    return f"https://drive.google.com/open?id={decoded_id}"
