from app.use_cases.acquire_matches import AcquireMatchesUseCase


def main():

    use_case = AcquireMatchesUseCase()

    matches = use_case.execute()

    print()

    print("=" * 60)

    print("BAgent")

    print("=" * 60)

    print()

    print(f"Match salvati: {matches}")

    print()


if __name__ == "__main__":

    main()