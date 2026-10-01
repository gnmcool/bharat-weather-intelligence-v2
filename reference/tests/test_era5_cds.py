"""The real ecmwf-datastores-client (pinned) with library retries disabled, and secret redaction (plan §8.3).

HTTP is intercepted at requests.Session.request: nothing reaches the network. These tests prove, against the
installed library code, that one BWI call is exactly one HTTP attempt, whatever the failure.
"""
import json
from importlib import metadata

import pytest
import requests

from reference.tests import KEY
import era5_cds as E
import era5_common as C


@pytest.fixture
def http(monkeypatch):
    calls, script = [], {}

    def fake(self, method, url, *a, **k):
        method = method.upper()
        tail = url.split("/api/")[1]
        calls.append((method, tail, (k.get("headers") or {}).get("PRIVATE-TOKEN")))
        r = requests.Response()
        r.url, r.request = url, requests.Request(method, url).prepare()
        r.headers["content-type"] = "application/json"
        if method == "GET" and tail.startswith("catalogue/v1/messages"):
            r.status_code, r._content = 200, b'{"messages": []}'
            return r
        if method == "GET" and tail == f"retrieve/v1/processes/{C.DATASET}":
            r.status_code, r._content = 200, json.dumps({"id": C.DATASET, "links": []}).encode()
            return r
        x = script.get(method)
        if isinstance(x, Exception):
            raise x
        r.status_code, r.reason, r._content = x or 500, "scripted", json.dumps({"title": f"error {KEY}"}).encode()
        return r

    monkeypatch.setattr(requests.Session, "request", fake)
    return calls, script


def test_pinned_versions():
    assert metadata.version("ecmwf-datastores-client") == "0.5.3"
    assert metadata.version("multiurl") == "0.3.9"


def test_client_built_with_maximum_tries_1(http):
    c = E.CDSClient(KEY)
    assert c.maximum_tries == 1 and E.MAXIMUM_TRIES == 1


@pytest.mark.parametrize("status", [500, 502, 503, 504, 429, 408])
def test_submit_retriable_status_is_attempted_exactly_once(http, status):
    calls, script = http
    script["POST"] = status
    c = E.CDSClient(KEY)
    with pytest.raises(E.CDSHTTPError) as ei:
        c.submit(C.build_requests("2026-10")["month"])
    assert ei.value.status == status
    posts = [x for x in calls if x[0] == "POST"]
    assert len(posts) == 1 and posts[0][1] == f"retrieve/v1/processes/{C.DATASET}/execution"
    assert KEY not in str(ei.value)


def test_submit_connection_error_is_attempted_once_and_classified_transport(http):
    calls, script = http
    script["POST"] = requests.ConnectionError(f"reset while sending PRIVATE-TOKEN: {KEY}")
    c = E.CDSClient(KEY)
    with pytest.raises(E.CDSTransportError) as ei:
        c.submit(C.build_requests("2026-10")["boundary"])
    assert sum(1 for x in calls if x[0] == "POST") == 1 and KEY not in str(ei.value)


def test_status_errors_single_attempt(http):
    calls, script = http
    script["GET"] = 503
    c = E.CDSClient(KEY)
    n0 = len(calls)
    with pytest.raises(E.CDSHTTPError):
        c.status("0000-rid")
    assert len(calls) - n0 == 1


def test_submit_4xx_is_http_error(http):
    calls, script = http
    script["POST"] = 403
    with pytest.raises(E.CDSHTTPError) as ei:
        E.CDSClient(KEY).submit(C.build_requests("2026-10")["month"])
    assert ei.value.status == 403 and KEY not in str(ei.value)


def test_key_is_sent_only_as_header(http):
    calls, script = http
    script["POST"] = 500
    with pytest.raises(E.CDSError):
        E.CDSClient(KEY).submit(C.build_requests("2026-10")["month"])
    assert all(KEY not in x[1] for x in calls)                     # never in a URL


def test_missing_key_refused():
    with pytest.raises(E.CDSError, match="CDS_API_KEY"):
        E.CDSClient("")


def test_redact():
    s = f"boom PRIVATE-TOKEN: {KEY} and again {KEY} 'PRIVATE-TOKEN': 'abc123'"
    out = E.redact(s, (KEY,))
    assert KEY not in out and "abc123" not in out and out.count("[REDACTED]") >= 3


def test_status_classes():
    assert [E.status_class(s) for s in ("accepted", "running", "successful", "failed", "rejected", "weird")] == \
        ["queued", "queued", "successful", "failed", "failed", "unknown"]


# ---------------------------------------------------------------- credential preflight (account endpoints only)
@pytest.fixture
def account_http(monkeypatch):
    """Intercepts HTTP: account endpoints answer from `replies` (status or exception); every call is recorded."""
    calls, replies = [], {"auth": 200, "licences": 200, "licence_body": {"licences": [{"id": "x", "revision": 3}]}}

    def fake(self, method, url, *a, **k):
        method, tail = method.upper(), url.split("/api/")[1]
        calls.append((method, tail, k.get("params")))
        r = requests.Response()
        r.url, r.request = url, requests.Request(method, url).prepare()
        r.headers["content-type"] = "application/json"
        if tail.startswith("catalogue/v1/messages"):
            r.status_code, r._content = 200, b'{"messages": []}'
            return r
        key = "auth" if tail == "profiles/v1/account/verification/pat" else \
            "licences" if tail == "profiles/v1/account/licences" else None
        x = replies.get(key, 500)
        if isinstance(x, Exception):
            raise x
        body = {"id": "account-id", "email": "someone@example.invalid"} if key == "auth" else replies["licence_body"]
        if x != 200:
            body = {"title": f"error {KEY}"}
        r.status_code, r.reason, r._content = x, "scripted", json.dumps(body).encode()
        return r

    monkeypatch.setattr(requests.Session, "request", fake)
    return calls, replies


def test_check_authentication_endpoint_single_attempt_no_retrieve(account_http):
    calls, replies = account_http
    c = E.CDSClient(KEY)
    assert c.check_authentication() is None                       # response (account details) is discarded
    auth = [x for x in calls if x[1] == "profiles/v1/account/verification/pat"]
    assert [x[0] for x in auth] == ["POST"]
    assert not any(x[1].startswith("retrieve/") for x in calls)   # no job endpoint touched


@pytest.mark.parametrize("status", [401, 403, 500, 503, 429])
def test_check_authentication_failures_are_classified_once(account_http, status):
    calls, replies = account_http
    replies["auth"] = status
    with pytest.raises(E.CDSHTTPError) as ei:
        E.CDSClient(KEY).check_authentication()
    assert ei.value.status == status and KEY not in str(ei.value)
    assert sum(1 for x in calls if x[1] == "profiles/v1/account/verification/pat") == 1
    assert not any(x[1].startswith("retrieve/") for x in calls)


def test_check_authentication_transport_error(account_http):
    calls, replies = account_http
    replies["auth"] = requests.ConnectionError(f"reset PRIVATE-TOKEN: {KEY}")
    with pytest.raises(E.CDSTransportError) as ei:
        E.CDSClient(KEY).check_authentication()
    assert KEY not in str(ei.value)


def test_accepted_dataset_licences(account_http):
    calls, replies = account_http
    c = E.CDSClient(KEY)
    assert c.accepted_dataset_licences() == [{"id": "x", "revision": 3}]
    lic = [x for x in calls if x[1] == "profiles/v1/account/licences"]
    assert len(lic) == 1 and lic[0][0] == "GET" and lic[0][2] == {"scope": "dataset"}
    replies["licence_body"] = {"licences": []}
    assert c.accepted_dataset_licences() == []
    assert not any(x[1].startswith("retrieve/") for x in calls)
    assert "does not" in E.CDSClient.accepted_dataset_licences.__doc__ and "PARTIAL" in \
        E.CDSClient.accepted_dataset_licences.__doc__
