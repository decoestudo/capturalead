"""
Busca leads diretamente na tabela cnpj_estabelecimentos (dados da Receita Federal).
Zero custo, zero rate limit, zero dependência de API externa.
"""
import logging
from database.db import get_connection

logger = logging.getLogger(__name__)

# CNAEs por nicho (mesmos do casadosdados_scraper)
NICHE_CNAES = {
    "barbearia":               ["9602501"],
    "salão de beleza":         ["9602501"],
    "manicure":                ["9602501"],
    "pedicure":                ["9602501"],
    "nail designer":           ["9602501", "9602502"],
    "designer de sobrancelha": ["9602501", "9602502"],
    "nutricionista":           ["8630503", "8630599"],
    "lava jato":               ["4520001", "4520002", "4520006"],
}

SKIP_EMAILS = [
    "sentry", "example", "noreply", "no-reply", "microsoft.com",
    "bing.com", "wix", "wordpress", "zappysoftware", "google.com",
    "press@", "partners@", "people@", "support@", "privacy@", "legal@",
    "contab", "contador", "juridico",
]


def _check_table_exists() -> bool:
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'cnpj_estabelecimentos'
                    )
                """)
                return cur.fetchone()[0]
    except Exception:
        return False


def scrape_receita(niche: str, country: str, max_results: int = 100,
                   offset: int = 0) -> list[dict]:
    """
    Busca empresas ativas com email na tabela local da Receita Federal.
    Muito mais rápido que qualquer API — consulta direta no PostgreSQL.
    """
    if not _check_table_exists():
        logger.warning("[Receita] Tabela cnpj_estabelecimentos não existe. "
                       "Execute: docker-compose run --rm importer")
        return []

    cnaes = NICHE_CNAES.get(niche.lower(), [])
    if not cnaes:
        logger.warning(f"[Receita] Nicho '{niche}' sem CNAE mapeado.")
        return []

    results = []
    seen_emails: set = set()

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        e.cnpj_basico || e.cnpj_ordem || e.cnpj_dv AS cnpj,
                        e.nome_fantasia,
                        e.email,
                        e.ddd1,
                        e.telefone1,
                        e.uf,
                        COALESCE(m.nome, e.municipio_cod) AS municipio
                    FROM cnpj_estabelecimentos e
                    LEFT JOIN cnpj_municipios m ON m.codigo = e.municipio_cod
                    WHERE e.cnae_fiscal_principal = ANY(%s)
                      AND e.situacao_cadastral = '02'
                      AND e.email IS NOT NULL
                      AND e.email != ''
                    ORDER BY e.id
                    LIMIT %s OFFSET %s
                """, (cnaes, max_results * 3, offset))  # pede 3x para compensar filtros

                rows = cur.fetchall()

        for row in rows:
            if len(results) >= max_results:
                break

            cnpj, nome_fantasia, email, ddd, telefone, uf, municipio = row
            email = (email or "").lower().strip()

            if not email or "@" not in email:
                continue
            if any(skip in email for skip in SKIP_EMAILS):
                continue
            if email in seen_emails:
                continue

            seen_emails.add(email)

            phone = f"({ddd}) {telefone}" if ddd and telefone else ""
            location = f"{municipio}/{uf}" if municipio and uf else (uf or country)

            results.append({
                "company_name": nome_fantasia or f"CNPJ {cnpj}",
                "email": email,
                "website": "",
                "phone": phone,
                "source": "receita_federal",
                "niche": niche,
                "country": location,
            })

        logger.info(f"[Receita] {len(results)} leads para '{niche}' (CNAE={cnaes})")

    except Exception as e:
        logger.error(f"[Receita] Erro ao consultar banco: {e}")

    return results
