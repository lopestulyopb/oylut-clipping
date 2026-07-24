import re
import unicodedata


BROAD_TERMS = {
    "cidade",
    "estado",
    "governo",
    "justica",
    "ministerio",
    "noticia",
    "noticias",
    "orgao",
    "politica",
    "prefeitura",
    "presidente",
    "secretaria",
    "tribunal",
}


def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", without_accents.casefold()).strip()


def validate_search_terms(terms: list[str]) -> None:
    """Reject only clearly generic expressions without blocking names or acronyms."""
    for term in terms:
        cleaned = " ".join(term.split())
        if _normalize(cleaned) in BROAD_TERMS:
            raise ValueError(
                f'O termo "{cleaned}" é muito amplo. Acrescente o nome completo, '
                "a localização, o órgão ou outra palavra que torne a pesquisa mais específica."
            )


def prepare_terms(main_term: str, variations: list[str]) -> list[str]:
    """Prepare and validate search terms without removing collected publications."""
    terms = [main_term, *variations]
    cleaned_terms: list[str] = []
    seen: set[str] = set()

    for term in terms:
        cleaned = " ".join(term.split())
        normalized = cleaned.casefold()

        if cleaned and normalized not in seen:
            cleaned_terms.append(cleaned)
            seen.add(normalized)

    validate_search_terms(cleaned_terms)
    return cleaned_terms
