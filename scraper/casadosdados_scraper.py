"""
Scraper de leads via API oficial da Casa dos Dados (v5).

Usa a pesquisa avançada por CNAE para encontrar empresas ativas
com email cadastrado, sem depender de Google/Bing.

Documentação: https://docs.casadosdados.com.br
"""
import logging
import os
import random
import time

import cloudscraper
from config.settings import CASADOSDADOS_API_KEY

logger = logging.getLogger(__name__)

# Mapeamento nicho → CNAEs relevantes
NICHE_CNAES = {
    "barbearia":                ["9602501"],           # Cabeleireiros, manicure e pedicure (inclui barbearia)
    "salão de beleza":          ["9602501"],
    "manicure":                 ["9602501"],
    "pedicure":                 ["9602501"],
    "nail designer":            ["9602501", "9602502"],
    "designer de sobrancelha":  ["9602501", "9602502"],  # 9602502 = estética e beleza
    "nutricionista":            ["8630503", "8630599"],  # ambulatorial consultas + não especificados
    "lava jato":                ["4520001", "4520002", "4520006"],
}

SKIP_EMAILS = [
    "sentry", "example", "noreply", "no-reply", "microsoft.com",
    "bing.com", "wix", "wordpress", "zappysoftware", "google.com",
    "press@", "partners@", "people@", "support@", "privacy@", "legal@",
    "contab", "contador", "escritório", "juridico",
]

BASE_URL = "https://api.casadosdados.com.br"


def _make_scraper():
    s = cloudscraper.create_scraper()
    s.headers.update({
        "api-key": CASADOSDADOS_API_KEY,
        "Content-Type": "application/json",
    })
    return s


def scrape_casadosdados(niche: str, country: str, max_results: int = 50) -> list[dict]:
    """
    Busca empresas via API Casa dos Dados pelo CNAE do nicho.
    Retorna lista de dicts com email, empresa, telefone, etc.
    """
    cnaes = NICHE_CNAES.get(niche.lower(), [])
    if not cnaes:
        logger.warning(f"[CasaDados API] Nicho '{niche}' sem CNAE mapeado. Pulando.")
        return []

    if not CASADOSDADOS_API_KEY:
        logger.warning("[CasaDados API] CASADOSDADOS_API_KEY não configurada. Pulando.")
        return []

    results = []
    seen_emails: set = set()
    scraper = _make_scraper()
    pagina = 1

    while len(results) < max_results:
        payload = {
            "codigo_atividade_principal": cnaes,
            "situacao_cadastral": ["ATIVA"],
            "mais_filtros": {
                "com_email": True,
                "excluir_email_contab": True,
            },
            "limite": 100,
            "pagina": pagina,
        }

        try:
            logger.info(f"[CasaDados API] Pesquisando '{niche}' CNAE={cnaes} página {pagina}")
            resp = scraper.post(
                f"{BASE_URL}/v5/cnpj/pesquisa?tipo_resultado=completo",
                json=payload,
                timeout=20,
            )

            if resp.status_code == 401:
                logger.error("[CasaDados API] Chave inválida (401).")
                break
            if resp.status_code == 403:
                logger.error("[CasaDados API] Saldo insuficiente ou acesso negado (403).")
                break
            if resp.status_code != 200:
                logger.error(f"[CasaDados API] Erro {resp.status_code}: {resp.text[:200]}")
                break

            data = resp.json()
            total = data.get("total", 0)
            cnpjs = data.get("cnpjs", [])

            if not cnpjs:
                logger.info(f"[CasaDados API] Sem mais resultados na página {pagina}.")
                break

            logger.info(f"[CasaDados API] Total disponível: {total} | Página {pagina}: {len(cnpjs)} empresas")

            for company in cnpjs:
                if len(results) >= max_results:
                    break

                emails_raw = company.get("contato_email") or []
                telefones = company.get("contato_telefonico") or []

                phone = ""
                if telefones:
                    t = telefones[0]
                    phone = t.get("completo", "")

                nome = company.get("nome_fantasia") or company.get("razao_social", "")
                municipio = company.get("endereco", {}).get("municipio", "")
                uf = company.get("endereco", {}).get("uf", "")

                for e in emails_raw:
                    email = e.get("email", "").lower().strip()
                    if not email or "@" not in email:
                        continue
                    if any(skip in email for skip in SKIP_EMAILS):
                        continue
                    if email in seen_emails:
                        continue

                    seen_emails.add(email)
                    results.append({
                        "company_name": nome,
                        "email": email,
                        "website": "",
                        "phone": phone,
                        "source": "casadosdados_api",
                        "niche": niche,
                        "country": f"{municipio}/{uf}" if municipio else country,
                    })
                    logger.info(f"[CasaDados API] ✅ {len(results)}: {email} ({nome})")

            # Se a página retornou menos que 100, não há mais páginas
            if len(cnpjs) < 100:
                break

            pagina += 1
            time.sleep(random.uniform(1, 2))

        except Exception as e:
            logger.error(f"[CasaDados API] Exceção na página {pagina}: {e}")
            break

    logger.info(f"[CasaDados API] Total: {len(results)} leads para '{niche}'")
    return results
