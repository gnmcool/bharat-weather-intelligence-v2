"""Thin CDS client wrapper (D2 plan §7–§8).

Uses ecmwf-datastores-client 0.5.3 (pinned) with **maximum_tries=1**: its multiurl.robust wrapper then makes exactly
one HTTP call per operation (no retry on any status or connection error) and its downloader runs with
maximum_retries=0. All retries are BWI's own (era5_run.RetryPolicy). The client's blocking helpers
(`retrieve`, `submit_and_wait_on_results`, `Remote.download` before completion) are never used: jobs are polled by
request id in era5_run.

Every exception leaving this module is one of the classes below, with its text redacted (the CDS key never appears).
"""
from __future__ import annotations

import pathlib
import re

from era5_common import CDS_URL, DATASET

MAXIMUM_TRIES = 1                         # library-level retries disabled (plan §8.3, §15 item 9)
QUEUED = {"accepted", "queued", "running"}
SUCCESSFUL = {"successful"}
FAILED = {"failed", "rejected", "dismissed", "deleted"}


class CDSError(RuntimeError):
    kind = "cds"


class CDSTransportError(CDSError):
    """Connection error or timeout: the outcome of the call is unknown."""
    kind = "transport"


class CDSHTTPError(CDSError):
    kind = "http"

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = int(status)


class CDSJobFailed(CDSError):
    kind = "job_failed"


class CDSDownloadError(CDSError):
    """The downloaded file is incomplete (size differs from the announced length)."""
    kind = "download"


_TOKEN_RE = re.compile(r"(PRIVATE-TOKEN['\"]?\s*[:=]\s*['\"]?)([^\s'\",}]+)", re.I)


def redact(text: object, secrets: tuple[str, ...] = ()) -> str:
    """Remove the key (and anything shaped like a token header) from text that may be recorded or printed."""
    s = str(text)
    for sec in secrets:
        if sec:
            s = s.replace(sec, "[REDACTED]")
    return _TOKEN_RE.sub(r"\1[REDACTED]", s)[:1000]


def _classify(exc: Exception, secrets: tuple[str, ...]) -> CDSError:
    import requests
    msg = redact(f"{type(exc).__name__}: {exc}", secrets)
    if isinstance(exc, CDSError):
        return exc
    if isinstance(exc, requests.HTTPError) and exc.response is not None:
        return CDSHTTPError(exc.response.status_code, msg)
    if isinstance(exc, (requests.ConnectionError, requests.Timeout, requests.exceptions.ChunkedEncodingError)):
        return CDSTransportError(msg)
    try:
        from ecmwf.datastores.processing import DownloadError, ProcessingFailedError
        if isinstance(exc, ProcessingFailedError):
            return CDSJobFailed(msg)
        if isinstance(exc, DownloadError):
            return CDSDownloadError(msg)
    except ImportError:  # pragma: no cover
        pass
    return CDSTransportError(msg)     # anything unexpected: treat the outcome as unknown (never as success)


class CDSClient:
    """Submit once, read status by request id, download a completed result by request id."""

    def __init__(self, key: str, url: str = CDS_URL, client=None):
        if not key:
            raise CDSError("CDS_API_KEY is not set")
        self._secrets = (key,)
        if client is None:
            from ecmwf.datastores import Client
            client = Client(url=url, key=key, maximum_tries=MAXIMUM_TRIES, progress=False)
        self._c = client

    @property
    def maximum_tries(self) -> int:
        return int(getattr(self._c, "maximum_tries", MAXIMUM_TRIES))

    def submit(self, request: dict) -> str:
        try:
            return str(self._c.submit(DATASET, request).request_id)
        except Exception as e:  # noqa: BLE001
            raise _classify(e, self._secrets) from None

    def status(self, request_id: str) -> str:
        try:
            s = str(self._c.get_remote(request_id).status)
        except Exception as e:  # noqa: BLE001
            raise _classify(e, self._secrets) from None
        return s

    def download(self, request_id: str, target: pathlib.Path) -> dict:
        """Download a *completed* job's result. Returns the announced size."""
        try:
            res = self._c.get_remote(request_id).get_results()
            size = int(res.content_length)
            res.download(str(target))
        except Exception as e:  # noqa: BLE001
            raise _classify(e, self._secrets) from None
        got = pathlib.Path(target).stat().st_size
        if got != size:
            raise CDSDownloadError(f"downloaded {got} bytes, announced {size}")
        return {"announced_bytes": size}

    # ------------------------------------------------------------ credential preflight (no job, no data)
    def check_authentication(self) -> None:
        """POST {api}/profiles/v1/account/verification/pat (one attempt). Raises a CDSError on failure.

        The response may contain account details; it is deliberately discarded and never returned or recorded."""
        try:
            self._c.check_authentication()
        except Exception as e:  # noqa: BLE001
            raise _classify(e, self._secrets) from None

    def accepted_dataset_licences(self) -> list[dict]:
        """GET {api}/profiles/v1/account/licences?scope=dataset (one attempt): [{"id", "revision"}, ...].

        PARTIAL check only: the client cannot tell which licence a dataset requires, so a non-empty list does not
        prove that the ERA5 terms specifically were accepted."""
        try:
            lic = self._c.get_accepted_licences(scope="dataset")
        except Exception as e:  # noqa: BLE001
            raise _classify(e, self._secrets) from None
        return [{"id": str(x.get("id")), "revision": x.get("revision")} for x in (lic or []) if isinstance(x, dict)]

    def redact(self, text: object) -> str:
        return redact(text, self._secrets)


def status_class(status: str) -> str:
    s = status.lower()
    if s in SUCCESSFUL:
        return "successful"
    if s in FAILED:
        return "failed"
    if s in QUEUED:
        return "queued"
    return "unknown"
