"""Configurações do projeto IAEmpreendedora."""
import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carrega o arquivo backend/.env, quando existir. Variáveis já definidas
# no ambiente (por exemplo, no painel do Render) têm prioridade.
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "chave-temporaria-apenas-para-desenvolvimento",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if host.strip()
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "formularios",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Origens permitidas para o servidor de desenvolvimento do Vite.
# A lista pode ser sobrescrita pela variável CORS_ALLOWED_ORIGINS,
# separando as origens por vírgula.
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# SQLite em todos os ambientes. O caminho do arquivo pode ser definido
# pela variável SQLITE_DB_PATH (em produção, apontando para um disco
# persistente). Sem a variável, usa backend/db.sqlite3. Caminhos
# relativos são resolvidos a partir da pasta backend/.
caminho_banco = os.environ.get("SQLITE_DB_PATH", "").strip()

# O Render sempre define RENDER=true. Lá, a variável é obrigatória:
# sem ela, o banco seria criado no sistema de arquivos temporário do
# serviço e as respostas seriam apagadas a cada deploy ou reinício.
if not caminho_banco and os.environ.get("RENDER") == "true":
    raise ImproperlyConfigured(
        "A variável SQLITE_DB_PATH não foi definida. No Render, ela deve "
        "apontar para um arquivo no disco persistente, por exemplo "
        "/var/data/db.sqlite3. Veja backend/BANCO_DE_DADOS.md."
    )

SQLITE_DB_PATH = Path(caminho_banco or "db.sqlite3")
if not SQLITE_DB_PATH.is_absolute():
    SQLITE_DB_PATH = BASE_DIR / SQLITE_DB_PATH

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": SQLITE_DB_PATH,
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
