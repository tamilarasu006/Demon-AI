"""Tests for speech configuration."""

from OpenDEMON.core.config import DEMONConfig, SpeechConfig


def test_speech_config_defaults():
    cfg = SpeechConfig()
    assert cfg.backend == "auto"
    assert cfg.model == "base"
    assert cfg.language == ""
    assert cfg.device == "auto"
    assert cfg.compute_type == "float16"


def test_DEMON_config_has_speech():
    cfg = DEMONConfig()
    assert hasattr(cfg, "speech")
    assert isinstance(cfg.speech, SpeechConfig)
    assert cfg.speech.backend == "auto"


def test_DEMON_system_has_speech_backend():
    """DEMONSystem has a speech_backend attribute."""
    from OpenDEMON.system import DEMONSystem

    assert "speech_backend" in DEMONSystem.__dataclass_fields__
 ds__
