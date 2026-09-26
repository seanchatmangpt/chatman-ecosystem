import importlib.util
from pathlib import Path

ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location("cs2_contract", ROOT/"scripts/cs2_contract.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def test_canonical_contract_admits_exact_subject():
    r=m.verify(ROOT/"cs2/canonical.ttl", "0"*40)
    assert r["standing"] == "CANDIDATE"
    assert r["authority_ceiling"] == "CONSTRUCT"
    assert set(r["consumers"]) == {"ggen-marketplace","ash-a2a"}

def test_bad_sha_refused():
    r=m.verify(ROOT/"cs2/canonical.ttl", "main")
    assert r["standing"] == "REFUSED"

def test_divergent_surrogate_refused(tmp_path):
    p=tmp_path/"copied.ttl"
    p.write_text("@prefix cs2: <https://chatman.ai/cs2#> .\ncs2:RFC-CS2-001 a cs2:SemanticWorld .\n")
    r=m.verify(p, "0"*40)
    assert r["standing"] == "REFUSED"
    assert r["missing"]
