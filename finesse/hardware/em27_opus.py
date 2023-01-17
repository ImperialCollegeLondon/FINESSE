"""Module containing code for sending commands to the OPUS program for the EM27.

Communication is based on a protocol using HTTP and HTML.

The OPUS program must be running on the computer at OPUS_IP for the commands to work.
Note that this is a separate machine from the EM27!
"""
from typing import Optional, cast

import requests
from bs4 import BeautifulSoup
from pubsub import pub

from ..config import OPUS_IP

STATUS_FILENAME = "stat.htm"
COMMAND_FILENAME = "cmd.htm"


def make_request(filename: str, topic: str):
    """Make a request to the OPUS program.

    Args:
        filename: The final part of the path on the HTTP server
        topic: The topic on which to publish the response
    """
    url = f"http://{OPUS_IP}/opusrs/{filename}"
    response = requests.get(url)
    assert response.status_code == 200

    status: Optional[int] = None
    text = ""
    errcode: Optional[int] = None
    errtext = ""
    soup = BeautifulSoup(response.content, "html.parser")
    for td in soup.find_all("td"):
        if "id" not in td.attrs:
            continue

        id = td.attrs["id"]
        data = td.contents[0]
        if id == "STATUS":
            status = int(data)
        elif id == "TEXT":
            text = data
        elif id == "ERRCODE":
            errcode = int(data)
        elif id == "ERRTEXT":
            errtext = data

    if status is None or not text:
        raise ValueError("Required tags not found")
    error = None if errcode is None else (errcode, errtext)

    pub.sendMessage(topic, url=url, status=cast(int, status), text=text, error=error)


def request_status() -> None:
    """Request an update on the device's status."""
    make_request(STATUS_FILENAME, "opus.status.response")


def request_command(command: str) -> None:
    """Request that OPUS run the specified command."""
    make_request(f"{COMMAND_FILENAME}?opusrs{command}", "opus.command.response")


pub.subscribe(request_status, "opus.status.request")
pub.subscribe(request_command, "opus.command.request")
