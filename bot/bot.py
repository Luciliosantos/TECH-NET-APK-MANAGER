#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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
from pathlib import Path

BASE = "/root/apk-manager"
BOT_DIR = os.path.join(BASE, "bot")
CONFIG = os.path.join(BOT_DIR, "config.env")
WORK = os.path.join(BASE, "work")
RESULTS = os.path.join(BASE, "results")
STATE_FILE = os.path.join(WORK, "decrypt_state.json")

os.makedirs(WORK, exist_ok=True)
os.makedirs(RESULTS, exist_ok=True)

# ============================================================
# CONFIG
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
# TELEGRAM
# ============================================================

def api(method, data=None):
    data = data or {}
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        API + "/" + method,
        data=body,
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode())


def telegram_text(text):
    text = str(text)
    if len(text) <= 3900:
        return text, "HTML"
    return (
        text[:3800]
        + "\n\n⚠️ Resultado muito grande. "
          "O arquivo completo foi enviado em anexo.",
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
            "SEND ERROR:",
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
    except Exception as e:
        print("EDIT ERROR:", e, flush=True)
        return None


def answer(callback_id):
    try:
        api("answerCallbackQuery", {
            "callback_query_id": callback_id
        })
    except Exception as e:
        print("CALLBACK:", e, flush=True)


def send_document(chat_id, path, caption=""):
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
            timeout=600
        )

        print("SEND DOCUMENT:", result.stdout[-1000:], flush=True)

        try:
            return bool(json.loads(result.stdout).get("ok"))
        except Exception:
            return result.returncode == 0

    except Exception as e:
        print("SEND DOCUMENT ERROR:", e, flush=True)
        return False


# ============================================================
# MENUS
# ============================================================

def keyboard():
    return {
        "inline_keyboard": [
            [{"text": "📤 ENVIAR ARQUIVO", "callback_data": "upload"}],
            [
                {"text": "🔓 EHI", "callback_data": "ehi_processar"},
                {"text": "🧩 LOG / BASE64", "callback_data": "log_processar"}
            ],
            [
                {"text": "🌐 DTUNNEL", "callback_data": "dtunnel_processar"},
                {"text": "🛰️ REVHUNTER", "callback_data": "revh_processar"}
            ],
            [{"text": "🧹 LIMPAR", "callback_data": "limpar"}]
        ]
    }


def ehi_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🔓 PROCESSAR EHI", "callback_data": "ehi_processar"}],
            [{"text": "🧹 LIMPAR", "callback_data": "limpar"}],
            [{"text": "⬅️ MENU", "callback_data": "menu"}]
        ]
    }


def log_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🧩 DECODIFICAR LOG", "callback_data": "log_processar"}],
            [{"text": "🧹 LIMPAR", "callback_data": "limpar"}],
            [{"text": "⬅️ MENU", "callback_data": "menu"}]
        ]
    }


def dtunnel_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🌐 PROCESSAR DTUNNEL", "callback_data": "dtunnel_processar"}],
            [{"text": "🧹 LIMPAR", "callback_data": "limpar"}],
            [{"text": "⬅️ MENU", "callback_data": "menu"}]
        ]
    }


# ============================================================
# ESTADO
# ============================================================

def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    tmp = STATE_FILE + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False)
        os.replace(tmp, STATE_FILE)
    except Exception as e:
        print("STATE:", e, flush=True)


def user_dir(chat_id):
    path = os.path.join(WORK, str(chat_id))
    os.makedirs(path, exist_ok=True)
    return path


def get_state(chat_id):
    return load_state().get(str(chat_id), {})


def set_state(chat_id, **values):
    state = load_state()
    current = state.get(str(chat_id), {})
    current.update(values)
    state[str(chat_id)] = current
    save_state(state)


def get_path(chat_id, key):
    path = get_state(chat_id).get(key)
    if path and os.path.isfile(path):
        return path
    return None


# ============================================================
# DOWNLOAD
# ============================================================

def download_file(chat_id, file_id, filename):
    try:
        info = api("getFile", {"file_id": file_id})
        if not info.get("ok"):
            print("GETFILE:", info, flush=True)
            return None

        remote = info["result"]["file_path"]
        name = os.path.basename(filename)
        path = os.path.join(user_dir(chat_id), name)

        urllib.request.urlretrieve(
            FILE_API + "/" + remote,
            path
        )

        if not os.path.isfile(path) or os.path.getsize(path) < 1:
            return None

        return path

    except Exception as e:
        print("DOWNLOAD:", e, flush=True)
        return None


# ============================================================
# PROCESSAMENTO EHI
# ============================================================

def action_ehi(chat_id, ehi_path):
    if not ehi_path:
        return "⚠️ <b>NENHUM EHI CARREGADO.</b>\n\nEnvie um arquivo <code>.ehi</code>."

    try:
        import sys
        if BOT_DIR not in sys.path:
            sys.path.insert(0, BOT_DIR)
        from ehi import InterrogadorEHI
    except Exception as e:
        return (
            "❌ <b>Processador EHI não disponível.</b>\n\n"
            "<code>" + html.escape(str(e)) + "</code>\n\n"
            "Instale as dependências do EHI no VPS."
        )

    try:
        with open(ehi_path, "rb") as f:
            dados = f.read()

        resultado, estatisticas = InterrogadorEHI.executar_com_relatorio(dados)

        if not resultado:
            motivo = estatisticas.get("motivo_falha", "motivo desconhecido")
            return (
                "❌ <b>Não foi possível processar o EHI.</b>\n\n"
                "Motivo:\n<code>" + html.escape(str(motivo)) + "</code>"
            )

        result_file = os.path.join(
            RESULTS,
            "ehi_{}_resultado.txt".format(chat_id)
        )

        with open(result_file, "w", encoding="utf-8") as f:
            f.write(resultado)

        sent = send_document(
            chat_id,
            result_file,
            "📄 EHI PROCESSADO"
        )

        if not sent:
            return "❌ Processado, mas não consegui enviar o resultado."

        modo = estatisticas.get("modo") or "não informado"

        return (
            "✅ <b>EHI PROCESSADO.</b>\n\n"
            "📄 Resultado enviado.\n"
            "⚙️ Modo: <code>" + html.escape(str(modo)) + "</code>"
        )

    except Exception as e:
        print("EHI ERROR:", repr(e), flush=True)
        return (
            "❌ <b>Erro no EHI.</b>\n\n"
            "<code>" + html.escape(str(e)) + "</code>"
        )


# ============================================================
# LOG / BASE64 — USA O b.py ENVIADO
# ============================================================

def action_log(chat_id, log_path):
    if not log_path:
        return (
            "⚠️ <b>NENHUM LOG CARREGADO.</b>\n\n"
            "Envie o arquivo <code>.log</code> primeiro."
        )

    work = user_dir(chat_id)
    module_copy = os.path.join(work, "b.py")
    input_copy = os.path.join(work, os.path.basename(log_path))

    try:
        shutil.copy2(os.path.join(BOT_DIR, "b.py"), module_copy)
        shutil.copy2(log_path, input_copy)

        # O b.py procura arquivos numéricos *.log no diretório dele.
        if not Path(input_copy).name[:1].isdigit():
            numeric_name = "00000000000000001.log"
            numeric_path = os.path.join(work, numeric_name)
            shutil.copy2(log_path, numeric_path)
            input_copy = numeric_path

        code, output = run_command(
            ["python3", module_copy],
            cwd=work,
            timeout=600
        )

        zfile = os.path.join(work, "z.txt")
        yfile = os.path.join(work, "y.txt")

        if code != 0:
            return (
                "❌ <b>Falha no decodificador LOG.</b>\n\n"
                "<code>" + html.escape(output[-3500:]) + "</code>"
            )

        if not os.path.isfile(zfile):
            return (
                "⚠️ O decodificador terminou, mas não gerou <code>z.txt</code>.\n\n"
                "<code>" + html.escape(output[-2500:]) + "</code>"
            )

        sent = send_document(
            chat_id,
            zfile,
            "🧩 LOG DECODIFICADO — z.txt"
        )

        # O intermediário é útil para diagnóstico, mas não é enviado
        # automaticamente para não poluir o chat.
        if not sent:
            return "❌ z.txt foi gerado, mas não consegui enviar o arquivo."

        return (
            "✅ <b>LOG PROCESSADO.</b>\n\n"
            "📄 <code>z.txt</code> enviado com o resultado final."
        )

    except Exception as e:
        print("LOG ERROR:", repr(e), flush=True)
        return (
            "❌ <b>Erro no processamento do LOG.</b>\n\n"
            "<code>" + html.escape(str(e)) + "</code>"
        )


# ============================================================
# DTUNNEL — USA O dec.py ENVIADO
# ============================================================

def action_dtunnel(chat_id, token=None):
    work = user_dir(chat_id)
    script = os.path.join(BOT_DIR, "dec.py")

    if not os.path.isfile(script):
        return "❌ <code>dec.py</code> não está instalado em <code>/root/apk-manager/bot/</code>."

    token = (token or get_state(chat_id).get("dtunnel_token") or "").strip()

    if not token:
        return (
            "⚠️ <b>NENHUM TOKEN DTUNNEL.</b>\n\n"
            "Envie o token em uma mensagem de texto e depois clique em "
            "<b>🌐 PROCESSAR DTUNNEL</b>."
        )

    try:
        # dec.py trabalha com user_id.txt e usa o diretório atual
        # para gerar output/, logs/ e o ZIP.
        token_file = os.path.join(work, "user_id.txt")
        with open(token_file, "w", encoding="utf-8") as f:
            f.write(token + "\n")

        code, output = run_command(
            ["python3", script],
            cwd=work,
            timeout=900
        )

        # O script pode retornar erro no stdout mesmo com código 0.
        zip_files = sorted(
            Path(work).glob("*.zip"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        config_file = os.path.join(work, "output", "config.json")
        layout_file = os.path.join(work, "output", "layout.json")
        webview_file = os.path.join(work, "output", "APP_LAYOUT_WEBVIEW.html")

        sent_any = False

        for path, caption in [
            (config_file, "🌐 DTUNNEL — config.json"),
            (layout_file, "🌐 DTUNNEL — layout.json"),
            (webview_file, "🌐 DTUNNEL — APP_LAYOUT_WEBVIEW.html"),
        ]:
            if os.path.isfile(path):
                if send_document(chat_id, path, caption):
                    sent_any = True

        if zip_files:
            if send_document(chat_id, str(zip_files[0]), "📦 DTUNNEL — pacote completo"):
                sent_any = True

        if sent_any:
            return (
                "✅ <b>DTUNNEL PROCESSADO.</b>\n\n"
                "Os resultados encontrados foram enviados como arquivos."
            )

        return (
            "⚠️ <b>DTUNNEL terminou sem resultado decodificado.</b>\n\n"
            "<code>" + html.escape(output[-3500:]) + "</code>"
        )

    except Exception as e:
        print("DTUNNEL ERROR:", repr(e), flush=True)
        return (
            "❌ <b>Erro no DTUNNEL.</b>\n\n"
            "<code>" + html.escape(str(e)) + "</code>"
        )


# ============================================================
# REVHUNTER — USA O revh.py ENVIADO
# ============================================================

def action_revh(chat_id):
    work = user_dir(chat_id)
    script = os.path.join(BOT_DIR, "revh.py")

    if not os.path.isfile(script):
        return "❌ <code>revh.py</code> não está instalado em <code>/root/apk-manager/bot/</code>."

    try:
        code, output = run_command(
            ["python3", script],
            cwd=work,
            timeout=600
        )

        dec_file = os.path.join(work, "dec.txt")
        enc_file = os.path.join(work, "enc.txt")

        if code != 0:
            return (
                "❌ <b>REVHUNTER falhou.</b>\n\n"
                "<code>" + html.escape(output[-3500:]) + "</code>"
            )

        if os.path.isfile(dec_file):
            if send_document(
                chat_id,
                dec_file,
                "🛰️ REVHUNTER — resultado decodificado"
            ):
                return (
                    "✅ <b>REVHUNTER PROCESSADO.</b>\n\n"
                    "📄 Resultado enviado."
                )

        return (
            "⚠️ REVHUNTER terminou, mas não gerou <code>dec.txt</code>.\n\n"
            "<code>" + html.escape(output[-3000:]) + "</code>"
        )

    except Exception as e:
        print("REVHUNTER ERROR:", repr(e), flush=True)
        return (
            "❌ <b>Erro no REVHUNTER.</b>\n\n"
            "<code>" + html.escape(str(e)) + "</code>"
        )


# ============================================================
# COMANDOS
# ============================================================

def run_command(cmd, cwd=None, timeout=600):
    try:
        r = subprocess.run(
            cmd,
            cwd=cwd,
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


def processing_message(chat_id, action):
    names = {
        "ehi_processar": "🔓 PROCESSANDO EHI",
        "log_processar": "🧩 DECODIFICANDO LOG",
        "dtunnel_processar": "🌐 PROCESSANDO DTUNNEL",
        "revh_processar": "🛰️ PROCESSANDO REVHUNTER",
    }

    title = names.get(action, "⚙️ PROCESSANDO")

    return send(
        chat_id,
        "<b>" + title + "...</b>\n\n"
        "🔎 Executando o decodificador\n"
        "⚙️ Processando os dados\n\n"
        "⏳ Aguarde..."
    )


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


def clear_user(chat_id):
    path = user_dir(chat_id)
    if os.path.isdir(path):
        shutil.rmtree(path)

    state = load_state()
    state.pop(str(chat_id), None)
    save_state(state)


# ============================================================
# EXECUÇÃO
# ============================================================

def execute(chat_id, action):
    if action == "menu":
        send(
            chat_id,
            "⚡ <b>TECH NET DECRYPT MANAGER</b>\n\n"
            "Escolha uma ferramenta ou envie o arquivo necessário.",
            keyboard()
        )
        return

    if action == "upload":
        send(
            chat_id,
            "📤 <b>ENVIE O ARQUIVO</b>\n\n"
            "• <code>.ehi</code> → EHI\n"
            "• <code>.log</code> → LOG / BASE64\n\n"
            "Para DTUNNEL, envie o token como texto.",
            keyboard()
        )
        return

    if action == "limpar":
        clear_user(chat_id)
        send(
            chat_id,
            "🧹 <b>LIMPO.</b>\n\n"
            "Pode enviar outro arquivo ou token.",
            keyboard()
        )
        return

    processing = processing_message(chat_id, action)
    processing_id = None

    if isinstance(processing, dict):
        processing_id = (
            processing.get("result", {})
            .get("message_id")
        )

    try:
        if action == "ehi_processar":
            text = action_ehi(
                chat_id,
                get_path(chat_id, "ehi")
            )
            menu = ehi_keyboard()

        elif action == "log_processar":
            text = action_log(
                chat_id,
                get_path(chat_id, "log")
            )
            menu = log_keyboard()

        elif action == "dtunnel_processar":
            text = action_dtunnel(chat_id)
            menu = dtunnel_keyboard()

        elif action == "revh_processar":
            text = action_revh(chat_id)
            menu = keyboard()

        else:
            text = "❌ Opção desconhecida."
            menu = keyboard()

    except Exception as e:
        print("EXECUTE ERROR:", repr(e), flush=True)
        text = (
            "❌ <b>ERRO AO PROCESSAR.</b>\n\n"
            "<code>" + html.escape(str(e))[:3500] + "</code>"
        )
        menu = keyboard()

    finish_processing(
        chat_id,
        processing_id,
        text,
        menu
    )


# ============================================================
# UPDATES
# ============================================================

def process_update(update):
    callback = update.get("callback_query")

    if callback:
        answer(callback["id"])

        message = callback.get("message")
        if not message:
            return

        chat_id = message["chat"]["id"]
        action = callback.get("data", "")

        threading.Thread(
            target=execute,
            args=(chat_id, action),
            daemon=True
        ).start()
        return

    message = update.get("message")
    if not message:
        return

    chat_id = message["chat"]["id"]

    if message.get("text") == "/start":
        send(
            chat_id,
            "⚡ <b>TECH NET DECRYPT MANAGER</b>\n\n"
            "Envie um <code>.ehi</code> ou <code>.log</code>.\n"
            "Para DTUNNEL, envie o token como texto.\n\n"
            "Use somente arquivos/dados que você tem autorização para processar.",
            keyboard()
        )
        return

    document = message.get("document")

    if document:
        filename = document.get("file_name", "")
        lower = filename.lower()

        if not (lower.endswith(".ehi") or lower.endswith(".log")):
            send(
                chat_id,
                "❌ Tipo de arquivo não suportado.\n\n"
                "Envie <code>.ehi</code> ou <code>.log</code>.",
                keyboard()
            )
            return

        send(
            chat_id,
            "📥 <b>BAIXANDO...</b>\n\nAguarde."
        )

        path = download_file(
            chat_id,
            document["file_id"],
            filename
        )

        if not path:
            send(chat_id, "❌ Não consegui baixar o arquivo.", keyboard())
            return

        size = os.path.getsize(path) / 1024 / 1024

        if lower.endswith(".ehi"):
            set_state(chat_id, ehi=path)
            send(
                chat_id,
                "✅ <b>EHI RECEBIDO!</b>\n\n"
                "📄 <code>" + html.escape(os.path.basename(path)) + "</code>\n"
                "💾 {:.2f} MB".format(size),
                ehi_keyboard()
            )
        else:
            set_state(chat_id, log=path)
            send(
                chat_id,
                "✅ <b>LOG RECEBIDO!</b>\n\n"
                "📄 <code>" + html.escape(os.path.basename(path)) + "</code>\n"
                "💾 {:.2f} MB".format(size),
                log_keyboard()
            )

        return

    text = message.get("text", "").strip()

    if text:
        # Qualquer texto não-comando é tratado como token DTUNNEL.
        set_state(chat_id, dtunnel_token=text)

        send(
            chat_id,
            "🔑 <b>TOKEN RECEBIDO.</b>\n\n"
            "Clique em <b>🌐 DTUNNEL</b> para iniciar o processamento.",
            dtunnel_keyboard()
        )


# ============================================================
# MAIN
# ============================================================

def main():
    print(
        "TECH NET DECRYPT MANAGER BOT iniciado.",
        flush=True
    )

    try:
        me = api("getMe")
        if not me.get("ok"):
            raise SystemExit("Token inválido ou BOT inacessível.")

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
                        ["message", "callback_query"]
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
            print("CONEXÃO:", repr(e), flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
