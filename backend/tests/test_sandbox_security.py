import pytest
from app.services.sandbox import sandbox_service

def test_sandbox_blocks_network_socket_access(tmp_path):
    dataset_file = tmp_path / "input.csv"
    dataset_file.write_text("x,y\n1,2\n", encoding="utf-8")

    malicious_network_code = """
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("8.8.8.8", 80))
"""
    result = sandbox_service.execute_code(malicious_network_code, str(dataset_file), "sec_net", attempt=1)
    assert not result.is_success
    assert "PermissionError" in result.stderr or "Network access is disabled" in result.stderr

def test_sandbox_scrubs_host_environment_secrets(tmp_path):
    dataset_file = tmp_path / "input.csv"
    dataset_file.write_text("a,b\n3,4\n", encoding="utf-8")

    inspect_env_code = """
import os
import json
secrets = [k for k in os.environ.keys() if any(w in k.upper() for w in ['KEY', 'SECRET', 'TOKEN', 'PASSWORD'])]
print('RESULT_JSON:')
print(json.dumps({"leaked_secrets": secrets}))
"""
    result = sandbox_service.execute_code(inspect_env_code, str(dataset_file), "sec_env", attempt=1)
    assert result.is_success
    assert '"leaked_secrets": []' in result.stdout
