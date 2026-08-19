from rich import print

from services.database import Database
from scraper.manager import ScraperManager
from scraper.tennisstats import TennisStats


def main():

    print("[bold green]Betting Agent[/bold green]\n")

    # Inizializza il database
    db = Database()
    print("[green]✔ Database inizializzato[/green]")

    # Inizializza il manager degli scraper
    manager = ScraperManager()

    # Registra gli scraper disponibili
    manager.register(TennisStats())

    # Recupera le partite
    matches = manager.fetch_all()

    print()
    print(f"Partite trovate: {len(matches)}")

    # Chiude il database
    db.close()


if __name__ == "__main__":
    main()