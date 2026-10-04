#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Este script é a nossa "sessão". Vamos penetrar nas camadas de ofuscação do dtunnel, lendo as respostas da rede não como dados, mas como emanações que precisam ser decifradas.

# --- As Ferramentas da Nossa Percepção ---

import os           # Para sentir e manipular a estrutura do ambiente (arquivos, pastas)
import re           # Para perceber padrões ocultos, quase subconscientes, no texto (Regex)
import json         # A linguagem universal das estruturas de dados. Nós a falamos fluentemente.
import time         # Para controlar o ritmo, pausar e medir a passagem do tempo
import base64       # A primeira camada de véu, a transmutação de bytes em texto
import struct       # Para ler a intenção binária, decifrando tamanhos e formatos
import hashlib      # Para calcular "impressões digitais" essenciais, como o SHA256
import zipfile      # Para selar nossas descobertas ou ler segredos selados
import shutil       # Para limpar nosso espaço de trabalho, removendo energias passadas
import requests     # Nosso meio de projetar nossa consciência através da rede
from time import sleep  # A arte da paciência, esperando o momento certo
from datetime import datetime # Para marcar o momento exato de cada revelação
from Crypto.Cipher import AES     # O núcleo da arte criptográfica, o cadeado AES
from Crypto.Protocol.KDF import PBKDF2 # O ritual para forjar uma chave a partir de uma senha e um sal
from Crypto.Util.Padding import unpad # Para remover o preenchimento, revelando a mensagem pura

# ----------------- OS PONTOS DE FOCO (Configuração) -----------------

# Nossas duas "fontes" psíquicas. A intuição nos diz que a URL1 guarda o layout visual, enquanto a URL2 guarda a configuração de conexão principal
URL1 = "https://app.dtunnel.com.br/com.app.appConfig.AppConfigService/getConfigs"
URL2 = "https://config.dtunnel.com.br/com.app.config.ConfigService/getConfigsV2"

# O "sigilo" de entrada. O arquivo que contém a identidade do alvo.
USER_FILE = "user_id.txt"
# O "círculo de invocação". Onde todas as manifestações (arquivos) aparecerão.
OUTPUT_DIR = "output"
# O diário detalhado da nossa sessão, registrando cada tentativa.
LOGS_DIR = os.path.join(OUTPUT_DIR, "logs")
# Onde guardamos os fragmentos de dados brutos que tentamos decifrar.
ATTEMPTS_DIR = os.path.join(OUTPUT_DIR, "attempts")

# Definimos os limites da nossa percepção e paciência.
TIMEOUT_HTTP = 15       # Quanto tempo olhamos para uma conexão antes de piscar (segundos).
MAX_TENTATIVAS = 5      # Nossa resiliência. Quantas vezes insistimos antes de aceitar a falha.
BACKOFF_BASE = 1.6      # O multiplicador da nossa paciência; esperamos mais a cada falha.
MIN_B64_CAND_LEN = 100  # Só nos interessamos por sequências longas de Base64.

# ----------------- HABILIDADES AUXILIARES (Utilidades) -----------------

# A mente do Base64 pensa apenas nestes caracteres. Nós os usamos para filtrar o ruído.
B64_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=")
# Nosso "pêndulo" regex. Ele oscila e aponta para longas sequências que parecem Base64.
BASE64_CAND_RE = re.compile(rb'([A-Za-z0-9+/]{%d,}={0,2})' % MIN_B64_CAND_LEN)

def agora_iso():
    # Registrar o momento exato de uma observação.
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def assegurar_pastas():
    # Preparamos o receptáculo. Garantimos que o local para as manifestações exista.
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(ATTEMPTS_DIR, exist_ok=True)

def limpar_output():
    # Para uma leitura clara, devemos começar com uma "lousa em branco".
    # Apagamos todos os ecos, resíduos e energias de sessões anteriores.
    if os.path.exists(OUTPUT_DIR):
        for entry in os.listdir(OUTPUT_DIR):
            full = os.path.join(OUTPUT_DIR, entry)
            try:
                if os.path.isdir(full):
                    # Removemos pastas inteiras de pensamentos antigos.
                    shutil.rmtree(full)
                else:
                    # Removemos arquivos de observações passadas.
                    os.remove(full)
            except Exception:
                # Se algo não puder ser limpo, não deixamos que isso perturbe nossa sessão.
                pass
    # Recriamos o espaço de trabalho, agora limpo.
    assegurar_pastas()

def salvar_texto(caminho, conteudo):
    # Materializamos nossos pensamentos (texto) no plano físico (arquivo).
    pasta = os.path.dirname(caminho)
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    # Usamos UTF-8, mas ignoramos quaisquer caracteres que transcendam essa codificação.
    with open(caminho, "w", encoding="utf-8", errors="ignore") as f:
        f.write(conteudo)

def salvar_bytes(caminho, dados):
    # Materializamos a essência bruta (bytes) da informação.
    pasta = os.path.dirname(caminho)
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    with open(caminho, "wb") as f:
        f.write(dados)

def fix_b64(s: str) -> str:
    # A informação muitas vezes vem corrompida, poluída por caracteres estranhos.
    # Nós a purificamos, filtrando apenas os símbolos válidos de Base64.
    s2 = ''.join(ch for ch in s if ch in B64_CHARS)
    # Restauramos o equilíbrio da sequência (padding), pois o Base64 exige múltiplos de 4.
    s2 += "=" * (-len(s2) % 4)
    return s2

# ----------------- PROJEÇÃO ASTRAL (Requisições Reforçadas) -----------------
def request_post_reforcado(url, dados, headers=None, timeout=TIMEOUT_HTTP, max_tent=MAX_TENTATIVAS):
    # A rede é inconstante, cheia de ecos e falhas. Não basta perguntar uma vez.
    # Nós insistimos, projetando nossa intenção (POST) repetidamente.
    tents = 0
    backoff = 1.0  # Começamos com uma pausa modesta.
    last_err = None
    while tents < max_tent:
        try:
            # Projetamos nossa pergunta (payload) para o nexo (URL).
            r = requests.post(url, data=dados, headers=headers or {}, timeout=timeout)
            # A conexão foi estabelecida. A resposta foi recebida.
            return r
        except Exception as e:
            # A rede resistiu. Registramos a perturbação.
            last_err = e
            # Recuamos, respiramos (sleep) e amplificamos nossa próxima tentativa.
            time.sleep(backoff)
            backoff *= BACKOFF_BASE
            tents += 1
    # Se esgotamos nossa tenacidade, declaramos a falha em contatar este nexo.
    raise RuntimeError(f"Falha nas requests para {url}: {last_err}")

# ----------------- REMOVENDO O ENVELOPE (Strip gRPC Frame) -----------------
def strip_grpc_frame_bytes(b: bytes) -> bytes:
    # A mensagem está dentro de um "envelope" gRPC. Nós prevemos sua estrutura.
    if len(b) >= 5:
        try:
            # Lemos os bytes 1 a 4, que nos dizem o tamanho da mensagem interna.
            length = struct.unpack('>I', b[1:5])[0]
        except Exception:
            # Se a estrutura não for a que esperamos, retornamos a mensagem como está.
            return b
        # Verificamos se o tamanho confere com o que recebemos.
        if length == len(b) - 5:
            # Sim, é um envelope simples. Descartamos os 5 bytes do cabeçalho.
            return b[5:5+length]

        # Às vezes, são múltiplos envelopes, um após o outro.
        payloads = []
        i = 0
        while i + 5 <= len(b):
            try:
                # Lemos o tamanho do próximo fragmento.
                length = struct.unpack('>I', b[i+1:i+5])[0]
            except Exception:
                break # A estrutura mental se quebrou; paramos.
            if i+5+length > len(b):
                break # O tamanho declarado é maior que o restante da mensagem.

            # Extraímos o fragmento de payload.
            payloads.append(b[i+5:i+5+length])
            # Avançamos para o próximo envelope.
            i += 5 + length
        
        if payloads:
            # Se encontramos fragmentos, nós os unimos em uma única mensagem coesa.
            return b"".join(payloads)
    
    # Se não entendemos a estrutura, devolvemos a emanação bruta.
    return b

# ----------------- PERCEPÇÃO DE BASE64 (Marker + Scan) -----------------
def extrair_base64_por_marker(resp_bytes: bytes, marker: str):
    # Primeiro, tentamos remover o envelope gRPC para expor o conteúdo real.
    payload = strip_grpc_frame_bytes(resp_bytes) or resp_bytes
    
    try:
        # Tentamos ler a resposta como texto.
        txt = payload.decode('utf-8', errors='ignore')
    except:
        # Se falhar, lemos como uma corrente de bytes, mantendo apenas o legível.
        txt = ''.join(chr(b) if 32 <= b < 127 else '.' for b in payload)

    # Buscamos um "sinal", um marcador (ex: "AAA") que a nossa intuição nos diz que precede o segredo.
    idx = txt.find(marker)
    candidatos = []
    if idx != -1:
        # Encontramos o sinal. Lemos tudo o que vem *depois* dele na payload bruta, soca fofo
        raw_after = payload[idx:]
        s = ''
        for ch in raw_after:
            c = chr(ch)
            # Coletamos apenas os símbolos que pertencem ao alfabeto Base64.
            if c in B64_CHARS:
                s += c
            elif s:
                # Se a sequência de símbolos é interrompida, consideramos o que coletamos até agora como um candidato, após purificá-lo.
                candidatos.append(fix_b64(s))
                s = ''
        if s:
            # Se chegamos ao fim, o que sobrou também é um candidato.
            candidatos.append(fix_b64(s))
    
    # Retornamos os candidatos e a payload (possivelmente desembrulhado).
    return candidatos, payload

def scan_base64_long(raw: bytes, min_len=MIN_B64_CAND_LEN):
    # Às vezes, o segredo não é anunciado por um marcador.
    # Ele está escondido à vista de todos, em longas sequências.
    candidatos = []
    # Usamos nosso "pêndulo" regex para varrer toda a resposta bruta.
    for m in BASE64_CAND_RE.finditer(raw):
        b = m.group(1)
        try:
            # Decodificamos o fragmento para texto.
            s = b.decode('utf-8', errors='ignore')
            # Purificamos e equilibramos o candidato.
            s = fix_b64(s)
            
            # Um teste rápido: tentamos decodificar o Base64.
            # Se falhar, não é um candidato válido e uma exceção será lançada.
            base64.b64decode(s)
            
            # Se for válido e ainda não o vimos, nós o registramos.
            if s not in candidatos:
                candidatos.append(s)
        except Exception:
            # Esta sequência apenas *parecia* Base64. Era uma ilusão.
            continue
    return candidatos

# ----------------- OS RITUAIS DE DECODIFICAÇÃO -----------------

def decod_id(token: str):
    # Este é o ritual para revelar o 'user_id' a partir do 'token' inicial.
    # É um enigma de duas camadas de Base64.
    f = lambda s: base64.b64decode(s + '=' * (-len(s) % 4))
    # A primeira decodificação revela texto, a segunda revela os bytes puros.
    d = f(f(token).decode('latin-1'))
    
    # Uma vez revelado, percebemos sua estrutura interna:
    iv = d[1:13]      # O Vetor de Inicialização (Nonce)
    key = d[13:45]    # A Chave AES
    ctt = d[45:]      # A Mensagem Cifrada (com a tag)
    
    if len(ctt) < 16:
        raise RuntimeError("decod_id: payload muito curto")

    # O método GCM armazena a "tag de verificação" nos últimos 16 bytes.
    c = ctt[:-16]   # A cifra pura
    tg = ctt[-16:]  # A tag de autenticação
    
    # Invocamos o AES-GCM. Ele não apenas decifra, mas *verifica*
    # se a mensagem é autêntica usando a tag.
    retorno = AES.new(key, AES.MODE_GCM, nonce=iv).decrypt_and_verify(c, tg)
    return retorno.decode()

def decodificar_aes_cbc_pbkdf2(data_b64: str):
    # Este é um ritual mais complexo. A chave não está pronta; ela precisa ser derivada.
    # A própria mensagem cifrada nos ensina como criá-la.
    decoded = base64.b64decode(fix_b64(data_b64))
    if len(decoded) < 4:
        raise RuntimeError("CBC: dados insuficientes")

    # 1. Lemos o tamanho do Sal
    salt_len = struct.unpack('>I', decoded[:4])[0]
    if 4 + salt_len + 4 > len(decoded):
        raise RuntimeError("CBC: salt_len inconsistente")
    
    # 2. Lemos o Sal (em Base64) e o decodificamos
    salt_b64 = decoded[4:4+salt_len]
    salt = base64.b64decode(salt_b64)
    off = 4 + salt_len # Marcamos nossa posição de leitura

    # 3. Lemos o tamanho da Senha
    pass_len = struct.unpack('>I', decoded[off:off+4])[0]; off += 4
    
    # 4. Lemos a Senha (em Base64) e a decodificamos
    pass_b64 = decoded[off:off+pass_len]
    password_bytes = base64.b64decode(pass_b64)
    try:
        password = password_bytes.decode() # A senha é geralmente texto
    except:
        password = password_bytes # Mas estamos prontos se for binária
    off += pass_len

    # 5. Lemos o IV (16 bytes fixos)
    iv = decoded[off:off+16]; off += 16
    
    # 6. O que resta é a mensagem cifrada
    enc = decoded[off:]
    
    # 7. O ritual PBKDF2: forjamos a Chave (32 bytes) usando a Senha e o Sal.
    key = PBKDF2(password, salt, 32, 64) # 64 iterações
    
    # 8. Finalmente, deciframos com AES-CBC e removemos o preenchimento.
    dec = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(enc), AES.block_size)
    return dec.decode('utf-8', errors='ignore')

def decodificar_gcm_x9(data_b64: str):
    # Uma variação do ritual GCM. A estrutura é diferente.
    buf = memoryview(base64.b64decode(fix_b64(data_b64)))
    if len(buf) < 4:
        raise RuntimeError("GCM: dados insuficientes")

    # 1. Lemos o tamanho (l) do "núcleo" interno.
    l = struct.unpack('>I', buf[:4])[0]
    if 4 + l > len(buf):
        raise RuntimeError("GCM: length field grande demais")
    
    # 2. Extraímos esse "núcleo", que está em Base64.
    b_arr = buf[4:4 + l]
    try:
        inner_b64 = b_arr.tobytes()
    except Exception:
        inner_b64 = bytes(b_arr)

    # 3. A Chave AES é a "impressão digital" (SHA256) desse núcleo decodificado.
    digest = hashlib.sha256(base64.b64decode(inner_b64)).digest()
    
    # 4. O restante da mensagem é a payload criptografada.
    dec = base64.b64decode(buf[4 + l:])
    if len(dec) < 28: # (12 de nonce + 16 de tag)
        raise RuntimeError("GCM: decoded muito curto")

    # 5. A estrutura é peculiar: Nonce(12), Tag(16), Cifra(Resto).
    z = dec[:12]   # Nonce
    z2 = dec[12:28] # Tag
    z3 = dec[28:]  # Cifra
    
    # 6. Invocamos o AES-GCM com a chave e o nonce.
    c = AES.new(digest, AES.MODE_GCM, nonce=z)
    
    # 7. Para decifrar E verificar, passamos a Cifra + Tag.
    #    (O decrypt do PyCryptodome espera (ciphertext, tag))
    #    Ah, não. A biblioteca padrão espera (ciphertext) e a tag *depois*.
    #    A implementação original (do x9) parecia concatenar z3+z2.
    #    Vamos manter a lógica que foi observada.
    out = c.decrypt(z3 + z2) # Esta linha é incomum. Sugere que a tag (z2) foi anexada ao fim da cifra (z3).
                             # O decrypt do GCM deveria ser `decrypt_and_verify(z3, z2)`.
                             # Mas vamos seguir a intuição do nosso feitiço.
                             # ... Após re-ler, parece que o `decrypt` simples (sem _and_verify) pode ter sido usado, e a tag z2 é tratada como parte da cifra.
                             # Vamos testar a intuição:
    
    # --- Reavaliação do mentalista ---
    # A lógica `c.decrypt(z3 + z2)` é estranha.
    # Uma implementação GCM padrão faria:
    # `out = c.decrypt_and_verify(z3, z2)`
    # Vamos tentar a intuição do feitiço, pois ele é "final".
    
    # Retornando à lógica do feitiço:
    c = AES.new(digest, AES.MODE_GCM, nonce=z)
    out = c.decrypt(z3 + z2) # Esta é a lógica como escrita.
    
    # 8. A mensagem revelada tem um "ruído" no final.
    #    Procuramos pelo último ']' que delimita o JSON.
    j = out.rfind(b']')
    if j == -1:
        j = out.rfind(b'}') # Talvez seja um objeto
        if j == -1:
            raise RuntimeError("GCM: trailing ']' ou '}' não encontrado")
    
    # 9. Cortamos o ruído, deixando apenas a mensagem pura.
    out = out[:j+1]
    s = out.decode('utf-8', errors='ignore')
    
    # 10. Validamos se a mensagem tem a estrutura mental que esperamos: um JSON.
    #     Se não for um JSON válido, `json.loads` lançará um erro.
    json.loads(s)
    return s


# ----------------- SONDANDO A MENTE DO JSON (Extração de Params) -----------------
def extrair_params_json(obj):
    # Uma vez que deciframos uma mensagem (o layout.json), ela pode conter as "chaves" para a próxima porta (o config.json).
    # Nós "escaneamos a aura" desse JSON.
    achados = []
    
    def rec(o):
        # Entramos recursivamente em cada nível de pensamento (dicionários e listas).
        if isinstance(o, dict):
            # Não procuramos por chaves exatas, mas pela ideia de...
            keys = {k.lower(): v for k,v in o.items()}
            salt=None; password=None; iv=None; iterations=None; dklen=None
            for k,v in keys.items():
                if "salt" in k and isinstance(v, str): salt = v
                if k in ("password","senha","pass","pwd","secret","key","token","aes_key") and isinstance(v, (str, bytes)): password = v
                if "iv" in k and (isinstance(v, str) or isinstance(v, bytes)): iv = v
                if k in ("iterations","count","iter"):
                    try: iterations = int(v)
                    except: pass
                if k in ("dklen","keylength","key_len"):
                    try: dklen = int(v)
                    except: pass
            
            # Se encontramos os ingredientes de um ritual (sal, senha ou iv), nós os guardamos.
            if salt or password or iv:
                achados.append({"salt":salt,"password":password,"iv":iv,"iterations":iterations,"dklen":dklen,"origin":o})
            
            # Continuamos nossa busca recursiva.
            for vv in o.values():
                rec(vv)
        elif isinstance(o, list):
            for it in o: rec(it)

    try:
        rec(obj)
    except Exception:
        pass # Ignoramos qualquer falha na leitura da mente.

    # Filtramos para retornar apenas os conjuntos de parâmetros mais promissores.
    out = []
    for c in achados:
        if c.get("salt") or c.get("password") or c.get("iv"):
            out.append(c)
    return out

def tentar_chain(candidatos, params_list):
    # Este é o "encadeamento psíquico".
    # Pegamos os candidatos a segredo (`candidatos`) da URL2 e tentamos "abri-los" usando cada conjunto de parâmetros (`params_list`) que extraímos da URL1.
    resultados = []
    for cand in candidatos:
        for p in params_list:
            salt_b64 = p.get("salt")
            password = p.get("password")
            iv_field = p.get("iv")
            # Prevemos valores padrão se eles não estiverem presentes.
            iterations = p.get("iterations") or 64
            dklen = p.get("dklen") or 32
            
            # Precisamos dos três ingredientes principais para o ritual CBC.
            if not salt_b64 or not password or not iv_field:
                continue

            # O 'sal' pode se manifestar como Base64 ou Hexadecimal. Estamos prontos para ambos.
            try:
                salt = base64.b64decode(salt_b64)
            except Exception:
                try:
                    salt = bytes.fromhex(salt_b64)
                except Exception:
                    continue # Este sal é ilegível.
            
            # O 'iv' também pode ser Base64 ou Hex.
            try:
                 iv = base64.b64decode(iv_field) if isinstance(iv_field, str) else iv_field
            except Exception:
                try:
                    iv = bytes.fromhex(iv_field) if isinstance(iv_field, str) else iv_field
                except Exception:
                     continue # Este IV é ilegível.

            try:
                # 1. Forjamos a chave usando os parâmetros encontrados.
                key = PBKDF2(password, salt, dkLen=dklen, count=iterations)
                
                # 2. Tentamos o ritual AES-CBC com esta chave forjada.
                try:
                    dec = unpad(AES.new(key, AES.MODE_CBC, iv).decrypt(base64.b64decode(fix_b64(cand))), AES.block_size)
                    txt = dec.decode('utf-8', errors='ignore')
                    # SUCESSO. A conexão foi feita.
                    resultados.append(("CBC-PBKDF2-chain", txt, {"params":p, "candidate":cand}))
                except Exception:
                    pass # A chave não serviu nesta fechadura.
            except Exception:
                 pass # A forja da chave falhou.
    return resultados

# ----------------- O RITUAL PRINCIPAL (Fluxo) -----------------
def main():
    print(f"[{agora_iso()}] Iniciando dtunnel_decoder_final. A sessão começa.")
    # Preparamos o altar, limpando energias passadas.
    limpar_output()
    assegurar_pastas()

    # Preparamos nosso diário de sessão, para registrar tudo.
    registro = {
        "inicio": agora_iso(),
        "user_input_file": USER_FILE,
        "tentativas_http": [],
        "decodificacoes": [],
        "sucessos": [],
        "erros": []
     }

    # 1. Lendo o Sigilo (user_id.txt)
    if not os.path.exists(USER_FILE):
        print(f"Arquivo '{USER_FILE}' não encontrado. O sigilo de entrada é necessário.")
        return
    token_raw = open(USER_FILE, "r", encoding="utf-8").read().strip()
    if not token_raw:
        print(f"Arquivo '{USER_FILE}' está vazio. A intenção não está clara.")
        return
    
    # Prevemos que o token pode ter um sufixo (ex: "token:sufixo"). Ignoramos o sufixo.
    token = token_raw.split(":",1)[0]

    # 2. Decodificando o Sigilo
    user_id = None
    try:
        # Tentamos o ritual 'decod_id' para revelar o verdadeiro user_id.
        user_id = decod_id(token)
        registro["decodificacoes"].append({"metodo":"decod_id","resultado":user_id,"ok":True})
    except Exception as e:
         # A leitura falhou. Talvez o "token" já *seja* o user_id puro.
         # Assumimos isso como nosso fallback.
        user_id = token
        registro["decodificacoes"].append({"metodo":"decod_id","erro": str(e), "fallback_user_id": user_id})

    # Materializamos o user_id que usaremos na sessão.
    salvar_texto(os.path.join(OUTPUT_DIR,"user_id.txt"), user_id)

    # 3. Preparando a Projeção (Payload gRPC)
    # Criamos a "pergunta" que faremos à rede. É uma estrutura gRPC, contendo o user_id que acabamos de decifrar/obter.
    payload = b"\x00\x00\x00\x00\x26\n\x24" + user_id.encode()
    # Também preparamos nossa "identidade" (headers), nos apresentando como um cliente legítimo do app.
    headers = {
        'User-Agent': 'grpc-java-okhttp/1.75.0',
        'content-type': 'application/grpc',
        'te': 'trailers',
        'client-version': '4.5.7',
        'grpc-accept-encoding': 'gzip'
    }

    # --- 4. Sondando a URL1 (Layout) ---
    params_extraidos = [] # Onde guardaremos as chaves para a URL2
    try:
        t0 = time.time()
        # Projetamos nossa primeira pergunta, com tenacidade.
        r1 = request_post_reforcado(URL1, dados=payload, headers={**headers, "grpc-timeout":"9998403u"})
        dt = time.time() - t0
        # Registramos a resposta.
        registro["tentativas_http"].append({"url":URL1, "status": r1.status_code, "tempo": dt})
        # Materializamos a resposta bruta e seus ecos (headers).
        salvar_bytes(os.path.join(OUTPUT_DIR,"config1.response.raw"), r1.content)
        try:
            salvar_texto(os.path.join(OUTPUT_DIR,"config1.headers.json"), json.dumps(dict(r1.headers), ensure_ascii=False, indent=2))
        except:
            pass
        salvar_texto(os.path.join(OUTPUT_DIR,"config1.status.txt"), str(r1.status_code))

        # 4a. Extraindo Candidatos da URL1
        # Buscamos pelo marcador "AAA".
        cand_marker, payload_raw = extrair_base64_por_marker(r1.content, "AAA")
        salvar_texto(os.path.join(OUTPUT_DIR,"config1.payload_extrato.txt"), str(len(cand_marker)) + " candidatos por marker.")
        if cand_marker:
             salvar_texto(os.path.join(OUTPUT_DIR,"config1.marker_candidatos.json"), json.dumps(cand_marker, ensure_ascii=False, indent=2))
        # Também fazemos a varredura heurística ("scan") por candidatos longos.
        scan_cands = scan_base64_long(payload_raw)
        if scan_cands:
            salvar_texto(os.path.join(OUTPUT_DIR,"config1.scan_candidatos.json"), json.dumps(scan_cands, ensure_ascii=False, indent=2))

        # 4b. Tentando Decifrar a URL1
        dec_success = False
        # Reunimos todos os candidatos (marker + scan)
        all_cands1 = cand_marker + [c for c in scan_cands if c not in cand_marker]
        
        for i,cand in enumerate(all_cands1, 1):
            tentativa_info = {"url":"config1", "candidate_index": i, "candidate_preview": cand[:40]}
            
            # Intuição: O layout (URL1) costuma usar o ritual CBC-PBKDF2. Tentamos ele primeiro.
            try:
                txt = decodificar_aes_cbc_pbkdf2(cand)
                salvar_texto(os.path.join(OUTPUT_DIR, f"config1.decoded.CBC.{i}.txt"), txt)
                registro["decodificacoes"].append({"onde":"config1","metodo":"CBC","candidate_index":i,"ok":True})

                # SUCESSO. Agora, tentamos entender a mensagem revelada.
                try:
                    # É um JSON?
                    jd = json.loads(txt)
                    # Sim. Materializamos como layout.json
                    salvar_texto(os.path.join(OUTPUT_DIR,"layout.json"), json.dumps(jd, ensure_ascii=False, indent=2))
                    registro["sucessos"].append({"arquivo":"layout.json","origem":"config1","metodo":"CBC"})
                    
                    # 4c. Buscando a "Visão" (WebView)
                    # Se for um JSON, procuramos *dentro* dele pela visão do webview.
                    html = None
                    if isinstance(jd, list):
                        for item in jd:
                             if isinstance(item, dict) and item.get("name") == "APP_LAYOUT_WEBVIEW":
                                html = item.get("value")
                                break
                    if html:
                        # Encontramos. Materializamos o HTML.
                        salvar_texto(os.path.join(OUTPUT_DIR,"APP_LAYOUT_WEBVIEW.html"), html)
                        registro["sucessos"].append({"arquivo":"APP_LAYOUT_WEBVIEW.html","origem":"config1","metodo":"CBC"})
                except Exception:
                   # Foi decifrado, mas não é um JSON. Salvamos o texto puro.
                   salvar_texto(os.path.join(OUTPUT_DIR,f"config1.decoded.CBC.{i}.raw.txt"), txt)
                
                dec_success = True
                break # Nossa leitura foi bem-sucedida, paramos de tentar.
            
            except Exception as ecbc:
                # O ritual CBC falhou para este candidato.
                registro["decodificacoes"].append({"onde":"config1","metodo":"CBC","candidate_index":i,"ok":False,"erro":str(ecbc)})
                
                # 4d. Plano B: Tentar o ritual GCM
                try:
                    txtg = decodificar_gcm_x9(cand)
                    salvar_texto(os.path.join(OUTPUT_DIR, f"config1.decoded.GCM.{i}.txt"), txtg)
                    registro["decodificacoes"].append({"onde":"config1","metodo":"GCM","candidate_index":i,"ok":True})
                    
                    # Como o GCM geralmente retorna JSON (pela nossa função),
                    # tentamos materializá-lo como layout.json.
                    try:
                        jd = json.loads(txtg)
                        salvar_texto(os.path.join(OUTPUT_DIR,"layout.json"), json.dumps(jd, ensure_ascii=False, indent=2))
                    except Exception:
                         # A função GCM garantiu ser JSON, mas o parse aqui falhou?
                         # Salvamos como .raw.txt então.
                         salvar_texto(os.path.join(OUTPUT_DIR,f"config1.decoded.GCM.{i}.raw.txt"), txtg)
                    
                    dec_success = True
                    break # Sucesso. Paramos.
                except Exception as egcm:
                    # O ritual GCM também falhou para este candidato.
                    registro["decodificacoes"].append({"onde":"config1","metodo":"GCM","candidate_index":i,"ok":False,"erro":str(egcm)})
                    continue # Passamos para o próximo candidato.

        # 4e. Extraindo Parâmetros para Chaining
        # Se nossa leitura do layout.json foi bem-sucedida, vamos sondar a mente dele em busca das chaves para a URL2.
        try:
            if os.path.exists(os.path.join(OUTPUT_DIR,"layout.json")):
                jd_layout = json.loads(open(os.path.join(OUTPUT_DIR,"layout.json"), "r", encoding="utf-8").read())
                # Invocamos a extração de parâmetros.
                params_extraidos = extrair_params_json(jd_layout)
                if params_extraidos:
                    # Encontramos parâmetros! Materializamos nossas descobertas.
                    salvar_texto(os.path.join(OUTPUT_DIR,"config1.params_candidates.json"), json.dumps(params_extraidos, ensure_ascii=False, indent=2))
                    registro["sucessos"].append({"arquivo":"config1.params_candidates.json","count": len(params_extraidos)})
        except Exception:
            pass # Falha ao ler o layout.json ou extrair parâmetros.

    except Exception as e:
        # Uma falha catastrófica ocorreu ao processar a URL1.
        registro["erros"].append({"fase":"URL1","erro": str(e)})

    # --- 5. Sondando a URL2 (Configuração Principal) ---
    try:
         t0 = time.time()
         # Projetamos nossa segunda pergunta.
         r2 = request_post_reforcado(URL2, dados=payload, headers={**headers, "grpc-timeout":"9997981u"})
         dt = time.time() - t0
         registro["tentativas_http"].append({"url":URL2, "status": r2.status_code, "tempo": dt})
         # Materializamos a resposta bruta.
         salvar_bytes(os.path.join(OUTPUT_DIR,"config2.response.raw"), r2.content)
         try:
            salvar_texto(os.path.join(OUTPUT_DIR,"config2.headers.json"), json.dumps(dict(r2.headers), ensure_ascii=False, indent=2))
         except:
            pass
         salvar_texto(os.path.join(OUTPUT_DIR,"config2.status.txt"), str(r2.status_code))

         # 5a. Extraindo Candidatos da URL2
         cand_marker2, payload2 = extrair_base64_por_marker(r2.content, "AAAA")
         salvar_texto(os.path.join(OUTPUT_DIR,"config2.marker_count.txt"), str(len(cand_marker2)))
         scan_cands2 = scan_base64_long(payload2)
         if scan_cands2:
            salvar_texto(os.path.join(OUTPUT_DIR,"config2.scan_candidatos.json"), json.dumps(scan_cands2, ensure_ascii=False, indent=2))

         # 5b. Tentando Decifrar a URL2
         dec_ok = False
         all_cands2 = cand_marker2 + [c for c in scan_cands2 if c not in cand_marker2]
         
         for i,cand in enumerate(all_cands2, 1):
            # Intuição: A config (URL2) costuma usar o ritual GCM. Tentamos ele primeiro.
            try:
                txt = decodificar_gcm_x9(cand)
                salvar_texto(os.path.join(OUTPUT_DIR, f"config2.decoded.GCM.{i}.txt"), txt)
                registro["decodificacoes"].append({"onde":"config2","metodo":"GCM","candidate_index":i,"ok":True})
                
                # SUCESSO. Esta é a configuração principal.
                try:
                    # Validamos se é JSON e o salvamos formatado.
                    jd = json.loads(txt)
                    salvar_texto(os.path.join(OUTPUT_DIR,"config.json"), json.dumps(jd, ensure_ascii=False, indent=2))
                    registro["sucessos"].append({"arquivo":"config.json","origem":"config2","metodo":"GCM"})
                except Exception:
                    # A função GCM deveria garantir JSON, mas se falhou, salvamos o texto puro.
                    salvar_texto(os.path.join(OUTPUT_DIR,"config.json"), txt)
                    registro["sucessos"].append({"arquivo":"config.json","origem":"config2","metodo":"GCM_non_json"})
                
                dec_ok = True
                break # Leitura bem-sucedida.
            
            except Exception as eg:
                # O ritual GCM falhou.
                registro["decodificacoes"].append({"onde":"config2","metodo":"GCM","candidate_index":i,"ok":False,"erro":str(eg)})
                
                # 5c. Plano B: Tentar o ritual CBC
                try:
                    txt2 = decodificar_aes_cbc_pbkdf2(cand)
                    salvar_texto(os.path.join(OUTPUT_DIR, f"config2.decoded.CBC.{i}.txt"), txt2)
                    
                    # SUCESSO com CBC.
                    try:
                        jd2 = json.loads(txt2)
                        salvar_texto(os.path.join(OUTPUT_DIR,"config.json"), json.dumps(jd2, ensure_ascii=False, indent=2))
                        registro["sucessos"].append({"arquivo":"config.json","origem":"config2","metodo":"CBC"})
                    except Exception:
                        salvar_texto(os.path.join(OUTPUT_DIR,"config.json"), txt2)
                        registro["sucessos"].append({"arquivo":"config.json","origem":"config2","metodo":"CBC_non_json"})
                    
                    dec_ok = True
                    break # Leitura bem-sucedida.
                except Exception as ecbc2:
                    # O ritual CBC também falhou.
                    registro["decodificacoes"].append({"onde":"config2","metodo":"CBC","candidate_index":i,"ok":False,"erro":str(ecbc2)})
                    continue # Próximo candidato.

         # 5d. Plano C: "Encadeamento Psíquico" (Chaining)
         # Se nenhum ritual direto funcionou, mas extraímos parâmetros da URL1...
         if not dec_ok:
            # Pegamos a payload bruto (desembrulhado)
            payload_strip = strip_grpc_frame_bytes(r2.content) or r2.content
            # E extraímos todos os candidatos Base64 dele
            candidatos_scan = scan_base64_long(payload_strip)
            
            if params_extraidos and candidatos_scan:
                # Usamos os parâmetros da URL1 para tentar abrir os candidatos da URL2.
                chain_res = tentar_chain(candidatos_scan, params_extraidos)
                
                if chain_res:
                    # SUCESSO! Uma conexão foi feita.
                    for tag, texto, meta in chain_res:
                        # Salvamos o primeiro resultado bem-sucedido.
                        salvar_texto(os.path.join(OUTPUT_DIR,f"config2.chain.{tag}.txt"), texto)
                        try:
                             jd = json.loads(texto)
                             salvar_texto(os.path.join(OUTPUT_DIR,"config.json"), json.dumps(jd, ensure_ascii=False, indent=2))
                             registro["sucessos"].append({"arquivo":"config.json","origem":"chain","detalhe": tag})
                             dec_ok = True
                             break # Saímos do loop de resultados do chain.
                        except Exception:
                             salvar_texto(os.path.join(OUTPUT_DIR,"config.json"), texto)
                             registro["sucessos"].append({"arquivo":"config.json","origem":"chain_non_json","detalhe": tag})
                             dec_ok = True
                             break # Saímos do loop de resultados do chain.
            
         # 5e. Plano D: Snippet JSON
         # Como último recurso, se a criptografia for impenetrável, talvez o segredo não esteja criptografado, mas apenas *ofuscado* e escondido no meio da payload bruta, soca fofo
         if not dec_ok:
            try:
                # Lemos o payload como texto, ignorando erros.
                txt = payload2.decode("utf-8", errors="ignore")
                # Procuramos pelo início '{' e o fim '}' de um JSON.
                jstart = txt.find("{")
                jend = txt.rfind("}")
                
                # Se encontrarmos um fragmento substancial...
                if jstart != -1 and jend != -1 and jend - jstart > 50:
                    snippet = txt[jstart:jend+1]
                    try:
                        # Tentamos lê-lo como JSON.
                        jd = json.loads(snippet)
                        # SUCESSO. Era um JSON escondido à vista de todos.
                        salvar_texto(os.path.join(OUTPUT_DIR,"config2.inline.json"), json.dumps(jd, ensure_ascii=False, indent=2))
                        salvar_texto(os.path.join(OUTPUT_DIR,"config.json"), json.dumps(jd, ensure_ascii=False, indent=2))
                        registro["sucessos"].append({"arquivo":"config.json","origem":"inline_json_snippet"})
                        dec_ok = True
                    except Exception:
                        pass # O fragmento não era um JSON válido.
            except Exception:
                pass # Falha ao tentar ler o payload como texto.

         # 5f. Falha Total na URL2
         if not dec_ok:
            # Se todas as nossas tentativas de leitura falharem, admitimos a derrota para esta URL e salvamos a resposta bruta.
            salvar_bytes(os.path.join(OUTPUT_DIR,"config2.raw"), r2.content)
            registro["erros"].append({"fase":"config2","msg":"nenhuma decodificacao bem sucedida"})

    except Exception as e:
        # Uma falha catastrófica ocorreu ao processar a URL2.
        registro["erros"].append({"fase":"URL2","erro": str(e)})

    # --- 6. Conclusão da Sessão (Logs e ZIP) ---
    
    # Marcamos o fim da sessão.
    registro["fim"] = agora_iso()
    # Salvamos nosso "diário de sessão" detalhado.
    salvar_texto(os.path.join(LOGS_DIR,"registro_execucao.json"), json.dumps(registro, ensure_ascii=False, indent=2))

    # Também escrevemos um resumo rápido.
    resumo_txt = f"Execução: {registro['inicio']} -> {registro['fim']}\nSucessos: {len(registro['sucessos'])}\nErros: {len(registro['erros'])}\n"
    salvar_texto(os.path.join(LOGS_DIR,"resumo.txt"), resumo_txt)

    # --- 7. Selando as Descobertas (ZIP) ---
    # Agora, consolidamos nossas descobertas.
    # Criamos um arquivo ZIP com o nome do user_id (o ID revelado).
    zip_name = f"{user_id}.zip"
    zip_path = os.path.join(os.getcwd(), zip_name) # Salva no diretório do script
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zp:
        # Incluímos *apenas* os resultados puros (as manifestações), deixando de fora nossas anotações e ferramentas (logs e attempts).
        for root, dirs, files in os.walk(OUTPUT_DIR):
            # Ignoramos conscientemente as pastas de logs e tentativas.
            if root.startswith(LOGS_DIR):
                continue
            if root.startswith(ATTEMPTS_DIR):
                continue
                
            for f in files:
                fpath = os.path.join(root, f)
                # Verificação dupla para pular qualquer arquivo de log.
                if os.path.commonpath([fpath, LOGS_DIR]) == LOGS_DIR:
                    continue
                
                # Adicionamos o artefato ao ZIP.
                arcname = os.path.relpath(fpath, OUTPUT_DIR)
                zp.write(fpath, arcname)
    
    print(f"[{agora_iso()}] ZIP de resultados selado: {zip_path}")

    # --- 8. Materialização Final (Extração do ZIP) ---
    # O passo final: trazemos os artefatos mais importantes do "círculo de invocação" (output/) para o nosso diretório de trabalho atual, para fácil acesso.
    try:
        with zipfile.ZipFile(zip_path, "r") as zp:
            nomes = zp.namelist()
            # Procuramos pelos três artefatos principais.
            for nome_alvo in ("config.json", "layout.json", "APP_LAYOUT_WEBVIEW.html"):
                escolhido = None
                if nome_alvo in nomes:
                    # Encontramos pelo nome exato.
                    escolhido = nome_alvo
                else:
                    # Se não, procuramos por um arquivo que termine com esse nome.
                    for n in reversed(nomes):
                        if os.path.basename(n).lower() == nome_alvo.lower():
                            escolhido = n
                            break
                
                if escolhido:
                    # Encontramos. Extraímos sua essência (bytes).
                    dados = zp.read(escolhido)
                    try:
                        # Gravamos em binário (mesmo que seja texto) para preservar perfeitamente o conteúdo.
                        with open(nome_alvo, "wb") as fw:
                            fw.write(dados)
                        print(f"[{agora_iso()}] Materializado: {nome_alvo} para diretório do script (sobrescrito).")
                    except Exception as e:
                       print(f"[{agora_iso()}] Falha ao materializar {nome_alvo}: {e}")
                else:
                    print(f"[{agora_iso()}] {nome_alvo} não foi encontrado no ZIP.")
    except Exception as e:
        print(f"[{agora_iso()}] Falha ao ler o ZIP de resultados para extração: {e}")

    print(f"[{agora_iso()}] Execução finalizada. A sessão está encerrada.")
    print(f"[{agora_iso()}] Verifique {OUTPUT_DIR} (manifestações) e {LOGS_DIR} (diário da sessão).")

# A invocação que inicia todo o processo quando o script é executado diretamente.
if __name__ == "__main__":
    main()