@"
import pandas as pd
from core.logic import ema_rsi_atr as s

df = pd.DataFrame({'close':[100,101,102,101,103,104,103,105,106,105]})
params = {'ema_fast':9,'ema_slow':21,'rsi':14,'atr':14,'atr_mult':2.0,'tp_r':1.5}
print("Has Strategy.decide:", hasattr(s, "Strategy") and hasattr(s.Strategy, "decide"))
print("decide():", s.decide(df, params))
"@ | python -
