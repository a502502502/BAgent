import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding='utf-8')
from services.betting.netwin_automator import NetwinAutomator

automator = NetwinAutomator(headless=True)
automator.open_sportsbook()
automator.page.screenshot(path="reports/automator_debug.png")
print("Screenshot salvato in reports/automator_debug.png")

# Check all search inputs
inputs = automator.page.locator("input").all()
print(f"Totale input: {len(inputs)}")
for i, inp in enumerate(inputs):
    try:
        print(f"Input {i}: id='{inp.get_attribute('id')}' visible={inp.is_visible()}")
    except Exception:
        pass

automator.close()
