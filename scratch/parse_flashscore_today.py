import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
    'x-fsign': 'SW9D1eZo',
}
r = requests.get('https://local-global.flashscore.ninja/2/x/feed/f_1_0_2_it_1', headers=headers, timeout=10)
text = r.text

blocks = text.split("~")
print("Total blocks:", len(blocks))

target_matches = []
for b in blocks:
    if any(k in b for k in ["HJK", "VPS", "KuPS", "Oulu", "Shamrock", "Drogheda", "FAR Rabat", "Cluj"]):
        # Extract fields: AA is match id, AD is time, CX/AE is home, AF is away, AB is status
        fields = {}
        for item in b.split("¬"):
            if "÷" in item:
                k, v = item.split("÷", 1)
                fields[k] = v
        target_matches.append(fields)

for m in target_matches:
    mid = m.get("AA")
    time_stamp = m.get("AD")
    home = m.get("AE") or m.get("CX")
    away = m.get("AF") or m.get("WN")
    status = m.get("AB")
    print(f"Match ID: {mid} | Kickoff Epoch: {time_stamp} | Home: {home} | Away: {away} | Status: {status}")
