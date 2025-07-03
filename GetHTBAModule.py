import sys
import os
import json
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

token = "......<SNIP>....."
user_id = "<YOUR_USER_ID>"

headers = {
    "Accept": "application/json, text/plain, */*",
    "Authorization": f"Bearer {token}",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

base_list_url = "https://labs.hackthebox.com/api/v4/machine/list/retired/paginated?page={}"
base_achievement_url = "https://labs.hackthebox.com/api/v4/user/achievement/machine/{}/{}"
retired_json_path = "retired_machines.json"

url = sys.argv[1]

options = Options()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
options.add_argument('--no-sandbox')

driver = webdriver.Chrome(options=options)
driver.get(url)
WebDriverWait(driver, 20).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.card-node.machine-card')))
html = driver.page_source
driver.quit()

soup = BeautifulSoup(html, 'html.parser')
module_machines = [m.text.strip() for m in soup.select('.card-node.machine-card [data-testid="machine-name"]')]

retired_machines = {}
if os.path.exists(retired_json_path) and os.path.getsize(retired_json_path) > 0:
    with open(retired_json_path, "r") as f:
        try:
            retired_machines = json.load(f)
        except json.JSONDecodeError:
            retired_machines = {}
else:
    page = 1
    while True:
        r = requests.get(base_list_url.format(page), headers=headers)
        if r.status_code != 200 or not r.json().get("data"):
            break
        for m in r.json()["data"]:
            retired_machines[m["name"]] = m["id"]
        page += 1
    with open(retired_json_path, "w") as f:
        json.dump(retired_machines, f)

results = []
max_name_len = max(len(name) for name in module_machines) if module_machines else 10
header_name = "Machine"
header_status = "Pwned?"
max_name_len = max(max_name_len, len(header_name))
results.append(f"   {header_name.ljust(max_name_len)}   │  {header_status}")
results.append(f"{'─' * max_name_len}──────┼──────────")

for machine in module_machines:
    if machine not in retired_machines:
        status = "❌ (not found)"
    else:
        machine_id = retired_machines[machine]
        r = requests.get(base_achievement_url.format(user_id, machine_id), headers=headers)
        if r.status_code == 200:
            status = "✔️"
        elif r.status_code == 400:
            status = "❌"
        else:
            status = f"ERR {r.status_code}"
    results.append(f"   {machine.ljust(max_name_len)}   │  {status}")

print("\n".join(results))
