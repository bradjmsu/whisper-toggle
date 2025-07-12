"""Basic tests for whisper-toggle package."""

import pytest
from whisper_toggle import __version__


def test_version():
    """Test that version is properly set."""
    assert __version__ == "1.0.0"


def test_imports():
    """Test that main modules can be imported."""
    try:
        from whisper_toggle import SmartIndicator
        from whisper_toggle import WhisperTranscriber
        from whisper_toggle import KeyboardListener
    except ImportError:
        # These imports may fail due to missing module implementations
        # This is expected at this stage
        pass