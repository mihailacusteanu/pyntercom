import time
from src.helper.sleep import sleep
from src.config import MOCK_SLEEP

def test_sleep_mocked(monkeypatch, capsys):
    """Test that sleep prints mock message when MOCK_SLEEP is True and force_real is False."""
    monkeypatch.setattr("src.config.MOCK_SLEEP", True)
    sleep(1.0)

    # Capture the printed output
    captured = capsys.readouterr()
    assert "Mock sleep for 1.0 seconds" in captured.out

def test_sleep_forced_real(monkeypatch, capsys):
    """Test that sleep actually sleeps when force_real=True."""
    monkeypatch.setattr("src.config.MOCK_SLEEP", False)
    start_time = time.time()
    sleep(0.5)
    elapsed_time = time.time() - start_time
    assert (
        elapsed_time >= 0.5
    ), f"Expected at least 0.5 seconds, but got {elapsed_time} seconds"


def test_sleep_respects_mock_config():
    """Test that sleep behavior depends on MOCK_SLEEP config when force_real=False."""
    if MOCK_SLEEP:
        # Should be mocked - test with capsys
        def test_with_capsys(capsys):
            sleep(2.0)
            captured = capsys.readouterr()
            assert "Mock sleep for 2.0 seconds" in captured.out

        # Run the nested test (this is a bit awkward, see alternative below)
        import sys
        from io import StringIO

        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        sleep(2.0)
        sys.stdout = old_stdout
        assert "Mock sleep for 2.0 seconds" in captured_output.getvalue()
    else:
        # Should actually sleep
        start_time = time.time()
        sleep(0.3)
        elapsed_time = time.time() - start_time
        assert elapsed_time >= 0.3
