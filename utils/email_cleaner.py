"""
Corrige typos comuns em domínios de email antes de salvar na base.

Estratégia:
  1. Mapa explícito — domínios sabidamente errados → correto (sem falso positivo).
  2. Fuzzy matching via difflib — só para domínios de 2 segmentos (ex: "hormail.com")
     contra os provedores pessoais mais usados, com limiar alto (0.90).
     Domínios corporativos (ex: "contecbh.com.br") não são alterados.
"""

import difflib
import logging
import re

# ── Provedores pessoais (onde local genérico = inválido) ─────────────────────
_PERSONAL_DOMAINS = {
    "gmail.com", "hotmail.com", "outlook.com", "yahoo.com", "yahoo.com.br",
    "icloud.com", "live.com", "me.com", "msn.com", "ymail.com",
    "uol.com.br", "terra.com.br", "bol.com.br", "ig.com.br",
}

# ── Padrões inválidos na parte local (antes do @) ────────────────────────────
_INVALID_LOCAL_RE = re.compile(
    r"^(.)\1{4,}$"          # mesmo caractere 5+ vezes: xxxxxxx, 111111, aaaaa
    r"|^\d{6,}$"            # só números com 6+ dígitos: 123456789
    r"|^0{5,}"              # placeholder Receita Federal: 00000000_142, 00000000 etc.
    r"|^(test(e|ing)?|email|sememail|noemail|semcadastro|placeholder"
    r"|xxxxx+|zzzzz+|aaaaa+|nada|vazio|invalido|invalid|dummy|fake)$",
    re.IGNORECASE,
)

# ── Locais genéricos que só valem como inválido em provedores pessoais ────────
_GENERIC_LOCAL = {
    "contato", "email", "teste", "test", "info", "faleconosco",
    "atendimento", "comercial", "vendas", "suporte", "support",
    "admin", "administracao", "noreply", "no-reply",
}

# ── Emails completos conhecidos como inválidos ────────────────────────────────
_INVALID_FULL_EMAILS = {
    "nihil@nihil.com.br",
    "contato@gmail.com",
    "contato@hotmail.com",
    "contato@yahoo.com",
    "contato@yahoo.com.br",
    "email@gmail.com",
    "teste@gmail.com",
    "test@gmail.com",
    "mei@gov.br",
}

logger = logging.getLogger(__name__)

# ── Mapa explícito de typos conhecidos ──────────────────────────────────────
# Chave = domínio errado  |  Valor = domínio correto
DOMAIN_TYPO_MAP: dict[str, str] = {
    # ── Gmail ────────────────────────────────────────────────────────────────
    "gmail.con":        "gmail.com",
    "gmail.coom":       "gmail.com",
    "gmail.comm":       "gmail.com",
    "gmail.ocm":        "gmail.com",
    "gmail.co":         "gmail.com",
    "gmail.com.br":     "gmail.com",   # Google não tem .br
    "gmai.com":         "gmail.com",
    "gmial.com":        "gmail.com",
    "gamil.com":        "gmail.com",
    "gnail.com":        "gmail.com",
    "gmaill.com":       "gmail.com",
    "gmal.com":         "gmail.com",
    "gmailcom":         "gmail.com",
    "gmail.cm":         "gmail.com",
    "gmail.vom":        "gmail.com",
    "gmaio.com":        "gmail.com",

    # ── Hotmail ──────────────────────────────────────────────────────────────
    "hotmail.com.br":   "hotmail.com",  # Microsoft não tem .br
    "hormail.com":      "hotmail.com",
    "hotamil.com":      "hotmail.com",
    "hotmal.com":       "hotmail.com",
    "hotmai.com":       "hotmail.com",
    "hotmial.com":      "hotmail.com",
    "hotmaill.com":     "hotmail.com",
    "hotmeil.com":      "hotmail.com",
    "homail.com":       "hotmail.com",
    "hotmailcom":       "hotmail.com",
    "hot.com":          "hotmail.com",
    "hotmail.cm":       "hotmail.com",
    "hortmail.com":     "hotmail.com",
    "hotmali.com":      "hotmail.com",
    "rotmail.com":      "hotmail.com",

    # ── Yahoo ────────────────────────────────────────────────────────────────
    "yahoo.com.r":      "yahoo.com.br",   # faltou 'b'
    "yohoo.com":        "yahoo.com",
    "yohoo.com.br":     "yahoo.com.br",
    "yahooo.com":       "yahoo.com",
    "yahooo.com.br":    "yahoo.com.br",
    "yaho.com":         "yahoo.com",
    "yaho.com.br":      "yahoo.com.br",
    "yahoocom":         "yahoo.com",
    "yahoo.vom":        "yahoo.com",
    "ymail.con":        "ymail.com",

    # ── Outlook / Live ───────────────────────────────────────────────────────
    "outlook.com.br":   "outlook.com",   # Microsoft não tem .br
    "outlok.com":       "outlook.com",
    "outllook.com":     "outlook.com",
    "outlookcom":       "outlook.com",
    "outloook.com":     "outlook.com",
    "live.com.br":      "live.com",

    # ── iCloud ───────────────────────────────────────────────────────────────
    "icloud.com.br":    "icloud.com",

    # ── UOL / Terra / BOL / IG ──────────────────────────────────────────────
    "uol.com":          "uol.com.br",
    "terra.com":        "terra.com.br",
    "bol.com":          "bol.com.br",
    "ig.com":           "ig.com.br",

    # ── Outros ──────────────────────────────────────────────────────────────
    "globomail.com":    "globo.com",
}

# ── Alvos para fuzzy (só provedores pessoais de 2 segmentos) ────────────────
_FUZZY_TARGETS = [
    "gmail.com",
    "hotmail.com",
    "yahoo.com",
    "outlook.com",
    "live.com",
    "icloud.com",
    "ymail.com",
    "msn.com",
    "mail.com",     # domínio legítimo — evita ser corrigido erroneamente para ymail.com
]


def _fuzzy_fix_2seg(domain: str) -> str:
    """
    Tenta corrigir domínios com exatamente 2 segmentos (ex: 'hormail.com')
    contra a lista de provedores pessoais conhecidos.
    Limiar 0.90 — muito conservador, evita falsos positivos.
    """
    if domain.count(".") != 1:
        return domain  # Não meche em domínios corporativos como contecbh.com.br
    matches = difflib.get_close_matches(domain, _FUZZY_TARGETS, n=1, cutoff=0.90)
    if matches and matches[0] != domain:
        return matches[0]
    return domain


def is_valid_email(email: str) -> bool:
    """
    Retorna False para emails obviamente inválidos, de teste ou placeholder.
    Deve ser chamado APÓS clean_email().
    """
    if not email or "@" not in email:
        return False

    email = email.lower().strip()

    if email in _INVALID_FULL_EMAILS:
        return False

    local, domain = email.rsplit("@", 1)

    if not local or not domain or "." not in domain:
        return False

    # Parte local claramente inválida (xxxx, 123456, teste, etc.)
    if _INVALID_LOCAL_RE.match(local):
        return False

    # Local genérico em provedor pessoal (contato@gmail.com, info@hotmail.com)
    if local in _GENERIC_LOCAL and domain in _PERSONAL_DOMAINS:
        return False

    return True


def clean_email(email: str) -> str:
    """
    Normaliza e corrige typos no email.
    Retorna o email corrigido (ou o original se já estiver correto).
    """
    if not email or "@" not in email:
        return email

    # Normaliza: minúsculas e remove espaços (ex: "santomello @ig.com.br")
    email = re.sub(r"\s+", "", email.lower().strip())

    if "@" not in email:
        return email

    local, domain = email.rsplit("@", 1)

    if not local or not domain or "." not in domain:
        return email

    # 1. Mapa explícito
    fixed = DOMAIN_TYPO_MAP.get(domain)

    # 2. Fuzzy (só domínios simples de 2 segmentos)
    if fixed is None:
        fixed = _fuzzy_fix_2seg(domain)
        if fixed == domain:
            fixed = None  # Sem alteração

    if fixed and fixed != domain:
        corrected = f"{local}@{fixed}"
        logger.info(f"[EmailCleaner] {email!r} → {corrected!r}")
        return corrected

    return email
