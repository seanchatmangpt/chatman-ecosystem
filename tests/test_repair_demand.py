import pytest
from scripts.repair_demand import manufacture,replay,ROUTES
S="a"*40
def test_routes_every_known_crown_finding_and_replays():
    r=manufacture(S,list(ROUTES)); assert len(r["demands"])==6; assert r["authority"]=="NONE"; assert replay(r)["replay"]
def test_order_and_duplicate_invariant():
    a=manufacture(S,["R_missing_replay","R_missing_identity","R_missing_replay"])
    b=manufacture(S,["R_missing_identity","R_missing_replay"])
    assert a["receipt_digest"]==b["receipt_digest"]
def test_semantic_change_changes_receipt():
    assert manufacture(S,["R_missing_identity"])["receipt_digest"] != manufacture(S,["R_missing_replay"])["receipt_digest"]
def test_mutable_subject_refused():
    with pytest.raises(ValueError,match="MUTABLE_SUBJECT"): manufacture("main",["R_missing_identity"])
def test_unknown_preserved_as_refusal_not_guessed():
    with pytest.raises(ValueError,match="UNKNOWN_FINDING"): manufacture(S,["R_future_unknown"])
def test_authority_never_inherited():
    r=manufacture(S,["R_missing_authority"]); assert {d["authority"] for d in r["demands"]}=={"NONE"}
