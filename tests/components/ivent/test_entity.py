from custom_components.ivent.entity import IVentGroupEntity


def test_remote_control_work_mode_defaults_to_normal() -> None:
    """Test only exact Bypass maps to Bypass; everything else defaults to Normal."""
    assert IVentGroupEntity._normalize_remote_control_work_mode("Bypass") == "Bypass"
    assert IVentGroupEntity._normalize_remote_control_work_mode("Normal") == "Normal"
    assert IVentGroupEntity._normalize_remote_control_work_mode(None) == "Normal"
    assert IVentGroupEntity._normalize_remote_control_work_mode("Unknown") == "Normal"


def test_work_mode_for_remote_settings_uses_documented_modes() -> None:
    """Test remote mode and speed map to documented i-Vent work modes."""
    assert IVentGroupEntity._work_mode_for_remote_settings("Normal", 3) == "IVentRecuperation3"
    assert IVentGroupEntity._work_mode_for_remote_settings("Bypass", 2) == "IVentBypass2"
    assert IVentGroupEntity._work_mode_for_remote_settings("Unknown", 1) == "IVentRecuperation1"