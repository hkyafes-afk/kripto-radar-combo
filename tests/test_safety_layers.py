import json
import pytest
from persistence.ledger import EventLedger,LedgerCorruption
from persistence.recovery import RecoveryManager,RecoveryError
from runner.lifecycle import RunnerLease,AlreadyRunning

def test_ledger_is_append_only_hash_chained_and_idempotent(tmp_path):
 p=tmp_path/"events.jsonl";l=EventLedger(p);assert l.append("e1","fill",{"qty":.013}) is not None;assert l.append("e1","fill",{"qty":.013}) is None;assert l.append("e2","cancel",{})["seq"]==2;assert len(EventLedger(p).verify())==2
 rows=p.read_text().splitlines();r=json.loads(rows[0]);r["payload"]["qty"]=9;rows[0]=json.dumps(r);p.write_text("\n".join(rows)+"\n")
 with pytest.raises(LedgerCorruption):EventLedger(p)
def test_recovery_latest_checkpoint_and_snapshot_loss(tmp_path):
 l=EventLedger(tmp_path/"events.jsonl");r=RecoveryManager(l);p=tmp_path/"state.json";r.write_checkpoint(p,{"qty":.013},"cp1");r.write_checkpoint(p,{"qty":.026},"cp2");assert r.recover(p)=={"qty":.026};p.unlink();assert r.recover(p)=={"qty":.026}
def test_recovery_rejects_uncheckpointed_tail(tmp_path):
 l=EventLedger(tmp_path/"events.jsonl");r=RecoveryManager(l);p=tmp_path/"state.json";r.write_checkpoint(p,{"qty":.013},"cp1");l.append("event-after-checkpoint","fill",{"qty":.001})
 with pytest.raises(RecoveryError):r.recover(p)
def test_runner_lease_blocks_second_runner(tmp_path):
 p=tmp_path/"runner.lock";a=RunnerLease(p).acquire()
 with pytest.raises(AlreadyRunning):RunnerLease(p).acquire()
 a.release();b=RunnerLease(p).acquire();b.release()
def test_paper_checkpoint_recovers_from_journal_when_snapshot_missing(tmp_path):
 from combo.config import ComboConfig
 from combo.paper import ComboPaperAdapter
 p=ComboPaperAdapter(ComboConfig(),root=tmp_path);p.save();(tmp_path/"combo_paper.json").unlink();q=ComboPaperAdapter(ComboConfig(),root=tmp_path);assert q.initialized is False and q.position.qty==0
