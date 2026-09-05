const categoriaInput = document.getElementById("categoria-input");
const addCategoriaBtn = document.getElementById("add-categoria-btn");
const chipsEl = document.getElementById("chips");
const cidadeInput = document.getElementById("cidade-input");
const estadoInput = document.getElementById("estado-input");
const quantidadeInput = document.getElementById("quantidade-input");
const quantidadeLabel = document.getElementById("quantidade-label");
const startBtn = document.getElementById("start-btn");
const statusTexto = document.getElementById("statusTexto");
const progressoWrap = document.getElementById("progressoWrap");
const progressoFill = document.getElementById("progressoFill");
const progressoLabel = document.getElementById("progressoLabel");
const tabelaBody = document.getElementById("tabelaBody");
const logEl = document.getElementById("log");
const mensagemErro = document.getElementById("mensagemErro");

let categorias = [];
let poller = null;

// ---------------------------------------------------------------------
// Chips de categoria
// ---------------------------------------------------------------------
function renderChips() {
  chipsEl.innerHTML = "";
  categorias.forEach((categoria) => {
    const chip = document.createElement("div");
    chip.className = "chip";

    const label = document.createElement("span");
    label.textContent = categoria;
    chip.appendChild(label);

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.textContent = "×";
    removeBtn.addEventListener("click", () => {
      categorias = categorias.filter((c) => c !== categoria);
      renderChips();
    });
    chip.appendChild(removeBtn);

    chipsEl.appendChild(chip);
  });
}

function adicionarCategoria() {
  const texto = categoriaInput.value.trim();
  if (!texto) return;
  if (!categorias.includes(texto)) {
    categorias.push(texto);
    renderChips();
  }
  categoriaInput.value = "";
  categoriaInput.focus();
}

addCategoriaBtn.addEventListener("click", adicionarCategoria);
categoriaInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    adicionarCategoria();
  }
});

quantidadeInput.addEventListener("input", () => {
  quantidadeLabel.textContent = quantidadeInput.value;
});

// ---------------------------------------------------------------------
// Mensagens de erro
// ---------------------------------------------------------------------
function mostrarErro(msg) {
  mensagemErro.textContent = msg;
  mensagemErro.hidden = false;
}

function limparErro() {
  mensagemErro.hidden = true;
  mensagemErro.textContent = "";
}

// ---------------------------------------------------------------------
// Tabela de progresso por categoria
// ---------------------------------------------------------------------
function normalizarStatus(status) {
  return status
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .split("...")[0]
    .trim();
}

function renderTabela(progresso) {
  tabelaBody.innerHTML = "";
  const entradas = Object.entries(progresso || {});
  entradas.forEach(([categoria, status], i) => {
    const tr = document.createElement("tr");
    const chave = normalizarStatus(status);
    tr.innerHTML = `
      <td>${i + 1}</td>
      <td>${categoria}</td>
      <td class="status ${chave}">${status}</td>
    `;
    tabelaBody.appendChild(tr);
  });
}

function atualizarProgressoBarra(progresso, rodando) {
  const valores = Object.values(progresso || {});
  const total = valores.length;
  if (total === 0) {
    progressoWrap.hidden = true;
    return;
  }
  const feitos = valores.filter((s) => s === "concluido" || s === "erro").length;
  progressoWrap.hidden = false;
  const pct = Math.round((feitos / total) * 100);
  progressoFill.style.width = pct + "%";
  progressoLabel.textContent = `${feitos} / ${total}`;
  statusTexto.textContent = rodando ? "Buscando..." : "Concluído.";
}

// ---------------------------------------------------------------------
// Polling de status
// ---------------------------------------------------------------------
async function consultarStatus() {
  try {
    const resp = await fetch("/api/status");
    const dados = await resp.json();

    logEl.textContent = (dados.log || []).join("\n");
    logEl.scrollTop = logEl.scrollHeight;

    renderTabela(dados.progresso);
    atualizarProgressoBarra(dados.progresso, dados.rodando);

    if (!dados.rodando) {
      if (poller) {
        clearInterval(poller);
        poller = null;
      }
      startBtn.disabled = false;
      startBtn.textContent = "▶ INICIAR BUSCA";
    } else {
      startBtn.disabled = true;
      startBtn.textContent = "BUSCANDO...";
    }
  } catch (e) {
    statusTexto.textContent = "Erro ao consultar status.";
  }
}

// ---------------------------------------------------------------------
// Iniciar busca
// ---------------------------------------------------------------------
startBtn.addEventListener("click", async () => {
  limparErro();

  if (categorias.length === 0) {
    mostrarErro("Adicione ao menos uma categoria.");
    return;
  }
  const cidade = cidadeInput.value.trim();
  const estado = estadoInput.value.trim();
  if (!cidade) {
    mostrarErro("A cidade não pode ficar vazia.");
    return;
  }
  if (!estado) {
    mostrarErro("O estado não pode ficar vazio.");
    return;
  }

  const payload = {
    categorias,
    cidade,
    estado,
    quantidade: parseInt(quantidadeInput.value, 10),
  };

  startBtn.disabled = true;
  startBtn.textContent = "BUSCANDO...";
  statusTexto.textContent = "Iniciando...";
  tabelaBody.innerHTML = "";
  logEl.textContent = "";

  try {
    const resp = await fetch("/api/buscar", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const dados = await resp.json();

    if (!resp.ok) {
      mostrarErro(dados.erro || "Erro ao iniciar a busca.");
      startBtn.disabled = false;
      startBtn.textContent = "▶ INICIAR BUSCA";
      return;
    }

    if (!poller) {
      poller = setInterval(consultarStatus, 800);
    }
    consultarStatus();
  } catch (e) {
    mostrarErro("Não foi possível conectar ao servidor local.");
    startBtn.disabled = false;
    startBtn.textContent = "▶ INICIAR BUSCA";
  }
});

// ---------------------------------------------------------------------
// Ao carregar a página, verifica se já existe uma busca em andamento
// ---------------------------------------------------------------------
(async function inicializar() {
  await consultarStatus();
  try {
    const resp = await fetch("/api/status");
    const dados = await resp.json();
    if (dados.rodando && !poller) {
      poller = setInterval(consultarStatus, 800);
    }
  } catch (e) {
    // silencioso: servidor pode ainda nao ter respondido no primeiro load
  }
})();
