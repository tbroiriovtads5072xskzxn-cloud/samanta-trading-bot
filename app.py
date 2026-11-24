from flask import Flask, jsonify, render_template_string
import requests

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SAMANTA TRADING BOT</title>
<style>
body {
  background:#101522; color:white;
  font-family:Arial; text-align:center;
  padding:20px;
}
.card {
  background:#202b40; padding:22px;
  border-radius:18px; margin-top:25px;
}
h1 {color:#42d9ff;}
.signal {font-size:38px;font-weight:bold;margin:20px;}
button {
  background:#13b9db;color:white;
  border:0;padding:14px 25px;
  border-radius:10px;font-size:17px;
}
</style>
</head>
<body>
<h1>SAMANTA</h1>
<p>TRADING SIGNAL BOT</p>
<div class="card">
<h2>BTC / USDT</h2>
<div id="price">Loading...</div>
<div id="signal" class="signal">WAIT</div>
<div id="rsi">RSI: --</div>
<div id="ma">MA: --</div>
<p id="status">Connecting...</p>
<button onclick="loadData()">REFRESH</button>
</div>
<script>
async function loadData() {
 try {
  const r = await fetch('/api/signal');
  const d = await r.json();
  if (!r.ok) throw new Error(d.error || 'API error');
  document.getElementById('price').innerText =
    'BTC Price: $' + d.price;
  document.getElementById('signal').innerText = d.signal;
  document.getElementById('signal').style.color =
    d.signal === 'BUY' ? '#00e676' :
    d.signal === 'SELL' ? '#ff5252' : '#ffca28';
  document.getElementById('rsi').innerText = 'RSI: ' + d.rsi;
  document.getElementById('ma').innerText =
    'MA 7: ' + d.ma7 + ' | MA 25: ' + d.ma25;
  document.getElementById('status').innerText =
    'Updated: ' + new Date().toLocaleTimeString();
 } catch(e) {
  document.getElementById('status').innerText =
    'Connection error: ' + e.message;
 }
}
loadData();
setInterval(loadData, 60000);
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/api/signal")
def signal():
    try:
        params = {
            "symbol": "BTCUSDT",
            "interval": "1m",
            "limit": 100
        }
        response = requests.get(
            "https://api.binance.com/api/v3/klines",
            params=params, timeout=15
        )
        response.raise_for_status()
        data = response.json()
        closes = [float(c[4]) for c in data[:-1]]

        changes = [
            closes[i] - closes[i-1]
            for i in range(1, len(closes))
        ]
        gains = [max(x, 0) for x in changes]
        losses = [max(-x, 0) for x in changes]

        avg_gain = sum(gains[:14]) / 14
        avg_loss = sum(losses[:14]) / 14
        for i in range(14, len(gains)):
            avg_gain = (avg_gain * 13 + gains[i]) / 14
            avg_loss = (avg_loss * 13 + losses[i]) / 14

        rsi = 100 if avg_loss == 0 and avg_gain > 0 else (
            50 if avg_loss == 0 else
            100 - 100 / (1 + avg_gain / avg_loss)
        )

        ma7 = sum(closes[-7:]) / 7
        ma25 = sum(closes[-25:]) / 25

        if ma7 > ma25 and 50 < rsi < 70:
            result = "BUY"
        elif ma7 < ma25 and 30 < rsi < 50:
            result = "SELL"
        else:
            result = "WAIT"

        return jsonify({
            "price": round(closes[-1], 2),
            "ma7": round(ma7, 2),
            "ma25": round(ma25, 2),
            "rsi": round(rsi, 2),
            "signal": result
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 502

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(__import__("os").environ.get("PORT", 8080)))
