import time
from combo.strategy import ComboStrategy
from combo.feed import ComboWebSocketListener
from combo.instrument import OKXInstrumentMetadata
class FakeFeed:
 def __init__(self):self.callback=None;self.symbols=[]
 def add_tick_listener(self,cb):self.callback=cb
 def set_symbols(self,s):self.symbols=s
 def status(self):return {"connected":False,"healthy":False}
def build():
 s=ComboStrategy();f=FakeFeed();m=OKXInstrumentMetadata("BTC-USDT-SWAP","linear",.01,"BTC",.1,.01,.01,"live");return s,f,ComboWebSocketListener(s,feed=f,instrument_meta=m)
def test_missing_contract_unit_label_is_rejected():
 s,f,l=build();l.start();now=int(time.time()*1000);f.callback({"exchange":"okx","inst":"BTC-USDT-SWAP","last":78000,"bid":77999.9,"ask":78000.1,"bid_size_contracts":5,"ask_size_contracts":5,"ts_ms":now});assert l.last_error and "size unit" in l.last_error.lower();assert not s.paper.initialized
def test_nan_contract_size_is_rejected():
 s,f,l=build();l.start();now=int(time.time()*1000);f.callback({"exchange":"okx","inst":"BTC-USDT-SWAP","last":78000,"bid":77999.9,"ask":78000.1,"bid_size_contracts":float("nan"),"ask_size_contracts":5,"size_unit":"contracts_for_swap","ts_ms":now});assert l.last_error and not s.paper.initialized
def test_wrong_instrument_is_ignored():
 s,f,l=build();l.start();now=int(time.time()*1000);f.callback({"exchange":"okx","inst":"ETH-USDT-SWAP","last":3000,"bid":2999.9,"ask":3000.1,"bid_size_contracts":5,"ask_size_contracts":5,"size_unit":"contracts_for_swap","ts_ms":now});assert l.last_error is None and not s.paper.initialized
