"""
Envia um email de teste para verificar se abertura está sendo rastreada.

Uso dentro do container:
    docker-compose exec bot python scripts/send_test.py

Ou via docker-compose run:
    docker-compose run --rm bot python scripts/send_test.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import TRACKING_BASE_URL
from database.db import get_connection, insert_lead, record_sent
from mailer.smtp_sender import send_email

TEST_EMAIL   = "test-wf01qan5l@srv1.mail-tester.com"
TEST_COMPANY = "Salão Exemplo"
SUBJECT      = "Sua agenda ainda depende de você?"


def get_or_create_lead() -> int:
    """Retorna id do lead de teste, criando se não existir."""
    insert_lead(TEST_COMPANY, TEST_EMAIL, source="teste", niche="teste", country="BR")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM leads WHERE email = %s", (TEST_EMAIL,))
            row = cur.fetchone()
            if not row:
                raise RuntimeError(f"Lead {TEST_EMAIL} não encontrado após insert.")
            return row[0]


def main():
    print("=" * 55)
    print("  TESTE DE EMAIL + RASTREAMENTO")
    print("=" * 55)

    if not TRACKING_BASE_URL:
        print("\n⚠  TRACKING_BASE_URL não configurado no .env!")
        print("   O pixel de rastreamento NÃO será incluído.")
        print("   Configure TRACKING_BASE_URL=https://<ip-vps>:8080\n")
    else:
        print(f"\n✓  Tracking URL: {TRACKING_BASE_URL}")

    lead_id = get_or_create_lead()
    print(f"✓  Lead ID: {lead_id} ({TEST_EMAIL})")

    pixel_url = f"{TRACKING_BASE_URL}/t/o/{lead_id}" if TRACKING_BASE_URL else "(sem tracking)"
    click_url = f"{TRACKING_BASE_URL}/t/c/{lead_id}" if TRACKING_BASE_URL else "https://topagenda.online"
    print(f"✓  Pixel URL: {pixel_url}")
    print(f"✓  Click URL: {click_url}")

    print(f"\nEnviando email para {TEST_EMAIL}...")
    ok = send_email(
        to=TEST_EMAIL,
        subject=SUBJECT,
        company_name=TEST_COMPANY,
        template_id=1,
        lead_id=lead_id,
    )

    if ok:
        record_sent(lead_id, template_id=1, subject=SUBJECT)
        print(f"\n✓  Email enviado com sucesso!")
        print(f"\nPróximos passos:")
        print(f"  1. Abra o Gmail em {TEST_EMAIL}")
        print(f"  2. Procure o email '{SUBJECT}'")
        print(f"  3. Clique em 'Exibir imagens' ou 'Carregar imagens externas'")
        print(f"  4. Aguarde ~10s e verifique no monitor do Telegram se aparece 1 abertura")
        if TRACKING_BASE_URL:
            print(f"\n  Ou acesse diretamente no browser para simular abertura:")
            print(f"  {pixel_url}")
    else:
        print(f"\n✗  Falha ao enviar. Verifique as credenciais SMTP no .env.")

    print("=" * 55)


if __name__ == "__main__":
    main()
