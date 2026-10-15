"""MaterSphere Silver — demonstração local, acessível e com dados sintéticos."""

from __future__ import annotations

from datetime import datetime
import pandas as pd
import streamlit as st

from risk_engine import RiskAssessment, calculate_risk


st.set_page_config(
    page_title="MaterSphere Silver", page_icon="🩺", layout="wide",
    initial_sidebar_state="expanded",
)


PATIENTS = [
    {"id": "MS-001", "paciente": "Maria S.", "idade": 72, "faltas": 2, "dias": 1, "consulta": "14/10/2026 · 09:00", "especialidade": "Cardiologia"},
    {"id": "MS-002", "paciente": "José R.", "idade": 68, "faltas": 1, "dias": 2, "consulta": "15/10/2026 · 14:30", "especialidade": "Clínica geral"},
    {"id": "MS-003", "paciente": "Ana C.", "idade": 65, "faltas": 0, "dias": 5, "consulta": "18/10/2026 · 10:00", "especialidade": "Oftalmologia"},
    {"id": "MS-004", "paciente": "Carlos M.", "idade": 79, "faltas": 3, "dias": 1, "consulta": "14/10/2026 · 16:00", "especialidade": "Endocrinologia"},
]

LEVEL_META = {
    "BAIXO": ("🟢", "Baixo", "#167A5B", "Confirmação automática por SMS"),
    "MEDIO": ("🟡", "Médio", "#9A6700", "Lembrete por SMS/WhatsApp e reforço no dia anterior"),
    "ALTO": ("🔴", "Alto", "#B42318", "Ligação prioritária e alerta à equipe"),
}


def inject_style(font_size: int, high_contrast: bool) -> None:
    # O tema do projeto atende todo o Streamlit. Este CSS fica restrito ao
    # recurso de fonte ampliada escolhido pela pessoa usuária.
    scale = {16: "1rem", 18: "1.125rem", 20: "1.25rem", 22: "1.375rem"}[font_size]
    contrast_border = "#172033" if high_contrast else "#D7E0EC"
    contrast_surface = "#FFFFFF" if high_contrast else "#F4F7FB"
    contrast_ink = "#101828" if high_contrast else "#10213F"
    st.markdown(
        f"""
        <style>
        :root {{ --ms-ink:{contrast_ink}; --ms-muted:#40516D; --ms-line:{contrast_border}; --ms-canvas:{contrast_surface}; }}
        .stApp {{ background:var(--ms-canvas); color:var(--ms-ink); }}
        [data-testid="stAppViewContainer"] p,
        [data-testid="stAppViewContainer"] label,
        [data-testid="stAppViewContainer"] [data-testid="stMetricLabel"],
        [data-testid="stAppViewContainer"] [data-testid="stMetricValue"] {{ font-size:{scale}; }}
        #MainMenu, footer {{ visibility:hidden; }}
        .block-container {{ padding-top:2.5rem; padding-bottom:3rem; max-width:1400px; }}
        .ms-hero {{ border-radius:24px; padding:2.25rem 2.4rem; color:#fff;
          background:radial-gradient(circle at 88% 20%,rgba(255,255,255,.22),transparent 20%),linear-gradient(120deg,#123D8C,#2167DB 55%,#0FA3A1); }}
        .ms-kicker {{ font-size:.82rem; font-weight:800; letter-spacing:.10em; text-transform:uppercase; opacity:.92; }}
        .ms-hero h1 {{ color:#fff!important; font-size:2.55rem!important; margin:.35rem 0!important; }}
        .ms-hero p {{ font-size:1.12rem; max-width:720px; margin:0; }}
        .ms-card {{ min-height:128px; background:#fff; border:1px solid var(--ms-line); border-radius:18px; padding:1rem 1.1rem; box-shadow:0 6px 18px rgba(25,47,84,.06); }}
        .ms-card-label {{ color:var(--ms-muted); font-size:.86rem; font-weight:700; }}
        .ms-card-value {{ color:var(--ms-ink); font-size:2rem; font-weight:850; margin:.25rem 0; }}
        .ms-card-note {{ color:var(--ms-muted); font-size:.88rem; line-height:1.35; }}
        .ms-section {{ color:var(--ms-muted); font-size:.8rem; font-weight:800; letter-spacing:.08em; text-transform:uppercase; margin:1rem 0 .1rem; }}
        .ms-result {{ border-left:7px solid #2167DB; background:#fff; padding:1.2rem 1.35rem; border-radius:0 16px 16px 0; border-top:1px solid var(--ms-line); border-right:1px solid var(--ms-line); border-bottom:1px solid var(--ms-line); }}
        .ms-note {{ border-radius:14px; padding:1rem 1.1rem; background:#EDF5FF; border:1px solid #C7DCF7; color:#173E70; }}
        .stButton button, .stDownloadButton button {{ min-height:48px; font-size:1rem; font-weight:700; box-shadow:none; }}
        @media (max-width: 700px) {{ .ms-hero {{ padding:1.5rem; }} .ms-hero h1 {{ font-size:2rem!important; }} }}
        </style>
        """, unsafe_allow_html=True,
    )


def init_state() -> None:
    if "analyses" not in st.session_state:
        st.session_state.analyses = []
    if "last_assessment" not in st.session_state:
        st.session_state.last_assessment = None
    if "last_patient" not in st.session_state:
        st.session_state.last_patient = None


def card(label: str, value: str | int, note: str) -> None:
    st.markdown(f'<div class="ms-card"><div class="ms-card-label">{label}</div><div class="ms-card-value">{value}</div><div class="ms-card-note">{note}</div></div>', unsafe_allow_html=True)


def action_text(action: str) -> str:
    return {
        "CONFIRMACAO_AUTOMATICA": "Confirmação automática",
        "LEMBRETE_REFORCADO": "Lembrete reforçado",
        "LIGACAO_PRIORITARIA": "Ligação prioritária",
    }[action]


def assessment_rows() -> list[dict]:
    rows = []
    for item in st.session_state.analyses:
        icon, label, _, recommendation = LEVEL_META[item["risco"]]
        rows.append({"Paciente": item["paciente"], "Idade": f'{item["idade"]} anos', "Risco": f"{icon} {label}", "Score": item["score"], "Ação recomendada": recommendation, "Horário": item["horario"]})
    return rows


def render_result(patient: dict, assessment: RiskAssessment) -> None:
    icon, label, color, recommendation = LEVEL_META[assessment.level]
    st.markdown('<div class="ms-section">Resultado do pipeline</div>', unsafe_allow_html=True)
    left, center, right = st.columns((1, 1.15, 1.5))
    with left:
        st.markdown(f'<div class="ms-card"><div class="ms-card-label">NLP · sentimento</div><div class="ms-card-value">{assessment.sentiment.title()}</div><div class="ms-card-note">Leitura baseada em vocabulário explícito</div></div>', unsafe_allow_html=True)
    with center:
        st.markdown(f'<div class="ms-card"><div class="ms-card-label">Score de risco</div><div class="ms-card-value" style="color:{color}">{icon} {assessment.score}/100</div><div class="ms-card-note">Classificação: risco {label.lower()}</div></div>', unsafe_allow_html=True)
    with right:
        st.markdown(f'<div class="ms-card"><div class="ms-card-label">Ação sugerida</div><div class="ms-card-value" style="font-size:1.35rem">{action_text(assessment.action)}</div><div class="ms-card-note">{recommendation}</div></div>', unsafe_allow_html=True)

    st.markdown("#### Explicação do score")
    factors = pd.DataFrame([{"Fator": key, "Pontos": value} for key, value in assessment.factors.items()])
    st.dataframe(factors, hide_index=True, width="stretch", column_config={"Pontos": st.column_config.NumberColumn(format="%d")})
    if assessment.risk_terms:
        st.info("Termos de risco identificados: " + ", ".join(f'“{term}”' for term in assessment.risk_terms))
    else:
        st.caption("Nenhuma palavra-chave de risco foi identificada na mensagem.")
    st.markdown('<div class="ms-note"><b>Revisão humana obrigatória:</b> esta recomendação organiza o contato da agenda. Ela não informa diagnóstico, urgência nem probabilidade clínica.</div>', unsafe_allow_html=True)


def run_analysis(patient: dict, message: str) -> None:
    assessment = calculate_risk(message=message, age=patient["idade"], prior_no_shows=patient["faltas"], days_until_appointment=patient["dias"])
    st.session_state.last_assessment = assessment
    st.session_state.last_patient = patient
    st.session_state.analyses.insert(0, {
        "paciente": patient["paciente"], "idade": patient["idade"], "risco": assessment.level,
        "score": assessment.score, "acao": action_text(assessment.action),
        "horario": datetime.now().strftime("%d/%m/%Y %H:%M"),
    })


def render_overview() -> None:
    st.markdown("""<div class="ms-hero"><div class="ms-kicker">IA preventiva para acessibilidade clínica</div><h1>MaterSphere Silver</h1><p>Tecnologia de apoio à equipe para identificar barreiras de comparecimento e priorizar um contato mais humano com pessoas idosas.</p></div>""", unsafe_allow_html=True)
    st.write("")
    counts = {level: sum(item["risco"] == level for item in st.session_state.analyses) for level in LEVEL_META}
    cols = st.columns(4)
    with cols[0]: card("Análises nesta sessão", len(st.session_state.analyses), "Dados sintéticos para demonstração")
    with cols[1]: card("Prioridade alta", counts["ALTO"], "Casos que pedem ligação da equipe")
    with cols[2]: card("Risco médio", counts["MEDIO"], "Casos que pedem reforço do lembrete")
    with cols[3]: card("Fila acompanhada", len(PATIENTS), "Consultas sintéticas disponíveis")
    st.markdown('<div class="ms-section">Fluxo de atendimento</div>', unsafe_allow_html=True)
    st.markdown("### Mensagem → NLP → score → ação recomendada")
    flow = st.columns(4)
    for column, title, text in zip(flow, ["💬 Entrada", "🧠 NLP", "🔴 Score", "⚡ Ação"], ["Mensagem clara, com fonte ampliada e leitura simples.", "Identifica tom declarado e termos que indicam barreiras.", "Combina dados de agenda e os pesos documentados.", "Apresenta uma recomendação para revisão humana."]):
        with column:
            card(title, "", text)
    st.markdown('<div class="ms-note"><b>Ambiente demonstrativo:</b> todos os pacientes, mensagens e resultados desta aplicação são sintéticos. Nenhum contato é disparado automaticamente.</div>', unsafe_allow_html=True)


def render_analyze() -> None:
    st.markdown('<div class="ms-section">Entrada de mensagem</div>', unsafe_allow_html=True)
    st.title("Analisar risco de não comparecimento")
    st.caption("Simule o contato com um paciente. A aplicação analisa a mensagem e mostra por que cada recomendação apareceu.")
    lookup = {p["id"]: p for p in PATIENTS}
    with st.form("analysis_form", clear_on_submit=False):
        patient_id = st.selectbox("Consulta sintética", list(lookup), format_func=lambda key: f'{lookup[key]["paciente"]} · {lookup[key]["especialidade"]} · {lookup[key]["consulta"]}')
        patient = lookup[patient_id]
        c1, c2, c3 = st.columns(3)
        c1.metric("Idade", f'{patient["idade"]} anos')
        c2.metric("Faltas anteriores", patient["faltas"])
        c3.metric("Dias até a consulta", patient["dias"])
        message = st.text_area("Mensagem do paciente", placeholder="Ex.: Estou muito cansada e não sei se vou conseguir ir amanhã.", max_chars=500, height=135, help="Use apenas mensagens fictícias durante a demonstração.")
        submitted = st.form_submit_button("Analisar mensagem", type="primary", width="stretch")
    if submitted:
        if len(message.strip()) < 3:
            st.warning("Digite uma mensagem com pelo menos 3 caracteres.")
        else:
            run_analysis(patient, message)
    if st.session_state.last_assessment and st.session_state.last_patient:
        render_result(st.session_state.last_patient, st.session_state.last_assessment)


def render_queue() -> None:
    st.markdown('<div class="ms-section">Registro + CSV</div>', unsafe_allow_html=True)
    st.title("Fila de priorização")
    st.caption("Acompanhe os casos analisados durante a apresentação e exporte um registro local da sessão.")
    rows = assessment_rows()
    if not rows:
        st.info("Ainda não há análises. Comece pela página “Analisar mensagem”.")
        return
    st.dataframe(rows, hide_index=True, width="stretch", column_config={"Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d")})
    csv = pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig")
    st.download_button("Baixar registro CSV", csv, file_name="materphere-silver-sessao.csv", mime="text/csv", type="primary")
    selected = st.selectbox("Revisar caso", range(len(st.session_state.analyses)), format_func=lambda index: f'{st.session_state.analyses[index]["paciente"]} · {st.session_state.analyses[index]["risco"].title()}')
    item = st.session_state.analyses[selected]
    st.markdown(f'<div class="ms-result"><b>Decisão da equipe:</b> {item["acao"]}<br><span style="color:#52647D">O sistema recomenda, mas a equipe decide e executa o contato.</span></div>', unsafe_allow_html=True)


def render_method() -> None:
    st.markdown('<div class="ms-section">Transparência</div>', unsafe_allow_html=True)
    st.title("Lógica do score de risco")
    st.caption("Os fatores e cortes reproduzem a regra demonstrada na apresentação. O score é uma escala operacional, não uma probabilidade de falta.")
    st.dataframe(pd.DataFrame([
        {"Fator": "Sentimento negativo na mensagem", "Peso": "35%", "Fonte": "NLP por vocabulário explícito"},
        {"Fator": "Histórico de 2 ou mais faltas", "Peso": "30%", "Fonte": "Dataset sintético"},
        {"Fator": "Consulta em até 2 dias", "Peso": "20%", "Fonte": "Dataset sintético"},
        {"Fator": "Idade a partir de 70 anos", "Peso": "10%", "Fonte": "Cadastro sintético"},
        {"Fator": "Palavra-chave de risco", "Peso": "5%", "Fonte": "NLP por vocabulário explícito"},
    ]), hide_index=True, width="stretch")
    c1, c2, c3 = st.columns(3)
    with c1: card("🟢 Baixo", "0–39", "Confirmação automática por SMS")
    with c2: card("🟡 Médio", "40–69", "Lembrete por SMS/WhatsApp e reforço D-1")
    with c3: card("🔴 Alto", "70–100", "Ligação prioritária e alerta à equipe")
    st.markdown('<div class="ms-note"><b>Validação proposta:</b> medir a redução de faltas do grupo de alto risco após contato prioritário, comparando com grupo controle em um piloto institucional de quatro semanas.</div>', unsafe_allow_html=True)


def render_governance() -> None:
    st.markdown('<div class="ms-section">Uso responsável</div>', unsafe_allow_html=True)
    st.title("Privacidade e limites do MVP")
    left, right = st.columns(2)
    with left:
        st.subheader("O que a demonstração faz")
        st.markdown("- Prioriza contatos da agenda com dados sintéticos\n- Explica os fatores que formam o score\n- Mantém a decisão final com a equipe\n- Permite baixar o registro da sessão")
    with right:
        st.subheader("O que a demonstração não faz")
        st.markdown("- Não usa dados reais de pacientes\n- Não realiza diagnóstico ou triagem clínica\n- Não envia SMS, WhatsApp ou ligações\n- Não toma decisões sem revisão humana")
    st.markdown('<div class="ms-note"><b>LGPD e piloto real:</b> antes de utilizar dados reais, o hospital deve definir finalidade, base legal, controles de acesso, retenção, auditoria, segurança, consentimento quando aplicável e supervisão humana.</div>', unsafe_allow_html=True)


init_state()
with st.sidebar:
    st.markdown("## 🩺 MaterSphere Silver")
    st.caption("IA preventiva para acessibilidade clínica")
    st.divider()
    page = st.radio("Navegação", ["Visão geral", "Analisar mensagem", "Fila de priorização", "Lógica do score", "Privacidade e limites"], label_visibility="collapsed")
    st.divider()
    st.markdown("**Acessibilidade da tela**")
    font_size = st.select_slider("Tamanho do texto", options=[16, 18, 20, 22], value=18, format_func=lambda value: f"{value}px")
    high_contrast = st.toggle("Alto contraste", value=False)
    st.caption("Demonstração acadêmica com dados sintéticos")

inject_style(font_size, high_contrast)
if page == "Visão geral":
    render_overview()
elif page == "Analisar mensagem":
    render_analyze()
elif page == "Fila de priorização":
    render_queue()
elif page == "Lógica do score":
    render_method()
else:
    render_governance()
