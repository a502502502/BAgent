from pathlib import Path

from infrastructure.browser.browser import Browser


class TennisAbstractCollector:

    BASE_URL = (
        "https://www.tennisabstract.com/cgi-bin/player.cgi?p="
    )

    SNAPSHOT_DIR = Path(
        "infrastructure/providers/tennis/"
        "tennis_abstract/snapshots/players"
    )

    def __init__(self):

        self.SNAPSHOT_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

    def collect(
        self,
        player_slug: str
    ) -> str:

        browser = Browser(debug=False)

        try:

            url = (
                f"{self.BASE_URL}"
                f"{player_slug}"
            )

            print(
                f"\nApertura: {url}\n"
            )

            browser.get(url)

            html = browser.html()

            if not html:
                raise RuntimeError(
                    "Tennis Abstract ha restituito "
                    "HTML vuoto."
                )

            if len(html) < 20000:

                raise RuntimeError(
                    "Tennis Abstract ha restituito "
                    f"una pagina anomala per "
                    f"{player_slug}: "
                    f"{len(html)} caratteri. "
                    "Probabile rate limit, "
                    "Cloudflare o pagina di errore."
                )

            snapshot_path = (
                self.SNAPSHOT_DIR
                / f"{player_slug}.html"
            )

            snapshot_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            snapshot_path.write_text(
                html,
                encoding="utf-8"
            )

            print(
                f"✅ HTML acquisito: "
                f"{len(html)} caratteri"
            )

            print(
                f"✅ Snapshot salvato: "
                f"{snapshot_path}"
            )

            return html

        finally:

            browser.close()