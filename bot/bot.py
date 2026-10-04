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
import importlib.util
import re
from pathlib import Path

BASE = "/root/apk-manager"
BOT_DIR = os.path.join(BASE, "bot")
CONFIG = os.path.join(BOT_DIR, "config.env")
WORK = os.path.join(BASE, "work")
RESULTS = os.path.join(BASE, "results")
STATE_FILE = os.path.join(WORK, "decoder_state.json")

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


TOKEN = load_config().get("BOT_TOKEN", "")

if not TOKEN:
    raise SystemExit("BOT_TOKEN não configurado em bot/config.env")

API = "https://api.telegram.org/bot" + TOKEN
FILE_API = "https://api.telegram.org/file/bot" + TOKEN


# ============================================================
# TELEGRAM API
# ============================================================

def api(method, data=None):
    body = urllib.parse.urlencode(data or {}).encode()

    req = urllib.request.Request(
        API + "/" + method,
        data=body,
        method="POST"
    )

    with urllib.request.urlopen(req, timeout=120) as response:
        return json.loads(response.read().decode())


def send(chat_id, text, keyboard=None):
    text = str(text)

    if len(text) > 3900:
        text = (
            text[:3800]
            + "\n\n⚠️ Resultado muito grande. "
              "O arquivo completo foi enviado."
        )

    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if keyboard:
        data["reply_markup"] = json.dumps(
            keyboard,
            ensure_ascii=False
        )

    try:
        return api("sendMessage", data)
    except Exception as e:
        print("SEND:", e, flush=True)
        return None


def answer(callback_id):
    try:
        api(
            "answerCallbackQuery",
            {"callback_query_id": callback_id}
        )
    except Exception as e:
        print("CALLBACK:", e, flush=True)


def edit_message(chat_id, message_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": str(text),
        "parse_mode": "HTML"
    }

    if keyboard:
        data["reply_markup"] = json.dumps(
            keyboard,
            ensure_ascii=False
        )

    try:
        return api("editMessageText", data)
    except Exception as e:
        print("EDIT:", e, flush=True)
        return None


def send_document(chat_id, path, caption=""):
    if not os.path.isfile(path):
        return False

    try:
        result = subprocess.run(
            [
                "curl",
                "-sS",
                "-X",
                "POST",
                API + "/sendDocument",
                "-F",
                "chat_id=" + str(chat_id),
                "-F",
                "document=@" + path,
                "-F",
                "caption=" + caption
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=300
        )

        try:
            response = json.loads(result.stdout)
            return bool(response.get("ok"))
        except Exception:
            return result.returncode == 0

    except Exception as e:
        print("SEND DOCUMENT:", e, flush=True)
        return False


# ============================================================
# ESTADO / ARQUIVOS
# ============================================================

def user_dir(chat_id):
    path = os.path.join(WORK, str(chat_id))
    os.makedirs(path, exist_ok=True)
    return path


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    tmp = STATE_FILE + ".tmp"

    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)

    os.replace(tmp, STATE_FILE)


def set_file(chat_id, path):
    state = load_state()
    state[str(chat_id)] = path
    save_state(state)


def get_file(chat_id):
    path = load_state().get(str(chat_id))

    if path and os.path.isfile(path):
        return path

    return None


def clear_user(chat_id):
    path = user_dir(chat_id)

    if os.path.isdir(path):
        shutil.rmtree(path)

    state = load_state()
    state.pop(str(chat_id), None)
    save_state(state)


# ============================================================
# DOWNLOAD TELEGRAM
# ============================================================

def download_file(chat_id, file_id, filename):
    try:
        info = api(
            "getFile",
            {"file_id": file_id}
        )

        if not info.get("ok"):
            print("GETFILE:", info, flush=True)
            return None

        remote = info["result"]["file_path"]

        name = os.path.basename(filename) or "arquivo.bin"
        path = os.path.join(user_dir(chat_id), name)

        urllib.request.urlretrieve(
            FILE_API + "/" + remote,
            path
        )

        if (
            os.path.isfile(path)
            and os.path.getsize(path) > 0
        ):
            set_file(chat_id, path)
            return path

    except Exception as e:
        print("DOWNLOAD:", e, flush=True)

    return None


# ============================================================
# MENUS
# ============================================================

def main_menu():
    return {
        "inline_keyboard": [
            [
                {
                    "text": "🔓 EHI",
                    "callback_data": "ehi"
                }
            ],
            [
                {
                    "text": "🔐 B / BASE64",
                    "callback_data": "b"
                },
                {
                    "text": "🔐 DTUNNEL",
                    "callback_data": "dec"
                }
            ],
            [
                {
                    "text": "🕵️ REVHUNTER",
                    "callback_data": "revh"
                }
            ],
            [
                {
                    "text": "🗑️ LIMPAR",
                    "callback_data": "limpar"
                }
            ]
        ]
    }


def ehi_menu():
    return {
        "inline_keyboard": [
            [
                {
                    "text": "🔓 PROCESSAR EHI",
                    "callback_data": "ehi_processar"
                }
            ],
            [
                {
                    "text": "🗑️ LIMPAR",
                    "callback_data": "limpar"
                }
            ]
        ]
    }


def decoder_menu():
    return {
        "inline_keyboard": [
            [
                {
                    "text": "🔐 B / BASE64",
                    "callback_data": "b"
                },
                {
                    "text": "🔐 DTUNNEL",
                    "callback_data": "dec"
                }
            ],
            [
                {
                    "text": "🕵️ REVHUNTER",
                    "callback_data": "revh"
                }
            ],
            [
                {
                    "text": "🗑️ LIMPAR",
                    "callback_data": "limpar"
                }
            ]
        ]
    }


# ============================================================
# EXECUÇÃO DOS DECRYPTERS
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


# ============================================================
# EHI
# ============================================================

def action_ehi(chat_id, path):
    try:
        from ehi import InterrogadorEHI

    except Exception as e:
        return (
            "❌ <b>EHI indisponível.</b>\n\n"
            "<code>"
            + html.escape(str(e))
            + "</code>"
        )

    try:
        dados = Path(path).read_bytes()

        resultado, estatisticas = (
            InterrogadorEHI.executar_com_relatorio(
                dados
            )
        )

        if not resultado:
            motivo = estatisticas.get(
                "motivo_falha",
                "motivo desconhecido"
            )

            return (
                "❌ <b>EHI não processado.</b>\n\n"
                "<code>"
                + html.escape(str(motivo))
                + "</code>"
            )

        output = os.path.join(
            RESULTS,
            "ehi_"
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
            "📄 EHI PROCESSADO"
        ):
            return (
                "❌ O EHI foi processado, "
                "mas não consegui enviar o resultado."
            )

        modo = estatisticas.get(
            "modo",
            "não informado"
        )

        return (
            "✅ <b>EHI PROCESSADO</b>\n\n"
            "📄 Resultado enviado.\n"
            "⚙️ Modo: <code>"
            + html.escape(str(modo))
            + "</code>"
        )

    except Exception as e:
        return (
            "❌ <b>Erro no EHI:</b>\n\n"
            "<code>"
            + html.escape(str(e))
            + "</code>"
        )


# ============================================================
# B.PY — LOG / BASE64
# ============================================================

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


# ============================================================
# DEC.PY — DTUNNEL
# ============================================================

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


# ============================================================
# REVH.PY — PROCESSAMENTO LOCAL
# ============================================================

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


# ============================================================
# BOTÕES
# ============================================================

def execute(chat_id, action):
    if action == "limpar":
        clear_user(chat_id)

        send(
            chat_id,
            "🗑️ <b>ARQUIVOS LIMPOS.</b>\n\n"
            "Envie outro arquivo.",
            main_menu()
        )
        return

    path = get_file(chat_id)

    if action == "ehi":
        if (
            path
            and path.lower().endswith(".ehi")
        ):
            send(
                chat_id,
                "📄 <b>EHI carregado.</b>",
                ehi_menu()
            )
        else:
            send(
                chat_id,
                "📥 Envie um arquivo <b>.ehi</b>.",
                main_menu()
            )
        return

    if action in {
        "b",
        "dec",
        "revh",
        "ehi_processar"
    } and not path:
        send(
            chat_id,
            "📥 Primeiro envie o arquivo "
            "que será processado.",
            main_menu()
        )
        return

    processing = send(
        chat_id,
        "⚙️ <b>PROCESSANDO...</b>\n\n"
        "⏳ Aguarde."
    )

    processing_id = None

    if isinstance(processing, dict):
        processing_id = (
            processing
            .get("result", {})
            .get("message_id")
        )

    try:
        if action == "ehi_processar":
            result = action_ehi(
                chat_id,
                path
            )
            menu = ehi_menu()

        elif action == "b":
            result = action_b(
                chat_id,
                path
            )
            menu = decoder_menu()

        elif action == "dec":
            result = action_dec(
                chat_id,
                path
            )
            menu = decoder_menu()

        elif action == "revh":
            result = action_revh(
                chat_id,
                path
            )
            menu = decoder_menu()

        else:
            result = "❌ Opção desconhecida."
            menu = main_menu()

    except Exception as e:
        result = (
            "❌ <b>Erro:</b>\n\n"
            "<code>"
            + html.escape(str(e))
            + "</code>"
        )
        menu = main_menu()

    if processing_id:
        edited = edit_message(
            chat_id,
            processing_id,
            result,
            menu
        )

        if not edited:
            send(
                chat_id,
                result,
                menu
            )
    else:
        send(
            chat_id,
            result,
            menu
        )


# ============================================================
# UPDATES
# ============================================================

def process_update(update):
    callback = update.get(
        "callback_query"
    )

    if callback:
        answer(callback["id"])

        message = callback.get("message")

        if not message:
            return

        chat_id = message["chat"]["id"]
        action = callback.get(
            "data",
            ""
        )

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
            "⚡ <b>TECH NET APK MANAGER</b>\n\n"
            "🔓 EHI\n"
            "🔐 B / BASE64\n"
            "🔐 DTUNNEL\n"
            "🕵️ REVHUNTER\n\n"
            "Envie o arquivo correspondente "
            "e escolha o decrypter.\n\n"
            "⚠️ Use somente com arquivos e "
            "aplicativos que você tem autorização "
            "para analisar.",
            main_menu()
        )
        return

    document = message.get("document")

    if document:
        filename = document.get(
            "file_name",
            "arquivo"
        )

        lower = filename.lower()

        allowed = lower.endswith(
            (
                ".ehi",
                ".log",
                ".txt",
                ".json"
            )
        )

        if not allowed:
            send(
                chat_id,
                "❌ Formato não reconhecido.\n\n"
                "Envie <code>.ehi</code>, "
                "<code>.log</code>, "
                "<code>.txt</code> ou "
                "<code>.json</code>.",
                main_menu()
            )
            return

        send(
            chat_id,
            "📥 <b>Baixando arquivo...</b>\n\n"
            "Aguarde."
        )

        path = download_file(
            chat_id,
            document["file_id"],
            filename
        )

        if not path:
            send(
                chat_id,
                "❌ Não consegui baixar o arquivo.",
                main_menu()
            )
            return

        size = (
            os.path.getsize(path)
            / 1024
            / 1024
        )

        if lower.endswith(".ehi"):
            send(
                chat_id,
                "✅ <b>EHI RECEBIDO</b>\n\n"
                "📄 <code>"
                + html.escape(
                    os.path.basename(path)
                )
                + "</code>\n"
                "💾 {:.2f} MB".format(size),
                ehi_menu()
            )
        else:
            send(
                chat_id,
                "✅ <b>ARQUIVO RECEBIDO</b>\n\n"
                "📄 <code>"
                + html.escape(
                    os.path.basename(path)
                )
                + "</code>\n"
                "💾 {:.2f} MB\n\n"
                "Escolha o decrypter.",
                decoder_menu()
            )

        return

    text = message.get(
        "text",
        ""
    ).strip()

    if text:
        send(
            chat_id,
            "Use /start ou envie um arquivo.",
            main_menu()
        )


# ============================================================
# MAIN
# ============================================================

def main():
    print(
        "TECH NET APK MANAGER — "
        "DECRYPTERS BOT iniciado.",
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
            me["result"].get(
                "username",
                ""
            ),
            flush=True
        )

    except Exception as e:
        raise SystemExit(
            "Falha ao conectar no Telegram: "
            + str(e)
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
                        [
                            "message",
                            "callback_query"
                        ]
                    )
                }
            )

            for update in result.get(
                "result",
                []
            ):
                offset = (
                    update["update_id"]
                    + 1
                )

                try:
                    process_update(
                        update
                    )
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


if __name__ == "__main__":
    main()
