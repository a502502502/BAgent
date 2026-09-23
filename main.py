"""Entry point calcio. Il certificato di una selezione passa da StrictTicketPipeline."""

from services.betting.strict_ticket_pipeline import StrictTicketPipeline


def main() -> None:
    pipeline = StrictTicketPipeline()
    print("BAgent — solo calcio")
    print(f"Edge minimo: {pipeline.MIN_EDGE_THRESHOLD:.1%}")
    print("Certifica un esempio: python scripts/strict_validator.py --demo")


if __name__ == "__main__":
    main()
