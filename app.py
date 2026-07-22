import streamlit as st
import pandas as pd
from bs4 import BeautifulSoup
import re

# ==========================================
# 1. CONFIGURAÇÕES E ESTILOS CSS
# ==========================================
st.set_page_config(
    page_title="Grade & Planejador de Farmácia",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Estilos dos Cards das Disciplinas */
    .subject-card {
        background-color: #ffffff; border: 2px solid #e2e8f0; border-radius: 12px;
        padding: 16px; margin-bottom: 8px; margin-top: 16px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); transition: transform 0.2s;
    }
    .subject-card:hover { transform: translateY(-2px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
    .card-concluida { background-color: #eff6ff; border-color: #3b82f6; }
    .card-liberada { background-color: #f0fdf4; border-color: #22c55e; }
    .card-trancada { background-color: #fefce8; border-color: #eab308; opacity: 0.9; }
    
    .status-badge { font-size: 11px; padding: 4px 8px; border-radius: 6px; font-weight: bold; margin-bottom: 12px; display: inline-block; text-transform: uppercase; letter-spacing: 0.05em; }
    .badge-concluida { background-color: #3b82f6; color: white; }
    .badge-liberada { background-color: #22c55e; color: white; }
    .badge-trancada { background-color: #eab308; color: #713f12; }
    .subject-meta { font-size: 13px; color: #64748b; margin-bottom: 6px; text-transform: uppercase; font-weight: 600; }
    .subject-title { font-weight: bold; font-size: 14px; margin-bottom: 8px; line-height: 1.2; color: #0f172a; }
    .prereq-badge { display: inline-block; font-size: 11px; padding: 4px 8px; border-radius: 4px; margin-right: 4px; margin-top: 8px; font-weight: 600; border: 1px solid rgba(0,0,0,0.05); }
    .credit-badge { display: inline-block; background-color: #f1f5f9; color: #475569; font-size: 12px; padding: 3px 8px; border-radius: 4px; font-weight: 600; margin-bottom: 6px; }
    
    /* ESTILOS DA NOVA GRADE (LINHA DO TEMPO ABSOLUTA) */
    .calendar-event {
        position: absolute; left: 2.5%; width: 95%;
        border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.15);
        color: white; padding: 6px; overflow: hidden; 
        font-size: 11px; line-height: 1.2; font-family: sans-serif;
        transition: all 0.2s ease-in-out; cursor: default;
        z-index: 5; opacity: 0.9;
    }
    .calendar-event:hover {
        z-index: 10 !important;
        transform: scale(1.03);
        box-shadow: 0 6px 12px rgba(0,0,0,0.25);
        opacity: 1 !important;
    }
    .calendar-event b { font-size: 13px; display: block; margin-bottom: 2px; text-shadow: 0 1px 2px rgba(0,0,0,0.3); }
    .calendar-event span.turma-tag { font-size: 10px; font-weight: bold; background: rgba(0,0,0,0.2); padding: 2px 5px; border-radius: 4px; display: inline-block; margin-top: 4px;}
    
    /* Customização do Expander (Pastas na esquerda) */
    .streamlit-expanderHeader { font-weight: bold !important; font-size: 14px !important; color: #1e293b !important; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. BANCO DE DADOS (SESSION STATE)
# ==========================================
if "cadeiras_farmacia" not in st.session_state:
    st.session_state.cadeiras_farmacia = {
          # --- ETAPA 1 ---
        "CBS05511": {"name": "ANATOMIA HUMANA", "semester": 1, "credits": 3, "prerequisites": [], "classes": []},
        "QUI01044": {"name": "FUNDAMENTOS DE QUÍMICA INORGÂNICA", "semester": 1, "credits": 2, "prerequisites": [], "classes": []},
        "CBS05027": {"name": "HISTOLOGIA E EMBRIOLOGIA GERAL", "semester": 1, "credits": 4, "prerequisites": [], "classes": []},
        "FAR01011": {"name": "INTRODUÇÃO ÀS CIÊNCIAS FARMACÊUTICAS", "semester": 1, "credits": 3, "prerequisites": [], "classes": []},
        "QUI01161": {"name": "QUÍMICA GERAL EXPERIMENTAL B", "semester": 1, "credits": 3, "prerequisites": [], "classes": []},
        "QUI01049": {"name": "QUÍMICA GERAL TEÓRICA B", "semester": 1, "credits": 4, "prerequisites": [], "classes": []},
        "FAR02046": {"name": "SAÚDE COLETIVA - FAR", "semester": 1, "credits": 2, "prerequisites": [], "classes": []},
        
        # --- ETAPA 2 ---
        "FAR01038": {"name": "BIOÉTICA - FAR", "semester": 2, "credits": 2, "prerequisites": [], "classes": []},
        "BIO10387": {"name": "BIOFÍSICA F", "semester": 2, "credits": 4, "prerequisites": ["QUI01049"], "classes": []},
        "CBS03388": {"name": "FISIOLOGIA FARMACÊUTICA", "semester": 2, "credits": 6, "prerequisites": ["CBS05027", "CBS05511"], "classes": []},
        "BIO07714": {"name": "GENÉTICA", "semester": 2, "credits": 3, "prerequisites": ["CBS05027"], "classes": []},
        "MAT01122": {"name": "NOÇÕES DE CÁLCULO DIFERENCIAL E INTEGRAL", "semester": 2, "credits": 2, "prerequisites": [], "classes": []},
        "QUI01039": {"name": "QUÍMICA ANALÍTICA QUANTITATIVA E INSTRUMENTAL", "semester": 2, "credits": 5, "prerequisites": ["QUI01049", "QUI01161"], "classes": []},
        "QUI02014": {"name": "QUÍMICA ORGÂNICA I - B", "semester": 2, "credits": 4, "prerequisites": ["QUI01044", "QUI01049"], "classes": []},
        
        # --- ETAPA 3 ---
        "MAT02218": {"name": "BIOESTATÍSTICA", "semester": 3, "credits": 4, "prerequisites": ["MAT01122"], "classes": []},
        "EST0001": {"name": "ESTÁGIO OBSERVACIONAL EM SERVIÇOS E GESTÃO FARMACÊUTICA", "semester": 3, "credits": 0, "prerequisites": ["CBS03388", "FAR02046"], "classes": []},
        "CBS01031": {"name": "BIOQUÍMICA I", "semester": 3, "credits": 5, "prerequisites": ["CBS03388", "QUI02014"], "classes": []},
        "FAR01012": {"name": "OPERAÇÕES UNITÁRIAS FARMACÊUTICAS", "semester": 3, "credits": 4, "prerequisites": ["BIO10387"], "classes": []},
        "QUI02023": {"name": "QUÍMICA ORGÂNICA EXPERIMENTAL I", "semester": 3, "credits": 4, "prerequisites": ["QUI02014"], "classes": []},
        "QUI02015": {"name": "QUÍMICA ORGÂNICA II", "semester": 3, "credits": 4, "prerequisites": ["QUI02014"], "classes": []},

        # --- ETAPA 4 ---
        "FAR03028": {"name": "BASES DA IMUNOLOGIA", "semester": 4, "credits": 3, "prerequisites": ["CBS01031"], "classes": []},
        "CBS01032": {"name": "BIOQUÍMICA II", "semester": 4, "credits": 5, "prerequisites": ["CBS01031"], "classes": []},
        "FAR01015": {"name": "CONTROLE DE QUALIDADE DE MATÉRIA - PRIMA", "semester": 4, "credits": 3, "prerequisites": ["MAT02218", "QUI01039", "QUI02014"], "classes": []},
        "FAR02030": {"name": "EPIDEMIOLOGIA", "semester": 4, "credits": 2, "prerequisites": ["FAR01038", "FAR02046", "MAT02218"], "classes": []},
        "FAR02018": {"name": "FÍSICO-QUÍMICA", "semester": 4, "credits": 4, "prerequisites": ["BIO10387", "QUI01049"], "classes": []},
        "CBS06041": {"name": "MICROBIOLOGIA BÁSICA", "semester": 4, "credits": 3, "prerequisites": ["CBS01031"], "classes": []},
        "MED04403": {"name": "PATOLOGIA", "semester": 4, "credits": 4, "prerequisites": ["CBS01031"], "classes": []},

        # --- ETAPA 5 ---
        "FAR02026": {"name": "ASSISTÊNCIA FARMACÊUTICA", "semester": 5, "credits": 4, "prerequisites": ["FAR01038", "FAR02030", "FAR02046"], "classes": []},
        "CBS01045": {"name": "BIOQUÍMICA III", "semester": 5, "credits": 3, "prerequisites": ["CBS01032"], "classes": []},
        "FAR01013": {"name": "FARMACOGNOSIA", "semester": 5, "credits": 5, "prerequisites": ["QUI02015", "QUI02023"], "classes": []},
        "CBS09010": {"name": "FARMACOLOGIA I", "semester": 5, "credits": 2, "prerequisites": ["BIO10387", "CBS01032"], "classes": []},
        "FAR03008": {"name": "MICOLOGIA CLÍNICA", "semester": 5, "credits": 3, "prerequisites": ["CBS06041", "FAR03028"], "classes": []},
        "FAR03005": {"name": "PARASITOLOGIA CLÍNICA", "semester": 5, "credits": 4, "prerequisites": ["CBS03388", "FAR03028"], "classes": []},
        "FAR01016": {"name": "PROCESSOS INDUSTRIAIS E EQUIPAMENTOS I", "semester": 5, "credits": 2, "prerequisites": ["FAR01012"], "classes": []},

        # --- ETAPA 6 ---
        "FAR03007": {"name": "BACTERIOLOGIA CLÍNICA", "semester": 6, "credits": 5, "prerequisites": ["CBS06041", "FAR03028"], "classes": []},
        "FAR02015": {"name": "CUIDADO FARMACÊUTICO I", "semester": 6, "credits": 4, "prerequisites": ["CBS09010", "FAR01038", "FAR02046"], "classes": []},
        "FAR02038": {"name": "FARMACOCINÉTICA BÁSICA", "semester": 6, "credits": 4, "prerequisites": ["CBS01032", "CBS01045"], "classes": []},
        "CBS09011": {"name": "FARMACOLOGIA II", "semester": 6, "credits": 4, "prerequisites": ["CBS09010"], "classes": []},
        "FAR01031": {"name": "PRÁTICAS EM QUÍMICA FARMACÊUTICA", "semester": 6, "credits": 3, "prerequisites": ["CBS09010", "QUI01039", "QUI02015", "QUI02023"], "classes": []},
        "FAR02021": {"name": "PRODUÇÃO E CONTROLE DE FORMAS FARMACÊUTICAS SÓLIDAS", "semester": 6, "credits": 8, "prerequisites": ["FAR01016", "FAR02018", "QUI01039"], "classes": []},

        # --- ETAPA 7 ---
        "FAR02017": {"name": "CUIDADO FARMACÊUTICO II", "semester": 7, "credits": 4, "prerequisites": ["CBS09011", "FAR01038", "FAR02015", "FAR02046"], "classes": []},
        "FAR03009": {"name": "HEMATOLOGIA CLÍNICA", "semester": 7, "credits": 5, "prerequisites": ["CBS05027", "FAR03007", "FAR03028"], "classes": []},
        "FAR03006": {"name": "IMUNOLOGIA CLÍNICA", "semester": 7, "credits": 4, "prerequisites": ["FAR03005", "FAR03007", "FAR03028"], "classes": []},
        "FAR02022": {"name": "PRODUÇÃO E CONTROLE DE FORMAS FARMACÊUTICAS LÍQUIDAS", "semester": 7, "credits": 8, "prerequisites": ["FAR02021"], "classes": []},
        "FAR01030": {"name": "QUÍMICA FARMACÊUTICA I", "semester": 7, "credits": 3, "prerequisites": ["CBS09010", "FAR02038", "QUI02015"], "classes": []},
        "FAR01018": {"name": "TECNOLOGIA BIOQUÍMICA I", "semester": 7, "credits": 5, "prerequisites": ["CBS06041", "FAR01016"], "classes": []},

        # --- ETAPA 8 ---
        "ADM01017": {"name": "ADMINISTRAÇÃO DE EMPRESAS FARMACÊUTICAS", "semester": 8, "credits": 2, "prerequisites": [], "classes": []},
        "FAR03010": {"name": "BIOQUÍMICA CLÍNICA I", "semester": 8, "credits": 5, "prerequisites": ["CBS01032", "CBS01045", "FAR03006"], "classes": []},
        "FAR03013": {"name": "CITOLOGIA CLÍNICA", "semester": 8, "credits": 2, "prerequisites": ["FAR03009"], "classes": []},
        "FAR02210": {"name": "FARMÁCIA HOSPITALAR", "semester": 8, "credits": 2, "prerequisites": ["FAR01038", "FAR02017", "FAR02022", "FAR02046"], "classes": []},
        "FAR02024": {"name": "LEGISLAÇÃO PROFISSIONAL FARMACÊUTICA", "semester": 8, "credits": 2, "prerequisites": ["FAR02017"], "classes": []},
        "FAR02023": {"name": "PRODUÇÃO E CONTROLE DE FORMAS FARMACÊUTICAS SEMISSÓLIDAS", "semester": 8, "credits": 8, "prerequisites": ["FAR02022"], "classes": []},
        "FAR01017": {"name": "QUÍMICA FARMACÊUTICA II", "semester": 8, "credits": 3, "prerequisites": ["CBS09011", "FAR01030", "FAR01031"], "classes": []},
        "FAR03029": {"name": "TOXICOLOGIA NA SAÚDE HUMANA", "semester": 8, "credits": 2, "prerequisites": ["CBS09011"], "classes": []},

        # --- ETAPA 9 ---
        "FAR03012": {"name": "CONTROLE DE QUALIDADE EM LABORATÓRIO DE ANÁLISES CLÍNICAS I", "semester": 9, "credits": 2, "prerequisites": ["FAR03010"], "classes": []},
        "EST002": {"name": "ESTÁGIO EM FARMÁCIA", "semester": 9, "credits": 0, "prerequisites": ["FAR01038", "FAR02017", "FAR02021", "FAR02046"], "classes": []},
        "FAR02039": {"name": "FARMÁCIA CLÍNICA", "semester": 9, "credits": 2, "prerequisites": ["FAR01038", "FAR02046", "FAR02210"], "classes": []},
        "FAR01019": {"name": "SÍNTESE ORGÂNICA MEDICINAL I", "semester": 9, "credits": 3, "prerequisites": ["FAR01017"], "classes": []},
        "FAR03306": {"name": "TOXICOLOGIA", "semester": 9, "credits": 4, "prerequisites": ["CBS09011", "FAR01013", "FAR03009", "FAR03010"], "classes": []},
        "TCC0001": {"name": "TRABALHO DE CONCLUSÃO DE CURSO EM FARMÁCIA", "semester": 9, "credits": 0, "prerequisites": [], "classes": []},
    }

for state_var in ["cadeiras_concluidas", "cadeiras_selecionadas"]:
    if state_var not in st.session_state:
        st.session_state[state_var] = []

# ==========================================
# 3. FUNÇÕES CALLBACK E PARSER
# ==========================================
def toggle_concluida(code):
    if st.session_state[f"chk_hist_{code}"]:
        if code not in st.session_state.cadeiras_concluidas:
            st.session_state.cadeiras_concluidas.append(code)
        if code in st.session_state.cadeiras_selecionadas:
            st.session_state.cadeiras_selecionadas.remove(code)
    else:
        if code in st.session_state.cadeiras_concluidas:
            st.session_state.cadeiras_concluidas.remove(code)

def toggle_matricula(code):
    if st.session_state[f"chk_mat_{code}"]:
        if code not in st.session_state.cadeiras_selecionadas:
            st.session_state.cadeiras_selecionadas.append(code)
    else:
        if code in st.session_state.cadeiras_selecionadas:
            st.session_state.cadeiras_selecionadas.remove(code)

def parse_ufrgs_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')
    parsed_data = {}
    
    for table in tables:
        rows = table.find_all('tr')
        current_code = None 
        
        for row in rows:
            cols = row.find_all(['td', 'th'])
            cols_text = [ele.text.strip() for ele in cols]
            
            if len(cols_text) >= 10 and "Atividades de Ensino" not in cols_text[0]:
                raw_materia = cols_text[0]
                turma = cols_text[2]
                match = re.search(r'\(([A-Z0-9]+)\)', raw_materia)
                
                if match:
                    current_code = match.group(1)
                    if current_code not in parsed_data:
                        parsed_data[current_code] = {"classes": []}
                
                if current_code and turma:
                    horario_str = cols_text[8] 
                    professor = cols_text[9] 
                    
                    horarios_limpos = [h.strip() for h in horario_str.split('\n') if h.strip() and h.strip() != "2" and h.strip() != "1"]
                    horario_final = " | ".join(horarios_limpos)
                    prof_limpo = professor.split('-')[0].strip() if professor else "A definir"
                    
                    parsed_data[current_code]["classes"].append({
                        "id": f"Turma {turma}",
                        "professor": prof_limpo,
                        "raw_schedule": horario_final
                    })
    return parsed_data

# ==========================================
# 4. MENU LATERAL
# ==========================================
st.sidebar.title("🧪 Portal da Farmácia")
page = st.sidebar.radio("Navegação:", ["0. Meu Histórico", "1. Montar Grade", "2. Grade Semanal Visual", "3. Administração (Atualizar Horários)"], key="nav_page")
st.sidebar.markdown("---")

st.sidebar.subheader("Progresso do Histórico")
st.sidebar.metric("Cadeiras Concluídas", len(st.session_state.cadeiras_concluidas))
tot_cadeiras = len(st.session_state.cadeiras_farmacia)
porcentagem = (len(st.session_state.cadeiras_concluidas) / tot_cadeiras) * 100 if tot_cadeiras > 0 else 0
st.sidebar.progress(min(porcentagem / 100, 1.0), text=f"{porcentagem:.1f}% do curso")
st.sidebar.markdown("---")

st.sidebar.subheader("Resumo da Matrícula")
st.sidebar.metric("Cadeiras Pré-Selecionadas", len(st.session_state.cadeiras_selecionadas))
tot_credits = sum([st.session_state.cadeiras_farmacia[c].get("credits", 0) for c in st.session_state.cadeiras_selecionadas if c in st.session_state.cadeiras_farmacia])
st.sidebar.metric("Créditos Totais (Semestre)", tot_credits)

if st.sidebar.button("🗑️ Limpar Tudo"):
    st.session_state.cadeiras_concluidas.clear()
    st.session_state.cadeiras_selecionadas.clear()
    st.rerun()

all_semesters = sorted(list(set(info.get("semester", 1) for info in st.session_state.cadeiras_farmacia.values())))

# ==========================================
# PÁGINA 0: MEU HISTÓRICO
# ==========================================
if page == "0. Meu Histórico":
    st.title("📚 Meu Histórico Acadêmico")
    st.write("Marque as disciplinas que você **já concluiu**.")

    tabs = st.tabs([f"{sem}ª Etapa" for sem in all_semesters])

    for idx, sem in enumerate(all_semesters):
        with tabs[idx]:
            col_btn1, col_btn2, _ = st.columns([2, 2, 6])
            
            if col_btn1.button("✅ Marcar Etapa", key=f"all_h_{sem}"):
                for c, info in st.session_state.cadeiras_farmacia.items():
                    if info["semester"] == sem:
                        if c not in st.session_state.cadeiras_concluidas:
                            st.session_state.cadeiras_concluidas.append(c)
                        if c in st.session_state.cadeiras_selecionadas:
                            st.session_state.cadeiras_selecionadas.remove(c)
                        st.session_state[f"chk_hist_{c}"] = True
                st.rerun()
                
            if col_btn2.button("❌ Desmarcar Etapa", key=f"none_h_{sem}"):
                for c, info in st.session_state.cadeiras_farmacia.items():
                    if info["semester"] == sem:
                        if c in st.session_state.cadeiras_concluidas:
                            st.session_state.cadeiras_concluidas.remove(c)
                        st.session_state[f"chk_hist_{c}"] = False
                st.rerun()
            
            st.markdown("---")
            with st.container(height=500):
                sem_subjects = {c: i for c, i in st.session_state.cadeiras_farmacia.items() if i["semester"] == sem}
                cols_in_tab = st.columns(3) 
                
                for i, (code, info) in enumerate(sem_subjects.items()):
                    with cols_in_tab[i % 3]:
                        is_concluida = code in st.session_state.cadeiras_concluidas
                        card_class = "card-concluida" if is_concluida else ""
                        nome_materia = info.get("name", "Nome indisponível")
                        
                        st.markdown(f"""
                        <div class="subject-card {card_class}">
                            <div class="subject-meta">CÓDIGO: <b>{code}</b></div>
                            <div class="subject-title">{nome_materia}</div>
                            <span class="credit-badge">{info.get('credits', 0)} Créditos</span>
                        </div>
                        """, unsafe_allow_html=True)
                        st.checkbox("✓ Marcar como Concluída", value=is_concluida, key=f"chk_hist_{code}", on_change=toggle_concluida, args=(code,))

# ==========================================
# PÁGINA 1: MONTAR GRADE (MATRÍCULA)
# ==========================================
elif page == "1. Montar Grade":
    st.title("🌳 Montar Grade (Matrícula)")
    st.markdown("<span class='status-badge badge-concluida'>🟦 Já Realizada</span> <span class='status-badge badge-liberada'>🟩 Liberada</span> <span class='status-badge badge-trancada'>🟨 Trancada</span>", unsafe_allow_html=True)

    def render_mat_card(code, info):
        is_concluida = code in st.session_state.cadeiras_concluidas
        missing_prereqs = [req for req in info.get("prerequisites", []) if req not in st.session_state.cadeiras_concluidas]

        if is_concluida:
            card_class, status_badge = "card-concluida", "<span class='status-badge badge-concluida'>🟦 REALIZADA</span>"
        elif len(missing_prereqs) == 0:
            card_class, status_badge = "card-liberada", "<span class='status-badge badge-liberada'>🟩 LIBERADA</span>"
        else:
            card_class, status_badge = "card-trancada", "<span class='status-badge badge-trancada'>🟨 TRANCADA</span>"

        # --- AQUI: Inserido o semestre/etapa na frente do pré-requisito ---
        prereqs_html = ""
        for req in info.get("prerequisites", []):
            req_info = st.session_state.cadeiras_farmacia.get(req, {})
            sem_req = req_info.get("semester", "?")
            cor = "#dcfce7" if req in st.session_state.cadeiras_concluidas else "#fee2e2"
            texto = "Req OK" if req in st.session_state.cadeiras_concluidas else "Falta Req"
            cor_texto = "#15803d" if req in st.session_state.cadeiras_concluidas else "#b91c1c"
            
            prereqs_html += f"<span class='prereq-badge' style='background-color:{cor}; color:{cor_texto};'>{texto}: {req} ({sem_req}ª Etapa)</span> "

        nome_materia = info.get("name", "Nome indisponível")

        st.markdown(f"""
        <div class="subject-card {card_class}">
            {status_badge}
            <div class="subject-meta">CÓDIGO: <b>{code}</b></div>
            <div class="subject-title">{nome_materia}</div>
            <span class="credit-badge">{info.get('credits', 0)} Créditos</span>
            <div>{prereqs_html}</div>
        </div>
        """, unsafe_allow_html=True)

        is_selected = code in st.session_state.cadeiras_selecionadas
        if is_concluida:
            st.checkbox(f"Selecionar {code}", value=False, disabled=True, key=f"chk_mat_{code}")
        else:
            st.checkbox("Adicionar à Grade", value=is_selected, key=f"chk_mat_{code}", on_change=toggle_matricula, args=(code,))

    def render_cards_grid(subjects_dict):
        cols_in_tab = st.columns(3)
        for i, (code, info) in enumerate(subjects_dict.items()):
            with cols_in_tab[i % 3]:
                render_mat_card(code, info)

    tabs = st.tabs([f"{sem}ª Etapa" if sem != 10 else "10ª Etapa (FDC/Eletivas)" for sem in all_semesters])

    for idx, sem in enumerate(all_semesters):
        with tabs[idx]:
            if sem != 10:
                col_btn1, col_btn2, _ = st.columns([2, 2, 6])
                sem_subjects = {c: i for c, i in st.session_state.cadeiras_farmacia.items() if i["semester"] == sem}
                
                if col_btn1.button("➕ Adicionar Etapa", key=f"all_m_{sem}"):
                    for c, info in sem_subjects.items():
                        if c not in st.session_state.cadeiras_concluidas and c not in st.session_state.cadeiras_selecionadas:
                            st.session_state.cadeiras_selecionadas.append(c)
                        st.session_state[f"chk_mat_{c}"] = True
                    st.rerun()

                if col_btn2.button("➖ Remover Etapa", key=f"none_m_{sem}"):
                    for c, info in sem_subjects.items():
                        if c in st.session_state.cadeiras_selecionadas:
                            st.session_state.cadeiras_selecionadas.remove(c)
                        st.session_state[f"chk_mat_{c}"] = False
                    st.rerun()

                st.markdown("---")
                with st.container(height=500):
                    render_cards_grid(sem_subjects)

# ==========================================
# PÁGINA 2: GRADE SEMANAL (LINHA DO TEMPO)
# ==========================================
# ==========================================
# PÁGINA 2: GRADE SEMANAL (LINHA DO TEMPO)
# ==========================================
elif page == "2. Grade Semanal Visual":
    st.title("📅 Construtor de Grade Semanal")
    
    if not st.session_state.cadeiras_selecionadas:
        st.info("💡 Você ainda não selecionou nenhuma disciplina. Vá na aba '1. Montar Grade' primeiro!")
    else:
        col_left, col_right = st.columns([1.2, 2.8])

        with col_left:
            st.markdown("### 🛠️ Configurar Turmas")
            st.write("Abra a pasta da matéria e escolha a turma desejada.")
            
            cores_disponiveis = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#f97316", "#14b8a6", "#6366f1"]
            mapa_cores = {}
            
            for i, code in enumerate(st.session_state.cadeiras_selecionadas):
                info = st.session_state.cadeiras_farmacia.get(code)
                if not info: continue
                
                mapa_cores[code] = cores_disponiveis[i % len(cores_disponiveis)]
                nome_mat = info.get("name", code)
                
                with st.expander(f"📁 {nome_mat}"):
                    st.markdown(f"<span style='color:{mapa_cores[code]}; font-size:16px;'>⬤</span> **Código:** {code}", unsafe_allow_html=True)
                    classes_list = info.get("classes", [])
                    
                    if not classes_list:
                        st.warning("Sem turmas importadas. Vá na aba de Administração.")
                    else:
                        opcoes_labels = ["🚫 Não alocar ainda"]
                        mapa_opcoes = {"🚫 Não alocar ainda": "Nenhuma"}
                        
                        for c in classes_list:
                            raw_horario = c.get('raw_schedule', 'Sem horário')
                            prof = c.get('professor', 'A definir')
                            id_turma = c.get('id', 'X')
                            
                            # FILTRO NOVO: Limpa o lixo da UFRGS para o texto do menu lateral
                            matches_horario = re.findall(r'(Segunda|Terça|Quarta|Quinta|Sexta|Sábado).*?(\d{1,2}:\d{2}\s*-\s*\d{1,2}:\d{2})', raw_horario)
                            if matches_horario:
                                horario_limpo = " e ".join([f"{dia} {hora}" for dia, hora in matches_horario])
                            else:
                                horario_limpo = "Horário a definir"
                            
                            label = f"📍 {id_turma} | {prof}\n(Horário: {horario_limpo})"
                            opcoes_labels.append(label)
                            mapa_opcoes[label] = id_turma
                        
                        escolha = st.radio("Escolha a Turma:", opcoes_labels, key=f"radio_{code}")
                        st.session_state[f"sel_{code}"] = mapa_opcoes[escolha]

        with col_right:
            st.write("📊 **Sua Semana**")
            
            dias_semana = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
            agenda = {dia: [] for dia in dias_semana}
            turmas_alocadas = 0
            
            def time_to_mins(t_str):
                h, m = map(int, t_str.split(':'))
                return h * 60 + m
            
            START_DAY_MINS = 7 * 60 + 30
            END_DAY_MINS = 22 * 60 + 30
            TOTAL_HEIGHT_PX = END_DAY_MINS - START_DAY_MINS
            
            for code in st.session_state.cadeiras_selecionadas:
                info = st.session_state.cadeiras_farmacia.get(code)
                if not info: continue
                
                sel_id = st.session_state.get(f"sel_{code}", "Nenhuma")
                if sel_id == "Nenhuma": continue 
                
                turma_data = next((c for c in info["classes"] if c["id"] == sel_id), None)
                
                if turma_data and "raw_schedule" in turma_data:
                    raw_str = turma_data["raw_schedule"]
                    matches = re.findall(r'(Segunda|Terça|Quarta|Quinta|Sexta|Sábado).*?(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', raw_str)
                    
                    for day, start_t, end_t in matches:
                        agenda[day].append({
                            "start": start_t,
                            "end": end_t,
                            "name": info['name'],
                            "code": code,
                            "class_id": turma_data['id'],
                            "color": mapa_cores[code]
                        })
                    turmas_alocadas += 1

            if turmas_alocadas == 0:
                st.info("👈 Sua grade está vazia. Abra as pastas ao lado e selecione as turmas!")
            else:
                html_cal = f'<div style="display: flex; background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px 8px 0 0; font-weight: bold; color: #334155; margin-top: 10px;"><div style="width: 50px; text-align: center; padding: 12px 0; border-right: 1px solid #cbd5e1;">⏰</div>'
                
                for d in dias_semana:
                    html_cal += f'<div style="flex: 1; text-align: center; padding: 12px 0; border-right: 1px solid #cbd5e1;">{d}</div>'
                html_cal += '</div>'
                
                html_cal += f'<div style="display: flex; height: {TOTAL_HEIGHT_PX}px; border: 1px solid #cbd5e1; border-top: none; background: white; border-radius: 0 0 8px 8px; position: relative;">'
                
                html_cal += '<div style="position: absolute; width: 100%; height: 100%; pointer-events: none;">'
                for h in range(8, 23):
                    top_pos = (h * 60) - START_DAY_MINS
                    html_cal += f'<div style="position: absolute; top: {top_pos}px; width: 100%; border-top: 1px dashed #e2e8f0; opacity: 0.7;"></div>'
                html_cal += '</div>'
                
                html_cal += '<div style="width: 50px; position: relative; background: #f8fafc; border-right: 1px solid #cbd5e1;">'
                for h in range(8, 23):
                    top_pos = (h * 60) - START_DAY_MINS - 8
                    html_cal += f'<div style="position: absolute; top: {top_pos}px; width: 100%; text-align: center; font-size: 11px; color: #64748b;">{h}:00</div>'
                html_cal += '</div>'
                
                for day in dias_semana:
                    html_cal += '<div style="flex: 1; position: relative; border-right: 1px solid #f1f5f9;">'
                    
                    for item in agenda[day]:
                        s_mins = time_to_mins(item["start"])
                        e_mins = time_to_mins(item["end"])
                        top = s_mins - START_DAY_MINS
                        height = e_mins - s_mins
                        
                        # CORREÇÃO DO BUG HTML: Sem espaços ou quebras de linha para não acionar o Markdown
                        html_cal += f'<div class="calendar-event" style="top: {top}px; height: {height}px; background-color: {item["color"]}; border-left: 4px solid rgba(0,0,0,0.2);" title="{item["name"]}"><b>{item["code"]}</b><span class="turma-tag">{item["class_id"]}</span></div>'
                        
                    html_cal += '</div>'
                
                html_cal += '</div>'
                st.markdown(html_cal, unsafe_allow_html=True)

# ==========================================
# PÁGINA 3: ADMINISTRAÇÃO 
# ==========================================
elif page == "3. Administração (Atualizar Horários)":
    st.title("⚙️ Painel de Administração - Importar Horários")
    
    # --- AQUI: Retornadas as instruções originais do Ctrl + S ---
    st.markdown("""
    **Como utilizar:**
    1. Entre no Portal do Aluno da UFRGS > **Horários e Vagas por Grupo de Matrícula**.
    2. Pressione `Ctrl + S` e salve a página como **"Página Web, Somente HTML"**.
    3. Faça o upload do arquivo abaixo.
    """)
    
    uploaded_file = st.file_uploader("Envie o arquivo HTML (extensão .html ou .htm)", type=["html", "htm"])
    
    if uploaded_file is not None:
        html_bytes = uploaded_file.read()
        extracted_data = parse_ufrgs_html(html_bytes)
        
        st.success(f"Encontradas {len(extracted_data)} disciplinas no arquivo HTML fornecido!")
        
        with st.expander("Verificar Extração Bruta"):
            st.json(extracted_data)
        
        if st.button("💾 Atualizar Grade com os Horários Novos"):
            contagem = 0
            for code, data in extracted_data.items():
                if code in st.session_state.cadeiras_farmacia:
                    st.session_state.cadeiras_farmacia[code]["classes"] = data["classes"]
                    contagem += 1
            st.success(f"🎉 Horários de {contagem} disciplinas atualizados com sucesso no banco de dados interno!")