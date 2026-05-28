from pathlib import Path


PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
    b"\x1f\x15\xc4\x89"
    b"\x00\x00\x00\rIDATx\x9cc````\x00\x00\x00\x05\x00\x01"
    b"\x0d\n-\xb4"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_debug_upload_page_renders(client) -> None:
    response = client.get("/debug/uploads")

    assert response.status_code == 200
    assert "Upload screenshots" in response.text
    assert 'enctype="multipart/form-data"' in response.text
    assert "No screenshots uploaded yet." in response.text


def test_debug_upload_saves_and_serves_image(client) -> None:
    response = client.post(
        "/debug/uploads",
        files={"image": ("tablet-shot.png", PNG_BYTES, "image/png")},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert "Image uploaded." in response.text
    assert "tablet-shot" in response.text

    upload_dir = Path(client.app.state.debug_upload_dir)
    stored_files = list(upload_dir.iterdir())
    assert len(stored_files) == 1

    stored_file = stored_files[0]
    assert stored_file.read_bytes() == PNG_BYTES

    media_response = client.get(f"/debug-media/{stored_file.name}")
    assert media_response.status_code == 200
    assert media_response.content == PNG_BYTES


def test_debug_upload_rejects_non_images(client) -> None:
    response = client.post(
        "/debug/uploads",
        files={"image": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert "Only PNG, JPG, GIF, WEBP, and BMP images are supported." in response.text
    assert list(Path(client.app.state.debug_upload_dir).iterdir()) == []
