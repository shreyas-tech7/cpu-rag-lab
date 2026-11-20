import pytest

from cpu_rag_lab.memguard import MemGuard, MemoryLimitExceeded, rss_mb


def test_reads_real_rss():
    assert 1 < rss_mb() < 4096


def test_guard_trips_over_limit():
    """Broken case: a run that grows past the limit keeps going."""
    readings = iter([100, 150, 3000, 3000, 3000])
    g = MemGuard(limit_mb=2048, reader=lambda: next(readings, 3000))
    g.reset()
    g.check()
    with pytest.raises(MemoryLimitExceeded):
        g.check()
    assert g.peak_mb == 3000


def test_status_file_parse(tmp_path):
    p = tmp_path / "status"
    p.write_text("Name: x\nVmRSS:\t  204800 kB\n")
    assert rss_mb(str(p)) == 200
