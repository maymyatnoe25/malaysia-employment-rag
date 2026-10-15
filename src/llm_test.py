import time

import requests

URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2"

prompt = ("Answer using only this text. Text: 'A married male employee shall be "
          "entitled to seven consecutive days of paid paternity leave per "
          "confinement.' Question: How long is paternity leave?")

t = time.time()
r = requests.post(URL, json={"model": MODEL, "prompt": prompt, "stream": False,
                             "options": {"temperature": 0}}, timeout=600)
r.raise_for_status()
d = r.json()
print(d["response"])
print(f"\n{time.time() - t:.1f} s total, {d.get('eval_count')} tokens generated")