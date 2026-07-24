def prepare_terms(main_term: str, variations: list[str]) -> list[str]:
    """Prepare search terms without removing collected publications."""
    terms = [main_term, *variations]
    cleaned_terms: list[str] = []
    seen: set[str] = set()

    for term in terms:
        cleaned = " ".join(term.split())
        normalized = cleaned.casefold()

        if cleaned and normalized not in seen:
            cleaned_terms.append(cleaned)
            seen.add(normalized)

    return cleaned_terms
