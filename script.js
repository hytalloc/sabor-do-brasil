// No início do script, adicione essa linha para pegar o usuário do Jinja2
let usuarioAtual = JSON.parse(document.getElementById('user-data').getAttribute('data-usuario') || 'null');

async function submeterLogin() {
    limparErros();
    const nicknameEl = document.getElementById("login-nickname");
    const senhaEl = document.getElementById("login-senha");
    const nickname = nicknameEl.value.trim();
    const senha = senhaEl.value.trim();

    // Validação visual de campos vazios
    if (!nickname) nicknameEl.classList.add("campo-erro");
    if (!senha) senhaEl.classList.add("campo-erro");
    if (!nickname || !senha) return;

    try {
        const resposta = await fetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ nickname, senha })
        });

        const dados = await resposta.json();

        if (!resposta.ok) {
            // EXIBIÇÃO DE ERROS (DESAFIO DO PROFESSOR)
            document.getElementById("texto-erro-login").textContent = dados.erro;
            document.getElementById("erro-login").classList.add("visivel");
            nicknameEl.classList.add("campo-erro");
            senhaEl.classList.add("campo-erro");
            return;
        }

        location.reload(); // Recarrega para o Flask reconhecer a nova sessão
    } catch (e) {
        console.error("Erro de comunicação:", e);
    }
}

async function curtir(receitaId, botao) {
    if (!usuarioAtual) {
        abrirModal("login"); // DISPARA MODAL AUTOMATICAMENTE (DESAFIO)
        return;
    }
    try {
        const resposta = await fetch(`/curtir/${receitaId}`, { method: "POST" });
        const dados = await resposta.json();
        if (resposta.ok) {
            botao.querySelector(".contador-curtida").textContent = dados.total_curtidas;
            botao.classList.toggle("ativo", dados.curtiu);
        }
    } catch (e) { console.error(e); }
}

function toggleComentarios(receitaId) {
    if (!usuarioAtual) {
        abrirModal("login"); // DISPARA MODAL AUTOMATICAMENTE (DESAFIO)
        return;
    }
    const secao = document.getElementById(`comentarios-${receitaId}`);
    secao.classList.toggle("aberta");
}