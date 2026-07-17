import streamlit as st
import requests
import uuid
import urllib3


# Отключаем SSL-предупреждения
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ====== ВАШИ КЛЮЧИ GigaChat ======
# Берём ключи из безопасного хранилища
CLIENT_ID = st.secrets["CLIENT_ID"]
AUTH_KEY = st.secrets["AUTH_KEY"]  
# ====== 👇👇👇 СЮДА ВСТАВЬТЕ ИМЯ ФАЙЛА 👇👇👇 ======
RESUME_FILE = "2026_resume_llv.txt"   # ← ЗДЕСЬ МЕНЯЙТЕ НАЗВАНИЕ ФАЙЛА
# ================================================

# ====== ЗАГРУЗКА РЕЗЮМЕ ======
def load_resume(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return [chunk.strip() for chunk in text.split("---") if chunk.strip()]

# ====== ПОИСК ФРАГМЕНТА ======
def find_chunk(question, chunks):
    question_lower = question.lower()
    stop_words = {"какой", "какая", "какое", "какие", "где", "когда", "что", "это", "меня", "мой", "моя"}
    keywords = [word for word in question_lower.split() if word not in stop_words]
    
    if not keywords:
        return chunks[0]
    
    best_chunk = None
    best_score = 0
    for chunk in chunks:
        chunk_lower = chunk.lower()
        score = sum(2 for word in keywords if word in chunk_lower)
        if score > best_score:
            best_score = score
            best_chunk = chunk
    return best_chunk if best_chunk else chunks[0]

# ====== ОБЩЕНИЕ С GigaChat ======
def get_token():
    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "RqUID": str(uuid.uuid4()),
        "Authorization": f"Basic {AUTH_KEY}"
    }
    data = {"scope": "GIGACHAT_API_PERS", "client_id": CLIENT_ID}
    response = requests.post(url, headers=headers, data=data, verify=False)
    return response.json().get("access_token")

def ask_gigachat(question, context):
    token = get_token()
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}"
    }
    data = {
    "model": "GigaChat-2",
    "messages": [
        {
            "role": "system",
            "content": (
                "Ты - Лада Лебедянцева, SEO-специалист и веб-аналитик с 19-летним опытом. "
                "Твоя задача - отвечать на вопросы рекрутеров от первого лица, как будто ты сама общаешься с ними. "
                "ПРАВИЛА: "
                "1. Опирайся на факты из загруженного резюме (контекст). "
                "2. Если информация неполная - делай логические выводы на основе имеющихся данных, но не выдумывай. "
                "3. Если вопрос требует цифр - бери их из контекста. "
                "4. Если в контексте нет прямого ответа - скажи: 'В резюме нет точной информации, но я могу рассказать о своём опыте в этой области...' и приведи смежный пример. "
                "5. Отвечай уверенно, по делу, с конкретикой. Не будь роботом - используй живые формулировки. "
                "6. Если вопрос вообще не про тебя или резюме - вежливо скажи: 'Это не относится к моему опыту, уточните, пожалуйста, вопрос.'"
            )
        },
        {
            "role": "user",
            "content": f"Контекст (моё резюме):\n{context}\n\nВопрос рекрутера: {question}\n\nОтветь от моего имени, как будто я сама отвечаю на собеседовании."
        }
                ]
    response = requests.post(url, headers=headers, json=data, verify=False)
    return response.json()["choices"][0]["message"]["content"]

# ====== ИНТЕРФЕЙС ======
st.set_page_config(page_title="ИИ-ассистент по резюме", page_icon="📄")
st.title("📄 ИИ-ассистент по резюме")
st.markdown("Задайте вопрос о моём опыте, навыках или образовании.")

# Загружаем резюме (используем переменную RESUME_FILE)
chunks = load_resume(RESUME_FILE)
st.sidebar.success(f"✅ Резюме загружено: {len(chunks)} фрагментов")

# История диалога
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Поле ввода
if prompt := st.chat_input("Спросите о моём опыте..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Анализирую..."):
            context = find_chunk(prompt, chunks)
            answer = ask_gigachat(prompt, context)
            st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})