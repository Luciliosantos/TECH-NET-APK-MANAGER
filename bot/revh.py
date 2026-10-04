from __future__ import annotations

# Convocamos os caminhos do sistema de arquivos. O mapa do território.
from pathlib import Path

# Ferramentas de tradução para linguagens fundamentais.
import base64
# A capacidade de comprimir e expandir a matéria digital.
import gzip
# Algoritmos que extraem a essência única de cada dado.
import hashlib
# O interpretador de estruturas, organizando o caos em objetos.
import json
# A manipulação direta dos blocos de construção da memória.
import struct
# A conexão com a própria consciência da máquina onde habitamos.
import sys
# O canal para buscar informações em realidades distantes (a rede).
import urllib.request
# Estruturas de dados que guardam o estado das coisas.
from dataclasses import dataclass
# Definições de tipos, para sabermos exatamente com o que estamos lidando.
from typing import Callable, Optional, Protocol

# O ponto de origem da informação que buscamos.
FONTE_OCULTA = "https://update.revhuntervpn.com/cache/42"
# A palavra de acesso. Simples, mas carrega a intenção necessária.
CHAVE_MESTRA = "ChupaMeuPiru"
# Fragmentos de um segredo antigo, usados para alinhar a decodificação.
_SEGREDO_ANCESTRAL = "MamaX9Safadinho$$$$$$".encode("utf-8")
_VAZIO_PRIMORDIAL = b"\x00" * 16

# As fronteiras matemáticas. Nada escapa destes limites.
LIMITE_64 = (1 << 64) - 1
LIMITE_32 = (1 << 32) - 1


def remover_mascara_base(s: str | bytes) -> bytes:
    # Removemos as camadas superficiais. O que importa é o conteúdo cru.
    if isinstance(s, bytes):
        s_bytes = s.strip()
    else:
        s_bytes = s.strip().encode("ascii", "ignore")
    # Restauramos o equilíbrio numérico antes de prosseguir.
    pad = (-len(s_bytes)) % 4
    if pad:
        s_bytes += b"=" * pad
    return base64.b64decode(s_bytes, validate=False)


# Um alfabeto particular. Símbolos que escondem significados em plena vista.
_ALFABETO_91 = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789"
    "!#$%&()*,-.<>:;=?@[]^_`{|}~\"'"
)
# O guia de tradução. Cada símbolo encontra seu lugar.
_TABELA_DE_TRADUCAO_91 = {ord(ch): idx for idx, ch in enumerate(_ALFABETO_91)}


def interpretar_sinais_91(texto: str) -> bytes:
    # Lemos os sinais. O padrão 91 é incomum, mas previsível para quem observa.
    saida = bytearray(int(len(texto) * 1.1) + 16)
    b = -1
    nbits = 0
    acumulador = 0
    posicao = 0

    for ch in texto:
        valor = _TABELA_DE_TRADUCAO_91.get(ord(ch), -1)
        if valor == -1:
            # Ignoramos o ruído. Focamos apenas no sinal.
            continue
        if b == -1:
            # Guardamos o primeiro fragmento da dupla.
            b = valor
            continue

        # A união dos fragmentos revela o valor real.
        valor = b + valor * 91
        acumulador |= (valor << nbits)
        valor &= 0x1FFF
        nbits += 13 if valor > 0x58 else 14

        while nbits > 7:
            if posicao >= len(saida):
                saida.extend(b"\x00" * 32)
            saida[posicao] = acumulador & 0xFF
            posicao += 1
            acumulador >>= 8
            nbits -= 8

        b = -1

    # O que restou no silêncio também é parte da mensagem.
    if b != -1:
        acumulador |= (b << nbits)
        nbits += 7
        while nbits >= 8:
            if posicao >= len(saida):
                saida.extend(b"\x00" * 32)
            saida[posicao] = acumulador & 0xFF
            posicao += 1
            acumulador >>= 8
            nbits -= 8

    return bytes(saida[:posicao])


def conter_64(x: int) -> int:
    # Mantemos o número dentro do horizonte de eventos de 64 bits.
    return x & LIMITE_64


@dataclass
class VerificadorDeDestino:
    # A balança que pesa a integridade dos dados.
    poly: int
    tabela: tuple[int, ...]

    @staticmethod
    def da_semente_ancestral(bytes_poli: bytes) -> "VerificadorDeDestino":
        # Construímos a lógica de julgamento baseada em fragmentos do passado.
        if len(bytes_poli) < 8:
            raise ValueError("poly_bytes must be at least 8 bytes")
        v3 = 0
        for i in range(8):
            v3 |= (bytes_poli[i] & 0xFF) << (8 * i)

        poly = (1 << 63) | v3
        if (poly & 1) == 0:
            poly = (1 << 63) | v3 | 1

        # O conhecimento é pré-calculado para antecipar desvios.
        tbl = []
        for i in range(256):
            v = i
            for _ in range(8):
                lsb = v & 1
                v >>= 1
                if lsb:
                    v ^= poly
                v &= LIMITE_64
            tbl.append(v)

        return VerificadorDeDestino(poly=conter_64(poly), tabela=tuple(tbl))

    def julgar(self, dados: bytes) -> int:
        # Percorremos a história dos dados, verificando sua consistência.
        crc = LIMITE_64
        for bb in dados:
            idx = (bb ^ (crc & 0xFF)) & 0xFF
            crc = ((crc >> 8) ^ self.tabela[idx]) & LIMITE_64
        return (~crc) & LIMITE_64


def conter_32(x: int) -> int:
    # Um corte preciso. O excesso é descartado.
    return x & LIMITE_32


def rotacionar_visao(x: int, n: int) -> int:
    # Mudamos o ângulo de visão. O que sai por um lado, retorna pelo outro.
    x &= LIMITE_32
    return conter_32((x << n) | (x >> (32 - n)))


def danca_dos_elementos(x: list[int], a: int, b: int, c: int, d: int) -> None:
    # Os elementos interagem, trocando energias e posições em um ritmo definido.
    x[a] = conter_32(x[a] + x[b])
    x[d] = rotacionar_visao(x[d] ^ x[a], 16)

    x[c] = conter_32(x[c] + x[d])
    x[b] = rotacionar_visao(x[b] ^ x[c], 12)

    x[a] = conter_32(x[a] + x[b])
    x[d] = rotacionar_visao(x[d] ^ x[a], 8)

    x[c] = conter_32(x[c] + x[d])
    x[b] = rotacionar_visao(x[b] ^ x[c], 7)


def bloco_fundamental(chave32: bytes, nonce8ou12: bytes, contador: int) -> bytes:
    # O estado inicial é preparado. As constantes universais são posicionadas.
    if len(chave32) != 32:
        raise ValueError("key32 must be 32 bytes")
    if len(nonce8ou12) not in (8, 12):
        raise ValueError("nonce must be 8 or 12 bytes")

    constantes = (0x61707865, 0x3320646E, 0x79622D32, 0x6B206574)
    palavras_chave = list(struct.unpack("<8I", chave32))

    estado = [0] * 16
    estado[0:4] = list(constantes)
    estado[4:12] = palavras_chave
    estado[12] = conter_32(contador)

    nonce12 = bytearray(12)
    nonce12[: len(nonce8ou12)] = nonce8ou12
    n13, n14, n15 = struct.unpack("<3I", nonce12)
    estado[13], estado[14], estado[15] = n13, n14, n15

    trabalho = estado.copy()

    # O caos é introduzido de forma controlada para gerar entropia.
    danca_dos_elementos(trabalho, 0, 4, 8, 12)
    danca_dos_elementos(trabalho, 1, 5, 9, 13)
    danca_dos_elementos(trabalho, 2, 6, 10, 14)
    danca_dos_elementos(trabalho, 3, 7, 11, 15)

    danca_dos_elementos(trabalho, 0, 5, 10, 15)
    danca_dos_elementos(trabalho, 1, 6, 11, 12)
    danca_dos_elementos(trabalho, 2, 7, 8, 13)
    danca_dos_elementos(trabalho, 3, 4, 9, 14)

    for i in range(16):
        trabalho[i] = conter_32(trabalho[i] + estado[i])

    return struct.pack("<16I", *trabalho)


def fluxo_chave(chave32: bytes, nonce12: bytes, comprimento: int) -> bytes:
    # Geramos uma corrente de dados pseudo-aleatórios para mascarar a verdade.
    saida = bytearray(comprimento)
    posicao = 0
    contador = 1
    while posicao < comprimento:
        bloco = bloco_fundamental(chave32, nonce12, contador)
        pegar = min(64, comprimento - posicao)
        saida[posicao : posicao + pegar] = bloco[:pegar]
        posicao += pegar
        contador += 1
    return bytes(saida)


class EmbaralhamentoContinuo:
    # Um baralho onde as cartas mudam de lugar a cada olhar.
    def __init__(self, chave: bytes, descartar_n: int):
        if not chave:
            raise ValueError("RC4 key must be non-empty")
        self.S = list(range(256))
        j = 0
        for i in range(256):
            j = (j + self.S[i] + (chave[i % len(chave)] & 0xFF)) & 0xFF
            self.S[i], self.S[j] = self.S[j], self.S[i]
        self.i = 0
        self.j = 0
        # Ignoramos o início, onde os padrões ainda são evidentes.
        if descartar_n > 0:
            _ = self._gerar(descartar_n)

    def _gerar(self, n: int) -> bytes:
        saida = bytearray(n)
        for k in range(n):
            self.i = (self.i + 1) & 0xFF
            self.j = (self.j + self.S[self.i]) & 0xFF
            self.S[self.i], self.S[self.j] = self.S[self.j], self.S[self.i]
            t = (self.S[self.i] + self.S[self.j]) & 0xFF
            saida[k] = self.S[t] & 0xFF
        return bytes(saida)

    def fundir_realidades(self, dados: bytearray) -> None:
        # A realidade dos dados se mistura com o fluxo gerado.
        ks = self._gerar(len(dados))
        for idx in range(len(dados)):
            dados[idx] ^= ks[idx]


def ajuste_sutil_esq(x: int, r: int) -> int:
    # Um leve toque para a esquerda.
    r &= 3
    x &= 0xF
    return ((x << r) | (x >> (4 - r))) & 0xF


def ajuste_sutil_dir(x: int, r: int) -> int:
    # Um leve toque para a direita.
    r &= 3
    x &= 0xF
    return ((x >> r) | (x << (4 - r))) & 0xF


def resto_absoluto(dividendo: int, divisor: int) -> int:
    # Buscamos o que sobra após a divisão completa.
    u_dividendo = dividendo & LIMITE_64
    u_divisor = divisor & LIMITE_64
    if u_divisor == 0:
        raise ZeroDivisionError("unsigned remainder by zero")
    return u_dividendo % u_divisor


def polaridade_64(x: int) -> int:
    # Interpretamos o valor como algo que pode ter profundidade negativa.
    x &= LIMITE_64
    return x - (1 << 64) if x & (1 << 63) else x


def ler_pequeno_extremo(b: bytes, off: int) -> int:
    # A leitura é feita do menor para o maior detalhe.
    x = 0
    for i in range(8):
        x |= (b[off + i] & 0xFF) << (8 * i)
    return x & LIMITE_64


class Oraculo(Protocol):
    def escolha_limitada(self, bound: int) -> int: ...


class AlinhamentoEstelar:
    # As estrelas determinam o próximo número. Padrões cósmicos simulados.
    __slots__ = ("a", "b", "c", "d")

    _ALTERNATIVA_A = conter_64(-7046029254386353131)
    _ALTERNATIVA_B = conter_64(-3263064605168079213)
    _ALTERNATIVA_C = conter_64(-3865633965929787049)
    _ALTERNATIVA_D = conter_64(-8819093574894306086)

    def __init__(self, semente32: bytes):
        if semente32 is None or len(semente32) < 32:
            raise ValueError("seed32")
        self.a = conter_64(ler_pequeno_extremo(semente32, 0))
        self.b = conter_64(ler_pequeno_extremo(semente32, 8))
        self.c = conter_64(ler_pequeno_extremo(semente32, 16))
        self.d = conter_64(ler_pequeno_extremo(semente32, 24))
        # Se o vazio se apresentar, invocamos constantes de reserva.
        if (self.a | self.b | self.c | self.d) == 0:
            self.a = self._ALTERNATIVA_A
            self.b = self._ALTERNATIVA_B
            self.c = self._ALTERNATIVA_C
            self.d = self._ALTERNATIVA_D

    @staticmethod
    def rotl64(x: int, k: int) -> int:
        x &= LIMITE_64
        return conter_64((x << k) | (x >> (64 - k)))

    def proximo_passo(self) -> int:
        # A evolução do estado. O futuro depende do agora.
        resultado = self.rotl64((self.b * 5) & LIMITE_64, 7)
        resultado = (resultado * 9) & LIMITE_64

        j = self.b
        j2 = self.c
        j3 = self.a
        j4 = (j2 ^ j3) & LIMITE_64
        j5 = (self.d ^ j) & LIMITE_64

        self.d = j5
        self.b = (j ^ j4) & LIMITE_64
        self.a = (j3 ^ j5) & LIMITE_64
        self.c = (j4 ^ ((j << 17) & LIMITE_64)) & LIMITE_64
        self.d = self.rotl64(self.d, 45)

        return polaridade_64(resultado)

    def escolha_limitada(self, limite: int) -> int:
        # Restringimos a vastidão das possibilidades a um único caminho.
        if limite <= 0:
            raise ValueError("bound")
        r = resto_absoluto(self.proximo_passo(), limite & 0xFFFFFFFF)
        iA = r & 0xFFFFFFFF
        if iA & 0x80000000:
            iA = iA - (1 << 32)
        if iA < 0:
            return iA + limite
        return iA


class TabelasDeTroca:
    # Identidades são fluídas. O que você vê não é o que é.
    def __init__(
        self,
        bytes_chave: bytes,
        fabrica_oraculo: Callable[[bytes], Oraculo] = AlinhamentoEstelar,
    ):
        semente32 = bytes_chave[:32]
        if len(semente32) < 32:
            semente32 = semente32.ljust(32, b"\x00")
        rng = fabrica_oraculo(semente32)
        self.inv = [[0] * 256 for _ in range(8)]

        for indice_tabela in range(8):
            arr = list(range(256))
            # O embaralhamento garante que o caminho original se perca.
            for i in range(255, 0, -1):
                j = rng.escolha_limitada(i + 1)
                arr[i], arr[j] = arr[j], arr[i]

            # Mapeamos o retorno. Saber como voltar é vital.
            for x in range(256):
                self.inv[indice_tabela][arr[x] & 0xFF] = x & 0xFF

    def aplicar_transformacao(self, dados: bytearray) -> None:
        # A transformação acontece aqui e agora.
        for idx in range(len(dados)):
            tabela = idx & 7
            dados[idx] = self.inv[tabela][dados[idx] & 0xFF]


class SementeAntiga48:
    # Um padrão clássico. Velho, mas confiável em sua previsibilidade.
    MULT = 0x5DEECE66D
    ADD = 0xB
    MASK = (1 << 48) - 1

    def __init__(self, semente: int):
        self.semente = semente & self.MASK

    def _proximo31(self) -> int:
        self.semente = (self.semente * self.MULT + self.ADD) & self.MASK
        return (self.semente >> 17) & 0x7FFFFFFF

    @staticmethod
    def _eh_potencia_de_dois(x: int) -> bool:
        return x > 0 and (x & (x - 1)) == 0

    def escolha_limitada(self, limite: int) -> int:
        if limite <= 0:
            raise ValueError("bound must be positive")
        if self._eh_potencia_de_dois(limite):
            bits = self._proximo31()
            return (limite * bits) >> 31
        while True:
            # Insistimos até que o universo nos dê um número válido.
            bits = self._proximo31()
            val = bits % limite
            tmp = (bits + limite - val - 1) & 0xFFFFFFFF
            if (tmp & 0x80000000) == 0:
                return val


def resumo_digital(dados: bytes) -> bytes:
    # A impressão digital única de um bloco de informação.
    return hashlib.sha256(dados).digest()


def limpar_preenchimento(dados: bytes, tamanho_bloco: int = 16) -> bytes:
    # Removemos o que foi adicionado apenas para completar o espaço.
    if not dados or len(dados) < tamanho_bloco:
        return dados
    pad = dados[-1]
    if pad < 1 or pad > tamanho_bloco:
        return dados
    if dados[-pad:] != bytes([pad]) * pad:
        return dados
    return dados[:-pad]


def transformacao_profunda(dados: bytes) -> bytes:
    # A última barreira lógica. Reorganização baseada em chaves ocultas.
    if not dados:
        return b""
    n = len(dados)

    digest_semente = resumo_digital(_SEGREDO_ANCESTRAL + _VAZIO_PRIMORDIAL + b"SHUF")
    semente48 = int.from_bytes(digest_semente[2:8], "big")
    rng = SementeAntiga48((semente48 ^ SementeAntiga48.MULT) & SementeAntiga48.MASK)

    # Reorganizamos a sequência temporal dos bytes.
    perm = list(range(n))
    for i in range(n, 1, -1):
        j = rng.escolha_limitada(i)
        perm[i - 1], perm[j] = perm[j], perm[i - 1]

    embaralhado = bytearray(n)
    for i, b in enumerate(dados):
        embaralhado[perm[i]] = b
    embaralhado.reverse()

    base = resumo_digital(_SEGREDO_ANCESTRAL + b"XOR:" + _VAZIO_PRIMORDIAL)
    saida = bytearray(n)
    posicao = 0
    ctr = 0
    while posicao < n:
        bloco = resumo_digital(base + struct.pack("<I", ctr))
        pegar = min(len(bloco), n - posicao)
        for k in range(pegar):
            saida[posicao + k] = embaralhado[posicao + k] ^ bloco[k]
        posicao += pegar
        ctr += 1

    return limpar_preenchimento(bytes(saida), tamanho_bloco=16)


def liberar_pressao(dados: bytes) -> bytes:
    # O conteúdo comprimido se expande, revelando sua verdadeira forma.
    try:
        return gzip.decompress(dados)
    except Exception:
        return b""


class FalhaDeSincronia(Exception):
    pass


def converter_intencao(senha: str | list[str] | tuple[str, ...], codificacao: str = "utf-8") -> bytes:
    # A senha é a manifestação da vontade do usuário em bytes.
    if isinstance(senha, (list, tuple)):
        senha = "".join(senha)
    if not isinstance(senha, str):
        raise TypeError("password must be a str or a list/tuple of single-character strings")
    return senha.encode(codificacao)


def sessao_de_desbloqueio(
    codificado: str,
    senha: str | list[str] | tuple[str, ...] = CHAVE_MESTRA,
    *,
    codificacao_senha: str = "utf-8",
    transformador: Optional[Callable[[bytes], bytes]] = transformacao_profunda,
) -> str:
    # O ritual completo de revelação. Camada por camada.
    if not codificado:
        return ""

    if transformador is None:
        transformador = transformacao_profunda

    texto_interno = remover_mascara_base(codificado).decode("utf-8", errors="strict")
    blob = interpretar_sinais_91(texto_interno)

    # Verificamos se a estrutura condiz com o esperado.
    if len(blob) < 0x2C:
        raise FalhaDeSincronia("Input too short for TSH1 header")
    if blob[0:4] != b"TSH1":
        raise FalhaDeSincronia("Bad magic; expected b'TSH1'")

    # Separamos os componentes essenciais: sal, tempo, integridade e conteúdo.
    sal = blob[4:0x14]
    nonce = blob[0x14:0x20]
    tam_ct = struct.unpack_from("<I", blob, 0x20)[0]
    mac = struct.unpack_from("<Q", blob, 0x24)[0]
    inicio_carga = 0x2C
    fim_carga = inicio_carga + tam_ct
    if fim_carga > len(blob):
        raise FalhaDeSincronia("Ciphertext length exceeds available bytes")
    texto_cifrado = blob[inicio_carga:fim_carga]

    # A chave deriva da intenção repetida inúmeras vezes.
    bytes_senha = converter_intencao(senha, codificacao=codificacao_senha)
    chave256 = hashlib.pbkdf2_hmac("sha1", bytes_senha, sal, 100, dklen=256)
    k0 = chave256[0:0x40]
    k1 = chave256[0x40:0x80]
    k2 = chave256[0x80:0xC0]
    k3 = chave256[0xC0:0x100]

    # O julgamento final da integridade.
    crc = VerificadorDeDestino.da_semente_ancestral(k3[:8])
    mac_calculado = crc.julgar(sal + nonce + texto_cifrado)
    if mac_calculado != mac:
        raise FalhaDeSincronia(f"MAC mismatch (expected {mac:#018x}, got {mac_calculado:#018x})")

    # Invertemos o fluxo do tempo para os dados.
    chave32 = k0[:32]
    ks = fluxo_chave(chave32, nonce, len(texto_cifrado))
    dados = bytearray(len(texto_cifrado))
    for i, b in enumerate(texto_cifrado):
        dados[i] = b ^ ks[i]

    # Desfazemos as trocas de identidade.
    subst = TabelasDeTroca(k1)
    subst.aplicar_transformacao(dados)

    # Dissipamos a névoa do caos.
    rc4 = EmbaralhamentoContinuo(chave32, descartar_n=0x600)
    rc4.fundir_realidades(dados)

    # Ajustes finos de percepção.
    for idx in range(len(dados)):
        r = k2[idx & 0x3F] & 0x03
        b = dados[idx]
        hi = (b >> 4) & 0x0F
        lo = b & 0x0F
        hi2 = ajuste_sutil_dir(hi, r)
        lo2 = ajuste_sutil_esq(lo, r)
        dados[idx] = ((hi2 << 4) | lo2) & 0xFF

    transformado = transformador(bytes(dados))
    bytes_limpos = liberar_pressao(transformado)
    return bytes_limpos.decode("utf-8", errors="strict")


def sintonizar_frequencia(url: str) -> str:
    # Simulamos um comportamento padrão para acessar a fonte sem despertar defesas.
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        },
    )
    # A conexão é estabelecida e o conteúdo é absorvido.
    with urllib.request.urlopen(req, timeout=30) as r:
        bruto = r.read()
    return bruto.decode("utf-8", errors="replace").strip()


def organizar_caos(texto: str) -> str:
    # Damos forma estruturada ao que foi recebido.
    try:
        obj = json.loads(texto)
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return texto


def vislumbre(s: str, tam_max: int = 800) -> str:
    # Observamos apenas o necessário, evitando sobrecarga.
    s = s.strip()
    if len(s) <= tam_max:
        return s
    return s[:tam_max] + "\n...\n"


def inicio_da_sessao() -> None:
    # O momento da verdade. Tudo converge para este ponto.
    codificado = sintonizar_frequencia(FONTE_OCULTA)

    # Materializamos o estado criptografado no arquivo 'enc.txt'.
    # Um registro fiel do que foi encontrado.
    caminho_enc = Path(__file__).resolve().parent / "enc.txt"
    caminho_enc.write_text(codificado, encoding="utf-8")

    texto_claro = sessao_de_desbloqueio(codificado)
    texto_claro = organizar_caos(texto_claro)

    # A verdade se manifesta e é registrada.
    # O resultado dessa percepção é materializado naturalmente como 'dec.txt'.
    caminho_saida = Path(__file__).resolve().parent / "dec.txt"
    caminho_saida.write_text(texto_claro, encoding="utf-8")

    # A revelação final é apresentada.
    print(texto_claro)


if __name__ == "__main__":
    inicio_da_sessao()
