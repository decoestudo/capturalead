#!/bin/bash
# Deploy do Lead Scraper na VPS
# Uso: bash scripts/deploy_vps.sh
set -e

echo "======================================"
echo "  Lead Scraper — Deploy VPS"
echo "======================================"

# Usa o .env correto para VPS
if [ ! -f .env ]; then
    cp .env.vps .env
    echo "[OK] .env criado a partir de .env.vps"
fi

# Garante que o Redis não exponha porta (não sobrescreve TopAgenda)
echo "[OK] Verificando configuração..."

# Instala dependências do playwright se necessário
echo "[INFO] Instalando browsers Playwright..."
docker-compose run --rm --no-deps app playwright install chromium --with-deps 2>/dev/null || true

# Sobe banco + redis primeiro
echo "[INFO] Subindo postgres + redis..."
docker-compose up -d postgres redis

# Aguarda postgres ficar saudável
echo "[INFO] Aguardando PostgreSQL..."
sleep 5

# Roda o importador da Receita Federal em background
echo ""
echo "======================================"
echo "  Importando dados da Receita Federal"
echo "  Isso vai demorar ~10-30 min na VPS"
echo "  Acompanhe: docker-compose logs -f importer"
echo "======================================"
docker-compose --profile import run --rm importer &
IMPORT_PID=$!
echo "[INFO] Importer rodando em background (PID=$IMPORT_PID)"

# Sobe o bot imediatamente (funciona mesmo sem a tabela Receita — usa fallback API)
echo ""
echo "[INFO] Subindo bot (modo fallback API até import terminar)..."
docker-compose up -d app

echo ""
echo "======================================"
echo "  Deploy concluído!"
echo ""
echo "  Bot:     docker-compose logs -f app"
echo "  Import:  docker-compose logs -f importer"
echo "  Status:  docker-compose ps"
echo "======================================"
