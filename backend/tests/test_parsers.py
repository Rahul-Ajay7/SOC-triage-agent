from app.parsers import auth_log


def test_parse_failed_invalid_user():
    line = ("Jun 19 03:11:01 web-01 sshd[8801]: Failed password for invalid "
            "user admin from 45.155.205.233 port 40122 ssh2")
    p = auth_log.parse_line(line)
    assert p["status"] == "failure"
    assert p["user"] == "admin"
    assert p["src_ip"] == "45.155.205.233"
    assert p["invalid_user"] is True
    assert p["port"] == 40122


def test_parse_accepted_publickey():
    line = "Jun 19 09:14:02 web-01 sshd[2041]: Accepted publickey for alice from 10.0.0.42 port 51022 ssh2"
    p = auth_log.parse_line(line)
    assert p["status"] == "success"
    assert p["user"] == "alice"
    assert p["method"] == "publickey"


def test_non_auth_line_returns_none():
    assert auth_log.parse_line("Jun 19 09:14:02 web-01 systemd[1]: Started thing") is None


def test_summarize_counts():
    text = (
        "Jun 19 03:11:01 web-01 sshd[1]: Failed password for root from 1.2.3.4 port 22 ssh2\n"
        "Jun 19 03:11:05 web-01 sshd[2]: Accepted password for root from 1.2.3.4 port 22 ssh2\n"
    )
    s = auth_log.summarize(auth_log.parse_log(text))
    assert s["failures"] == 1
    assert s["successes"] == 1
    assert s["success_after_failures"] is True
    assert s["src_ip"] == "1.2.3.4"
