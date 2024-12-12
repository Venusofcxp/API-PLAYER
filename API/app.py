import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, request
import traceback

app = Flask(__name__)

# Função para buscar link no site "wix.maxcine.top" e retornar o link de reprodução
def buscar_link_filme_wix(titulo):
    try:
        # URL de pesquisa para "wix.maxcine.top"
        url_pesquisa = f"https://wix.maxcine.top/public/pesquisa-em-tempo-real?search={titulo}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Faz a requisição de pesquisa
        response = requests.get(url_pesquisa, headers=headers)
        
        if response.status_code != 200:
            return None, f"Erro na pesquisa do filme, status: {response.status_code}"

        # Usa BeautifulSoup para encontrar o link da página do filme
        soup = BeautifulSoup(response.content, 'html.parser')
        link_pagina_filme = None
        for link in soup.find_all('a', href=True):
            if "/public/filme/" in link['href']:
                link_pagina_filme = link['href']
                break

        if not link_pagina_filme:
            return None, "Filme não encontrado no wix.maxcine.top"

        # Formar a URL completa da página do filme
        url_pagina_filme = f"https://wix.maxcine.top{link_pagina_filme}" if link_pagina_filme.startswith('/') else link_pagina_filme
        
        # Faz a requisição para a página do filme e extrai o link de reprodução
        response = requests.get(url_pagina_filme, headers=headers)
        if response.status_code != 200:
            return None, f"Erro ao acessar a página do filme, status: {response.status_code}"

        soup = BeautifulSoup(response.content, 'html.parser')
        link_video = None

        # Extrair o link de reprodução do filme a partir do botão de webvideocast
        button = soup.find('button', {'class': 'webvideocast'})
        if button and 'onclick' in button.attrs:
            onclick_value = button['onclick']
            link_video = onclick_value.split("encodeURIComponent('")[1].split("'))")[0]

        # Se não encontrar o link de reprodução, procurar na div com a classe option
        if not link_video:
            option = soup.find('div', {'class': 'option', 'data-link': True})
            if option:
                link_video = option['data-link']

        if link_video:
            return link_video, None
        else:
            return None, "Link de reprodução não encontrado no wix.maxcine.top"
    
    except Exception as e:
        return None, f"Erro inesperado: {str(e)}\n{traceback.format_exc()}"

# Função para buscar página do filme no site "assistir.biz"
def buscar_pagina_do_filme_assistir(titulo):
    try:
        # Formata o título para URL
        titulo_formatado = titulo.lower().replace(" ", "-")
        url_filme = f"https://www.assistir.biz/filme/{titulo_formatado}"
        
        return url_filme, None
    except Exception as e:
        return None, f"Erro inesperado: {str(e)}\n{traceback.format_exc()}"

# Rota para pesquisar e retornar o link de reprodução ou página do filme
@app.route('/api/pesquisar', methods=['GET'])
def pesquisar_filme():
    try:
        titulo = request.args.get('titulo')
        if not titulo:
            return jsonify({"erro": "Parâmetro 'titulo' é obrigatório"}), 400

        # Primeiro, tenta buscar o filme no site "wix.maxcine.top" (link de reprodução)
        link_filme, erro = buscar_link_filme_wix(titulo)
        
        # Se não encontrar, tenta no "assistir.biz" (link da página do filme)
        if erro:
            link_filme, erro = buscar_pagina_do_filme_assistir(titulo)

        if erro:
            return jsonify({"erro": erro}), 404
        
        return jsonify({"titulo": titulo, "link_filme": link_filme})
    
    except Exception as e:
        return jsonify({"erro": f"Erro no servidor: {str(e)}\n{traceback.format_exc()}"}), 500

# Este bloco permite rodar o servidor Flask localmente
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
          
