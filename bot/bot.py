#!/usr/bin/env python3

import os
import json
import time
import html
import shutil
import subprocess
import threading
import urllib.request
import urllib.parse
import urllib.error
import importlib.util
import re
from pathlib import Path


BASE = "/root/apk-manager"
CONFIG = BASE + "/bot/config.env"
WORK = BASE + "/work"
RESULTS = BASE + "/results"
STATE_FILE = WORK + "/state.json"
EHI_STATE_FILE = WORK + "/ehi_state.json"

os.makedirs(WORK, exist_ok=True)
os.makedirs(RESULTS, exist_ok=True)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

def load_config():
    cfg = {}
    try:
        with open(CONFIG, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                cfg[key.strip()] = value.strip()
    except Exception as e:
        print("CONFIG:", e, flush=True)
    return cfg


def load_token():
    return load_config().get("BOT_TOKEN", "")


TOKEN = load_token()

if not TOKEN:
    raise SystemExit("BOT_TOKEN não configurado")

API = "https://api.telegram.org/bot" + TOKEN
FILE_API = "https://api.telegram.org/file/bot" + TOKEN


# ============================================================
# TELEGRAM API
# ============================================================

def api(method, data=None):
    data = data or {}
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        API + "/" + method,
        data=body,
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode())


def telegram_text(text):
    text = str(text)
    if len(text) <= 3900:
        return text, "HTML"
    return (
        text[:3800]
        + "\n\n⚠️ Resultado cortado. Use RELATÓRIO para o resultado completo.",
        None
    )


def send(chat_id, text, keyboard=None):
    text, parse_mode = telegram_text(text)
    data = {"chat_id": chat_id, "text": text}

    if parse_mode:
        data["parse_mode"] = parse_mode

    if keyboard:
        data["reply_markup"] = json.dumps(
            keyboard, ensure_ascii=False
        )

    try:
        return api("sendMessage", data)
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode()
        except Exception:
            detail = str(e)

        print(
            "SEND MESSAGE ERROR:",
            e.code,
            detail[:1500],
            flush=True
        )

        fallback = {
            "chat_id": chat_id,
            "text": str(text)
        }

        if keyboard:
            fallback["reply_markup"] = json.dumps(
                keyboard, ensure_ascii=False
            )

        try:
            return api("sendMessage", fallback)
        except Exception as e2:
            print("SEND FALLBACK ERROR:", e2, flush=True)
            return None

    except Exception as e:
        print("SEND ERROR:", e, flush=True)
        return None


def edit_message(chat_id, message_id, text, keyboard=None):
    text, parse_mode = telegram_text(text)
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text
    }

    if parse_mode:
        data["parse_mode"] = parse_mode

    if keyboard:
        data["reply_markup"] = json.dumps(
            keyboard, ensure_ascii=False
        )

    try:
        return api("editMessageText", data)
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode()
        except Exception:
            detail = str(e)
        print(
            "EDIT MESSAGE ERROR:",
            e.code,
            detail[:1500],
            flush=True
        )
        return None
    except Exception as e:
        print("EDIT MESSAGE ERROR:", e, flush=True)
        return None


def answer(callback_id):
    try:
        api("answerCallbackQuery", {
            "callback_query_id": callback_id
        })
    except Exception as e:
        print("CALLBACK:", e, flush=True)


# ============================================================
# MENUS
# ============================================================

def keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📦 ENVIAR APK", "callback_data": "upload"}],
            [
                {"text": "🔍 ANALISAR", "callback_data": "analisar"},
                {"text": "📋 MANIFEST", "callback_data": "manifest"}
            ],
            [
                {"text": "🔎 CONFIGURAÇÕES", "callback_data": "config"},
                {"text": "🌐 SERVIDORES", "callback_data": "servidores"}
            ],
            [
                {"text": "🔐 CRIPTOGRAFIA", "callback_data": "crypto"},
                {"text": "🔑 CHAVES", "callback_data": "chaves"}
            ],
            [
                {"text": "🔍 DEX / CÓDIGO", "callback_data": "dex"},
                {"text": "📊 RELATÓRIO", "callback_data": "relatorio"}
            ],
            [
                {"text": "🔨 RECOMPILAR", "callback_data": "recompilar"},
                {"text": "✍️ ASSINAR", "callback_data": "assinar"}
            ],
            [{"text": "🗑️ LIMPAR", "callback_data": "limpar"}]
        ]
    }


def ehi_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🔓 PROCESSAR EHI", "callback_data": "ehi_processar"}],
            [{"text": "🗑️ LIMPAR", "callback_data": "limpar"}]
        ]
    }


# ============================================================
# ESTADO
# ============================================================

def load_json_state(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_json_state(path, state):
    try:
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
        os.replace(tmp, path)
    except Exception as e:
        print("STATE:", e, flush=True)


def load_state():
    return load_json_state(STATE_FILE)


def save_state(state):
    save_json_state(STATE_FILE, state)


def load_ehi_state():
    return load_json_state(EHI_STATE_FILE)


def save_ehi_state(state):
    save_json_state(EHI_STATE_FILE, state)


def get_apk(chat_id):
    path = load_state().get(str(chat_id))
    if path and os.path.isfile(path):
        return path
    return None


def set_apk(chat_id, path):
    state = load_state()
    state[str(chat_id)] = path
    save_state(state)


def get_ehi(chat_id):
    path = load_ehi_state().get(str(chat_id))
    if path and os.path.isfile(path):
        return path
    return None


def set_ehi(chat_id, path):
    state = load_ehi_state()
    state[str(chat_id)] = path
    save_ehi_state(state)


def user_dir(chat_id):
    path = os.path.join(WORK, str(chat_id))
    os.makedirs(path, exist_ok=True)
    return path


# ============================================================
# EXECUÇÃO DE FERRAMENTAS
# ============================================================

def run(cmd, timeout=600):
    try:
        r = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout
        )
        return r.returncode, r.stdout
    except subprocess.TimeoutExpired:
        return 124, "Tempo limite excedido."
    except Exception as e:
        return 1, str(e)


# ============================================================
# DOWNLOAD DE ARQUIVOS TELEGRAM
# ============================================================

def download_file(chat_id, file_id, filename, extension):
    try:
        info = api("getFile", {"file_id": file_id})

        if not info.get("ok"):
            print("GETFILE:", info, flush=True)
            return None

        remote = info["result"]["file_path"]
        name = os.path.basename(filename)

        if not name.lower().endswith(extension):
            return None

        path = os.path.join(user_dir(chat_id), name)

        url = FILE_API + "/" + remote
        urllib.request.urlretrieve(url, path)

        if not os.path.isfile(path):
            return None

        if os.path.getsize(path) < 1:
            return None

        return path

    except Exception as e:
        print("DOWNLOAD:", e, flush=True)
        return None


def download_apk(chat_id, file_id, filename):
    path = download_file(chat_id, file_id, filename, ".apk")
    if path:
        set_apk(chat_id, path)
    return path


def download_ehi(chat_id, file_id, filename):
    path = download_file(chat_id, file_id, filename, ".ehi")
    if path:
        set_ehi(chat_id, path)
    return path


# ============================================================
# APKTOOL
# ============================================================

def decompile(chat_id, apk):
    out = os.path.join(user_dir(chat_id), "decompiled")

    if os.path.isdir(out):
        shutil.rmtree(out)

    code, result = run(
        ["apktool", "d", "-f", apk, "-o", out],
        900
    )
    return code, result, out


def ensure_decompiled(chat_id, apk):
    out = os.path.join(user_dir(chat_id), "decompiled")

    if os.path.isfile(
        os.path.join(out, "AndroidManifest.xml")
    ):
        return True, out, ""

    code, result, out = decompile(chat_id, apk)
    return code == 0, out, result


# ============================================================
# BUSCA
# ============================================================

def search(directory, words):
    found = []

    for root, dirs, files in os.walk(directory):
        for filename in files:
            path = os.path.join(root, filename)

            try:
                if os.path.getsize(path) > 10 * 1024 * 1024:
                    continue

                with open(
                    path,
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as f:
                    for n, line in enumerate(f, 1):
                        low = line.lower()

                        if any(
                            w.lower() in low
                            for w in words
                        ):
                            rel = os.path.relpath(path, directory)
                            found.append(
                                "{}:{}: {}".format(
                                    rel,
                                    n,
                                    line.strip()[:500]
                                )
                            )

                            if len(found) >= 100:
                                return found
            except Exception:
                pass

    return found


# ============================================================
# OPENAI
# ============================================================

def ask_openai(prompt):
    cfg = load_config()
    key = cfg.get("OPENAI_API_KEY", "")
    model = cfg.get("OPENAI_MODEL", "gpt-6-luna")

    if not key:
        return "❌ OPENAI_API_KEY não configurada no servidor."

    system = (
        "Você é a IA do TECH NET APK MANAGER. "
        "Analise resultados técnicos de APKs de forma objetiva e clara. "
        "Explique o que foi encontrado, indique arquivos, URLs, domínios, "
        "configurações, protocolos e possíveis riscos quando existirem. "
        "Não invente informações. Se algo não estiver nos resultados, "
        "diga que não foi encontrado. A análise deve ser feita somente "
        "para aplicativos que o usuário tem autorização para analisar."
    )

    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ]
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.loads(r.read().decode())

        result = data.get("output_text")
        if result:
            return str(result).strip()

        textos = []

        for item in data.get("output", []):
            if item.get("type") != "message":
                continue

            for content in item.get("content", []):
                if content.get("type") == "output_text":
                    texto = content.get("text", "")
                    if texto:
                        textos.append(texto)

        result = "\n\n".join(textos).strip()

        if result:
            return result

        return "❌ A IA respondeu, mas não foi encontrado texto."

    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode()
        except Exception:
            detail = str(e)

        return (
            "❌ Erro da API da IA: HTTP "
            + str(e.code)
            + "\n"
            + detail[:1200]
        )

    except Exception as e:
        return "❌ Erro ao consultar a IA: " + str(e)


# ============================================================
# ANÁLISE IA
# ============================================================

def action_analisar_ia(chat_id, apk):
    code, output, directory = decompile(chat_id, apk)

    if code != 0:
        return (
            "❌ <b>Falha ao descompilar.</b>\n\n"
            "<code>"
            + html.escape(output[-3000:])
            + "</code>"
        )

    partes = []

    mcode, manifest = run(
        ["aapt", "dump", "badging", apk],
        120
    )

    if mcode == 0:
        linhas = []

        for line in manifest.splitlines():
            if (
                line.startswith("package:")
                or line.startswith("uses-permission:")
                or line.startswith("application:")
                or line.startswith("launchable-activity:")
                or line.startswith("uses-feature:")
            ):
                linhas.append(line)

        partes.append(
            "=== MANIFEST ===\n" + "\n".join(linhas[:150])
        )

    palavras = [
        "http://", "https://", "server", "host", "proxy",
        "websocket", "xhttp", "vless", "vmess", "trojan",
        "ssh", "tls", "endpoint", "api", "token", "apikey",
        "secret", "encrypt", "decrypt", "aes", "rsa"
    ]

    try:
        encontrados = search(directory, palavras)
        partes.append(
            "=== REFERÊNCIAS ENCONTRADAS ===\n"
            + "\n".join(encontrados[:300])
        )
    except Exception as e:
        partes.append("=== ERRO NA BUSCA ===\n" + str(e))

    contexto = "\n\n".join(partes)[:30000]

    prompt = (
        "Analise tecnicamente os resultados abaixo referentes a um APK.\n\n"
        "Informe de forma organizada:\n"
        "1. Identificação do aplicativo\n"
        "2. Permissões relevantes\n"
        "3. Servidores, domínios, URLs ou endpoints encontrados\n"
        "4. Protocolos ou tecnologias identificadas\n"
        "5. Configurações importantes encontradas\n"
        "6. Possíveis mecanismos de criptografia ou ofuscação encontrados\n"
        "7. Pontos que merecem investigação adicional\n"
        "8. Resumo final em linguagem simples\n\n"
        "Não invente dados. Se algo não estiver presente nos resultados, "
        "informe que não foi encontrado.\n\n"
        + contexto
    )

    ia = html.escape(ask_openai(prompt))

    return (
        "🤖 <b>ANÁLISE IA — TECH NET APK MANAGER</b>\n\n"
        + ia
    )


# ============================================================
# MANIFEST
# ============================================================

def action_manifest(chat_id, apk):
    code, output = run(
        ["aapt", "dump", "badging", apk],
        120
    )

    if code != 0:
        return (
            "❌ Erro no Manifest.\n\n"
            "<code>"
            + html.escape(output[-3000:])
            + "</code>"
        )

    linhas = []

    for line in output.splitlines():
        if (
            line.startswith("package:")
            or line.startswith("uses-permission:")
            or line.startswith("application:")
            or line.startswith("launchable-activity:")
            or line.startswith("uses-feature:")
        ):
            linhas.append(line)

    return (
        "📋 <b>MANIFEST</b>\n\n"
        "<code>"
        + html.escape("\n".join(linhas)[:7000])
        + "</code>"
    )


# ============================================================
# BUSCA GENÉRICA
# ============================================================

def action_search(chat_id, apk, words, title):
    ok, directory, output = ensure_decompiled(chat_id, apk)

    if not ok:
        return (
            "❌ Não foi possível descompilar o APK.\n\n"
            "<code>"
            + html.escape(output[-3000:])
            + "</code>"
        )

    found = search(directory, words)

    if not found:
        return title + "\n\nℹ️ Nenhuma ocorrência encontrada."

    return (
        title
        + "\n\n<code>"
        + html.escape("\n".join(found)[:7000])
        + "</code>"
    )


# ============================================================
# ENVIO DE DOCUMENTOS
# ============================================================

def send_document(chat_id, path, caption):
    if not os.path.isfile(path):
        print("DOCUMENTO NÃO EXISTE:", path, flush=True)
        return False

    try:
        result = subprocess.run(
            [
                "curl", "-sS", "-X", "POST",
                API + "/sendDocument",
                "-F", "chat_id=" + str(chat_id),
                "-F", "document=@" + path,
                "-F", "caption=" + caption
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=300
        )

        print(
            "SEND DOCUMENT:",
            result.stdout[-1000:],
            flush=True
        )

        try:
            response = json.loads(result.stdout)
            return bool(response.get("ok"))
        except Exception:
            return result.returncode == 0

    except Exception as e:
        print("SEND DOCUMENT ERROR:", e, flush=True)
        return False


# ============================================================
# EHI
# ============================================================

def copy_script(name, workdir):
    source = os.path.join(BOT_DIR, name)

    if not os.path.isfile(source):
        raise FileNotFoundError(
            f"{name} não encontrado em {BOT_DIR}"
        )

    destination = os.path.join(workdir, name)

    shutil.copy2(source, destination)

    return destination

def run_script(name, workdir, timeout=900):
    script = copy_script(name, workdir)

    result = subprocess.run(
        [
            "python3",
            script
        ],
        cwd=workdir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout
    )

    return result.returncode, result.stdout

def send_new_files(
    chat_id,
    workdir,
    before,
    caption,
    excluded=None
):
    excluded = excluded or set()
    sent = 0

    for root, dirs, files in os.walk(workdir):
        for name in files:
            path = os.path.join(root, name)

            relative = os.path.relpath(
                path,
                workdir
            )

            if relative in before:
                continue

            if name in excluded:
                continue

            if (
                os.path.isfile(path)
                and os.path.getsize(path) > 0
            ):
                if send_document(
                    chat_id,
                    path,
                    caption
                ):
                    sent += 1

    return sent

def action_b(chat_id, path):
    workdir = user_dir(chat_id)

    if not path.lower().endswith(".log"):
        return (
            "⚠️ Para <b>B / BASE64</b>, "
            "envie um arquivo <code>.log</code>."
        )

    # b.py procura um .log com nome numérico de 15–20 dígitos.
    filename = os.path.basename(path)

    if not re.match(
        r"^\d{15,20}\.log$",
        filename
    ):
        new_name = (
            str(int(time.time() * 1000))[:17]
            + ".log"
        )

        new_path = os.path.join(
            workdir,
            new_name
        )

        os.replace(path, new_path)
        path = new_path

    before = set()

    for root, dirs, files in os.walk(workdir):
        for name in files:
            before.add(
                os.path.relpath(
                    os.path.join(root, name),
                    workdir
                )
            )

    try:
        code, output = run_script(
            "b.py",
            workdir,
            900
        )

    except Exception as e:
        return (
            "❌ <b>Erro executando B:</b>\n\n"
            "<code>"
            + html.escape(str(e))
            + "</code>"
        )

    sent = send_new_files(
        chat_id,
        workdir,
        before,
        "🔐 RESULTADO B / BASE64",
        {
            "b.py"
        }
    )

    if sent:
        return (
            "✅ <b>B / BASE64 concluído.</b>\n\n"
            "📄 "
            + str(sent)
            + " arquivo(s) enviado(s)."
        )

    return (
        "⚠️ B terminou sem gerar arquivo para envio.\n\n"
        "<code>"
        + html.escape(output[-3000:])
        + "</code>"
    )

def action_dec(chat_id, path):
    workdir = user_dir(chat_id)

    if os.path.basename(path) != "user_id.txt":
        return (
            "⚠️ Para <b>DTUNNEL</b>, envie o arquivo "
            "<code>user_id.txt</code>."
        )

    before = set()

    for root, dirs, files in os.walk(workdir):
        for name in files:
            before.add(
                os.path.relpath(
                    os.path.join(root, name),
                    workdir
                )
            )

    try:
        code, output = run_script(
            "dec.py",
            workdir,
            1200
        )

    except Exception as e:
        return (
            "❌ <b>Erro executando DTUNNEL:</b>\n\n"
            "<code>"
            + html.escape(str(e))
            + "</code>"
        )

    sent = 0

    for root, dirs, files in os.walk(workdir):
        for name in files:
            path2 = os.path.join(
                root,
                name
            )

            relative = os.path.relpath(
                path2,
                workdir
            )

            if relative in before:
                continue

            if name in {
                "dec.py",
                "user_id.txt"
            }:
                continue

            if (
                os.path.isfile(path2)
                and os.path.getsize(path2) > 0
            ):
                if send_document(
                    chat_id,
                    path2,
                    "🔐 DTUNNEL"
                ):
                    sent += 1

    if sent:
        return (
            "✅ <b>DTUNNEL concluído.</b>\n\n"
            "📄 "
            + str(sent)
            + " arquivo(s) enviado(s)."
        )

    return (
        "⚠️ DTUNNEL terminou sem arquivo novo.\n\n"
        "<code>"
        + html.escape(output[-3000:])
        + "</code>"
    )

def action_revh(chat_id, path):
    if not path or not os.path.isfile(path):
        return (
            "⚠️ Envie o arquivo codificado "
            "que deseja processar pelo REVHUNTER."
        )

    try:
        revh_path = os.path.join(
            BOT_DIR,
            "revh.py"
        )

        if not os.path.isfile(revh_path):
            raise FileNotFoundError(
                "revh.py não encontrado."
            )

        spec = importlib.util.spec_from_file_location(
            "revh_local",
            revh_path
        )

        if not spec or not spec.loader:
            raise RuntimeError(
                "Não foi possível carregar revh.py"
            )

        module = (
            importlib.util.module_from_spec(spec)
        )

        spec.loader.exec_module(module)

        texto = Path(path).read_text(
            encoding="utf-8",
            errors="strict"
        ).strip()

        resultado = module.sessao_de_desbloqueio(
            texto
        )

        output = os.path.join(
            RESULTS,
            "revh_"
            + str(chat_id)
            + "_"
            + os.path.basename(path)
            + ".txt"
        )

        Path(output).write_text(
            resultado,
            encoding="utf-8"
        )

        if not send_document(
            chat_id,
            output,
            "🕵️ REVHUNTER — resultado"
        ):
            return (
                "❌ REVHUNTER processou o arquivo, "
                "mas não consegui enviar o resultado."
            )

        return (
            "✅ <b>REVHUNTER PROCESSADO.</b>\n\n"
            "📄 Resultado enviado."
        )

    except Exception as e:
        return (
            "❌ <b>REVHUNTER não conseguiu processar "
            "o arquivo.</b>\n\n"
            "<code>"
            + html.escape(str(e))
            + "</code>"
        )

def action_ehi(chat_id, ehi_path):
    if not ehi_path or not os.path.isfile(ehi_path):
        return "❌ Nenhum arquivo .ehi carregado."

    try:
        from ehi import InterrogadorEHI
    except Exception as e:
        return (
            "❌ <b>Processador EHI não disponível.</b>\n\n"
            "<code>"
            + html.escape(str(e))
            + "</code>\n\n"
            "O arquivo <code>ehi.py</code> precisa estar em "
            "<code>/root/apk-manager/bot/</code> e suas dependências "
            "precisam estar instaladas."
        )

    try:
        with open(ehi_path, "rb") as f:
            dados = f.read()

        resultado, estatisticas = (
            InterrogadorEHI.executar_com_relatorio(dados)
        )

        if not resultado:
            motivo = estatisticas.get(
                "motivo_falha",
                "motivo desconhecido"
            )

            return (
                "❌ <b>Não foi possível processar o EHI.</b>\n\n"
                "Motivo:\n"
                "<code>"
                + html.escape(str(motivo))
                + "</code>"
            )

        nome = os.path.basename(ehi_path)
        result_file = os.path.join(
            RESULTS,
            "ehi_"
            + str(chat_id)
            + "_"
            + nome
            + ".txt"
        )

        with open(result_file, "w", encoding="utf-8") as f:
            f.write(resultado)

        sent = send_document(
            chat_id,
            result_file,
            "📄 EHI PROCESSADO — resultado .txt"
        )

        if not sent:
            return (
                "❌ O processamento terminou, mas não consegui "
                "enviar o arquivo .txt."
            )

        modo = estatisticas.get("modo") or "não informado"

        return (
            "✅ <b>EHI PROCESSADO COM SUCESSO.</b>\n\n"
            "📄 Resultado enviado como arquivo .txt\n"
            "⚙️ Modo: <code>"
            + html.escape(str(modo))
            + "</code>"
        )

    except Exception as e:
        print("EHI ERROR:", repr(e), flush=True)
        return (
            "❌ <b>Erro ao processar o EHI.</b>\n\n"
            "<code>"
            + html.escape(str(e))
            + "</code>"
        )


# ============================================================
# DEX
# ============================================================

def action_dex(chat_id, apk):
    base = os.path.join(user_dir(chat_id), "dex")

    if os.path.isdir(base):
        shutil.rmtree(base)

    os.makedirs(base)

    code, output = run(
        ["unzip", "-oq", apk, "-d", base],
        180
    )

    if code != 0:
        return (
            "❌ Falha ao extrair o APK.\n\n"
            "<code>"
            + html.escape(output[-3000:])
            + "</code>"
        )

    dex = []

    for root, dirs, files in os.walk(base):
        for name in files:
            if name.endswith(".dex"):
                dex.append(os.path.join(root, name))

    if not dex:
        return "🔍 Nenhum DEX encontrado."

    result_file = os.path.join(
        RESULTS,
        "dex_" + str(chat_id) + ".txt"
    )

    with open(result_file, "w", encoding="utf-8") as f:
        for item in dex:
            code, strings = run(
                ["strings", item],
                120
            )
            f.write(
                "\n===== "
                + os.path.basename(item)
                + " =====\n"
            )
            f.write(strings)

    sent = send_document(
        chat_id,
        result_file,
        "🔍 DEX / STRINGS"
    )

    if not sent:
        return (
            "❌ O DEX foi analisado, mas não consegui "
            "enviar o arquivo."
        )

    return "✅ DEX analisado. O relatório foi enviado como arquivo."


# ============================================================
# RELATÓRIO
# ============================================================

def action_report(chat_id, apk):
    ok, directory, output = ensure_decompiled(chat_id, apk)

    result_file = os.path.join(
        RESULTS,
        "relatorio_" + str(chat_id) + ".txt"
    )

    try:
        with open(result_file, "w", encoding="utf-8") as f:
            f.write("TECH NET APK MANAGER\n")
            f.write("=" * 60 + "\n\n")
            f.write(
                "APK: "
                + os.path.basename(apk)
                + "\n"
            )
            f.write(
                "TAMANHO: "
                + str(os.path.getsize(apk))
                + " bytes\n\n"
            )

            code, badging = run(
                ["aapt", "dump", "badging", apk],
                120
            )

            f.write("=== MANIFEST ===\n")
            f.write(badging)
            f.write("\n\n")

            if ok:
                words = [
                    "http://", "https://", "ws://", "wss://",
                    "vless://", "vmess://", "trojan://",
                    "server", "host", "proxy", "websocket",
                    "xhttp", "encrypt", "decrypt", "cipher",
                    "aes", "rsa", "token", "apikey", "secret"
                ]

                f.write("=== REFERÊNCIAS ===\n")

                for item in search(directory, words):
                    f.write(item + "\n")

    except Exception as e:
        return (
            "❌ Erro ao gerar relatório:\n\n"
            "<code>"
            + html.escape(str(e))
            + "</code>"
        )

    sent = send_document(
        chat_id,
        result_file,
        "📊 RELATÓRIO COMPLETO"
    )

    if not sent:
        return (
            "❌ Relatório gerado, mas não consegui enviar o arquivo."
        )

    return "✅ Relatório completo enviado."


# ============================================================
# RECOMPILAÇÃO
# ============================================================

def action_recompile(chat_id, apk):
    ok, directory, output = ensure_decompiled(chat_id, apk)

    if not ok:
        return (
            "❌ APK não pôde ser preparado para recompilação.\n\n"
            "<code>"
            + html.escape(output[-3000:])
            + "</code>"
        )

    output_apk = os.path.join(
        RESULTS,
        "recompilado_" + str(chat_id) + ".apk"
    )

    if os.path.exists(output_apk):
        os.remove(output_apk)

    code, result = run(
        ["apktool", "b", directory, "-o", output_apk],
        900
    )

    if code != 0:
        return (
            "❌ <b>Erro ao recompilar.</b>\n\n"
            "<code>"
            + html.escape(result[-4000:])
            + "</code>"
        )

    sent = send_document(
        chat_id,
        output_apk,
        "🔨 APK RECOMPILADO"
    )

    if not sent:
        return (
            "❌ APK recompilado, mas não consegui enviar o arquivo."
        )

    return "✅ APK recompilado e enviado."


# ============================================================
# ASSINATURA
# ============================================================

def action_sign(chat_id, apk):
    keystore = os.path.join(
        BASE,
        "tools",
        "technet.keystore"
    )

    if not os.path.isfile(keystore):
        return (
            "✍️ <b>ASSINATURA</b>\n\n"
            "O APK foi preparado, mas ainda não existe "
            "um keystore configurado em:\n\n"
            "<code>"
            + html.escape(keystore)
            + "</code>\n\n"
            "Configure seu keystore próprio antes de usar esta função."
        )

    return (
        "✍️ <b>ASSINATURA</b>\n\n"
        "Keystore encontrado.\n\n"
        "A etapa de assinatura ainda precisa dos dados "
        "do seu keystore antes de assinar o APK."
    )


# ============================================================
# LIMPAR
# ============================================================

def clear_user(chat_id):
    path = user_dir(chat_id)

    if os.path.isdir(path):
        shutil.rmtree(path)

    state = load_state()
    state.pop(str(chat_id), None)
    save_state(state)

    ehi_state = load_ehi_state()
    ehi_state.pop(str(chat_id), None)
    save_ehi_state(ehi_state)


# ============================================================
# MENSAGEM DE PROCESSAMENTO
# ============================================================

def processing_message(chat_id, action):
    nomes = {
        "analisar": "🤖 IA ANALISANDO",
        "manifest": "📋 ANALISANDO MANIFEST",
        "config": "🔎 PROCURANDO CONFIGURAÇÕES",
        "servidores": "🌐 PROCURANDO SERVIDORES",
        "crypto": "🔐 ANALISANDO CRIPTOGRAFIA",
        "chaves": "🔑 PROCURANDO CHAVES",
        "dex": "🔍 ANALISANDO DEX / CÓDIGO",
        "relatorio": "📊 GERANDO RELATÓRIO",
        "recompilar": "🔨 RECOMPILANDO APK",
        "assinar": "✍️ PREPARANDO ASSINATURA",
        "ehi_processar": "🔓 PROCESSANDO EHI"
    }

    titulo = nomes.get(action, "⚙️ PROCESSANDO")

    return send(
        chat_id,
        "<b>"
        + titulo
        + "...</b>\n\n"
        "📦 Processando o arquivo\n"
        "🔎 Executando as ferramentas\n"
        "🧠 Preparando o resultado\n\n"
        "⏳ <i>Aguarde, o serviço está sendo executado...</i>"
    )


# ============================================================
# FINALIZA PROCESSAMENTO
# ============================================================

def finish_processing(chat_id, processing_id, text, menu=None):
    menu = menu or keyboard()

    if processing_id:
        result = edit_message(
            chat_id,
            processing_id,
            text,
            menu
        )

        if result and result.get("ok"):
            return

    send(chat_id, text, menu)


# ============================================================
# EXECUÇÃO DOS BOTÕES
# ============================================================

def execute(chat_id, action):

    if action == "upload":
        send(
            chat_id,
            "📦 <b>ENVIE O APK</b>\n\n"
            "Envie o arquivo .apk nesta conversa.",
            keyboard()
        )
        return

    if action == "limpar":
        clear_user(chat_id)
        send(
            chat_id,
            "🗑️ <b>ARQUIVOS REMOVIDOS.</b>\n\n"
            "Pode enviar outro APK ou EHI.",
            keyboard()
        )
        return

    processing_id = None

    try:
        processing = processing_message(chat_id, action)

        if isinstance(processing, dict):
            processing_id = (
                processing
                .get("result", {})
                .get("message_id")
            )
    except Exception as e:
        print("PROCESSING MESSAGE:", e, flush=True)

    try:
        # ----------------------------------------------------
        # EHI
        # ----------------------------------------------------
        if action == "ehi_processar":
            ehi_path = get_ehi(chat_id)

            if not ehi_path:
                text = (
                    "⚠️ <b>NENHUM EHI CARREGADO.</b>\n\n"
                    "Envie um arquivo .ehi primeiro."
                )
            else:
                text = action_ehi(chat_id, ehi_path)

            finish_processing(
                chat_id,
                processing_id,
                text,
                ehi_keyboard()
            )
            return

        # ----------------------------------------------------
        # APK
        # ----------------------------------------------------
        apk = get_apk(chat_id)

        if not apk:
            text = (
                "⚠️ <b>NENHUM APK CARREGADO.</b>\n\n"
                "Envie o APK primeiro."
            )

            finish_processing(
                chat_id,
                processing_id,
                text
            )
            return

        if action == "analisar":
            text = action_analisar_ia(chat_id, apk)

        elif action == "manifest":
            text = action_manifest(chat_id, apk)

        elif action == "config":
            text = action_search(
                chat_id,
                apk,
                [
                    "config", "server", "host", "proxy",
                    "websocket", "xhttp", "vless", "vmess",
                    "trojan", "ssh", "tls", "endpoint",
                    "http://", "https://"
                ],
                "🔎 <b>CONFIGURAÇÕES</b>"
            )

        elif action == "servidores":
            text = action_search(
                chat_id,
                apk,
                [
                    "server", "host", "hostname", "address",
                    "endpoint", "remote", "http://", "https://",
                    "ws://", "wss://"
                ],
                "🌐 <b>SERVIDORES / ENDPOINTS</b>"
            )

        elif action == "crypto":
            text = action_search(
                chat_id,
                apk,
                [
                    "cipher", "encrypt", "decrypt", "aes", "des",
                    "rsa", "gcm", "cbc", "ecb", "secretkey",
                    "base64", "sha256"
                ],
                "🔐 <b>CRIPTOGRAFIA</b>"
            )

        elif action == "chaves":
            text = action_search(
                chat_id,
                apk,
                [
                    "apikey", "api_key", "token", "secret",
                    "password", "passwd", "privatekey",
                    "publickey", "key", "credential"
                ],
                "🔑 <b>CHAVES / MÉTODOS</b>"
            )

        elif action == "dex":
            text = action_dex(chat_id, apk)

        elif action == "relatorio":
            text = action_report(chat_id, apk)

        elif action == "recompilar":
            text = action_recompile(chat_id, apk)

        elif action == "assinar":
            text = action_sign(chat_id, apk)

        else:
            text = "❌ Opção desconhecida."

    except Exception as e:
        print("EXECUTE ERROR:", repr(e), flush=True)

        text = (
            "❌ <b>ERRO AO PROCESSAR.</b>\n\n"
            "<code>"
            + html.escape(str(e))[:3500]
            + "</code>"
        )

    finish_processing(
        chat_id,
        processing_id,
        text
    )


# ============================================================
# PROCESSAR UPDATE
# ============================================================

def auto_apk(chat_id, apk):
    """Analisa automaticamente um APK usando as ferramentas existentes."""
    workdir = user_dir(chat_id)
    report = os.path.join(RESULTS, "auto_apk_%s.txt" % chat_id)

    lines = []
    lines.append("TECH NET APK MANAGER — ANÁLISE AUTOMÁTICA")
    lines.append("=" * 70)
    lines.append("APK: " + os.path.basename(apk))
    lines.append("TAMANHO: %d bytes" % os.path.getsize(apk))
    lines.append("")

    # Manifest / identificação
    code, badging = run(["aapt", "dump", "badging", apk], 180)
    lines.append("=== IDENTIFICAÇÃO / MANIFEST ===")
    if code == 0:
        lines.append(badging)
    else:
        lines.append("Falha no aapt: " + badging[-3000:])
    lines.append("")

    # Descompilação para pesquisa de informações
    ok, directory, dec_output = ensure_decompiled(chat_id, apk)
    if ok:
        words = [
            "http://", "https://", "ws://", "wss://",
            "vless://", "vmess://", "trojan://", "ssh://",
            "server", "host", "hostname", "address", "endpoint",
            "proxy", "remote", "websocket", "xhttp", "tls",
            "api", "token", "apikey", "key", "secret", "password",
            "username", "login", "config", "encrypt", "decrypt",
            "cipher", "aes", "des", "rsa", "rc4", "chacha",
            "base64", "openssl", "keystore", "certificate", "publickey",
            "privatekey", "iv", "salt", "nonce"
        ]
        found = search(directory, words)
        lines.append("=== SERVIDORES / URLS / CONFIGURAÇÕES / CHAVES / CRIPTO ===")
        if found:
            lines.extend(found[:2000])
        else:
            lines.append("Nenhuma ocorrência encontrada.")
        lines.append("")
    else:
        lines.append("=== DESCOMPILAÇÃO ===")
        lines.append("Falhou: " + dec_output[-5000:])
        lines.append("")

    # DEX e strings
    dexdir = os.path.join(workdir, "auto_dex")
    if os.path.isdir(dexdir):
        shutil.rmtree(dexdir)
    os.makedirs(dexdir, exist_ok=True)
    code, output = run(["unzip", "-oq", apk, "-d", dexdir], 240)
    lines.append("=== DEX / STRINGS ===")
    dex_files=[]
    if code == 0:
        for root, dirs, files in os.walk(dexdir):
            for name in files:
                if name.endswith('.dex'):
                    dex_files.append(os.path.join(root,name))
        lines.append("DEX encontrados: " + str(len(dex_files)))
        for item in dex_files:
            scode, strings = run(["strings", item], 180)
            if scode == 0:
                # Só inclui linhas potencialmente úteis no relatório, para não gerar um arquivo gigantesco.
                useful=[]
                for line in strings.splitlines():
                    low=line.lower()
                    if any(k in low for k in ["http", "server", "host", "proxy", "vless", "vmess", "trojan", "ssh", "xhttp", "key", "secret", "token", "aes", "rsa", "base64", "decrypt", "encrypt", "password", "login"]):
                        useful.append(line)
                lines.append("--- " + os.path.basename(item) + " ---")
                lines.extend(useful[:1500])
    else:
        lines.append("Falha ao extrair APK: " + output[-3000:])
    lines.append("")

    # Análise IA sobre o material encontrado, sem inventar dados.
    contexto="\n".join(lines)[-50000:]
    prompt=(
        "Analise tecnicamente este APK autorizado. Use somente os dados abaixo. "
        "Identifique aplicativo, permissões, servidores/domínios/URLs, protocolos, "
        "configurações, possíveis chaves/segredos encontrados, mecanismos de "
        "criptografia/ofuscação e referências a decrypt/descriptografia. "
        "Separe claramente fatos de hipóteses e não invente valores.\n\n" + contexto
    )
    try:
        ia=ask_openai(prompt)
    except Exception as e:
        ia="IA indisponível: " + str(e)

    lines.append("=== ANÁLISE IA ===")
    lines.append(ia)

    Path(report).write_text("\n".join(lines), encoding="utf-8", errors="ignore")
    sent=send_document(chat_id, report, "📊 ANÁLISE AUTOMÁTICA — APK")

    # Também envia um arquivo enxuto com strings/DEX quando disponível.
    dex_report=os.path.join(RESULTS, "strings_%s.txt" % chat_id)
    if dex_files:
        with open(dex_report,"w",encoding="utf-8",errors="ignore") as f:
            for item in dex_files:
                f.write("\n===== %s =====\n" % os.path.basename(item))
                scode, strings=run(["strings", item],180)
                if scode==0:
                    f.write(strings)
        send_document(chat_id, dex_report, "🔍 DEX / STRINGS — extração automática")

    if sent:
        return "✅ <b>APK processado automaticamente.</b>\n\n📊 Relatório enviado com identificação, manifest, URLs/servidores, configurações, referências de chaves/cripto e DEX/strings."
    return "⚠️ O APK foi processado, mas não consegui enviar o relatório."


def auto_process(chat_id, path):
    """Escolhe automaticamente o processador pelo tipo/conteúdo."""
    name=os.path.basename(path).lower()

    if name.endswith('.apk'):
        return auto_apk(chat_id, path)
    if name.endswith('.ehi'):
        return action_ehi(chat_id, path)
    if name.endswith('.log'):
        return action_b(chat_id, path)
    if name == 'user_id.txt':
        return action_dec(chat_id, path)

    # TXT/JSON: tenta reconhecer formatos conhecidos sem exigir botão.
    try:
        raw=Path(path).read_text(encoding='utf-8',errors='ignore').strip()
        low=raw.lower()
    except Exception:
        raw=''; low=''

    if 'config_openvpn' in low or 'config_v2ray' in low or re.search(r'\d{15,20}\.log', name):
        return action_b(chat_id, path)
    if raw.startswith('TSH1') or 'TSH1' in raw[:100]:
        return action_revh(chat_id, path)
    if name.endswith('.json') and 'user_id' in low:
        return action_dec(chat_id, path)

    # Último recurso: pesquisa o arquivo localmente e devolve um relatório, sem botões.
    out=os.path.join(RESULTS,"auto_%s.txt" % chat_id)
    Path(out).write_text(raw if raw else "Arquivo binário/sem texto legível.",encoding='utf-8',errors='ignore')
    send_document(chat_id,out,"📄 ANÁLISE AUTOMÁTICA")
    return "ℹ️ Arquivo recebido e analisado automaticamente; o formato não correspondeu a um decrypter específico."


def process_update(update):
    message=update.get("message")
    if not message:
        return

    chat_id=message["chat"]["id"]

    if message.get("text")=="/start":
        send(chat_id,
             "⚡ <b>TECH NET APK MANAGER</b>\n\n"
             "Envie qualquer arquivo autorizado.\n"
             "O bot identifica o formato e processa automaticamente.")
        return

    document=message.get("document")
    if document:
        filename=document.get("file_name","arquivo.bin")
        send(chat_id,"📥 <b>Arquivo recebido. Baixando e identificando...</b>")
        path=download_file(chat_id,document["file_id"],filename,os.path.splitext(filename)[1].lower())
        if not path:
            send(chat_id,"❌ Não consegui baixar o arquivo. A API padrão do Telegram pode limitar arquivos grandes.")
            return
        size=os.path.getsize(path)/1024/1024
        send(chat_id,"🔎 <b>Formato identificado.</b>\n\n📄 <code>%s</code>\n💾 %.2f MB\n\n⚙️ Processando automaticamente..." % (html.escape(filename),size))
        threading.Thread(target=lambda: send(chat_id, auto_process(chat_id,path)), daemon=True).start()
        return

    # Fotos/áudio/outros anexos sem nome não são decrypter de arquivo.
    if message.get("text"):
        send(chat_id,"📥 Envie o arquivo que deseja analisar. Nenhum botão é necessário.")


# ============================================================
# MAIN
# ============================================================

def main():
    print(
        "TECH NET APK MANAGER BOT iniciado.",
        flush=True
    )

    try:
        me = api("getMe")

        if not me.get("ok"):
            raise SystemExit(
                "Token inválido ou BOT inacessível."
            )

        print(
            "BOT conectado:",
            me["result"].get("username", ""),
            flush=True
        )

    except Exception as e:
        raise SystemExit(
            "Falha ao conectar no Telegram: " + str(e)
        )

    offset = 0

    while True:
        try:
            result = api(
                "getUpdates",
                {
                    "offset": offset,
                    "timeout": 50,
                    "allowed_updates": json.dumps(
                        ["message"]
                    )
                }
            )

            for update in result.get("result", []):
                offset = update["update_id"] + 1

                try:
                    process_update(update)
                except Exception as e:
                    print(
                        "UPDATE:",
                        repr(e),
                        flush=True
                    )

        except KeyboardInterrupt:
            print("BOT encerrado.")
            break

        except Exception as e:
            print(
                "CONEXÃO:",
                repr(e),
                flush=True
            )
            time.sleep(5)


# ============================================================
# START
# ============================================================

if __name__ == "__main__":
    main()
