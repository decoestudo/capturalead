"""
Baixa os dados da Receita Federal (CNPJ) diretamente da fonte
e importa na tabela `cnpj_estabelecimentos` do PostgreSQL.

Pode rodar:
  - Dentro do container:  docker-compose run --rm importer
  - Na VPS direto:        python scripts/importar_receita.py
  - Localmente:           python scripts/importar_receita.py
"""
import base64
import csv
import io
import logging
import os
import sys
import zipfile

import psycopg2
import requests
import urllib3

urllib3.disable_warnings()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger(__name__)

# ── Configuração ──────────────────────────────────────────────────────────────

TOKEN     = "YggdBLfdninEJX9"
BASE_URL  = "https://arquivos.receitafederal.gov.br"
PASTA     = "2026-02"
DB_URL    = os.getenv("DATABASE_URL", "postgresql://leads_user:leads_pass@postgres:5432/leads_db")

# Só Estabelecimentos (tem email, CNAE, situação) + Municipios (decodifica nomes)
ARQUIVOS = [
    "Estabelecimentos0.zip",
    "Estabelecimentos1.zip",
    "Estabelecimentos2.zip",
    "Estabelecimentos3.zip",
    "Estabelecimentos4.zip",
    "Estabelecimentos5.zip",
    "Estabelecimentos6.zip",
    "Estabelecimentos7.zip",
    "Estabelecimentos8.zip",
    "Estabelecimentos9.zip",
    "Municipios.zip",
]

# Colunas do arquivo Estabelecimentos (ordem oficial Receita Federal)
COLS_ESTAB = [
    "cnpj_basico", "cnpj_ordem", "cnpj_dv", "matriz_filial",
    "nome_fantasia", "situacao_cadastral", "data_situacao",
    "motivo_situacao", "cidade_exterior", "pais",
    "data_inicio_atividade", "cnae_fiscal_principal", "cnae_fiscal_secundario",
    "tipo_logradouro", "logradouro", "numero", "complemento",
    "bairro", "cep", "uf", "municipio_cod",
    "ddd1", "telefone1", "ddd2", "telefone2",
    "ddd_fax", "fax", "email", "situacao_especial", "data_situacao_especial",
]

# ── HTTP session ──────────────────────────────────────────────────────────────

def make_session():
    cred = base64.b64encode(f"{TOKEN}:".encode()).decode()
    s = requests.Session()
    s.headers["Authorization"] = f"Basic {cred}"
    s.verify = False
    return s


# ── Banco de dados ────────────────────────────────────────────────────────────

def get_conn():
    return psycopg2.connect(DB_URL)


def create_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cnpj_municipios (
                codigo  VARCHAR(7)  PRIMARY KEY,
                nome    VARCHAR(100)
            );

            CREATE TABLE IF NOT EXISTS cnpj_estabelecimentos (
                id                      SERIAL PRIMARY KEY,
                cnpj_basico             VARCHAR(8),
                cnpj_ordem              VARCHAR(4),
                cnpj_dv                 VARCHAR(2),
                cnpj                    VARCHAR(14) GENERATED ALWAYS AS
                                            (cnpj_basico || cnpj_ordem || cnpj_dv) STORED,
                matriz_filial           CHAR(1),
                nome_fantasia           VARCHAR(200),
                situacao_cadastral      CHAR(2),
                data_inicio_atividade   VARCHAR(8),
                cnae_fiscal_principal   VARCHAR(7),
                uf                      CHAR(2),
                municipio_cod           VARCHAR(7),
                ddd1                    VARCHAR(4),
                telefone1               VARCHAR(9),
                email                   VARCHAR(200),
                UNIQUE (cnpj_basico, cnpj_ordem, cnpj_dv)
            );
        """)
        conn.commit()
    log.info("Tabelas criadas/verificadas.")


def create_indexes(conn):
    log.info("Criando índices (pode demorar alguns minutos)...")
    with conn.cursor() as cur:
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_estab_cnae
                ON cnpj_estabelecimentos (cnae_fiscal_principal);
            CREATE INDEX IF NOT EXISTS idx_estab_situacao
                ON cnpj_estabelecimentos (situacao_cadastral);
            CREATE INDEX IF NOT EXISTS idx_estab_email
                ON cnpj_estabelecimentos (email)
                WHERE email IS NOT NULL AND email != '';
            CREATE INDEX IF NOT EXISTS idx_estab_cnae_situacao
                ON cnpj_estabelecimentos (cnae_fiscal_principal, situacao_cadastral);
        """)
        conn.commit()
    log.info("Índices criados.")


# ── Download + import streaming ───────────────────────────────────────────────

def import_municipios(session, conn):
    log.info("Baixando Municipios.zip...")
    url = f"{BASE_URL}/public.php/webdav/{PASTA}/Municipios.zip"
    resp = session.get(url, timeout=60)
    resp.raise_for_status()

    with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
        fname = z.namelist()[0]
        with z.open(fname) as f:
            rows = []
            reader = csv.reader(
                io.TextIOWrapper(f, encoding="iso-8859-1"),
                delimiter=";", quotechar='"',
            )
            for row in reader:
                if len(row) >= 2:
                    rows.append((row[0].strip(), row[1].strip()))

    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO cnpj_municipios (codigo, nome) VALUES (%s, %s) ON CONFLICT DO NOTHING",
            rows,
        )
        conn.commit()
    log.info(f"  {len(rows)} municípios importados.")


def import_estabelecimentos(session, conn, filename):
    url = f"{BASE_URL}/public.php/webdav/{PASTA}/{filename}"
    log.info(f"Baixando {filename} (streaming)...")

    # Verifica se já foi importado
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM cnpj_estabelecimentos")
        antes = cur.fetchone()[0]

    INSERT_SQL = """
        INSERT INTO cnpj_estabelecimentos
            (cnpj_basico, cnpj_ordem, cnpj_dv, matriz_filial, nome_fantasia,
             situacao_cadastral, data_inicio_atividade, cnae_fiscal_principal,
             uf, municipio_cod, ddd1, telefone1, email)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (cnpj_basico, cnpj_ordem, cnpj_dv) DO NOTHING
    """

    BATCH = 5000
    total = 0

    with session.get(url, stream=True, timeout=600) as resp:
        resp.raise_for_status()
        content_length = int(resp.headers.get("content-length", 0))
        log.info(f"  Tamanho: {content_length // 1024 // 1024} MB")

        # Baixa em memória (zip não suporta streaming nativo)
        log.info("  Recebendo arquivo...")
        data = resp.content
        log.info(f"  Recebido {len(data)//1024//1024} MB. Extraindo...")

    with zipfile.ZipFile(io.BytesIO(data)) as z:
        fname = z.namelist()[0]
        log.info(f"  Arquivo interno: {fname}")
        with z.open(fname) as f:
            reader = csv.reader(
                io.TextIOWrapper(f, encoding="iso-8859-1"),
                delimiter=";", quotechar='"',
            )
            batch = []
            with conn.cursor() as cur:
                for row in reader:
                    if len(row) < len(COLS_ESTAB):
                        continue

                    d = dict(zip(COLS_ESTAB, row))
                    email = d.get("email", "").strip().lower()

                    # Filtra: só ativas com email
                    if d.get("situacao_cadastral") != "02":
                        continue
                    if not email or "@" not in email:
                        continue

                    batch.append((
                        d["cnpj_basico"].strip(),
                        d["cnpj_ordem"].strip(),
                        d["cnpj_dv"].strip(),
                        d["matriz_filial"].strip(),
                        d["nome_fantasia"].strip() or None,
                        d["situacao_cadastral"].strip(),
                        d["data_inicio_atividade"].strip() or None,
                        d["cnae_fiscal_principal"].strip() or None,
                        d["uf"].strip() or None,
                        d["municipio_cod"].strip() or None,
                        d["ddd1"].strip() or None,
                        d["telefone1"].strip() or None,
                        email,
                    ))

                    if len(batch) >= BATCH:
                        cur.executemany(INSERT_SQL, batch)
                        conn.commit()
                        total += len(batch)
                        log.info(f"  {total:,} registros importados de {filename}...")
                        batch = []

                if batch:
                    cur.executemany(INSERT_SQL, batch)
                    conn.commit()
                    total += len(batch)

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM cnpj_estabelecimentos")
        depois = cur.fetchone()[0]

    novos = depois - antes
    log.info(f"  {filename}: +{novos:,} registros (total na tabela: {depois:,})")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("Importador CNPJ - Receita Federal")
    log.info(f"Fonte: {BASE_URL}/{PASTA}")
    log.info(f"Banco: {DB_URL}")
    log.info("=" * 60)

    session = make_session()
    conn = get_conn()

    create_tables(conn)

    # Verifica o que já foi importado
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM cnpj_estabelecimentos")
        existentes = cur.fetchone()[0]

    if existentes > 0:
        log.info(f"Já existem {existentes:,} registros. Continuando de onde parou...")

    # Importa municípios primeiro (pequeno)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM cnpj_municipios")
        mun = cur.fetchone()[0]
    if mun == 0:
        import_municipios(session, conn)

    # Importa cada arquivo de Estabelecimentos
    estab_files = [a for a in ARQUIVOS if a.startswith("Estabelecimentos")]
    for i, filename in enumerate(estab_files, 1):
        log.info(f"\n[{i}/{len(estab_files)}] {filename}")
        try:
            import_estabelecimentos(session, conn, filename)
        except Exception as e:
            log.error(f"Erro em {filename}: {e}")
            log.info("Continuando com o próximo arquivo...")

    # Cria índices ao final
    create_indexes(conn)

    # Resultado final
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM cnpj_estabelecimentos")
        total = cur.fetchone()[0]
        cur.execute("""
            SELECT cnae_fiscal_principal, COUNT(*) as qtd
            FROM cnpj_estabelecimentos
            WHERE cnae_fiscal_principal IN ('9602501','9602502','4520001','4520002','8630503')
            GROUP BY cnae_fiscal_principal ORDER BY qtd DESC
        """)
        cnaes = cur.fetchall()

    log.info("\n" + "=" * 60)
    log.info(f"IMPORTACAO CONCLUIDA: {total:,} estabelecimentos com email")
    log.info("CNAEs do projeto:")
    for cnae, qtd in cnaes:
        log.info(f"  {cnae}: {qtd:,} empresas")
    log.info("=" * 60)
    conn.close()


if __name__ == "__main__":
    main()
