import streamlit as st
import random
import math
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === 英語クイズデータ（解説付き） ===
ENG_QUIZZES_DATA = [
    # (既存の英語クイズデータは省略)
]

# === 【追加】理科クイズデータ（仮） ===
SCI_QUIZZES_DATA = [
    {
        "q": "水が固体になったときの呼び名は？",
        "correct": "氷",
        "choices": ["氷", "水蒸気", "湯気", "ドライアイス"],
        "explanation": "水は摂氏0度以下で固体になり、これを「氷」と呼びます。「水蒸気」は気体になったときの呼び名です。"
    },
    {
        "q": "太陽系で最も大きい惑星は？",
        "correct": "木星",
        "choices": ["地球", "土星", "木星", "太陽"],
        "explanation": "木星は太陽系最大の惑星です。「太陽」は恒星であり、惑星ではありません。"
    },
    {
        "q": "植物が光を使ってエネルギーを作り出す過程を何という？",
        "correct": "光合成",
        "choices": ["呼吸", "蒸散", "光合成", "電離"],
        "explanation": "光合成は、植物が光エネルギーを利用して二酸化炭素と水から有機物（デンプンなど）を合成する働きです。"
    }
]


# --- クイズ種別選択 ---
def select_quiz(qtype):
    st.session_state.quiz_type = qtype

if "quiz_type" not in st.session_state:
    st.title("クイズを選んでください")
    # 【変更】理科クイズボタンを追加するために列を3つに
    c1, c2, c3 = st.columns(3)
    with c1:
        st.button(
            "平方根クイズ",
            on_click=select_quiz,
            args=("sqrt",)
        )
    with c2:
        st.button(
            "中３英語クイズ",
            on_click=select_quiz,
            args=("eng",)
        )
    # 【追加】理科クイズボタン
    with c3:
        st.button(
            "理科クイズ",
            on_click=select_quiz,
            args=("sci",)
        )
    st.stop()

# === Google Sheets 連携 ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_available = False
if "gcp_service_account" in st.secrets:
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open("ScoreBoard") # スプレッドシート名を正確に指定
        creds_available = True
    except Exception as e:
        st.error(f"Google Sheets認証情報に問題があります: {e}")
else:
    st.warning("Google Sheetsの認証情報が設定されていません。ランキング機能は利用できません。")

# quiz_type が確定した後に sheet を設定
if "quiz_type" in st.session_state and creds_available:
    try:
        # 【変更】理科クイズのシート選択を追加
        if st.session_state.quiz_type == "sqrt":
            sheet = spreadsheet.get_worksheet(1) # Sheet2 (インデックス1)
        elif st.session_state.quiz_type == "eng":
            sheet = spreadsheet.get_worksheet(2) # Sheet3 (インデックス2)
        elif st.session_state.quiz_type == "sci":
            sheet = spreadsheet.get_worksheet(3) # Sheet4 (インデックス3)
        else:
            sheet = spreadsheet.get_worksheet(0) # Fallback
    except Exception as e:
        st.error(f"ワークシートの取得に失敗しました: {e}")
        creds_available = False # シート取得失敗も利用不可扱い

if not creds_available: # creds_availableがFalseならダミーシートを使用
    class DummySheet:
        def append_row(self, data): st.info("（ランキング機能無効：スコアは保存されません）")
        def get_all_records(self): return []
    sheet = DummySheet()

# === 効果音 URL ===
NAME_URL    = "https://github.com/trpv1/square-root-app/raw/main/static/name.mp3"
START_URL   = "https://github.com/trpv1/square-root-app/raw/main/static/start.mp3"
CORRECT_URL = "https://github.com/trpv1/square-root-app/raw/main/static/correct.mp3"
WRONG_URL   = "https://github.com/trpv1/square-root-app/raw/main/static/wrong.mp3"
RESULT1_URL = "https://github.com/trpv1/square-root-app/raw/main/static/result_1.mp3"
RESULT2_URL = "https://github.com/trpv1/square-root-app/raw/main/static/result_2.mp3"

def play_sound(url: str):
    st.markdown(
        f"<audio autoplay style='display:none'><source src='{url}' type='audio/mpeg'></audio>",
        unsafe_allow_html=True,
    )

# === セッション初期化 ===
def init_state():
    defaults = dict(
        nickname="",
        started=False,
        start_time=None,
        score=0,
        total=0,
        current_problem=None,
        answered=False,
        is_correct=None,
        user_choice="",
        saved=False,
        played_name=False,
        # 【変更】理科クイズ用の状態変数を追加
        asked_eng_indices_this_session=[],
        incorrectly_answered_eng_questions=[],
        asked_sci_indices_this_session=[],
        incorrectly_answered_sci_questions=[],
        current_problem_display_choices=[],
    )
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init_state()

# --- 問題生成（√問題 or 英語問題 or 理科問題） ---
def make_problem():
    if st.session_state.quiz_type == "sqrt":
        fav = {12, 18, 20, 24, 28, 32, 40, 48, 50, 54, 56, 58}
        population = list(range(2, 101))
        weights = [10 if n in fav else 1 for n in population]
        a = random.choices(population, weights)[0]

        for i in range(int(math.sqrt(a)), 0, -1):
            if a % (i * i) == 0:
                outer, inner = i, a // (i * i)
                correct = (
                    str(outer)
                    if inner == 1
                    else (f"√{inner}" if outer == 1 else f"{outer}√{inner}")
                )
                choices_set = {correct}
                while len(choices_set) < 4:
                    o_fake = random.randint(1, max(9, outer + 2))
                    i_fake = random.randint(1, max(10, inner + 5))
                    if i_fake == 1 and o_fake == outer: continue
                    if o_fake == outer and i_fake == inner: continue
                    fake = (
                        str(o_fake)
                        if i_fake == 1
                        else (f"√{i_fake}" if o_fake == 1 else f"{o_fake}√{i_fake}")
                    )
                    choices_set.add(fake)
                choices = random.sample(list(choices_set), k=min(len(choices_set), 4))
                return a, correct, choices
        return None # ループで見つからなかった場合 (通常はありえないが)

    # 【変更】英語と理科のロジックを共通化できるように条件を変更
    elif st.session_state.quiz_type in ["eng", "sci"]:
        # クイズ種別に応じて使用するデータとセッション変数を決定
        if st.session_state.quiz_type == "eng":
            quiz_data = ENG_QUIZZES_DATA
            session_key = "asked_eng_indices_this_session"
        else: # "sci"
            quiz_data = SCI_QUIZZES_DATA
            session_key = "asked_sci_indices_this_session"

        available_quizzes_with_indices = []
        for i, quiz_item in enumerate(quiz_data):
            if i not in st.session_state[session_key]:
                available_quizzes_with_indices.append({"original_index": i, "data": quiz_item})
        
        if not available_quizzes_with_indices:
            return None

        selected_item = random.choice(available_quizzes_with_indices)
        quiz_data_with_explanation = selected_item["data"]
        st.session_state[session_key].append(selected_item["original_index"])
        return quiz_data_with_explanation
    else:
        return None

# === スコア保存／取得 ===
def save_score(name, score_val):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        sheet.append_row([name, score_val, ts])
    except Exception as e:
        st.error(f"スコアの保存に失敗しました: {e}")

def top3():
    try:
        records = sheet.get_all_records()
        valid_records = []
        for r in records:
            try:
                score_value = r.get("score")
                if isinstance(score_value, str):
                    if score_value.isdigit() or (score_value.startswith('-') and score_value[1:].isdigit()):
                        score_value = int(score_value)
                    else:
                        score_value = 0
                elif not isinstance(score_value, int):
                    score_value = 0
                r["score"] = score_value
                valid_records.append(r)
            except ValueError:
                r["score"] = 0 
                valid_records.append(r)
        return sorted(valid_records, key=lambda x: x.get("score", 0), reverse=True)[:3]
    except Exception as e:
        print(f"ランキング取得エラー: {e}")
        return []

# --- ページ制御：クラス選択、パスワード、同意、ニックネーム ---
# (このセクションのコードは変更なし)
if "class_selected" not in st.session_state:
    st.title("所属を選択してください")
    def select_class(cls):
        st.session_state.class_selected = cls
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: st.button("3R1", on_click=select_class, args=("3R1",))
    with c2: st.button("3R2", on_click=select_class, args=("3R2",))
    with c3: st.button("3R3", on_click=select_class, args=("3R3",))
    with c4: st.button("講師", on_click=select_class, args=("講師",))
    with c5: st.button("その他", on_click=select_class, args=("その他",))
    st.stop()

if not st.session_state.get("password_ok", False):
    st.text_input("Password：作成者の担当クラスは？", type="password", key="pw_input")
    def check_password():
        if st.session_state.pw_input == "3R3": # パスワード
            st.session_state.password_ok = True
        else:
            st.error("パスワードが違います")
    st.button("確認", on_click=check_password)
    st.stop()

if not st.session_state.get("agreed", False):
    st.markdown("## ⚠️ 注意事項", unsafe_allow_html=True)
    st.write("""
    - **個人情報**（本名・住所・電話番号など）の入力は禁止です。  
    - **1日30分以上**の継続使用はお控えください（他の勉強時間を優先しましょう）。  
    - 本アプリは**初めて作成したアプリ**のため、低クオリティです。すみません。  
    - エラーメッセージが出ることがありますが、**ページを更新**すると改善される場合があります。  
    - 上記ルールを遵守いただけない場合は、利用を中止いたします。  
    """)
    def agree_and_continue():
        st.session_state.agreed = True
    st.button("■ 同意して次へ", on_click=agree_and_continue)
    st.stop()

if not st.session_state.get("nickname"):
    if not st.session_state.get("played_name", False):
        play_sound(NAME_URL)
        st.session_state.played_name = True
    st.title("1分間クイズ")
    st.text_input("ニックネームを入力してください", key="nick_input", max_chars=12)
    def set_nickname():
        val = st.session_state.nick_input.strip()
        if val:
            st.session_state.nickname = val
        else:
            st.warning("ニックネームを入力してください。")
    st.button("決定", on_click=set_nickname)
    st.stop()

# === クイズ本体の表示ロジック ===
if not st.session_state.get("started", False):
    # 【変更】理科クイズのラベル表示に対応
    quiz_labels = {"sqrt": "平方根クイズ", "eng": "中3英語クイズ", "sci": "理科クイズ"}
    quiz_label = quiz_labels.get(st.session_state.quiz_type, "クイズ")
    
    st.title(f"{st.session_state.nickname} さんの{quiz_label}")
    st.write("**ルール**: 制限時間1分、正解+1点、不正解-1点")

    def start_quiz():
        play_sound(START_URL)
        st.session_state.started = True
        st.session_state.start_time = time.time()
        # init_stateで設定した値をここでリセット
        st.session_state.score = 0
        st.session_state.total = 0
        st.session_state.answered = False
        st.session_state.is_correct = None
        st.session_state.user_choice = ""
        st.session_state.saved = False
        st.session_state.asked_eng_indices_this_session = []
        st.session_state.incorrectly_answered_eng_questions = []
        # 【追加】理科クイズ用の状態もリセット
        st.session_state.asked_sci_indices_this_session = []
        st.session_state.incorrectly_answered_sci_questions = []
        
        st.session_state.current_problem = make_problem()

        if st.session_state.current_problem is None:
            st.session_state.current_problem_display_choices = []
        # 【変更】英語と理科で共通の処理
        elif st.session_state.quiz_type in ["eng", "sci"]:
            problem_data = st.session_state.current_problem
            if "choices" in problem_data and problem_data["choices"]:
                shuffled_choices = random.sample(problem_data["choices"], len(problem_data["choices"]))
                st.session_state.current_problem_display_choices = shuffled_choices
            else:
                st.session_state.current_problem_display_choices = []
        elif st.session_state.quiz_type == "sqrt":
            _, _, sqrt_choices = st.session_state.current_problem
            st.session_state.current_problem_display_choices = sqrt_choices
    
    st.button("スタート！", on_click=start_quiz)
    st.stop()

# --- クイズ実行中のメインループ ---
current_time = time.time()
elapsed_time = 0
if st.session_state.get("start_time") is not None:
    elapsed_time = int(current_time - st.session_state.start_time)
remaining = max(0, 60 - elapsed_time)

st.markdown(f"## ⏱️ {st.session_state.nickname} さんのタイムアタック！")

mm_display, ss_display = divmod(remaining, 60)
st.info(f"残り {mm_display:02d}:{ss_display:02d} ｜ スコア {st.session_state.score} ｜ 挑戦 {st.session_state.total}")

if remaining == 0: # --- タイムアップ処理 ---
    if not st.session_state.get("time_up_processed", False):
        st.warning("⏰ タイムアップ！")
        st.write(f"最終スコア: {st.session_state.score}点 ({st.session_state.total}問)")

        # 【変更】理科クイズの間違い復習にも対応
        incorrect_questions = []
        if st.session_state.quiz_type == "eng":
            incorrect_questions = st.session_state.incorrectly_answered_eng_questions
        elif st.session_state.quiz_type == "sci":
            incorrect_questions = st.session_state.incorrectly_answered_sci_questions
        
        if incorrect_questions:
            st.markdown("---") 
            st.subheader("📝 間違えた問題の復習")
            for i, item in enumerate(incorrect_questions):
                container = st.container(border=True)
                container.markdown(f"**問題 {i+1}**")
                container.markdown(item['question_text'])
                container.markdown(f"あなたの解答: <span style='color:red;'>{item['user_answer']}</span>", unsafe_allow_html=True)
                container.markdown(f"正解: <span style='color:green;'>{item['correct_answer']}</span>", unsafe_allow_html=True)
                with container.expander("💡 解説を見る"):
                    st.markdown(item['explanation'])
            st.markdown("---")

        if not st.session_state.saved:
            full_name = f"{st.session_state.class_selected}_{st.session_state.nickname}"
            save_score(full_name, st.session_state.score)
            st.session_state.saved = True
            
            ranking = top3()
            is_in_top3 = False
            if ranking:
                if len(ranking) < 3 or st.session_state.score >= ranking[min(len(ranking)-1, 2)].get("score", -float('inf')):
                    is_in_top3 = any(r.get("name") == full_name and r.get("score") == st.session_state.score for r in ranking[:3])
                    if not is_in_top3 and (len(ranking) <3 or st.session_state.score >= ranking[min(len(ranking)-1, 2)].get("score", -float('inf'))):
                        is_in_top3 = True
            else:
                is_in_top3 = True

            if is_in_top3:
                play_sound(RESULT1_URL)
            else:
                play_sound(RESULT2_URL)
            st.balloons()
        st.session_state.time_up_processed = True

    st.write("### 🏆 歴代ランキング（上位3名）")
    current_ranking_data = top3() 
    if current_ranking_data:
        for i, r_data in enumerate(current_ranking_data, 1):
            name_display = r_data.get("name", "名無し")
            score_display = r_data.get("score", 0)
            st.write(f"{i}. {name_display} — {score_display}点")
    else:
        st.write("まだランキングデータがありません。")

    def restart_all():
        keys_to_remove = [
            "started", "start_time", "score", "total", "current_problem",
            "answered", "is_correct", "user_choice", "saved",
            "asked_eng_indices_this_session", "incorrectly_answered_eng_questions",
            # 【追加】理科クイズ用の状態もリセット対象に
            "asked_sci_indices_this_session", "incorrectly_answered_sci_questions",
            "current_problem_display_choices", "time_up_processed",
            "nick_input", "nickname"
        ]
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
        init_state()
        st.rerun()

    st.button("🔁 もう一度挑戦", on_click=restart_all)
    st.stop()

# --- 問題表示と解答プロセス (タイムアップしていない場合) ---
problem_data = st.session_state.current_problem

if problem_data is None:
    st.warning("全ての問題を解きました！お疲れ様でした。もう一度挑戦する場合は下のボタンを押してください。")
    # ここでリスタートボタンなどを表示
    def force_restart():
        st.session_state.start_time = time.time() - 60 # 強制的にタイムアップさせる
        st.rerun()
    st.button("結果画面へ", on_click=force_restart)
    st.stop()

question_text_to_display = ""
correct_answer_string = ""

if st.session_state.quiz_type == "sqrt":
    q_display_value, correct_answer_string_local, _ = problem_data
    question_text_to_display = f"√{q_display_value} を簡約すると？"
    correct_answer_string = correct_answer_string_local
# 【変更】英語と理科で共通の処理
elif st.session_state.quiz_type in ["eng", "sci"]:
    q_dict = problem_data
    question_text_to_display = q_dict["q"]
    correct_answer_string = q_dict["correct"]

st.subheader(question_text_to_display)
choices_for_radio = st.session_state.current_problem_display_choices

if not st.session_state.answered:
    if not choices_for_radio:
        st.error("選択肢が読み込めませんでした。ページを更新するか、やり直してください。")
    else:
        user_choice = st.radio(
            "選択肢を選んでください",
            choices_for_radio,
            key=f"radio_choice_{st.session_state.total}"
        )
        if st.button("解答する", key=f"answer_button_{st.session_state.total}"):
            st.session_state.answered = True
            st.session_state.user_choice = user_choice
            st.session_state.total += 1

            if st.session_state.user_choice == correct_answer_string:
                st.session_state.score += 1
                st.session_state.is_correct = True
                play_sound(CORRECT_URL)
            else:
                st.session_state.score -= 1
                st.session_state.is_correct = False
                play_sound(WRONG_URL)

                # 【変更】理科クイズの間違いも記録
                if st.session_state.quiz_type in ["eng", "sci"]:
                    current_q_data = st.session_state.current_problem
                    incorrect_list_key = f"incorrectly_answered_{st.session_state.quiz_type}_questions"
                    
                    st.session_state[incorrect_list_key].append({
                        "question_text": current_q_data["q"],
                        "user_answer": st.session_state.user_choice,
                        "correct_answer": correct_answer_string,
                        "explanation": current_q_data["explanation"]
                    })
            st.rerun() # 解答後に即座に再実行して結果表示に移行

# --- 結果表示と次の問題へのボタン (解答済みの場合) ---
if st.session_state.answered:
    if st.session_state.is_correct:
        st.success("🎉 正解！ +1点")
    else:
        st.error(f"😡 不正解！ 正解は {correct_answer_string} でした —1点")

    def next_q():
        st.session_state.current_problem = make_problem()
        st.session_state.answered = False
        st.session_state.is_correct = None
        st.session_state.user_choice = ""

        if st.session_state.current_problem is None:
            st.session_state.current_problem_display_choices = []
        # 【変更】英語と理科で共通の処理
        elif st.session_state.quiz_type in ["eng", "sci"]:
            eng_problem_data = st.session_state.current_problem
            if "choices" in eng_problem_data and eng_problem_data["choices"]:
                shuffled_choices = random.sample(eng_problem_data["choices"], len(eng_problem_data["choices"]))
                st.session_state.current_problem_display_choices = shuffled_choices
            else:
                st.session_state.current_problem_display_choices = []
        elif st.session_state.quiz_type == "sqrt":
            _, _, sqrt_choices = st.session_state.current_problem
            st.session_state.current_problem_display_choices = sqrt_choices
        st.rerun() # 次の問題へボタンで再実行

    st.button("次の問題へ", on_click=next_q, key=f"next_q_button_{st.session_state.total}")
    st.stop()
