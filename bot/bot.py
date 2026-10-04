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

BASE = "/root/apk-manager"
CONFIG = BASE + "/bot/config.env"
WORK = BASE + "/work"
RESULTS = BASE + "/results"
STATE_FILE = WORK + "/state.json"

os.makedirs(WORK, exist_ok=True)
os.makedirs(RESULTS, exist_ok=True)


def load_token():
    with open(CONFIG, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("BOT_TOKEN="):
                return line.strip().split("=", 1)[1]
    return ""


TOKEN = load_token()

if not TOKEN:
    raise SystemExit("BOT_TOKEN não configurado")

API = "https://api.telegram.org/bot" + TOKEN
FILE_API = "https://api.telegram.org/file/bot" + TOKEN


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


def send(chat_id, text, keyboard=None):
    # Telegram limita mensagens a 4096 caracteres
    if len(text) > 3900:
        text = text[:3800] + "\n\n⚠️ Resultado cortado. Use RELATÓRIO para obter o resultado completo."

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

    return api("sendMessage", data)



def edit_message(chat_id, message_id, text, keyboard=None):
    # Telegram limita mensagens a 4096 caracteres
    if len(text) > 3900:
        text = text[:3800] + (
            "\n\n⚠️ Resultado completo disponível em RELATÓRIO."
        )

    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
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
        print("EDIT MESSAGE ERROR:", e)
        return None


def answer(callback_id):
    try:
        api("answerCallbackQuery", {
            "callback_query_id": callback_id
        })
    except Exception:
        pass


def keyboard():
    return {
        "inline_keyboard": [
            [
                {"text": "📦 ENVIAR APK", "callback_data": "upload"}
            ],
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
            [
                {"text": "🗑️ LIMPAR", "callback_data": "limpar"}
            ]
        ]
    }


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)


def get_apk(chat_id):
    state = load_state()
    path = state.get(str(chat_id))

    if path and os.path.isfile(path):
        return path

    return None


def set_apk(chat_id, path):
    state = load_state()
    state[str(chat_id)] = path
    save_state(state)


def user_dir(chat_id):
    path = WORK + "/" + str(chat_id)
    os.makedirs(path, exist_ok=True)
    return path


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
    except Exception as e:
        return 1, str(e)


def download_apk(chat_id, file_id, filename):
    info = api("getFile", {"file_id": file_id})

    if not info.get("ok"):
        return None

    remote = info["result"]["file_path"]
    name = os.path.basename(filename)

    if not name.lower().endswith(".apk"):
        return None

    path = user_dir(chat_id) + "/" + name

    url = FILE_API + "/" + remote

    try:
        urllib.request.urlretrieve(url, path)

        if not os.path.isfile(path):
            return None

        if os.path.getsize(path) < 1000:
            return None

        set_apk(chat_id, path)

        return path

    except Exception as e:
        print("DOWNLOAD:", e)
        return None


def decompile(chat_id, apk):
    out = user_dir(chat_id) + "/decompiled"

    if os.path.isdir(out):
        shutil.rmtree(out)

    code, result = run([
        "apktool",
        "d",
        "-f",
        apk,
        "-o",
        out
    ])

    return code, result, out


def ensure_decompiled(chat_id, apk):
    out = user_dir(chat_id) + "/decompiled"

    if os.path.isfile(out + "/AndroidManifest.xml"):
        return True, out, ""

    code, result, out = decompile(chat_id, apk)

    return code == 0, out, result


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

                        if any(w.lower() in low for w in words):
                            rel = os.path.relpath(
                                path,
                                directory
                            )

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



def ask_openai(prompt):
    """Envia uma análise resumida para a OpenAI e retorna a resposta."""
    import urllib.request
    import urllib.error
    import json

    cfg = {}
    try:
        with open(CONFIG, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    cfg[k] = v.strip()
    except Exception as e:
        return "❌ Não consegui carregar a configuração da IA: " + str(e)

    key = cfg.get("OPENAI_API_KEY", "")
    model = cfg.get("OPENAI_MODEL", "gpt-6-luna")

    if not key:
        return "❌ OPENAI_API_KEY não configurada no servidor."

    system = (
        "Você é a IA do TECH NET APK MANAGER. "
        "Analise resultados técnicos de APKs de forma objetiva e clara. "
        "Explique o que foi encontrado, indique arquivos, URLs, domínios, "
        "configurações e possíveis riscos quando existirem. "
        "Não invente informações que não estejam nos resultados. "
        "A análise deve ser feita somente para aplicativos que o usuário "
        "tem autorização para analisar."
    )

    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": system
            },
            {
                "role": "user",
                "content": prompt
            }
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
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode())

        result = data.get("output_text")

        if not result:
            textos = []

            for item in data.get("output", []):
                if item.get("type") != "message":
                    continue

                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        texto = content.get("text", "")
                        if texto:
                            textos.append(texto)

            result = "\n\n".join(textos)
            return result.strip()

        return "❌ A IA respondeu, mas não retornou texto."

    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode()
        except Exception:
            detail = str(e)
        return "❌ Erro da API da IA: HTTP " + str(e.code) + "\n" + detail[:1000]

    except Exception as e:
        return "❌ Erro ao consultar a IA: " + str(e)

def action_analisar(chat_id, apk):
    code, output, directory = decompile(chat_id, apk)

    if code != 0:
        return "❌ <b>Falha ao descompilar.</b>\n\n<code>" + html.escape(output[-3000:]) + "</code>"

    return (
        "✅ <b>ANÁLISE CONCLUÍDA</b>\n\n"
        "📦 APK descompilado\n"
        "📂 Arquivos extraídos\n"
        "📋 Manifest disponível\n"
        "🔍 Código disponível\n\n"
        "Agora você pode usar as outras ferramentas."
    )



def action_analisar_ia(chat_id, apk):
    """Descompila o APK, coleta informações básicas e pede uma análise à IA."""
    code, output, directory = decompile(chat_id, apk)

    if code != 0:
        return (
            "❌ <b>Falha ao descompilar.</b>\n\n"
            "<code>" + html.escape(output[-3000:]) + "</code>"
        )

    partes = []

    # Manifest
    mcode, manifest = run([
        "aapt",
        "dump",
        "badging",
        apk
    ], 120)

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
            "=== MANIFEST ===\n" +
            "\n".join(linhas[:150])
        )

    # Procura referências importantes nos arquivos extraídos
    palavras = [
        "http://",
        "https://",
        "server",
        "host",
        "proxy",
        "websocket",
        "xhttp",
        "vless",
        "vmess",
        "trojan",
        "ssh",
        "tls",
        "endpoint",
        "api",
        "token",
        "apikey",
        "secret",
        "encrypt",
        "decrypt",
        "aes",
        "rsa"
    ]

    try:
        encontrados = search(directory, palavras)
        partes.append(
            "=== REFERÊNCIAS ENCONTRADAS ===\n" +
            "\n".join(encontrados[:300])
        )
    except Exception as e:
        partes.append("=== ERRO NA BUSCA ===\n" + str(e))

    contexto = "\n\n".join(partes)

    # Limita o conteúdo enviado para a IA
    contexto = contexto[:30000]

    prompt = (
        "Analise tecnicamente os resultados abaixo referentes a um APK.\n\n"
        "Informe de forma organizada:\n"
        "1. Identificação do aplicativo\n"
        "2. Permissões relevantes\n"
        "3. Servidores, domínios, URLs ou endpoints encontrados\n"
        "4. Protocolos ou tecnologias identificadas\n"
        "5. Configurações importantes encontradas\n"
        "6. Possíveis mecanismos de criptografia/obfuscação encontrados\n"
        "7. Pontos que merecem investigação adicional\n"
        "8. Resumo final em linguagem simples\n\n"
        "Não invente dados. Se algo não estiver presente nos resultados, "
        "informe que não foi encontrado.\n\n"
        + contexto
    )

    ia = ask_openai(prompt)

    return (
        "🤖 <b>ANÁLISE IA — TECH NET APK MANAGER</b>\n\n"
        + ia
    )


def action_manifest(chat_id, apk):
    code, output = run([
        "aapt",
        "dump",
        "badging",
        apk
    ], 120)

    if code != 0:
        return "❌ Erro no Manifest."

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

    texto = "\n".join(linhas)

    return (
        "📋 <b>MANIFEST</b>\n\n"
        "<code>" +
        html.escape(texto[:7000]) +
        "</code>"
    )


def action_search(chat_id, apk, words, title):
    ok, directory, output = ensure_decompiled(
        chat_id,
        apk
    )

    if not ok:
        return "❌ Não foi possível descompilar o APK."

    found = search(directory, words)

    if not found:
        return "ℹ️ Nenhuma ocorrência encontrada."

    return (
        title +
        "\n\n<code>" +
        html.escape("\n".join(found)[:7000]) +
        "</code>"
    )


def action_dex(chat_id, apk):
    base = user_dir(chat_id) + "/dex"

    if os.path.isdir(base):
        shutil.rmtree(base)

    os.makedirs(base)

    code, output = run([
        "unzip",
        "-oq",
        apk,
        "-d",
        base
    ], 180)

    if code != 0:
        return "❌ Falha ao extrair o APK."

    dex = []

    for root, dirs, files in os.walk(base):
        for name in files:
            if name.endswith(".dex"):
                dex.append(
                    os.path.join(root, name)
                )

    if not dex:
        return "🔍 Nenhum DEX encontrado."

    result_file = RESULTS + "/dex_" + str(chat_id) + ".txt"

    with open(result_file, "w", encoding="utf-8") as f:
        for item in dex:
            code, strings = run(
                ["strings", item],
                120
            )

            f.write(
                "\n===== " +
                os.path.basename(item) +
                " =====\n"
            )

            f.write(strings)

    send_document(
        chat_id,
        result_file,
        "🔍 DEX / STRINGS"
    )

    return "✅ DEX analisado. O relatório foi enviado como arquivo."


def send_document(chat_id, path, caption):
    if not os.path.isfile(path):
        return

    subprocess.run([
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
    ], timeout=180)


def action_report(chat_id, apk):
    ok, directory, output = ensure_decompiled(
        chat_id,
        apk
    )

    result_file = RESULTS + "/relatorio_" + str(chat_id) + ".txt"

    with open(result_file, "w", encoding="utf-8") as f:

        f.write("TECH NET APK MANAGER\n")
        f.write("=" * 60 + "\n\n")

        f.write("APK: " + os.path.basename(apk) + "\n")
        f.write("TAMANHO: " + str(os.path.getsize(apk)) + "\n\n")

        code, badging = run([
            "aapt",
            "dump",
            "badging",
            apk
        ], 120)

        f.write("=== MANIFEST ===\n")
        f.write(badging)
        f.write("\n\n")

        if ok:
            words = [
                "http://",
                "https://",
                "ws://",
                "wss://",
                "vless://",
                "vmess://",
                "trojan://",
                "server",
                "host",
                "proxy",
                "websocket",
                "xhttp",
                "encrypt",
                "decrypt",
                "cipher",
                "aes",
                "rsa",
                "token",
                "apikey",
                "secret"
            ]

            f.write("=== REFERÊNCIAS ===\n")

            for item in search(directory, words):
                f.write(item + "\n")

    send_document(
        chat_id,
        result_file,
        "📊 RELATÓRIO COMPLETO"
    )

    return "✅ Relatório completo enviado."


def action_recompile(chat_id, apk):
    ok, directory, output = ensure_decompiled(
        chat_id,
        apk
    )

    if not ok:
        return "❌ APK não pôde ser preparado para recompilação."

    output_apk = RESULTS + "/recompilado_" + str(chat_id) + ".apk"

    if os.path.exists(output_apk):
        os.remove(output_apk)

    code, result = run([
        "apktool",
        "b",
        directory,
        "-o",
        output_apk
    ], 900)

    if code != 0:
        return (
            "❌ <b>Erro ao recompilar.</b>\n\n"
            "<code>" +
            html.escape(result[-4000:]) +
            "</code>"
        )

    send_document(
        chat_id,
        output_apk,
        "🔨 APK RECOMPILADO"
    )

    return "✅ APK recompilado e enviado."


def clear_user(chat_id):
    path = user_dir(chat_id)
    if os.path.isdir(path):
        shutil.rmtree(path)

    state = load_state()
    state.pop(str(chat_id), None)
    save_state(state)



def processing_message(chat_id, action):
    nomes = {
        "analisar": "🤖 IA ANALISANDO",
        "manifest": "📋 ANALISANDO MANIFEST",
        "config": "🔎 PROCURANDO CONFIGURAÇÕES",
        "servidores": "🌐 PROCURANDO SERVIDORES",
        "cripto": "🔐 ANALISANDO CRIPTOGRAFIA",
        "chaves": "🔑 PROCURANDO CHAVES",
        "dex": "🔍 ANALISANDO DEX / CÓDIGO",
        "relatorio": "📊 GERANDO RELATÓRIO",
        "recompilar": "🔨 RECOMPILANDO APK",
        "assinar": "✍️ ASSINANDO APK",
    }

    titulo = nomes.get(action, "⚙️ PROCESSANDO")

    return send(
        chat_id,
        "<b>" + titulo + "...</b>\n\n"
        "📦 Processando o APK\n"
        "🔎 Executando as ferramentas\n"
        "🧠 Preparando o resultado\n\n"
        "⏳ <i>Aguarde, o serviço está sendo executado...</i>"
    )

def execute(chat_id, action):

    if action == "upload":
        send(
            chat_id,
            "📦 <b>ENVIE O APK</b>\n\n"
            "Envie o arquivo .apk nesta conversa."
        )
        return

    if action == "limpar":
        clear_user(chat_id)

        send(
            chat_id,
            "🗑️ <b>APK REMOVIDO.</b>\n\n"
            "Pode enviar outro APK.",
            keyboard()
        )
        return

    # Mostra imediatamente que o serviço começou
    processing_id = None

    if action not in ("upload", "limpar"):
        processing = processing_message(chat_id, action)
        if isinstance(processing, dict):
            processing_id = processing.get("result", {}).get("message_id")

    apk = get_apk(chat_id)

    if not apk:
        send(
            chat_id,
            "⚠️ <b>NENHUM APK CARREGADO.</b>\n\n"
            "Envie o APK primeiro.",
            keyboard()
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
                "websocket", "xhttp", "vless",
                "vmess", "trojan", "ssh", "tls",
                "endpoint", "http://", "https://"
            ],
            "🔎 <b>CONFIGURAÇÕES</b>"
        )

    elif action == "servidores":
        text = action_search(
            chat_id,
            apk,
            [
                "server", "host", "hostname",
                "address", "endpoint", "remote",
                "http://", "https://", "ws://", "wss://"
            ],
            "🌐 <b>SERVIDORES / ENDPOINTS</b>"
        )

    elif action == "crypto":
        text = action_search(
            chat_id,
            apk,
            [
                "cipher", "encrypt", "decrypt",
                "aes", "des", "rsa", "gcm",
                "cbc", "ecb", "secretkey",
                "base64", "sha256"
            ],
            "🔐 <b>CRIPTOGRAFIA</b>"
        )

    elif action == "chaves":
        text = action_search(
            chat_id,
            apk,
            [
                "apikey", "api_key", "token",
                "secret", "password", "passwd",
                "privatekey", "publickey",
                "key", "credential"
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
        text = (
            "✍️ <b>ASSINATURA</b>\n\n"
            "A assinatura será configurada depois "
            "com um keystore próprio."
        )

    else:
        text = "❌ Opção desconhecida."

    if processing_id:
        edit_message(
            chat_id,
            processing_id,
            text,
            keyboard()
        )
    else:
        send(
            chat_id,
            text,
            keyboard()
        )


def process_update(update):

    callback = update.get("callback_query")

    if callback:
        answer(callback["id"])

        chat_id = callback["message"]["chat"]["id"]
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
            "⚡ <b>TECH NET APK MANAGER</b>\n\n"
            "Envie seu APK ou um APK que você "
            "tenha autorização para analisar.",
            keyboard()
        )
        return

    document = message.get("document")

    if document:

        filename = document.get(
            "file_name",
            ""
        )

        if not filename.lower().endswith(".apk"):
            send(
                chat_id,
                "❌ Envie somente arquivos .apk."
            )
            return

        send(
            chat_id,
            "📥 <b>Baixando APK...</b>\n\n"
            "Aguarde."
        )

        path = download_apk(
            chat_id,
            document["file_id"],
            filename
        )

        if not path:
            send(
                chat_id,
                "❌ Não consegui baixar o APK."
            )
            return

        size = os.path.getsize(path) / 1024 / 1024

        send(
            chat_id,
            "✅ <b>APK RECEBIDO!</b>\n\n"
            "📦 <code>" +
            html.escape(os.path.basename(path)) +
            "</code>\n"
            "💾 {:.2f} MB\n\n"
            "Agora escolha uma ferramenta:".format(size),
            keyboard()
        )


def main():

    print("TECH NET APK MANAGER BOT iniciado.")

    me = api("getMe")

    if not me.get("ok"):
        raise SystemExit(
            "Token inválido ou BOT inacessível."
        )

    print(
        "BOT conectado:",
        me["result"].get("username", "")
    )

    offset = 0

    while True:

        try:

            result = api(
                "getUpdates",
                {
                    "offset": offset,
                    "timeout": 50
                }
            )

            for update in result.get(
                "result",
                []
            ):

                offset = update["update_id"] + 1

                try:
                    process_update(update)
                except Exception as e:
                    print(
                        "UPDATE:",
                        e
                    )

        except KeyboardInterrupt:
            print("BOT encerrado.")
            break

        except Exception as e:
            print(
                "CONEXÃO:",
                e
            )

            time.sleep(5)


if __name__ == "__main__":
    main()
