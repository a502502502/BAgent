from services.browser import Browser

browser = Browser()

browser.open("https://www.tennisstats.com")

browser.screenshot("tennisstats.png")

browser.save_html("tennisstats.html")

print("Screenshot e HTML salvati.")

input("Premi INVIO per chiudere...")

browser.close()