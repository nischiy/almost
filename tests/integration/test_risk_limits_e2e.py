from app.run import TraderApp

class FakeMD:
    def __init__(self, df):
        self.df = df
    def get_klines(self, symbol, interval, limit=60):
        return self.df

class FakeSIG:
    def __init__(self, price):
        self.price = price
    def decide(self, df, params):
        return {"action":"LONG","price":float(self.price),"qty":0.001}

class CountingEXE:
    def __init__(self):
        self.calls = 0
        self.last = None
    def place(self, decision):
        self.calls += 1
        self.last = decision

class NoopTEL:
    def snapshot(self, df): pass
    def decision(self, d): pass
    def health(self, ok=True, msg="", **kw): pass

def test_consecutive_losses_block_after_threshold(df_klines):
    app = TraderApp(cfg=None, symbol="BTCUSDT", interval="1m")
    app.md = FakeMD(df_klines)
    app.sig = FakeSIG(df_klines['close'].iloc[-1])
    exe = CountingEXE()
    app.exe = exe
    app.tel = NoopTEL()

    class RiskConsec:
        def __init__(self, limit=3):
            self.limit = limit
            self.losses = 0
        def can_open(self, decision):
            self.losses += 1
            if self.losses > self.limit:
                return False, "max_consecutive_losses"
            return True, ""
    app.risk = RiskConsec(limit=3)

    # 4 cycles -> expect first 3 executed, 4th blocked
    for _ in range(4):
        app.run_once()
    assert exe.calls == 3

def test_daily_loss_cap_blocks(df_klines):
    app = TraderApp(cfg=None, symbol="BTCUSDT", interval="1m")
    app.md = FakeMD(df_klines)
    app.sig = FakeSIG(df_klines['close'].iloc[-1])
    exe = CountingEXE()
    app.exe = exe
    app.tel = NoopTEL()

    class RiskDailyLoss:
        def __init__(self, cap_usd=2.0):
            self.cap = cap_usd
            self.acc = 0.0
        def can_open(self, decision):
            # pretend each trade risks $0.75
            self.acc += 0.75
            if self.acc > self.cap:
                return False, "daily_loss_cap"
            return True, ""
    app.risk = RiskDailyLoss(cap_usd=2.0)

    for _ in range(5):
        app.run_once()
    # cap 2.0 with 0.75 per trade -> allows 2 or 3, blocks rest; exactly floor(2.0/0.75)=2 trades
    assert exe.calls == 2
