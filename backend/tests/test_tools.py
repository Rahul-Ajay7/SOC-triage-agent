from app.tools import geo_lookup, ioc_extractor, ip_reputation, mitre_mapper


def test_ioc_extract_ips_and_hashes():
    text = "login from 203.0.113.66 hash 44d88612fea8a8f36de82e1278abb02f evil.ru"
    iocs = ioc_extractor.extract(text)
    assert "203.0.113.66" in iocs["ips"]
    assert "44d88612fea8a8f36de82e1278abb02f" in iocs["hashes"]
    assert "evil.ru" in iocs["domains"]


def test_ip_reputation_private_is_internal():
    r = ip_reputation.check_ip("10.0.0.5")
    assert r["category"] == "internal"
    assert r["is_malicious"] is False


def test_ip_reputation_known_bad():
    r = ip_reputation.check_ip("45.155.205.233")
    assert r["is_malicious"] is True


def test_impossible_travel_demo_ips():
    # Singapore vs Moscow -> impossible
    res = geo_lookup.impossible_travel(["159.89.113.10", "185.220.101.66"])
    assert res["impossible"] is True
    assert res["max_distance_km"] > 1000


def test_mitre_maps_brute_force():
    alert = {"failures": 8, "success_after_failures": False}
    techs = mitre_mapper.map_techniques(alert, {})
    assert any(t["id"].startswith("T1110") for t in techs)
