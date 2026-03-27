import json
import os
from flask import Flask, render_template, request, jsonify, session
import bcrypt

app = Flask(__name__)
# Chave essencial para as sessões (Login) funcionarem
app.secret_key = "sabor_do_brasil_chave_secreta_2024"
ARQUIVO_DADOS = "usuarios.json"

# =============================================================================
#   FUNÇÕES DE ARQUIVO E SEGURANÇA
# =============================================================================

def ler_dados() -> dict:
    if not os.path.exists(ARQUIVO_DADOS):
        # Caso o arquivo não exista, cria a estrutura inicial
        return {"proximo_usuario_id": 1, "proximo_comentario_id": 1, "usuarios": [], "receitas": []}
    with open(ARQUIVO_DADOS, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)

def salvar_dados(dados: dict) -> None:
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=2, ensure_ascii=False)

def hash_senha(senha_texto_puro: str) -> str:
    senha_bytes = senha_texto_puro.encode("utf-8")
    return bcrypt.hashpw(senha_bytes, bcrypt.gensalt()).decode("utf-8")

def verificar_senha(senha_texto_puro: str, senha_hash: str) -> bool:
    return bcrypt.checkpw(senha_texto_puro.encode("utf-8"), senha_hash.encode("utf-8"))

def usuario_pode_editar(id_usuario_acao: int, id_autor_comentario: int) -> bool:
    dados = ler_dados()
    usuario = next((u for u in dados["usuarios"] if u["id"] == id_usuario_acao), None)
    if not usuario: return False
    # Admin pode tudo OU o usuário é o dono do comentário
    return usuario["perfil"] == "admin" or id_usuario_acao == id_autor_comentario

# =============================================================================
#   ROTAS PRINCIPAIS (INDEX, CADASTRO, LOGIN)
# =============================================================================

@app.route("/")
def index():
    dados = ler_dados()
    # Passamos o 'usuario' da sessão para o template saber se mostra "Login" ou "Sair"
    return render_template("index.html", receitas=dados.get("receitas", []), usuario=session.get("usuario"))

@app.route("/cadastrar", methods=["GET", "POST"])
def cadastrar():
    if request.method == "GET":
        return render_template("cadastro.html")

    dados_req = request.get_json() if request.is_json else request.form
    nickname = dados_req.get("nickname")
    senha = dados_req.get("senha")

    if not nickname or not senha:
        return jsonify({"erro": "Nickname e senha são obrigatórios"}), 400

    dados = ler_dados()
    if any(u["nickname"].lower() == nickname.lower() for u in dados["usuarios"]):
        return jsonify({"erro": "Este nickname já existe"}), 400

    novo_usuario = {
        "id": dados["proximo_usuario_id"],
        "nickname": nickname,
        "senha": hash_senha(senha),
        "perfil": "comum"
    }

    dados["usuarios"].append(novo_usuario)
    dados["proximo_usuario_id"] += 1
    salvar_dados(dados)
    return jsonify({"mensagem": "Usuário criado com sucesso!"}), 201

@app.route("/login", methods=["POST"])
def login():
    corpo = request.get_json()
    nickname = corpo.get("nickname", "").strip()
    senha = corpo.get("senha", "").strip()

    dados = ler_dados()
    user = next((u for u in dados["usuarios"] if u["nickname"].lower() == nickname.lower()), None)

    if user is None or not verificar_senha(senha, user["senha"]):
        return jsonify({"erro": "Usuário ou senha incorretos"}), 401

    # Cria a sessão oficial de login
    session["usuario"] = {
        "id": user["id"],
        "nickname": user["nickname"],
        "perfil": user["perfil"]
    }
    return jsonify({"mensagem": "Bem-vindo!", "usuario": session["usuario"]}), 200

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("usuario", None)
    return jsonify({"mensagem": "Até logo!"})

# =============================================================================
#   ROTAS DE INTERAÇÃO (CURTIDAS E COMENTÁRIOS)
# =============================================================================

@app.route("/curtir/<int:receita_id>", methods=["POST"])
def curtir(receita_id: int):
    usuario = session.get("usuario")
    if not usuario:
        return jsonify({"erro": "Você precisa estar logado para curtir"}), 401

    dados = ler_dados()
    for receita in dados["receitas"]:
        if receita["id"] == receita_id:
            nickname = usuario["nickname"]
            if nickname in receita["curtidas"]:
                receita["curtidas"].remove(nickname)
                acao = "removida"
            else:
                receita["curtidas"].append(nickname)
                acao = "adicionada"
            salvar_dados(dados)
            return jsonify({
                "mensagem": f"Curtida {acao}!",
                "total_curtidas": len(receita["curtidas"]),
                "curtiu": nickname in receita["curtidas"]
            })
    return jsonify({"erro": "Receita não encontrada"}), 404

@app.route("/comentar/<int:receita_id>", methods=["POST"])
def comentar(receita_id: int):
    usuario = session.get("usuario")
    if not usuario:
        return jsonify({"erro": "Você precisa estar logado para comentar"}), 401

    corpo = request.get_json()
    texto = corpo.get("texto", "").strip()
    if not texto:
        return jsonify({"erro": "O comentário não pode estar vazio"}), 400

    dados = ler_dados()
    for receita in dados["receitas"]:
        if receita["id"] == receita_id:
            novo_comentario = {
                "id": dados["proximo_comentario_id"],
                "autor_id": usuario["id"],
                "autor_nickname": usuario["nickname"],
                "texto": texto
            }
            receita["comentarios"].append(novo_comentario)
            dados["proximo_comentario_id"] += 1
            salvar_dados(dados)
            return jsonify({"mensagem": "Comentário adicionado!", "comentario": novo_comentario})
    return jsonify({"erro": "Receita não encontrada"}), 404

@app.route("/comentario/<int:comentario_id>", methods=["DELETE"])
def excluir_comentario(comentario_id: int):
    usuario = session.get("usuario")
    if not usuario:
        return jsonify({"erro": "Você precisa estar logado"}), 401

    dados = ler_dados()
    for receita in dados["receitas"]:
        for comentario in receita["comentarios"]:
            if comentario["id"] == comentario_id:
                if usuario_pode_editar(usuario["id"], comentario["autor_id"]):
                    receita["comentarios"].remove(comentario)
                    salvar_dados(dados)
                    return jsonify({"mensagem": "Comentário excluído!"}), 200
                else:
                    return jsonify({"erro": "Sem permissão para excluir"}), 403
    return jsonify({"erro": "Comentário não encontrado"}), 404

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    app.run(debug=True)