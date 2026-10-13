from pathlib import Path

import requests

RAW = Path("data/raw")

# Official Laws of Malaysia (Attorney General's Chambers), English edition.
FILES = {
    "employment_act_1955.pdf":
        "https://lom.agc.gov.my/ilims/upload/portal/akta/LOM/EN/"
        "Act%20265%20-%20Employment%20Act%201955.pdf",
}


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    for name, url in FILES.items():
        target = RAW / name
        if target.exists():
            print(name, "already exists, skipping")
            continue
        print("Downloading", name)
        r = requests.get(url, timeout=120, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        target.write_bytes(r.content)
        print("  saved", len(r.content) // 1024, "KB")


if __name__ == "__main__":
    main()