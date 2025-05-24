import streamlit as st
import random
import math
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# === 英語クイズデータ（解説付き） ===
ENG_QUIZZES_DATA = [
    {
        "q": "I got sleepy ( ) the meeting.\n（会議の間に眠くなった）",
        "correct": "during",
        "choices": ["for", "while", "during", "since"],
        "explanation": "「during + 名詞」は「～の間（特定の期間）」を示します。例: during the meeting (会議の間), during summer vacation (夏休みの間)。"
    },
    {
        "q": "We stayed in Kyoto ( ) five days.\n（私たちは5日間京都に滞在した）",
        "correct": "for",
        "choices": ["during", "while", "for", "within"],
        "explanation": "「for + 期間の長さ」は「～の間」を示します。例: for five days (5日間), for three years (3年間)。"
    },
    {
        "q": "He was cooking ( ) I was watching TV.\n（彼が料理している間、私はテレビを見ていた）",
        "correct": "while",
        "choices": ["during", "while", "for", "by"],
        "explanation": "「while + 主語 + 動詞」は「～する間に（接続詞）」として、同時に行われている2つの動作を示します。"
    },
    {
        "q": "Please finish the report ( ) Friday.\n（金曜日までにレポートを終えてください）",
        "correct": "by",
        "choices": ["until", "during", "by", "for"],
        "explanation": "「by + 時点」は「～までに（期限）」を示します。動作の完了期限を表します。「until」は「～までずっと（継続）」です。"
    },
    {
        "q": "I’ve lived here ( ) 2010.\n（2010年からずっとここに住んでいます）",
        "correct": "since",
        "choices": ["from", "for", "since", "at"],
        "explanation": "「since + 起点となる過去の時点」は「～以来ずっと」を示し、現在完了形と共によく使われます。"
    },
    {
        "q": "The shop is open ( ) 9 a.m. to 7 p.m.\n（その店は午前9時から午後7時まで開いている）",
        "correct": "from",
        "choices": ["since", "at", "within", "from"],
        "explanation": "「from A to B」は「AからBまで」という範囲（時間、場所）を示します。"
    },
    {
        "q": "She arrived ( ) the airport at noon.\n（彼女は正午に空港に到着した）",
        "correct": "at",
        "choices": ["on", "in", "at", "by"],
        "explanation": "「at + 比較的狭い場所・特定の地点」 (例: at the airport, at the station) や「at + 時刻」 (例: at noon, at 3 p.m.) で使います。"
    },
    {
        "q": "The train will arrive ( ) an hour.\n（電車は1時間以内に到着するでしょう）",
        "correct": "within",
        "choices": ["for", "during", "in", "within"],
        "explanation": "「within + 期間」は「～以内に」という期限内を示します。「in an hour」は「1時間後に」という意味にもなりますが、「1時間以内に」のニュアンスなら「within」がより明確です。"
    },
    {
        "q": "He didn’t sleep ( ) the movie.\n（彼は映画の間、眠らなかった）",
        "correct": "during",
        "choices": ["for", "while", "within", "during"],
        "explanation": "「during + 名詞」は「～の間（特定の期間）」を示します。例: during the movie (映画の間)。"
    },
    {
        "q": "Let’s wait here ( ) the rain stops.\n（雨が止むまでここで待とう）",
        "correct": "until",
        "choices": ["by", "since", "until", "for"],
        "explanation": "「until + 主語 + 動詞」または「until + 時/出来事」は「～までずっと（継続）」を示します。"
    },
    {
        "q": "He walked ( ) the bridge.\n（彼は橋を渡って歩いた）",
        "correct": "across",
        "choices": ["along", "through", "across", "over"],
        "explanation": "「across」は平面を横切る、または何かを渡る（橋、道、川など）動きを示します。「through」は何かを通り抜ける（トンネル、森など）、「along」は〜に沿って、です。"
    },
    {
        "q": "The cat jumped ( ) the wall.\n（その猫は塀を飛び越えた）",
        "correct": "over",
        "choices": ["above", "over", "across", "onto"],
        "explanation": "「over」は何かを越えて上を通過する動き（障害物など）を示します。「above」は位置関係で「～の上に」です。"
    },
    {
        "q": "She is good ( ) mathematics.\n（彼女は数学が得意だ）",
        "correct": "at",
        "choices": ["at", "in", "on", "about"],
        "explanation": "「be good at ～」で「～が得意である」という意味の一般的な表現です。"
    },
    {
        "q": "Tom is absent ( ) school today.\n（トムは今日学校を欠席している）",
        "correct": "from",
        "choices": ["from", "of", "in", "at"],
        "explanation": "「be absent from ～」で「～を欠席している」という意味になります。"
    },
    {
        "q": "I prefer tea ( ) coffee.\n（私はコーヒーより紅茶のほうが好きだ）",
        "correct": "to",
        "choices": ["with", "on", "than", "to"],
        "explanation": "「prefer A to B」で「BよりもAを好む」という意味です。「than」は使いません。"
    },
    {
        "q": "He succeeded ( ) passing the exam.\n（彼は試験に合格することに成功した）",
        "correct": "in",
        "choices": ["in", "at", "on", "with"],
        "explanation": "「succeed in ～ing」で「～することに成功する」という意味です。"
    },
    {
        "q": "The train runs ( ) Tokyo and Osaka.\n（その列車は東京と大阪の間を走っている）",
        "correct": "between",
        "choices": ["among", "to", "between", "through"],
        "explanation": "「between A and B」で「（2つのものの）間」を示します。「among」は「（3つ以上のものの）間」です。"
    },
    {
        "q": "The book was written ( ) Shakespeare.\n（その本はシェイクスピアによって書かれた）",
        "correct": "by",
        "choices": ["from", "of", "with", "by"],
        "explanation": "受動態で「～によって」行為者を示す場合は「by」を使います。"
    },
    {
        "q": "Let’s meet ( ) noon.\n（正午に会いましょう）",
        "correct": "at",
        "choices": ["on", "in", "by", "at"],
        "explanation": "「at + 時刻」 (例: at noon, at 5 o'clock) で特定の時刻を示します。"
    },
    {
        "q": "He divided the cake ( ) four pieces.\n（彼はケーキを4つに分けた）",
        "correct": "into",
        "choices": ["into", "in", "to", "by"],
        "explanation": "「divide A into B」で「AをBに分ける」という意味です。変化の結果「～の中に」入るニュアンスです。"
    },
    {
        "q": "I want to ( ) you about the plan.\n（その計画についてあなたと話したい）",
        "correct": "talk to",
        "choices": ["talk", "talk to", "tell", "say"],
        "explanation": "「talk to someone」または「talk with someone」で「（人）と話す」です。「tell someone something」は「（人）に（事）を告げる」。「say something (to someone)」は「（事）を言う（（人）に）」です。"
    },
    {
        "q": "She always speaks ( ) her grandfather kindly.\n（彼女はいつも優しく祖父に話しかける）",
        "correct": "to",
        "choices": ["with", "to", "at", "for"],
        "explanation": "「speak to someone」で「（人）に話しかける」という意味です。「speak with someone」も「（人）と話す」ですが、相互の会話のニュアンスが強まることがあります。"
    },
    {
        "q": "Please ( ) me the truth.\n（私に真実を話してください）",
        "correct": "tell",
        "choices": ["tell", "tell to", "tell with", "say"],
        "explanation": "「tell + 人 + 事」で「（人）に（事）を告げる、教える」という意味です。「say」は通常「say something」のように目的語を直接取ります。"
    },
    {
        "q": "My birthday is ( ) May 3rd.\n（私の誕生日は5月3日です）",
        "correct": "on",
        "choices": ["in", "at", "on", "by"],
        "explanation": "特定の日付や曜日には前置詞「on」を使います。例: on May 3rd, on Monday。"
    },
    {
        "q": "The meeting starts ( ) 3 p.m.\n（会議は午後3時に始まる）",
        "correct": "at",
        "choices": ["on", "in", "at", "by"],
        "explanation": "特定の時刻には前置詞「at」を使います。例: at 3 p.m., at noon。"
    },
    {
        "q": "School is closed ( ) Sundays.\n（学校は日曜日は休みです）",
        "correct": "on",
        "choices": ["in", "on", "at", "for"],
        "explanation": "特定の曜日（複数形にして習慣を表す場合も含む）には前置詞「on」を使います。例: on Sundays (毎週日曜日に)。"
    },
    {
        "q": "He will finish the work ( ) two hours.\n（彼は2時間後にその仕事を終えるだろう）",
        "correct": "in",
        "choices": ["for", "after", "in", "during"],
        "explanation": "「in + 期間」で「（今から）～後に」という未来の時間を示します。例: in two hours (2時間後に)。「within two hours」なら「2時間以内に」。"
    },
    {
        "q": "Wine is made ( ) grapes.\n（ワインはブドウから作られる）",
        "correct": "from",
        "choices": ["of", "from", "in", "by"],
        "explanation": "「be made from ～（材料）」は、原料が変化して元の形をとどめない場合に使います。例: Wine is made from grapes."
    },
    {
        "q": "This table is made ( ) wood.\n（このテーブルは木で作られている）",
        "correct": "of",
        "choices": ["of", "from", "in", "with"],
        "explanation": "「be made of ～（材料）」は、材料が見てわかり、性質が変わらない場合に使います。例: This table is made of wood."
    },
    {
        "q": "These watches are made ( ) Switzerland.\n（これらの時計はスイス製だ）",
        "correct": "in",
        "choices": ["of", "from", "by", "in"],
        "explanation": "「be made in ～（場所）」で「～で作られた、～製」という生産地を示します。例: made in Japan (日本製)。"
    },
    {
        "q": "I went to school ( ) bus.\n（私はバスで学校へ行った）",
        "correct": "by",
        "choices": ["in", "by", "with", "on"],
        "explanation": "「by + 交通手段（無冠詞）」で「～（交通手段）で」を示します。例: by bus, by train, by car。ただし、「on foot」（徒歩で）は例外。"
    },
    {
        "q": "She wrote the letter ( ) English.\n（彼女はその手紙を英語で書いた）",
        "correct": "in",
        "choices": ["at", "with", "by", "in"],
        "explanation": "「in + 言語」で「～語で」を示します。例: in English, in Japanese。"
    },
    {
        "q": "He cut the paper ( ) scissors.\n（彼ははさみで紙を切った）",
        "correct": "with",
        "choices": ["by", "in", "with", "through"],
        "explanation": "「with + 道具」で「～（道具）を使って」を示します。例: cut with scissors, write with a pen。"
    },
    {
        "q": "It's a piece of ( ).\n（朝飯前だ）",
        "correct": "cake",
        "choices": ["cake", "pizza", "steak", "sushi"],
        "explanation": "「a piece of cake」は「とても簡単なこと、楽勝」という意味のイディオムです。"
    }
]

# --- クイズ種別選択 ---
def select_quiz(qtype):
    st.session_state.quiz_type = qtype

if "quiz_type" not in st.session_state:
    st.title("クイズを選んでください")
    c1, c2 = st.columns(2)
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
    st.stop()
    
# === Google Sheets 連携 ===
# !!! 注意: Streamlit Cloudで secrets を使う場合、st.secrets["gcp_service_account"] は辞書として扱われます。
# ローカル環境で JSON ファイルを使う場合は from_json_keyfile_name を使用します。
# ここでは st.secrets を使う前提で進めます。
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
try:
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    client = gspread.authorize(creds)
    spreadsheet = client.open("ScoreBoard") # スプレッドシート名を正確に指定

    if st.session_state.quiz_type == "sqrt":
        sheet = spreadsheet.get_worksheet(1) # Sheet2 (インデックス1)
    elif st.session_state.quiz_type == "eng":
        sheet = spreadsheet.get_worksheet(2) # Sheet3 (インデックス2)
    else:
        # デフォルトまたはエラー処理 (例: 最初のシートを使うか、エラー表示)
        # この段階では quiz_type が未定義の場合もあるので、実行順序に注意。
        # quiz_type 選択後にこの部分が評価されるようにする。
        # ただし、現状のst.stop()の配置では問題ない。
        sheet = spreadsheet.get_worksheet(0) # Fallback or define specific sheet

except Exception as e:
    st.error(f"Google Sheetsへの接続に失敗しました: {e}")
    st.info("アプリの管理者は、Streamlit CloudのSecrets設定で 'gcp_service_account' が正しく設定されているか確認してください。")
    # 開発中はローカルのダミーシートを使うなどの対策も有効
    class DummySheet:
        def append_row(self, data): pass
        def get_all_records(self): return []
    sheet = DummySheet() # エラー発生時はダミーオブジェクトを使用

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
        asked_eng_indices_this_session=[],
        incorrectly_answered_eng_questions=[],
        current_problem_display_choices=[],
    )
    for k, v in defaults.items():
        if k not in st.session_state: # 存在しないキーのみ初期化
            st.session_state[k] = v
init_state() # アプリ起動時に一度だけ呼ばれるようにする

# --- 問題生成（√問題 or 英語問題） ---
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

    elif st.session_state.quiz_type == "eng":
        available_quizzes_with_indices = []
        for i, quiz_item in enumerate(ENG_QUIZZES_DATA):
            if i not in st.session_state.asked_eng_indices_this_session:
                available_quizzes_with_indices.append({"original_index": i, "data": quiz_item})
        
        if not available_quizzes_with_indices:
            return None

        selected_item = random.choice(available_quizzes_with_indices)
        quiz_data_with_explanation = selected_item["data"]
        st.session_state.asked_eng_indices_this_session.append(selected_item["original_index"])
        return quiz_data_with_explanation
    else:
        st.error("不正なクイズ種別です")
        return None # エラー時はNoneを返す

# === スコア保存／取得 ===
def save_score(name, score_val): # scoreだと関数のスコープと混同するためscore_valに変更
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        sheet.append_row([name, score_val, ts])
    except Exception as e:
        st.error(f"スコアの保存に失敗しました: {e}")

def top3():
    try:
        rec = sheet.get_all_records()
        # scoreが文字列として読み込まれる可能性を考慮し、数値に変換してソート
        for row in rec:
            if isinstance(row.get("score"), str) and row.get("score").isdigit():
                row["score"] = int(row["score"])
            elif not isinstance(row.get("score"), int):
                row["score"] = 0 # スコアが無効な場合は0として扱う
        return sorted(rec, key=lambda x: x.get("score", 0), reverse=True)[:3]
    except Exception as e:
        st.error(f"ランキングの取得に失敗しました: {e}")
        return []


# --- クラス選択などのページ制御 ---
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
        if st.session_state.pw_input == "3R3": # パスワードは適宜変更
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

if st.session_state.nickname == "":
    if not st.session_state.played_name:
        play_sound(NAME_URL)
        st.session_state.played_name = True
    st.title("1分間クイズ")
    st.text_input("ニックネームを入力してください", key="nick_input", max_chars=12)
    def set_nickname():
        val = st.session_state.nick_input.strip()
        if val:
            st.session_state.nickname = val
    st.button("決定", on_click=set_nickname)
    st.stop()

# === クイズ本体 ===
if not st.session_state.started:
    quiz_label = "平方根クイズ" if st.session_state.quiz_type == "sqrt" else "中3英語クイズ"
    st.title(f"{st.session_state.nickname} さんの{quiz_label}")
    st.write("**ルール**: 制限時間1分、正解+1点、不正解-1点")

    def start_quiz():
        play_sound(START_URL)
        st.session_state.started = True
        st.session_state.start_time = time.time()
        st.session_state.score = 0
        st.session_state.total = 0
        st.session_state.answered = False
        st.session_state.is_correct = None
        st.session_state.user_choice = ""
        st.session_state.saved = False

        if st.session_state.quiz_type == "eng":
            st.session_state.asked_eng_indices_this_session = []
            st.session_state.incorrectly_answered_eng_questions = []
            
        st.session_state.current_problem = make_problem()

        if st.session_state.current_problem is None:
            st.session_state.current_problem_display_choices = []
        elif st.session_state.quiz_type == "eng":
            eng_problem_data = st.session_state.current_problem
            if "choices" in eng_problem_data and eng_problem_data["choices"]:
                shuffled_choices = random.sample(eng_problem_data["choices"], len(eng_problem_data["choices"]))
                st.session_state.current_problem_display_choices = shuffled_choices
            else:
                 st.session_state.current_problem_display_choices = [] # 念のため
        elif st.session_state.quiz_type == "sqrt":
            _, _, sqrt_choices = st.session_state.current_problem
            st.session_state.current_problem_display_choices = sqrt_choices
    
    st.button("スタート！", on_click=start_quiz)
    st.stop()

# --- タイマー表示 ---
# start_time が None の場合の対策 (スタートボタン押下前など)
current_time = time.time()
elapsed_time = 0
if st.session_state.start_time is not None:
    elapsed_time = int(current_time - st.session_state.start_time)
remaining = max(0, 60 - elapsed_time)
mm, ss = divmod(remaining, 60)

st.markdown(f"## ⏱️ {st.session_state.nickname} さんのタイムアタック！")
st.info(f"残り {mm}:{ss:02d} ｜ スコア {st.session_state.score} ｜ 挑戦 {st.session_state.total}")

# --- タイムアップ処理 ---
if remaining == 0:
    st.warning("⏰ タイムアップ！")
    st.write(f"最終スコア: {st.session_state.score}点 ({st.session_state.total}問)")

    if st.session_state.quiz_type == "eng" and st.session_state.incorrectly_answered_eng_questions:
        st.markdown("---") 
        st.subheader("📝 間違えた問題の復習")
        for i, item in enumerate(st.session_state.incorrectly_answered_eng_questions):
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
        if ranking: # ランキングが取得できた場合のみ判定
            user_rank_data = next((r for r in ranking if r.get("name") == full_name and r.get("score") == st.session_state.score), None)
            if user_rank_data: # 自分の今回の記録がランキング(上位3件)に含まれるか
                 is_in_top3 = True
            elif len(ranking) < 3: # 3位未満しかいなければ、自分のスコアが0でもトップ3扱い（保存はされる）
                 is_in_top3 = True
            elif ranking[2].get("score", 0) <= st.session_state.score : # 3位のスコア以上か
                 is_in_top3 = True
        else: # ランキングが空ならトップランカー扱い
            is_in_top3 = True


        if is_in_top3:
            play_sound(RESULT1_URL)
        else:
            play_sound(RESULT2_URL)
        st.balloons()
        
    st.write("### 🏆 歴代ランキング（上位3名）")
    current_ranking = top3() # 最新のランキングを取得
    if current_ranking:
        for i, r in enumerate(current_ranking, 1):
            name_display = r.get("name", "名無し")
            score_display = r.get("score", 0)
            st.write(f"{i}. {name_display} — {score_display}点")
    else:
        st.write("まだランキングデータがありません。")

    def restart_all():
        keys_to_keep = ["quiz_type", "class_selected", "password_ok", "agreed", "played_name"] # 完全に最初からではない場合
        # 完全に最初からにする場合は空リスト
        # keys_to_keep = [] 
        
        # クイズ種別選択からやり直す場合
        # st.session_state.clear() -> 全て消える
        
        for key in list(st.session_state.keys()):
            if key not in keys_to_keep:
                del st.session_state[key]
        # init_state() を再度呼び出して、削除されなかったキー以外のデフォルト値を設定
        init_state()
        # st.rerun() # これでニックネーム入力からになるはず
        # もしクイズタイプ選択からに戻したいなら、quiz_typeもdelする
        if "quiz_type" in keys_to_keep: # ニックネーム入力から
            pass
        else: # クイズタイプ選択から
            if "quiz_type" in st.session_state: del st.session_state.quiz_type
        st.rerun()


    st.button("🔁 もう一度挑戦", on_click=restart_all)
    st.stop()

# --- 問題表示と解答プロセス ---
problem_data = st.session_state.current_problem

if problem_data is None:
    if st.session_state.quiz_type == "eng":
        st.warning("🎉 全ての英語の問題に挑戦しました！素晴らしい！")
        st.info("タイムアップまで待つか、もう一度挑戦してください。")
    else:
        st.warning("問題の読み込みエラー、または全ての問題に解答しました。")
    st.stop()

question_text_to_display = ""
correct_answer_string = ""

if st.session_state.quiz_type == "sqrt":
    q_display_value, correct_sqrt_ans, _ = problem_data
    question_text_to_display = f"√{q_display_value} を簡約すると？"
    correct_answer_string = correct_sqrt_ans
elif st.session_state.quiz_type == "eng":
    q_dict = problem_data
    question_text_to_display = q_dict["q"]
    correct_answer_string = q_dict["correct"]

st.subheader(question_text_to_display)
choices_for_radio = st.session_state.current_problem_display_choices

if not choices_for_radio and st.session_state.quiz_type == "eng" and problem_data.get("choices"):
    # フォールバック: display_choicesが空だが元の問題にはchoicesがある場合 (主にデバッグ用)
    choices_for_radio = random.sample(problem_data["choices"], len(problem_data["choices"]))
    st.session_state.current_problem_display_choices = choices_for_radio


if not st.session_state.answered:
    if not choices_for_radio:
        st.error("選択肢が読み込めませんでした。問題をスキップするか、やり直してください。")
        # ここで次の問題に進むボタンや、リスタートを促す処理を追加することも検討
    else:
        user_choice = st.radio(
            "選択肢を選んでください", 
            choices_for_radio, 
            key=f"choice_{st.session_state.total}_{st.session_state.quiz_type}"
        )
        if st.button("解答する"):
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
                
                if st.session_state.quiz_type == "eng":
                    current_q_data = st.session_state.current_problem
                    st.session_state.incorrectly_answered_eng_questions.append({
                        "question_text": current_q_data["q"],
                        "user_answer": st.session_state.user_choice,
                        "correct_answer": correct_answer_string, 
                        "explanation": current_q_data["explanation"]
                    })
            st.rerun() # 解答後に即座に結果表示エリアを更新するためにrerun

# --- 結果表示と次の問題へのボタン ---
if st.session_state.answered:
    result_box = st.empty() # result_boxの定義をここに移動
    with result_box.container():
        if st.session_state.is_correct:
            st.success("🎉 正解！ +1点")
        else:
            st.error(f"😡 不正解！ 正解は {correct_answer_string} でした —1点")

        def next_q():
            # result_box.empty() # コンテナごと消すので不要な場合もあるが、残してもOK
            st.session_state.current_problem = make_problem()
            st.session_state.answered = False # これをリセット
            st.session_state.is_correct = None
            st.session_state.user_choice = ""

            if st.session_state.current_problem is None:
                st.session_state.current_problem_display_choices = []
            elif st.session_state.quiz_type == "eng":
                eng_problem_data = st.session_state.current_problem
                if "choices" in eng_problem_data and eng_problem_data["choices"]:
                    shuffled_choices = random.sample(eng_problem_data["choices"], len(eng_problem_data["choices"]))
                    st.session_state.current_problem_display_choices = shuffled_choices
                else:
                    st.session_state.current_problem_display_choices = []
            elif st.session_state.quiz_type == "sqrt":
                _, _, sqrt_choices = st.session_state.current_problem
                st.session_state.current_problem_display_choices = sqrt_choices
            st.rerun() # 状態を更新して再描画

        st.button("次の問題へ", on_click=next_q)
    st.stop()
