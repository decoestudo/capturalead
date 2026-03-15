"""
Busca leads diretamente na tabela cnpj_estabelecimentos (dados da Receita Federal).
Zero custo, zero rate limit, zero dependência de API externa.
"""
import logging
from database.db import get_connection
from utils.email_cleaner import is_valid_email, clean_email

logger = logging.getLogger(__name__)

# CNAEs por nicho (mesmos do casadosdados_scraper)
NICHE_CNAES = {
    "barbearia":        ["9602501"],
    "salão de beleza":  ["9602501"],
    "manicure":         ["9602501"],
    "clínica dentária": ["8630504"],
    "psicólogo":        ["8650003"],
    "fisioterapia":     ["8650004"],
    "nutricionista":    ["8630503", "8630599"],
    "personal trainer": ["9313100"],
    "estética":         ["9602502"],
}

SKIP_EMAILS = [
    "sentry", "example", "noreply", "no-reply", "microsoft.com",
    "bing.com", "wix", "wordpress", "zappysoftware", "google.com",
    "press@", "partners@", "people@", "support@", "privacy@", "legal@",
    "contab", "contador", "juridico",
]


def _check_table_exists() -> bool:
    """Retorna True só se a tabela existe E tem dados importados."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'cnpj_estabelecimentos'
                    )
                """)
                if not cur.fetchone()[0]:
                    return False
                cur.execute("SELECT EXISTS (SELECT 1 FROM cnpj_estabelecimentos LIMIT 1)")
                return cur.fetchone()[0]
    except Exception:
        return False


def scrape_receita(niche: str, country: str, max_results: int = 100) -> list[dict]:
    """
    Busca empresas ativas com email na tabela local da Receita Federal.
    Sempre prioriza as mais recentes (data_inicio_atividade DESC) e pula
    emails que já estão na tabela leads (evita duplicatas e avança automaticamente).
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
                    LEFT JOIN leads l ON (
                        LOWER(l.email) = LOWER(e.email)
                        OR LOWER(l.email) = LOWER(REGEXP_REPLACE(e.email, '\.com\.br$', '.com', 'i'))
                    )
                    WHERE e.cnae_fiscal_principal = ANY(%s)
                      AND e.situacao_cadastral = '02'
                      AND e.email IS NOT NULL
                      AND e.email != ''
                      AND l.email IS NULL
                    ORDER BY e.data_inicio_atividade DESC NULLS LAST
                    LIMIT %s
                """, (cnaes, max_results * 3))  # pede 3x para compensar filtros
                logger.info(f"[Receita] '{niche}': buscando {max_results} leads mais recentes não coletados")

                rows = cur.fetchall()

        for row in rows:
            if len(results) >= max_results:
                break

            cnpj, nome_fantasia, email, ddd, telefone, uf, municipio = row
            email = clean_email((email or "").lower().strip())

            if not is_valid_email(email):
                continue
            if any(skip in email for skip in SKIP_EMAILS):
                continue
            if email in seen_emails:
                continue

            seen_emails.add(email)

            phone = f"({ddd}) {telefone}" if ddd and telefone else ""
            location = f"{municipio}/{uf}" if municipio and uf else (uf or country)

            results.append({
                "company_name": nome_fantasia or "",
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
