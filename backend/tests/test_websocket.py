import pytest
import uuid
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.services.job_bus import JobBus, job_bus

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.mark.anyio
async def test_job_bus_connection_and_broadcast_lifecycle():
    bus = JobBus()
    dataset_id = "test-dataset-123"

    mock_ws1 = AsyncMock()
    mock_ws2 = AsyncMock()

    # 1. Connect
    await bus.connect(dataset_id, mock_ws1)
    await bus.connect(dataset_id, mock_ws2)
    assert len(bus.active_connections[dataset_id]) == 2
    mock_ws1.accept.assert_awaited_once()
    mock_ws2.accept.assert_awaited_once()

    # 2. Broadcast
    msg = {"type": "pipeline_transition", "event": "sandbox_executing", "attempt": 1}
    await bus.broadcast(dataset_id, msg)
    mock_ws1.send_json.assert_awaited_once_with(msg)
    mock_ws2.send_json.assert_awaited_once_with(msg)

    # 3. Disconnect ws1
    bus.disconnect(dataset_id, mock_ws1)
    assert len(bus.active_connections[dataset_id]) == 1

    # 4. Handle failure during broadcast (auto-disconnect)
    mock_ws2.send_json.side_effect = Exception("Connection closed")
    await bus.broadcast(dataset_id, {"type": "ping"})
    assert dataset_id not in bus.active_connections


def test_websocket_endpoint_streaming():
    client = TestClient(app)
    dataset_id = f"ds-{uuid.uuid4()}"

    with client.websocket_connect(f"/ws/datasets/{dataset_id}/status") as websocket:
        assert dataset_id in job_bus.active_connections
        assert len(job_bus.active_connections[dataset_id]) == 1

        # Simulate broadcast from the job bus
        import anyio
        async def do_broadcast():
            await job_bus.broadcast(dataset_id, {
                "type": "run_started",
                "run_id": "r-1",
                "question_id": "q-1",
                "status": "Generating analysis code..."
            })
        anyio.run(do_broadcast)

        data = websocket.receive_json()
        assert data["type"] == "run_started"
        assert data["run_id"] == "r-1"
        assert data["status"] == "Generating analysis code..."

    # Once context manager exits, websocket disconnects
    # Note: disconnect is handled via WebSocketDisconnect exception inside the route
