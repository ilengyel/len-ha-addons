import contextlib
import http.server
import json
import re
import subprocess
import threading
import time
import uuid
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import pytest


ADDON = Path(__file__).resolve().parents[1]
PREFIX = "/api/hassio_ingress/test-session"


def docker(*args, **kwargs):
    result = subprocess.run(
        ["docker", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=180, **kwargs
    )
    if result.returncode:
        pytest.fail(
            "docker %s failed:\n%s\n%s" % (
                " ".join(args), result.stdout.decode(errors="replace"),
                result.stderr.decode(errors="replace"),
            )
        )
    return result


class Robot(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/disconnect":
            self.close_connection = True
            return
        if path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.end_headers()
            self.wfile.write(b"data: first\n\n")
            self.wfile.flush()
            time.sleep(2)
            self.wfile.write(b"data: second\n\n")
            return
        if path == "/websocket":
            self.protocol_version = "HTTP/1.1"
            self.send_response(101)
            self.send_header("Upgrade", "websocket")
            self.send_header("Connection", "Upgrade")
            self.end_headers()
            self.wfile.write(b"\x81\x04test")
            self.close_connection = True
            return
        redirects = {
            "/redirect": "/settings?tab=map",
            "/absolute": "http://host.docker.internal:%s/settings" % self.server.server_port,
            "/prefixed": PREFIX + "/settings",
        }
        if path in redirects:
            self.send_response(302)
            self.send_header("Location", redirects[path])
            self.end_headers()
            return
        if path == "/missing":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"robot error")
            return
        if path == "/":
            body = b'<script src="./static/app.js"></script>'
        elif path == "/static/app.js":
            body = b"/* robot frontend */"
        else:
            self.do_POST()
            return
        self.send_response(200)
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Valetudo-Version", "test")
        self.end_headers()
        self.wfile.write(json.dumps({
            "path": self.path, "method": self.command,
            "body": body.decode(), "headers": dict(self.headers),
        }).encode())


@pytest.fixture(scope="module")
def image():
    tag = "valetudo-proxy-test:" + uuid.uuid4().hex
    docker("version")
    docker("build", "-t", tag, str(ADDON))
    try:
        yield tag
    finally:
        docker("image", "rm", "-f", tag)


@pytest.fixture(scope="module")
def robot():
    server = http.server.ThreadingHTTPServer(("0.0.0.0", 0), Robot)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_port
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@contextlib.contextmanager
def running_proxy(image, data):
    name = "valetudo-proxy-test-" + uuid.uuid4().hex
    docker(
        "run", "-d", "--name", name, "--cap-add", "NET_ADMIN",
        "--mount", "type=bind,source=%s,target=/data,readonly" % data, image,
    )
    try:
        # Only the test container gets this loopback alias/capability.
        docker("exec", name, "ip", "addr", "add", "172.30.32.2/32", "dev", "lo")
        for _ in range(60):
            probe = subprocess.run(
                ["docker", "exec", name, "curl", "-s", "--max-time", "1",
                 "http://127.0.0.1:8099/"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10,
            )
            if probe.returncode == 0:
                break
            time.sleep(0.25)
        else:
            pytest.fail(docker("logs", name).stdout.decode())
        docker("exec", name, "nginx", "-t")
        yield name
    finally:
        docker("rm", "-f", name)


@pytest.fixture(scope="module")
def proxy(image, robot, tmp_path_factory):
    data = tmp_path_factory.mktemp("valetudo-options")
    (data / "options.json").write_text(json.dumps({
        "robot_host": "host.docker.internal", "robot_port": robot,
    }))
    with running_proxy(image, data) as name:
        yield name


def curl_command(proxy, ingress_path, *args, allowed=True):
    assert ingress_path.startswith(PREFIX + "/")
    stripped = ingress_path[len(PREFIX):]
    return [
        "exec", proxy, "curl", "--silent", "--show-error", "--max-time", "10",
        *(["--interface", "172.30.32.2"] if allowed else []),
        "-H", "X-Ingress-Path: " + PREFIX, *args,
        "http://127.0.0.1:8099" + stripped,
    ]


def request(proxy, path="/", *args, allowed=True):
    response = docker(*curl_command(
        proxy, PREFIX + path, "--include", *args, allowed=allowed
    )).stdout
    headers, body = response.split(b"\r\n\r\n", 1)
    lines = headers.decode().split("\r\n")
    return int(lines[0].split()[1]), {
        key.lower(): value.strip()
        for key, value in (line.split(":", 1) for line in lines[1:])
    }, body


def test_ingress_assets_and_api_forwarding(proxy, robot):
    status, _, html = request(proxy)
    assert status == 200
    asset = re.search(rb'src="([^"]+)"', html).group(1).decode()
    asset_url = urljoin("http://ha" + PREFIX + "/", asset)
    assert request(proxy, urlsplit(asset_url).path[len(PREFIX):])[2] == b"/* robot frontend */"

    status, headers, body = request(
        proxy, "/api/v2/echo?room=1&room=2", "-X", "POST",
        "-H", "Content-Type: application/json", "--data", '{"action":"mock-only"}',
        "-H", "Authorization: test-auth", "-H", "Cookie: test-cookie",
        "-H", "X-Remote-User-Id: test-user", "-H", "X-Remote-User-Name: tester",
        "-H", "X-Remote-User-Display-Name: Test User",
        "-H", "X-Forwarded-For: 192.0.2.1",
    )
    assert status == 200
    assert headers["x-valetudo-version"] == "test"
    echoed = json.loads(body)
    assert echoed["path"] == "/api/v2/echo?room=1&room=2"
    assert echoed["method"] == "POST"
    assert json.loads(echoed["body"]) == {"action": "mock-only"}
    forwarded = {key.lower(): value for key, value in echoed["headers"].items()}
    assert forwarded["host"] == "host.docker.internal:%s" % robot
    assert not {
        "authorization", "cookie", "x-remote-user-id", "x-remote-user-name",
        "x-remote-user-display-name", "x-ingress-path", "x-forwarded-for",
    }.intersection(forwarded)


@pytest.mark.parametrize("path,location", [
    ("/redirect", PREFIX + "/settings?tab=map"),
    ("/absolute", PREFIX + "/settings"),
    ("/prefixed", PREFIX + "/settings"),
])
def test_redirects_stay_under_ingress(proxy, path, location):
    status, headers, _ = request(proxy, path)
    assert status == 302
    assert headers["location"] == location


def test_errors_and_source_restriction(proxy):
    assert request(proxy, allowed=False)[0] == 403
    status, _, body = request(proxy, "/missing")
    assert status == 404
    assert body == b"robot error"
    assert request(proxy, "/disconnect")[0] == 502


def test_events_are_not_buffered(proxy):
    command = ["docker", *curl_command(proxy, PREFIX + "/events", "--no-buffer")]
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as stream:
        try:
            assert stream.stdout.readline() == b"data: first\n"
            first = time.monotonic()
            assert stream.stdout.readline() == b"\n"
            assert stream.stdout.readline() == b"data: second\n"
            second = time.monotonic()
            assert second - first > 1
            assert stream.wait(timeout=10) == 0
        finally:
            if stream.poll() is None:
                stream.kill()
                stream.wait()


def test_websocket_upgrade(proxy):
    status, headers, body = request(
        proxy, "/websocket", "-H", "Upgrade: websocket", "-H", "Connection: Upgrade",
    )
    assert status == 101
    assert headers["upgrade"] == "websocket"
    assert body == b"\x81\x04test"


@pytest.mark.parametrize("host,port", [
    ("127.0.0.1", 1),
    ("robot.example.invalid", 80),
])
def test_offline_robot_does_not_prevent_startup(image, tmp_path, host, port):
    (tmp_path / "options.json").write_text(json.dumps({
        "robot_host": host, "robot_port": port,
    }))
    with running_proxy(image, tmp_path) as proxy:
        assert request(proxy)[0] == 502


@pytest.mark.parametrize("host,port", [
    ("http://robot.example.invalid/", 80),
    ("robot;include /tmp/other;", 80),
    ("robot", 0),
    ("robot", 65536),
    ("robot", "not-a-port"),
])
def test_invalid_options_fail(image, tmp_path, host, port):
    (tmp_path / "options.json").write_text(json.dumps({
        "robot_host": host, "robot_port": port,
    }))
    result = subprocess.run([
        "docker", "run", "--rm", "--entrypoint", "/usr/bin/bashio",
        "--mount", "type=bind,source=%s,target=/data,readonly" % tmp_path,
        image, "/etc/services.d/nginx/run",
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30)
    assert result.returncode != 0
    logs = result.stdout + result.stderr
    assert b"robot_host must" in logs or b"robot_port must" in logs
