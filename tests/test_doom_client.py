from pathlib import Path
from doom.client.config import ClientConfig

def test_client_config_roundtrip(tmp_path: Path):
    path = tmp_path / "client.json"
    config = ClientConfig(control_url="http://localhost:8787", device_id="dev_x", token="tok")
    config.save(path)
    loaded = ClientConfig.load(path)
    assert loaded.device_id == "dev_x"
    assert loaded.token == "tok"
    assert loaded.control_url == "http://localhost:8787"
