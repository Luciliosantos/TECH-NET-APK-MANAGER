# Comentário: Importa o módulo 'os' para interagir com o sistema operacional,
# como manipulação de nomes de arquivo, caminhos e diretórios.
import os
# Comentário: Importa o módulo 're' para trabalhar com expressões regulares,
# que são usadas para encontrar padrões em strings (ex: nomes de arquivo .log e esquemas URI).
import re
# Comentário: Importa o módulo 'base64' para codificar e decodificar dados no formato Base64.
# Usado especificamente na Fase 2 para decodificar configurações.
import base64

# --- Configurações Globais para o Script Combinado ---
# Comentário: Define o nome padrão para o arquivo intermediário.
# Este arquivo é gerado pela Fase 1 e consumido pela Fase 2.
NOME_ARQUIVO_INTERMEDIARIO = "y.txt"
# Comentário: Define o nome padrão para o arquivo de saída final.
# Este arquivo é gerado pela Fase 2 e contém o resultado do processo de decodificação.
NOME_ARQUIVO_SAIDA_FINAL = "z.txt"
# Comentário: Lista das chaves específicas cujos valores associados (em Base64)
# devem ser procurados e decodificados durante a Fase 2.
CHAVES_ALVO_FASE2 = ["config_openvpn", "config_v2ray"]
# Comentário: Número máximo de vezes que a Fase 2 reprocessará o arquivo de saída inteiro
# em busca de novas decodificações que possam ter surgido de decodificações anteriores.
MAX_REPASSES_ARQUIVO_FASE2 = 3


# --- Variáveis Globais para Uso no Script ---
# Comentário: Dicionário global para a Fase 2. Armazena a contagem de quantas vezes
# o valor de cada chave alvo foi processado e decodificado com sucesso (considerando a decodificação inicial).
# Exemplo: {"config_openvpn": 2, "config_v2ray": 1}
# É reiniciado toda vez que a Fase 2 começa.
g_processed_counts_fase2 = {}
# Comentário: Variável global para a Fase 2. Indica qual das 'CHAVES_ALVO_FASE2'
# está sendo processada no momento pela função de callback do 're.sub'.
# Isso permite que a função de callback saiba qual contador em 'g_processed_counts_fase2' incrementar.
g_current_key_fase2 = None
# Comentário: Variável global para armazenar o caminho absoluto do diretório onde o script
# está sendo executado. É definida uma vez para ser usada por ambas as fases,
# garantindo consistência nos caminhos dos arquivos.
g_script_dir = None


# --- Lógica da Fase 1: Extrair conteúdo do .log para o arquivo intermediário ---
def executar_fase1_extrair_conteudo_log(nome_arquivo_saida_fase1):
    """
    Comentário: Esta função encapsula toda a lógica da primeira etapa do processo.
    Responsabilidades:
    1. Identificar e selecionar dinamicamente um arquivo de log (com extensão '.log' e nome numérico)
       localizado no mesmo diretório do script.
    2. Ler o conteúdo completo do arquivo de log selecionado.
    3. Procurar pela última ocorrência de um bloco de texto específico, delimitado por
       '[{"id":' (marcador de início) e '}}]' (marcador de fim).
    4. Extrair este bloco de texto.
    5. Salvar o bloco extraído em um arquivo intermediário (ex: "y.txt").

    Args:
        nome_arquivo_saida_fase1 (str): O nome do arquivo onde o conteúdo extraído será salvo.

    Returns:
        bool: True se a Fase 1 for concluída com sucesso (arquivo intermediário criado),
              False caso contrário (se ocorrer qualquer erro ou o bloco não for encontrado/salvo).
    """
    # Comentário: Acessa a variável global 'g_script_dir' para usar o caminho do diretório do script.
    global g_script_dir
    
    input_log_filename_fase1 = None
    
    if g_script_dir is None:
        try:
            g_script_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            g_script_dir = os.getcwd()
            print(f"AVISO (Fase 1): A variável '__file__' não está definida. "
                  f"Usando o diretório de trabalho atual como base: {g_script_dir}")

    try:
        log_files_found = []
        log_file_pattern = re.compile(r"^\d{15,20}\.log$")
        print(f"Info (Fase 1): Procurando por arquivos .log no diretório: {g_script_dir}")
        for f_name in os.listdir(g_script_dir):
            if log_file_pattern.match(f_name):
                log_files_found.append(f_name)
        
        if not log_files_found:
            print(f"ERRO (Fase 1): Nenhum arquivo .log com nome numérico (ex: 123...789.log) foi encontrado em '{g_script_dir}'.")
            return False
        elif len(log_files_found) == 1:
            input_log_filename_fase1 = log_files_found[0]
            print(f"Info (Fase 1): Arquivo .log encontrado para processamento: {os.path.join(g_script_dir, input_log_filename_fase1)}")
        else:
            log_files_found.sort(reverse=True) 
            input_log_filename_fase1 = log_files_found[0]
            print(f"Info (Fase 1): Múltiplos arquivos .log encontrados. Selecionado o mais recente (pelo nome): {os.path.join(g_script_dir, input_log_filename_fase1)}")
            if len(log_files_found) > 1:
                print(f"Info (Fase 1): Outros arquivos .log encontrados (não selecionados): {log_files_found[1:]}")
    except Exception as e:
        print(f"ERRO (Fase 1): Ocorreu um erro inesperado durante a busca pelo arquivo .log: {e}")
        return False
    
    if not input_log_filename_fase1:
        print("ERRO (Fase 1): Nenhum arquivo .log de entrada foi definido após a etapa de busca.")
        return False

    try:
        full_input_path_fase1 = os.path.join(g_script_dir, input_log_filename_fase1)
        print(f"Info (Fase 1): Lendo arquivo de entrada: {full_input_path_fase1}")
        with open(full_input_path_fase1, 'r', encoding='utf-8') as f:
            content = f.read()
        
        start_marker = r'[{"id":'
        end_marker = '}}]'
        
        num_starts = content.count(start_marker)
        num_ends = content.count(end_marker)
        
        print(f"Info (Fase 1): Número de ocorrências do marcador de início ('{start_marker}'): {num_starts}")
        print(f"Info (Fase 1): Número de ocorrências do marcador de fim ('{end_marker}'): {num_ends}")
        
        if num_starts > 0:
            pos_start = content.rfind(start_marker)
            if pos_start != -1:
                pos_end = content.find(end_marker, pos_start)
                if pos_end != -1:
                    captured_content = content[pos_start : pos_end + len(end_marker)]
                    full_output_path_fase1 = os.path.join(g_script_dir, nome_arquivo_saida_fase1)
                    print(f"Info (Fase 1): Salvando conteúdo capturado em: {full_output_path_fase1}")
                    with open(full_output_path_fase1, 'w', encoding='utf-8') as f_out:
                        f_out.write(captured_content)
                    print(f"Info (Fase 1): Conteúdo capturado e salvo com sucesso. Primeiros 100 caracteres: {captured_content[:100]}...")
                    return True
                else:
                    print(f"ERRO (Fase 1): Marcador de início encontrado no arquivo '{input_log_filename_fase1}', mas nenhum marcador de fim ('{end_marker}') correspondente foi encontrado após ele.")
            else:
                print("ERRO (Fase 1): Nenhum marcador de início foi encontrado via 'rfind', apesar da contagem inicial ser positiva (situação inesperada).")
        else:
            print(f"AVISO (Fase 1): Nenhum marcador de início ('{start_marker}') foi encontrado no arquivo '{input_log_filename_fase1}'. Nenhum conteúdo será extraído.")
        return False
    except FileNotFoundError:
        print(f"ERRO (Fase 1): O arquivo de entrada '{full_input_path_fase1}' não foi encontrado ou não pôde ser aberto.")
        return False
    except Exception as e:
        print(f"ERRO (Fase 1): Ocorreu um erro inesperado durante o processamento do arquivo '{input_log_filename_fase1}': {e}")
        return False

# --- Funções da Fase 2: Decodificar Base64 do arquivo intermediário ---
def _decode_and_replace_match_fase2(match_obj, line_number_for_error_reporting):
    """
    Comentário: Função de callback usada por 're.sub()' na Fase 2.
    Decodifica valores Base64, lidando com esquemas URI e múltiplas camadas de decodificação para chaves específicas.
    """
    global g_processed_counts_fase2
    global g_current_key_fase2

    key_and_opening_quote_part = match_obj.group(1) 
    original_json_value = match_obj.group(2)      
    closing_quote_part = match_obj.group(3)       

    current_value_being_processed = original_json_value 
    
    MAX_DECODE_ATTEMPTS_PER_VALUE = 3 
    attempts_count = 0
    first_successful_decode_for_this_instance = True 

    while attempts_count < MAX_DECODE_ATTEMPTS_PER_VALUE:
        attempts_count += 1
        
        string_payload_to_b64decode = current_value_being_processed 
        detected_uri_scheme = "" 

        keys_potentially_with_uri_schemes = ["config_v2ray"] 

        if g_current_key_fase2 in keys_potentially_with_uri_schemes:
            uri_match_obj = re.match(r"([a-zA-Z][a-zA-Z0-9+.-]*://)(.+)", current_value_being_processed, re.DOTALL)
            if uri_match_obj:
                detected_uri_scheme = uri_match_obj.group(1)      
                string_payload_to_b64decode = uri_match_obj.group(2)  
                # print(f"Debug (Fase 2 - Chave: {g_current_key_fase2}, Passe Interno: {attempts_count}): Esquema '{detected_uri_scheme}' separado. Tentando decodificar: '{string_payload_to_b64decode[:30]}...'")
        
        try:
            # print(f"Debug (Fase 2 - Chave: {g_current_key_fase2}, Passe Interno: {attempts_count}): Tentando b64decode em: '{string_payload_to_b64decode[:60]}'")
            decoded_bytes_payload = base64.b64decode(string_payload_to_b64decode)
            decoded_string_payload = decoded_bytes_payload.decode('utf-8')
            # print(f"Debug (Fase 2 - Chave: {g_current_key_fase2}, Passe Interno: {attempts_count}): Decodificado para: '{decoded_string_payload[:60]}'")

            if first_successful_decode_for_this_instance:
                if g_current_key_fase2 and g_current_key_fase2 in g_processed_counts_fase2:
                    g_processed_counts_fase2[g_current_key_fase2] += 1
                first_successful_decode_for_this_instance = False

            newly_processed_value = detected_uri_scheme + decoded_string_payload

            if newly_processed_value == current_value_being_processed:
                current_value_being_processed = newly_processed_value 
                # print(f"Debug (Fase 2 - Chave: {g_current_key_fase2}, Passe Interno: {attempts_count}): Valor não mudou após decodificação. Parando passes internos.")
                break 
            
            current_value_being_processed = newly_processed_value

            is_still_uri_formatted_for_relevant_key = False
            if g_current_key_fase2 in keys_potentially_with_uri_schemes:
                if re.match(r"([a-zA-Z][a-zA-Z0-9+.-]*://)(.+)", current_value_being_processed, re.DOTALL):
                    is_still_uri_formatted_for_relevant_key = True
            
            if not is_still_uri_formatted_for_relevant_key:
                # print(f"Debug (Fase 2 - Chave: {g_current_key_fase2}, Passe Interno: {attempts_count}): Resultado '{current_value_being_processed[:60]}' não parece ter mais esquema URI (ou chave não relevante para multi-camada URI). Parando passes internos.")
                break
            # else:
                # print(f"Debug (Fase 2 - Chave: {g_current_key_fase2}, Passe Interno: {attempts_count}): Resultado '{current_value_being_processed[:60]}' ainda tem esquema. Continuando passes internos (se limite permitir).")

        except (base64.binascii.Error, ValueError, UnicodeDecodeError) as e:
            if first_successful_decode_for_this_instance: 
                print(f"AVISO (Fase 2 - Passe Interno: {attempts_count}): Linha {line_number_for_error_reporting} (Chave: {g_current_key_fase2}): "
                      f"Falha ao decodificar (tentativa em: '{string_payload_to_b64decode[:30]}...'). "
                      f"Valor original JSON: '{original_json_value[:70]}...'. Erro: {e}. Mantendo original da chave.")
                return match_obj.group(0) 
            else:
                # print(f"Debug (Fase 2 - Chave: {g_current_key_fase2}, Passe Interno: {attempts_count}): Falha na decodificação de '{string_payload_to_b64decode[:30]}'. Usando resultado do passe interno anterior.")
                pass 
            break 
    
    return key_and_opening_quote_part + current_value_being_processed + closing_quote_part


def executar_fase2_decodificar_conteudo(nome_arquivo_entrada_fase2, nome_arquivo_saida_fase2, chaves_para_decodificar):
    """
    Comentário: Esta função encapsula toda a lógica da segunda etapa do processo, agora com múltiplos
    repasses sobre o conteúdo do arquivo para decodificações em cascata.
    """
    global g_processed_counts_fase2
    global g_current_key_fase2
    global g_script_dir 

    if g_script_dir is None:
        try:
            g_script_dir = os.path.dirname(os.path.abspath(__file__))
        except NameError:
            g_script_dir = os.getcwd()
            print(f"AVISO (Fase 2): A variável '__file__' não está definida. Usando o diretório de trabalho atual como base: {g_script_dir}")

    # Comentário: Contadores são resetados uma vez no início da Fase 2.
    # A flag 'first_successful_decode_for_this_instance' dentro do callback _decode_and_replace_match_fase2
    # garante que o contador só seja incrementado uma vez por instância original da chave, mesmo com repasses.
    g_processed_counts_fase2 = {key: 0 for key in chaves_para_decodificar}
    
    full_input_path_fase2 = os.path.join(g_script_dir, nome_arquivo_entrada_fase2)
    full_output_path_fase2 = os.path.join(g_script_dir, nome_arquivo_saida_fase2)

    try:
        print(f"Info (Fase 2): Lendo arquivo de entrada inicial: {full_input_path_fase2}")
        with open(full_input_path_fase2, 'r', encoding='utf-8') as f_in:
            current_lines_to_process = f_in.readlines()
    except FileNotFoundError:
        print(f"ERRO (Fase 2): O arquivo de entrada '{full_input_path_fase2}' não foi encontrado. Certifique-se que a Fase 1 foi concluída com sucesso.")
        return False
    except Exception as e:
        print(f"ERRO (Fase 2): Ao ler o arquivo '{full_input_path_fase2}': {e}")
        return False

    # Comentário: Prepara os padrões regex uma vez, pois eles não mudam entre os repasses do arquivo.
    regex_patterns_map_fase2 = {}
    if chaves_para_decodificar:
        print("\nInfo (Fase 2): --- Padrões Regex a serem utilizados para decodificação ---")
        for key_to_decode in chaves_para_decodificar:
            prefix_pattern_part = re.escape(f'"{key_to_decode}":"')
            pattern = re.compile(f'({prefix_pattern_part})([^"]*)(")')
            regex_patterns_map_fase2[key_to_decode] = pattern
            print(f"Info (Fase 2): Chave '{key_to_decode}', Padrão: {pattern.pattern}")
        print("--------------------------------------------------------------------")
    else:
        print("AVISO (Fase 2): Nenhuma chave alvo foi especificada. Nenhuma decodificação Base64 será tentada.")
        # Se não há chaves, podemos simplesmente escrever o conteúdo como está ou retornar.
        # Por ora, o loop abaixo não fará nada e o arquivo será reescrito como está.
        # Ou podemos adicionar um 'return True' aqui se quisermos evitar a escrita desnecessária.

    # Comentário: Loop de Repasses do Arquivo: Reprocessa o conjunto de linhas múltiplas vezes
    # para capturar decodificações em cascata que podem surgir de modificações anteriores.
    file_repass_count = 0
    while file_repass_count < MAX_REPASSES_ARQUIVO_FASE2:
        file_repass_count += 1
        print(f"\nInfo (Fase 2 - Repasse Geral {file_repass_count}/{MAX_REPASSES_ARQUIVO_FASE2}): Iniciando varredura de decodificação no conteúdo atual.")
        
        lines_after_this_repass = []
        content_changed_in_this_repass = False
        
        # Comentário: Itera sobre cada linha do conteúdo atual (que pode ser o resultado do repasse anterior).
        for i, line_content in enumerate(current_lines_to_process):
            line_number = i + 1
            modified_line_content_for_this_pass = line_content

            for key_to_decode in chaves_para_decodificar:
                g_current_key_fase2 = key_to_decode # Define a chave global para o callback
                current_regex_pattern = regex_patterns_map_fase2.get(key_to_decode)
                if not current_regex_pattern:
                    continue
                
                # Comentário: A função _decode_and_replace_match_fase2 agora tem seu próprio loop interno
                # para lidar com múltiplas camadas de decodificação DENTRO DE UM ÚNICO VALOR.
                processed_segment = current_regex_pattern.sub(
                    lambda m: _decode_and_replace_match_fase2(m, line_number),
                    modified_line_content_for_this_pass 
                )
                
                if processed_segment != modified_line_content_for_this_pass:
                    content_changed_in_this_repass = True
                modified_line_content_for_this_pass = processed_segment
            
            lines_after_this_repass.append(modified_line_content_for_this_pass)
        
        # Comentário: Verifica se houve alguma alteração no conteúdo durante este repasse completo.
        if not content_changed_in_this_repass:
            print(f"Info (Fase 2 - Repasse Geral {file_repass_count}): Nenhuma alteração adicional detectada. Processo de decodificação estabilizado.")
            current_lines_to_process = lines_after_this_repass # Garante que o último estado seja usado
            break # Sai do loop de repasses do arquivo, pois o conteúdo estabilizou.
        
        current_lines_to_process = lines_after_this_repass # Prepara as linhas modificadas para o próximo repasse.
        if file_repass_count < MAX_REPASSES_ARQUIVO_FASE2:
             print(f"Info (Fase 2 - Repasse Geral {file_repass_count}): Alterações detectadas. Preparando para próximo repasse (se o limite permitir).")
        else:
             print(f"Info (Fase 2 - Repasse Geral {file_repass_count}): Limite de repasses do arquivo atingido.")

    # Comentário: 'current_lines_to_process' agora contém o resultado final após todos os repasses.
    # Tenta escrever o resultado final no arquivo de saída.
    try:
        print(f"\nInfo (Fase 2): Escrevendo resultado final no arquivo de saída: {full_output_path_fase2}")
        with open(full_output_path_fase2, 'w', encoding='utf-8') as f_out:
            f_out.writelines(current_lines_to_process)

        print("\nInfo (Fase 2): --- Resumo Final do Processamento de Decodificação ---")
        any_key_processed_successfully_overall = False
        if not chaves_para_decodificar:
            print("Info (Fase 2): Nenhuma chave foi especificada para processamento.")
        else:
            for key, count in g_processed_counts_fase2.items(): # g_processed_counts_fase2 reflete o total de decodificações iniciais bem-sucedidas
                if count > 0:
                    print(f"Sucesso (Fase 2)! {count} ocorrência(s) da chave '{key}' tiveram pelo menos uma decodificação inicial bem-sucedida.")
                    any_key_processed_successfully_overall = True
                else:
                    print(f"AVISO (Fase 2): Nenhuma ocorrência da chave '{key}' no formato esperado resultou em uma decodificação inicial bem-sucedida em '{nome_arquivo_entrada_fase2}'.")
            
            if any_key_processed_successfully_overall:
                 print(f"\nSucesso (Fase 2): Arquivo final '{full_output_path_fase2}' salvo com decodificações.")
            else:
                print(f"\nAVISO (Fase 2): Nenhuma das chaves alvo resultou em decodificações iniciais. O arquivo '{full_output_path_fase2}' foi salvo.")
        return True
    except Exception as e:
        print(f"ERRO (Fase 2): Ao escrever o arquivo de saída final '{full_output_path_fase2}': {e}")
        return False

# --- Execução Principal Combinada ---
if __name__ == "__main__":
    print("--- Iniciando Processo Combinado de Duas Fases ---")
    
    try:
        g_script_dir = os.path.dirname(os.path.abspath(__file__))
    except NameError: 
        g_script_dir = os.getcwd()
        print(f"AVISO (Principal): A variável '__file__' não está definida. Usando o diretório de trabalho atual como base: {g_script_dir}")

    print(f"Info (Principal): O script está operando no diretório: {g_script_dir}")
    print(f"Info (Principal): O arquivo intermediário (saída da Fase 1, entrada da Fase 2) será: {os.path.join(g_script_dir, NOME_ARQUIVO_INTERMEDIARIO)}")
    print(f"Info (Principal): O arquivo de saída final (saída da Fase 2) será: {os.path.join(g_script_dir, NOME_ARQUIVO_SAIDA_FINAL)}")

    print("\n--- Executando Fase 1: Extração de conteúdo do arquivo .log ---")
    sucesso_fase1 = executar_fase1_extrair_conteudo_log(NOME_ARQUIVO_INTERMEDIARIO)

    if sucesso_fase1:
        print(f"--- Fase 1 CONCLUÍDA com sucesso. Arquivo intermediário '{NOME_ARQUIVO_INTERMEDIARIO}' foi gerado (ou atualizado). ---")
        
        print("\n--- Executando Fase 2: Decodificação Base64 do conteúdo do arquivo intermediário (com múltiplos repasses) ---")
        sucesso_fase2 = executar_fase2_decodificar_conteudo(
            NOME_ARQUIVO_INTERMEDIARIO, 
            NOME_ARQUIVO_SAIDA_FINAL,
            CHAVES_ALVO_FASE2
        )
        
        if sucesso_fase2:
            print(f"--- Fase 2 CONCLUÍDA. Verifique o arquivo de saída final '{NOME_ARQUIVO_SAIDA_FINAL}'. ---")
        else:
            print("--- Fase 2 FALHOU ou encontrou erros críticos. ---")
    else:
        print("--- Fase 1 FALHOU. A Fase 2 não será executada. ---")

    print("\n--- Processo Combinado FINALIZADO. ---")
