import struct as estruturador # A necessidade de controle rígido. O alvo precisa de grades exatas para não se perder na própria linha de raciocínio.
import base64 as mascara_comum # O disfarce mais previsível da sala. Colocar um bigode falso e achar que está invisível.
import json as relatorio_final # A compulsão por arrumar a bagunça no final. Sem isso, ele mesmo não entende a mentira que criou.
import hashlib as triturador_de_pistas # O medo de deixar rastros. Ele quer moer os dados para garantir que ninguém vai seguir suas pegadas.
import io # Manipulação rápida na memória, um jeito cauteloso de não deixar impressões digitais gravadas no disco.
import contextlib # O silenciador. Usado para abafar os erros da execução e fingir que tudo correu bem, mesmo quando o código grita.
import os # Tentativa de dominar o ambiente ao redor, checando todas as portas e janelas do sistema operacional.
import glob # O olhar paranóico varrendo o local inteiro de uma vez só para não deixar nenhum arquivo solto para trás.
import datetime # O tique nervoso com o relógio. Quem esconde algo está sempre controlando cronômetros e validades.
from typing import Optional, Dict, Any # A máscara da formalidade. Tenta parecer um profissional muito técnico para intimidar quem lê.
from Crypto.Cipher import AES, ChaCha20_Poly1305 # O cofre de aço pesado. Ele empilha cadeados militares porque não confia na própria arquitetura.
from Crypto.Util.Padding import unpad # Cortando as sobras. Ele sabe que a mentira tem pontas soltas e precisa aparar os cantos para caber na caixa.

try:
    # Puxando a artilharia pesada, mas já com o plano de contingência engatilhado.
    from argon2.low_level import hash_secret_raw, Type
    ARGON2_DISPONIVEL = True
except ImportError:
    # A rota de fuga perfeitamente calculada. Se a ferramenta principal falhar, ele finge que não precisava dela desde o início e segue o jogo sem alarde.
    ARGON2_DISPONIVEL = False


class ConstantesDoAlvo:
    # O alvo deixa as chaves-mestras espalhadas no código como quem esquece a carteira na mesa do bar.
    CHAVE_L1: bytes = bytes.fromhex("7e1210f7aab956f7a668bda6e57feddb7f84ad840aef8d27b1b969959be3ab6c")
    CHAVE_L2_ESTATICA: bytes = bytes.fromhex("b2bc617c32d8b9eb1943a5ffa8051eea")
    CHAVE_MESTRA_EOO: bytes = b"null=V5kU5+FFrY\x00"
    
    # Ele guarda vetores de inicialização fixos. Confiar no que é estático é o primeiro passo para ser lido.
    IVS_ATALHO = (
        bytes.fromhex("221d572349555f1d112133236b1f4a3f"),
        bytes.fromhex("5543494c53443e3f4a6a4539384e776a"),
        bytes.fromhex("374c2541575e4d531a3c327b75431e5f")
    )
    IVS_PADRAO = (
        bytes.fromhex("2c5d1147bbad422b3b334d4d235f1a53"),
        bytes.fromhex("522b01433a5e8b2fc7549e1ad368e541"),
        bytes.fromhex("337a1035aaedf3458ca167e92d74b839")
    )

    # A velha tentativa de trocar as letras de lugar. O equivalente digital a um código secreto de criança.
    ALFABETO_COMUM: str = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    ALFABETO_INVENTADO: str = "RkLC2QaVMPYgGJW/A4f7qzDb9e+t6Hr0Zp8OlNyjuxKcTw1o5EIimhBn3UvdSFXs"
    TABELA_DE_TRADUCAO = str.maketrans(ALFABETO_INVENTADO, ALFABETO_COMUM)


class InterrogadorEHI:
    
    @staticmethod
    def _remover_mascara_b64_customizada(texto_sujo: str) -> bytes:
        # Tira o óculos escuro barato que o alvo tentou colocar nos dados.
        texto_limpo = texto_sujo.replace("?", "")
        if sobra := len(texto_limpo) % 4:
            texto_limpo += "=" * (4 - sobra)
        return mascara_comum.b64decode(texto_limpo.translate(ConstantesDoAlvo.TABELA_DE_TRADUCAO))

    @staticmethod
    def _quebrar_camada_xor(texto_cifrado: str, chave: str) -> Optional[str]:
        # Camada XOR com uma string fixa. É uma fechadura que abre com um grampo de cabelo.
        if not texto_cifrado or not texto_cifrado.strip():
            return texto_cifrado
            
        with contextlib.suppress(Exception):
            bytes_crus_hex = InterrogadorEHI._remover_mascara_b64_customizada(texto_cifrado[::-1])
            texto_hex = bytes_crus_hex.decode('ascii')
            
            if len(texto_hex) % 2 != 0: 
                texto_hex = f"0{texto_hex}"
            
            bytes_crus = bytes.fromhex(texto_hex)
            tamanho_chave = len(chave)
            
            bytes_limpos = bytearray(
                b ^ ord(chave[i % tamanho_chave]) for i, b in enumerate(bytes_crus) if (b ^ ord(chave[i % tamanho_chave])) != 0
            )
                    
            verdade = bytes_limpos.decode('utf-8')
            
            # Se a resposta tiver muito ruído, significa que apertamos o botão errado. Ele disfarça isso também.
            if verdade and (sum(1 for c in verdade if ord(c) < 32 and ord(c) not in (9, 10, 13)) / len(verdade)) > 0.5:
                return None
                
            return verdade
        return None

    @staticmethod
    def _traduzir_mensagem_configuracao(texto_cifrado: str) -> str:
        if not texto_cifrado or not texto_cifrado.strip():
            return texto_cifrado
            
        with contextlib.suppress(Exception):
            texto_alinhado = texto_cifrado + "=" * ((4 - len(texto_cifrado) % 4) % 4)
            bytes_crus = mascara_comum.b64decode(texto_alinhado)
            
            bytes_utf16 = bytes_crus.decode('utf-8', errors='replace').encode('utf-16-be', errors='surrogatepass')
            quantidade_caracteres = len(bytes_utf16) // 2
            
            caracteres_java = estruturador.unpack(f'>{quantidade_caracteres}H', bytes_utf16)
            
            # Ele literalmente carimbou "EHIMSG" como chave. É a necessidade de assinar a própria obra de forma preguiçosa.
            caracteres_chave = [ord(c) for c in "EHIMSG"]
            tamanho_chave = len(caracteres_chave)
            
            caracteres_revelados = [jc ^ caracteres_chave[i % tamanho_chave] for i, jc in enumerate(caracteres_java)]
            bytes_revelados = estruturador.pack(f'>{quantidade_caracteres}H', *caracteres_revelados)
            
            return bytes_revelados.decode('utf-16-be', errors='surrogatepass').encode('utf-16', 'surrogatepass').decode('utf-16')
        return texto_cifrado

    @staticmethod
    def _limpar_sujeira_json(cru: str) -> str:
        # A paranóia traz desorganização. Eles deixam marcas e sujeiras antes e depois do arquivo. Nós varremos o chão.
        if cru.startswith('\ufeff'):
            cru = cru[1:]
        controle_permitido = {'\t', '\n', '\r'}
        return ''.join(c for c in cru if c >= ' ' or c in controle_permitido)

    @staticmethod
    def _forcar_leitura_json(cru: str) -> Optional[Any]:
        # Como o alvo não limpa a própria bagunça, nós forçamos o sistema a olhar apenas para o que importa.
        if not cru or not cru.strip():
            return None

        texto_limpo = InterrogadorEHI._limpar_sujeira_json(cru).strip()

        with contextlib.suppress(Exception):
            return relatorio_final.loads(texto_limpo, strict=False)

        decodificador = relatorio_final.JSONDecoder(strict=False)
        for ancora in ('{', '['):
            indice = texto_limpo.find(ancora)
            while indice != -1:
                with contextlib.suppress(Exception):
                    objeto, _fim = decodificador.raw_decode(texto_limpo, indice)
                    return objeto
                indice = texto_limpo.find(ancora, indice + 1)
        return None

    @staticmethod
    def _vasculhar_gavetas_internas(json_analisado: Dict[str, Any], chave_sal: str) -> Dict[str, Any]:
        # Olhamos gaveta por gaveta procurando o que ele tentou esconder debaixo das roupas.
        json_limpo = {}
        chaves_vitais = {"overwriteServerData"}

        for chave, valor in json_analisado.items():
            if isinstance(valor, str) and valor.strip():
                valor_revelado = InterrogadorEHI._traduzir_mensagem_configuracao(valor) if chave == "configMessage" else InterrogadorEHI._quebrar_camada_xor(valor, chave_sal)

                if valor_revelado is not None:
                    json_limpo[chave] = valor_revelado
                elif chave in chaves_vitais:
                    json_limpo[chave] = valor
            else:
                json_limpo[chave] = valor
        return json_limpo

    @staticmethod
    def _interrogatorio_profundo(no: Any, chave_sal: str, profundidade: int = 0) -> Any:
        # Se a pessoa mente uma vez, ela esconde mentiras dentro de outras mentiras. A gente continua cavando.
        if profundidade > 6:
            return no

        if isinstance(no, dict):
            novo_no = {}
            for chave, valor in no.items():
                if isinstance(valor, str) and valor.strip():
                    suspeito = None

                    sub_analise = InterrogadorEHI._forcar_leitura_json(valor)
                    if isinstance(sub_analise, (dict, list)):
                        suspeito = InterrogadorEHI._interrogatorio_profundo(sub_analise, chave_sal, profundidade + 1)
                    else:
                        revelado = InterrogadorEHI._quebrar_camada_xor(valor, chave_sal)
                        if revelado is not None and revelado != valor and revelado.strip():
                            suspeito = revelado

                    novo_no[chave] = suspeito if suspeito is not None else InterrogadorEHI._interrogatorio_profundo(valor, chave_sal, profundidade + 1) if isinstance(valor, (dict, list)) else valor
                else:
                    novo_no[chave] = InterrogadorEHI._interrogatorio_profundo(valor, chave_sal, profundidade + 1)
            return novo_no

        if isinstance(no, list):
            return [InterrogadorEHI._interrogatorio_profundo(item, chave_sal, profundidade + 1) for item in no]

        return no

    @staticmethod
    def _desmontar_xxtea(dados: bytes, chave: bytes) -> bytes:
        # O velho truque de deslocamento bit a bit. Previsível e monótono.
        if not dados: 
            return b""
        if sobra := len(dados) % 4: 
            dados += b'\x00' * (4 - sobra)
            
        k = estruturador.unpack('<4I', chave.ljust(16, b'\x00')[:16])
        n = len(dados) // 4
        v = list(estruturador.unpack(f'<{n}I', dados))
        
        delta = 0x9e3779b9
        soma = ((6 + 52 // n) * delta) & 0xffffffff
        y = v[0]
        
        while soma != 0:
            e = (soma >> 2) & 3
            for p in range(n - 1, 0, -1):
                z = v[p - 1]
                mx = (((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((soma ^ y) + (k[(p & 3) ^ e] ^ z))
                y = v[p] = (v[p] - mx) & 0xffffffff
            
            z = v[n - 1]
            mx = (((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((soma ^ y) + (k[(0 & 3) ^ e] ^ z))
            y = v[0] = (v[0] - mx) & 0xffffffff
            soma = (soma - delta) & 0xffffffff
            
        texto_limpo = estruturador.pack(f'<{n}I', *v)
        tamanho = v[-1]
        return texto_limpo[:tamanho] if 0 < tamanho <= n * 4 else texto_limpo.rstrip(b'\x00')

    @staticmethod
    def _verificar_cabecalho(bytes_arquivo: bytes) -> Optional[bytes]:
        # Verificando a etiqueta na frente do pacote.
        if not bytes_arquivo[:5] == b"\x00\x03ehi":
            return bytes_arquivo

        try:
            f = io.BytesIO(bytes_arquivo)
            
            def ler_utf() -> str:
                if len(l_bytes := f.read(2)) < 2: return ""
                return f.read(estruturador.unpack('>H', l_bytes)[0]).decode('utf-8', errors='ignore')
            
            ler_utf(); f.read(8); ler_utf(); f.read(8)
            if len(bytes_tamanho_payload := f.read(4)) < 4: 
                return None
            
            tamanho_payload = estruturador.unpack('>I', bytes_tamanho_payload)[0]
            f.read(8)
            return f.read(tamanho_payload)
        except estruturador.error:
            return None

    @staticmethod
    def _forjar_chave_mestra(config: Dict[str, Any]) -> bytes:
        # Ele recicla os dados da própria vítima para montar a fechadura. Astuto, mas preguiçoso.
        payload = "".join(str(p) for p in (
            config.get("configAesKey", ""),           
            config.get("configIdentifier", ""),       
            config.get("configSalt", ""),     
            str(config.get("configTimestamp", 0)),                                     
            str(config.get("configExpiryTimestamp", 0)),                             
            config.get("lockModes", ""),              
            config.get("lockModesHash", ""),          
            config.get("configHwid", ""),             
            config.get("configLockMobileOperatorId", "") 
        ) if p)
        return triturador_de_pistas.sha256(payload.encode('utf-8')).digest()

    @classmethod
    def executar(cls, bytes_arquivo: bytes) -> Optional[str]:
        resultado, _estatisticas = cls.executar_com_relatorio(bytes_arquivo)
        return resultado

    @classmethod
    def executar_com_relatorio(cls, bytes_arquivo: bytes) -> "tuple[Optional[str], Dict[str, Any]]":
        # A sala de interrogatório oficial. Nós desmontamos as mentiras e anotamos tudo o que acontece.
        estatisticas: Dict[str, Any] = {
            "ok": False,
            "motivo_falha": None,
            "modo": None,
            "campos_raiz_total": 0,
            "campos_raiz_decodificados": 0,
            "campos_json_aninhados": [],
            "erros_parsing_aninhado": [],
        }

        if not ARGON2_DISPONIVEL:
            estatisticas["motivo_falha"] = "biblioteca argon2-cffi ausente"
            return None, estatisticas

        payload = cls._verificar_cabecalho(bytes_arquivo)
        if not payload:
            estatisticas["motivo_falha"] = "cabecalho do .ehi nao pode ser lido (arquivo truncado ou formato desconhecido)"
            return None, estatisticas

        configuracao, iv_encontrado = None, None

        for iv in ConstantesDoAlvo.IVS_ATALHO + ConstantesDoAlvo.IVS_PADRAO:
            with contextlib.suppress(Exception):
                c1 = AES.new(ConstantesDoAlvo.CHAVE_L1, AES.MODE_CBC, iv)
                texto_l1 = unpad(c1.decrypt(payload), 16).decode('utf-8')

                if (partes := texto_l1.split(":")) and len(partes) >= 3:
                    c2 = AES.new(ConstantesDoAlvo.CHAVE_L2_ESTATICA, AES.MODE_CBC, mascara_comum.b64decode(partes[0]))
                    sujeira = unpad(c2.decrypt(mascara_comum.b64decode(partes[2])), 16)

                    cru_final = cls._desmontar_xxtea(sujeira, ConstantesDoAlvo.CHAVE_MESTRA_EOO)
                    if (inicio := cru_final.find(b'{')) != -1:
                        configuracao_candidata = cls._forcar_leitura_json(cru_final[inicio:].decode('utf-8', errors='ignore'))
                        if isinstance(configuracao_candidata, dict):
                            configuracao = configuracao_candidata
                            iv_encontrado = iv
                            break 

        if not configuracao:
            estatisticas["motivo_falha"] = "nenhum IV de L1/L2 bateu (chave-mestra incompativel com este arquivo)"
            return None, estatisticas

        sal_alvo = configuracao.get('configSalt', "EVZJNI")

        if iv_encontrado in ConstantesDoAlvo.IVS_ATALHO:
            final_analisado = configuracao
            estatisticas["modo"] = "bypass"
        else:
            estatisticas["modo"] = "camada_completa"
            dados_alvo = configuracao.get('configData')
            if not dados_alvo or not (resultado_aaa := cls._quebrar_camada_xor(dados_alvo, sal_alvo)):
                estatisticas["motivo_falha"] = "camada XOR de configData falhou (salt incompativel ou campo ausente)"
                return None, estatisticas

            payload_cru = mascara_comum.b64decode(resultado_aaa)
            if len(payload_cru) <= 50:
                estatisticas["motivo_falha"] = "payload apos base64 curto demais para conter cabecalho argon2/chacha"
                return None, estatisticas

            try:
                # Onde o alvo finalmente percebe o medo e joga os cadeados pesados na porta, mas sem trocar o miolo da chave.
                chave_argon = hash_secret_raw(
                    secret=cls._forjar_chave_mestra(configuracao), 
                    salt=payload_cru[0x0a:0x1a], 
                    time_cost=int.from_bytes(payload_cru[1:5], "little"),
                    memory_cost=int.from_bytes(payload_cru[5:9], "little"), 
                    parallelism=payload_cru[9],
                    hash_len=32, 
                    type=Type.ID
                )

                cifra3 = ChaCha20_Poly1305.new(key=chave_argon, nonce=payload_cru[0x1a:0x32])
                cifra3.update(payload_cru[:0x1a])
                bytes_json_decifrados = cifra3.decrypt_and_verify(payload_cru[0x32:-16], payload_cru[-16:])
                final_candidato = cls._forcar_leitura_json(bytes_json_decifrados.decode('utf-8', errors='ignore'))
                if not isinstance(final_candidato, dict):
                    estatisticas["motivo_falha"] = "ChaCha20-Poly1305 decodificou, mas conteudo final nao e um JSON valido"
                    return None, estatisticas
                final_analisado = final_candidato
            except Exception as desculpa:
                estatisticas["motivo_falha"] = f"falha no Argon2/ChaCha20-Poly1305: {desculpa}"
                return None, estatisticas

        estatisticas["campos_raiz_total"] = len(final_analisado)
        json_final_limpo = cls._vasculhar_gavetas_internas(final_analisado, sal_alvo)
        estatisticas["campos_raiz_decodificados"] = sum(
            1 for k, v in final_analisado.items()
            if isinstance(v, str) and v.strip() and json_final_limpo.get(k) != v
        )

        for campo_json in ("v2rRawJson", "overwriteServerData"):
            if campo_json in json_final_limpo and isinstance(string_crua := json_final_limpo[campo_json], str):
                if not string_crua.strip():
                    continue

                objeto_analisado = cls._forcar_leitura_json(string_crua)
                if isinstance(objeto_analisado, (dict, list)):
                    json_final_limpo[campo_json] = objeto_analisado
                    estatisticas["campos_json_aninhados"].append(campo_json)
                else:
                    json_final_limpo[f"{campo_json}_PARSING_ERROR"] = "conteudo nao e um objeto/lista JSON valido apos limpeza"
                    estatisticas["erros_parsing_aninhado"].append(campo_json)

        json_final_limpo = cls._interrogatorio_profundo(json_final_limpo, sal_alvo)

        estatisticas["ok"] = True
        return (
            f"{relatorio_final.dumps(json_final_limpo, indent=4, ensure_ascii=False)}"
        ), estatisticas


def executar(bytes_arquivo: bytes) -> Optional[str]:
    return InterrogadorEHI.executar(bytes_arquivo)


if __name__ == "__main__":
    arquivos_ehi = sorted(glob.glob("*.ehi"))
    nome_relatorio = "ehi_decoder_log.txt"

    if not arquivos_ehi:
        print("A cena está vazia. Nenhum arquivo .ehi encontrado por aqui.")
        with open(nome_relatorio, "w", encoding="utf-8") as arquivo_log:
            arquivo_log.write(
                f"=== Registro de interrogatório EHI ===\n"
                f"Momento: {datetime.datetime.now().isoformat(timespec='seconds')}\n"
                f"Nenhum arquivo .ehi encontrado neste diretório.\n"
            )
    else:
        linhas_relatorio = []
        total_resolvidos = 0
        total_fugas = 0

        for caminho_arquivo in arquivos_ehi:
            linhas_relatorio.append(f"--- {caminho_arquivo} ---")
            try:
                with open(caminho_arquivo, "rb") as f:
                    bytes_arquivo = f.read()

                resultado, estatisticas = InterrogadorEHI.executar_com_relatorio(bytes_arquivo)

                if resultado:
                    arquivo_saida = f"{caminho_arquivo}.txt"

                    with open(arquivo_saida, "w", encoding="utf-8") as arquivo_fora:
                        arquivo_fora.write(resultado)

                    total_resolvidos += 1
                    print(f"Confissão extraída: {caminho_arquivo} -> {arquivo_saida}")

                    linhas_relatorio.append("Veredito: máscara caída")
                    linhas_relatorio.append(f"Destino: {arquivo_saida}")
                    linhas_relatorio.append(f"Peso original da mentira: {len(bytes_arquivo)} bytes")
                    linhas_relatorio.append(f"Tática do alvo detectada: {estatisticas['modo']}")
                    linhas_relatorio.append(f"Camadas na raiz do problema: {estatisticas['campos_raiz_total']}")
                    linhas_relatorio.append(f"Segredos quebrados na raiz: {estatisticas['campos_raiz_decodificados']}")

                    if estatisticas["campos_json_aninhados"]:
                        linhas_relatorio.append(f"Mentiras embutidas descobertas: {', '.join(estatisticas['campos_json_aninhados'])}")
                    else:
                        linhas_relatorio.append("Mentiras embutidas descobertas: nenhuma")

                    if estatisticas["erros_parsing_aninhado"]:
                        linhas_relatorio.append(f"AVISO - O alvo surtou nesses pontos corrompidos: {', '.join(estatisticas['erros_parsing_aninhado'])}")
                else:
                    total_fugas += 1
                    print(f"O suspeito permaneceu calado: {caminho_arquivo}")
                    linhas_relatorio.append("Veredito: fuga")
                    linhas_relatorio.append(f"Desculpa dada: {estatisticas['motivo_falha']}")

            except Exception as desculpa_inesperada:
                total_fugas += 1
                print(f"O alvo explodiu sob pressão em {caminho_arquivo}: {desculpa_inesperada}")
                linhas_relatorio.append("Veredito: colapso emocional")
                linhas_relatorio.append(f"Detalhe: {desculpa_inesperada}")

            linhas_relatorio.append("")

        cabecalho = [
            "=== Registro de interrogatório EHI ===",
            f"Momento: {datetime.datetime.now().isoformat(timespec='seconds')}",
            f"Alvos investigados: {len(arquivos_ehi)}",
            f"Desmascarados: {total_resolvidos}",
            f"Escaparam ilesos: {total_fugas}",
            "",
        ]

        with open(nome_relatorio, "w", encoding="utf-8") as arquivo_log:
            arquivo_log.write("\n".join(cabecalho + linhas_relatorio))

        print(f"\nFichamento concluído em: {nome_relatorio}")
