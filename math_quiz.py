import streamlit as st
import random
import math
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import numpy as np # 斜面の計算で使用
import matplotlib.pyplot as plt          
import matplotlib.patches as patches     
import matplotlib.transforms as mtrans   


# === 英語クイズデータ（解説付き） ===
ENG_QUIZZES_DATA = [
    # (内容は変更なしのため省略)
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

# --- 初期化関連 ---
def initialize_simulation_common():
    """シミュレーション共通で使う可能性のある変数を初期化"""
    st.session_state.sim_stage = "intro" # 各シミュレーションの初期画面

def initialize_force_motion_sim():
    """力の運動シミュレーション用の変数を初期化"""
    initialize_simulation_common()
    st.session_state.sim_type = "force_motion"
    st.session_state.sim_fm_internal_mass = 1.0  # kg (力の運動用)
    st.session_state.sim_fm_force = 0.0         # N (力の運動用)
    st.session_state.sim_fm_time = 0.0          # s
    st.session_state.sim_fm_velocity = 0.0      # m/s
    st.session_state.sim_fm_position = 0.0      # m
    st.session_state.sim_fm_acceleration = 0.0  # m/s^2
    st.session_state.sim_fm_running_active = False

def initialize_inclined_plane_sim():
    """斜面の傾きシミュレーション用の変数を初期化"""
    initialize_simulation_common()
    st.session_state.sim_type = "inclined_plane"
    st.session_state.sim_ip_angle = 30.0  # 度 (斜面用)
    st.session_state.sim_ip_gravity_magnitude = 9.8 # N (仮の重力値、質量1kgと仮定)

def select_content_type(content_type):
    """コンテンツ種別（クイズかシミュレーションか）を選択"""
    st.session_state.content_type_selected = content_type
    if content_type == "sci_sim":
        # 理科シミュレーションが選ばれたら、次はシミュレーションタイプ選択画面へ
        st.session_state.sim_selection_stage = "choose_sim_type"
    # クイズの場合は、既存の quiz_type を設定する流れに繋げる
    elif content_type in ["sqrt", "eng"]:
        st.session_state.quiz_type = content_type
        # クイズ選択後はシミュレーション関連のstateをクリアする（逆もまた然り）
        keys_to_delete = [k for k in st.session_state if k.startswith("sim_") or k == "sim_selection_stage"]
        for key in keys_to_delete:
            if key in st.session_state: del st.session_state[key]

def select_sim_type(sim_type_selected):
    """実行するシミュレーションのタイプを選択し、初期化"""
    if sim_type_selected == "force_motion":
        initialize_force_motion_sim()
    elif sim_type_selected == "inclined_plane":
        initialize_inclined_plane_sim()
    st.session_state.sim_selection_stage = "sim_running" # シミュレーション実行段階へ

# --- メインのコンテンツ選択画面 ---
if "content_type_selected" not in st.session_state:
    st.title("学習コンテンツを選んでください")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.button("平方根クイズ", on_click=select_content_type, args=("sqrt",))
    with c2:
        st.button("中３英語クイズ", on_click=select_content_type, args=("eng",))
    with c3:
        st.button("理科シミュレーション", on_click=select_content_type, args=("sci_sim",))
    st.stop()

# --- 理科シミュレーションのタイプ選択画面 ---
if st.session_state.get("content_type_selected") == "sci_sim" and \
   st.session_state.get("sim_selection_stage") == "choose_sim_type":
    st.title("理科シミュレーションを選んでください")
    st.markdown("---")
    sim_col1, sim_col2 = st.columns(2)
    with sim_col1:
        st.button("運動と力 (ニュートンの法則)", on_click=select_sim_type, args=("force_motion",), use_container_width=True)
    with sim_col2:
        st.button("斜面の傾きと力の分解", on_click=select_sim_type, args=("inclined_plane",), use_container_width=True)
    st.markdown("---")
    if st.button("最初の選択に戻る", use_container_width=True):
        del st.session_state.content_type_selected
        if "sim_selection_stage" in st.session_state: del st.session_state.sim_selection_stage
        st.rerun()
    st.stop()

# --- 理科シミュレーション処理本体 ---
if st.session_state.get("content_type_selected") == "sci_sim" and \
   st.session_state.get("sim_selection_stage") == "sim_running":

    # --- 1. 力の運動（ニュートンの法則）シミュレーション ---
    if st.session_state.get("sim_type") == "force_motion":
        if st.session_state.sim_stage == "intro":
            st.title("力の運動シミュレーション: ニュートンの法則を探る")
            st.markdown("---")
            st.write("""
            このシミュレーションでは、物体に加える力と、それによる物体の運動（速度や位置の変化）の関係を視覚的に探求します。
            - 「物体に加える力 (F)」の大きさを下のスライダーで設定してください。
            - 「シミュレーション開始」ボタンを押すと、設定した力で物体が運動を開始します。
            - 運動の様子や、力の大きさが物体の加速にどのように影響するかを観察しましょう。
            - （このシミュレーションでは、物体の質量は1kgで一定であると仮定しています。）
            """)
            st.markdown("---")

            st.session_state.sim_fm_force = st.slider(
                "物体に加える力 (N)", 0.0, 2.0,
                st.session_state.get("sim_fm_force", 0.0), 0.1,
                help="物体に加える力の大きさをニュートン(N)単位で設定します。0Nは力を加えていない状態です。",
                key="fm_force_intro"
            )

            col_sim_buttons1, col_sim_buttons2 = st.columns(2)
            with col_sim_buttons1:
                if st.button("シミュレーション開始/リセット 🔄", use_container_width=True, key="fm_start_reset"):
                    st.session_state.sim_stage = "running"
                    st.session_state.sim_fm_time = 0.0
                    st.session_state.sim_fm_velocity = 0.0
                    st.session_state.sim_fm_position = 0.0
                    st.session_state.sim_fm_acceleration = st.session_state.sim_fm_force / st.session_state.sim_fm_internal_mass
                    st.session_state.sim_fm_running_active = True
                    st.rerun()
            with col_sim_buttons2:
                if st.button("シミュレーション選択に戻る", use_container_width=True, key="fm_back_to_sim_select_intro"):
                    st.session_state.sim_selection_stage = "choose_sim_type"
                    # sim_type や個別のシミュレーション変数は保持したままで良いか、クリアするか検討
                    # ここではクリアせず、再選択時に上書き・初期化される想定
                    st.rerun()

        elif st.session_state.sim_stage == "running":
            st.title("力の運動シミュレーション実行中 ⚙️")
            st.markdown("---")

            new_force_on_run = st.slider(
                "加える力を変更 (N)", 0.0, 2.0,
                st.session_state.sim_fm_force, 0.1,
                key="fm_force_running",
                help="シミュレーション中に力を変更できます。変更は即座に加速度に反映されます。"
            )
            if new_force_on_run != st.session_state.sim_fm_force:
                st.session_state.sim_fm_force = new_force_on_run
                st.session_state.sim_fm_acceleration = st.session_state.sim_fm_force / st.session_state.sim_fm_internal_mass

            st.info(f"現在の力: $F = {st.session_state.sim_fm_force:.1f}$ N  |  現在の加速度: $a = {st.session_state.sim_fm_acceleration:.2f}$ m/s² (質量1kgの場合)")

            delta_t = 0.1
            sim_active = st.session_state.get("sim_fm_running_active", False)
            button_label = "一時停止 ⏸️" if sim_active else "再生 ▶️"

            col_anim_ctrl1, col_anim_ctrl2, col_anim_ctrl3 = st.columns(3)
            with col_anim_ctrl1:
                if st.button(button_label, use_container_width=True, key="fm_play_pause"):
                    st.session_state.sim_fm_running_active = not sim_active
                    st.rerun()
            with col_anim_ctrl2:
                if st.button("初期設定に戻る ↩️", use_container_width=True, key="fm_back_to_intro"):
                    st.session_state.sim_stage = "intro"
                    st.session_state.sim_fm_running_active = False
                    st.rerun()
            with col_anim_ctrl3:
                 if st.button("シミュレーション選択に戻る", use_container_width=True, key="fm_back_to_sim_select_running"):
                    st.session_state.sim_selection_stage = "choose_sim_type"
                    st.rerun()

            if sim_active:
                prev_velocity = st.session_state.sim_fm_velocity
                st.session_state.sim_fm_velocity += st.session_state.sim_fm_acceleration * delta_t
                st.session_state.sim_fm_position += prev_velocity * delta_t + 0.5 * st.session_state.sim_fm_acceleration * (delta_t ** 2)
                st.session_state.sim_fm_time += delta_t

            st.markdown("---")
            st.subheader("シミュレーション結果")
            col1, col2, col3 = st.columns(3)
            col1.metric("経過時間 (秒)", f"{st.session_state.sim_fm_time:.1f}")
            col2.metric("現在の速度 (m/s)", f"{st.session_state.sim_fm_velocity:.2f}")
            col3.metric("現在の位置 (m)", f"{st.session_state.sim_fm_position:.2f}")

            st.write("物体の位置 (0m から右方向に進みます):")
            max_display_length = 60
            current_pos_for_bar = int(round(st.session_state.sim_fm_position))
            bar_length = min(max(0, current_pos_for_bar), max_display_length)
            bar = "─" * bar_length + "🚗"
            display_line = f"0m |{bar}"
            st.markdown(f"<pre style='overflow-x: auto; white-space: pre;'>{display_line}</pre>", unsafe_allow_html=True)
            if current_pos_for_bar > max_display_length:
                st.caption(f"表示範囲 ({max_display_length}m) を超えました (現在位置: {st.session_state.sim_fm_position:.1f}m)")

            st.markdown("---")
            if sim_active:
                time.sleep(0.03)
                st.rerun()
        st.stop() # 力の運動シミュレーションここまで

        # --- 2. 斜面の傾きと力の分解シミュレーション ------------------
    elif st.session_state.get("sim_type") == "inclined_plane":

        # ------------------------------------------------------------ #
        # イントロ画面（角度スライダーだけ表示）
        # ------------------------------------------------------------ #
        if st.session_state.sim_stage == "intro":
            st.title("斜面の傾きと力の分解シミュレーション")
            st.markdown("---")
            st.write("""
            このシミュレーションでは、斜面上の物体にはたらく重力を
            斜面に平行な成分と垂直な成分に分解して可視化します。
            スライダーで角度 θ を変えると、矢印の**長さだけ**が
            $mg\\sinθ$、$mg\\cosθ$ に比例して伸び縮みします。
            """)

            # 角度スライダー（変更すると即 rerun）
            st.session_state.sim_ip_angle = st.slider(
                "斜面の角度 θ (°)", 0.0, 90.0,
                st.session_state.get("sim_ip_angle", 30.0), 1.0,
                key="ip_angle_intro"
            )

            # intro → running へ遷移
            st.session_state.sim_stage = "running"
            st.rerun()

        # ------------------------------------------------------------ #
        # 可視化画面（running）
        # ------------------------------------------------------------ #
        elif st.session_state.sim_stage == "running":

            # ===== 1. 入力（角度スライダー）==========================
            angle_deg = st.slider(
                "斜面の角度を変更 (°)", 0.0, 90.0,
                st.session_state.sim_ip_angle, 1.0,
                key="ip_angle_running"
            )
            st.session_state.sim_ip_angle = angle_deg

            # ===== 2. 力の計算 =======================================
            theta   = math.radians(angle_deg)
            g       = st.session_state.sim_ip_gravity_magnitude    # 9.8 N
            F_para  = g * math.sin(theta)      # 平行成分
            F_perp  = g * math.cos(theta)      # 垂直成分（＝垂直抗力）

            # ===== 3. 描画関数 =======================================
            def draw_incline(theta_deg, g, F_para, F_perp) -> plt.Figure:
                theta  = math.radians(theta_deg)
                L      = 6.0                       # 斜面長さ（図尺度）
                scale  = 1.7 / g                  # mg を 1.7 図単位に

                fig, ax = plt.subplots(figsize=(6, 4))
                ax.set_aspect("equal")
                ax.axis("off")

                # ==== 斜面（線を細く）=================================
                x2, y2 = L*math.cos(theta), L*math.sin(theta)
                ax.plot([0, x2], [0, y2], lw=1.6, color="navy", zorder=1)

                # ==== 物体（枠線も細く）===============================
                cx, cy = 2*math.cos(theta), 2*math.sin(theta)
                trans  = (
                    mtrans.Affine2D()
                    .rotate_deg(theta_deg)
                    .translate(cx, cy) + ax.transData
                )
                rect = patches.Rectangle(
                    (-0.65, -0.65), 1.3, 1.3,
                    facecolor="#16c0ff", edgecolor="k", linewidth=1.2,
                    transform=trans, zorder=2
                )
                ax.add_patch(rect)

                # ==== 力ベクトル（zorder を最大に）====================
                head_w, z_arrow = 0.12, 5
                # ① 重力 mg
                ax.arrow(cx, cy, 0, -g*scale,
                         width=head_w, color="red",
                         length_includes_head=True, zorder=z_arrow)
                # ② 平行成分
                ax.arrow(cx, cy,
                         -math.cos(theta)*F_para*scale,
                         -math.sin(theta)*F_para*scale,
                         width=head_w, color="red",
                         length_includes_head=True, zorder=z_arrow)
                # ③ 垂直成分（外向き）
                ax.arrow(cx, cy,
                         -math.sin(theta)*F_perp*scale,
                          math.cos(theta)*F_perp*scale,
                         width=head_w, color="red",
                         length_includes_head=True, zorder=z_arrow)

                # ==== 角度ラベル（図内リアルタイム表示）===============
                ax.text(
                    0.05, 0.95, rf"$\theta = {theta_deg:.1f}^\circ$",
                    transform=ax.transAxes, ha="left", va="top",
                    fontsize=13, fontweight="bold"
                )

                # ==== 描画範囲 ========================================
                ax.set_xlim(-1, L+1)
                ax.set_ylim(-1, L*math.sin(theta)+2)
                return fig

            # ===== 4. 図を表示 =======================================
            fig = draw_incline(angle_deg, g, F_para, F_perp)
            st.pyplot(fig)

            # ===== 5. 数値表示 =======================================
            st.markdown("---")
            st.info(
                f"**θ = {angle_deg:.1f}°**  ｜  "
                f"$mg\\sinθ$ = {F_para:.2f} N  ｜  "
                f"$mg\\cosθ$ = {F_perp:.2f} N"
            )

            # ===== 6. 戻るボタン =====================================
            if st.button("シミュレーション選択に戻る",
                         use_container_width=True,
                         key="ip_back_to_sim_select"):
                st.session_state.sim_selection_stage = "choose_sim_type"
                st.rerun()


        st.stop() # 斜面の傾きシミュレーションここまで
    st.stop() # 理科シミュレーション処理全体ここまで

# --- ここから下はクイズ用のコード (変更なし) ---
# === Google Sheets 連携 (クイズ用) ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_available = False
sheet = None
if "gcp_service_account" in st.secrets:
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
        client = gspread.authorize(creds)
        spreadsheet = client.open("ScoreBoard")
        creds_available = True
        
        if st.session_state.get("quiz_type") == "sqrt": # quiz_type はクイズ選択時に設定される
            sheet = spreadsheet.get_worksheet(1)
        elif st.session_state.get("quiz_type") == "eng":
            sheet = spreadsheet.get_worksheet(2)
        # quiz_typeがNone (まだクイズが選択されていない、またはシミュレーションモード) の場合、
        # または未定義のクイズタイプの場合、シートはNoneのまま。
        # elif st.session_state.get("quiz_type") is not None: 
        #      st.warning(f"未対応のクイズタイプ ({st.session_state.quiz_type}) のため、ランキングは利用できません。")

    except Exception as e:
        st.error(f"Google Sheets認証またはシート取得に問題があります: {e}")
        creds_available = False
else:
    if st.session_state.get("content_type_selected") in ["sqrt", "eng"]: # クイズ選択時のみ警告
        st.warning("Google Sheetsの認証情報が設定されていません。ランキング機能は利用できません。")

if not creds_available or sheet is None:
    # クイズが選択されているがシートがない場合のみダミーシート
    if st.session_state.get("content_type_selected") in ["sqrt", "eng"]:
        class DummySheet:
            def append_row(self, data): st.info("（ランキング機能無効：スコアは保存されません）")
            def get_all_records(self): return []
        sheet = DummySheet()
    elif sheet is None : # クイズ以外でsheetがNoneなら、そのままNoneで良い（エラー回避）
        pass


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

# === セッション初期化 (クイズ用) ===
def init_quiz_state(): # 関数名をより明確に
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
        # クイズ種別ごとの状態
        asked_eng_indices_this_session=[],
        incorrectly_answered_eng_questions=[],
        # asked_sqrt_... のようなものも必要ならここに追加
        current_problem_display_choices=[],
        # ページ制御用 (クイズのフローで使用)
        class_selected=None,
        password_ok=False,
        agreed=False,
    )
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# init_quiz_state() はクイズフローに入る直前で呼び出すのが適切かもしれない
# ここではグローバルに一度呼び出す形にしておく
if st.session_state.get("content_type_selected") in ["sqrt", "eng"]:
    init_quiz_state()


# --- 問題生成（√問題 or 英語問題）---
def make_problem():
    if st.session_state.get("quiz_type") == "sqrt":
        fav = {12, 18, 20, 24, 28, 32, 40, 48, 50, 54, 56, 58}
        population = list(range(2, 101))
        weights = [10 if n in fav else 1 for n in population]
        a = random.choices(population, weights)[0]
        for i in range(int(math.sqrt(a)), 0, -1):
            if a % (i * i) == 0:
                outer, inner = i, a // (i * i)
                correct = (
                    str(outer) if inner == 1
                    else (f"√{inner}" if outer == 1 else f"{outer}√{inner}")
                )
                choices_set = {correct}
                while len(choices_set) < 4:
                    o_fake = random.randint(1, max(9, outer + 2))
                    i_fake = random.randint(1, max(10, inner + 5))
                    if i_fake == 1 and o_fake == outer: continue
                    if o_fake == outer and i_fake == inner: continue
                    fake = (
                        str(o_fake) if i_fake == 1
                        else (f"√{i_fake}" if o_fake == 1 else f"{o_fake}√{i_fake}")
                    )
                    choices_set.add(fake)
                choices = random.sample(list(choices_set), k=min(len(choices_set), 4))
                return a, correct, choices
        return None
    elif st.session_state.get("quiz_type") == "eng":
        quiz_data = ENG_QUIZZES_DATA
        session_key = "asked_eng_indices_this_session"
        # セッションキーが存在しない場合のエラーを防ぐため、デフォルト値を設定
        if session_key not in st.session_state:
            st.session_state[session_key] = []

        available_quizzes_with_indices = [
            {"original_index": i, "data": quiz_item}
            for i, quiz_item in enumerate(quiz_data)
            if i not in st.session_state[session_key]
        ]
        if not available_quizzes_with_indices: return None
        selected_item = random.choice(available_quizzes_with_indices)
        quiz_data_with_explanation = selected_item["data"]
        st.session_state[session_key].append(selected_item["original_index"])
        return quiz_data_with_explanation
    else:
        return None

# === スコア保存／取得 (クイズ用) ===
def save_score(name, score_val):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(sheet, DummySheet) or sheet is None:
        st.info(f"スコア保存試行 (デバッグ用): {name}, {score_val}, {ts}（実際には保存されません）")
        return
    try:
        sheet.append_row([name, score_val, ts])
    except Exception as e:
        st.error(f"スコアの保存に失敗しました: {e}")

def top3():
    if isinstance(sheet, DummySheet) or sheet is None:
        return []
    try:
        records = sheet.get_all_records()
        valid_records = []
        for r in records:
            try:
                score_value = r.get("score")
                if isinstance(score_value, str):
                    if score_value.isdigit() or (score_value.startswith('-') and score_value[1:].isdigit()):
                        score_value = int(score_value)
                    else: score_value = 0
                elif not isinstance(score_value, int): score_value = 0
                r["score"] = score_value
                valid_records.append(r)
            except ValueError:
                r["score"] = 0
                valid_records.append(r)
        return sorted(valid_records, key=lambda x: x.get("score", 0), reverse=True)[:3]
    except Exception as e:
        print(f"ランキング取得エラー: {e}")
        return []

# --- クイズ用のページ制御フロー ---
if st.session_state.get("content_type_selected") in ["sqrt", "eng"]:
    # クイズが選択された場合のみ、以下のページ制御を実行
    if "class_selected" not in st.session_state or st.session_state.class_selected is None:
        st.title("所属を選択してください")
        def select_class(cls): st.session_state.class_selected = cls
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
            if st.session_state.pw_input == "3R3": st.session_state.password_ok = True
            else: st.error("パスワードが違います")
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
        def agree_and_continue(): st.session_state.agreed = True
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
            if val: st.session_state.nickname = val
            else: st.warning("ニックネームを入力してください。")
        st.button("決定", on_click=set_nickname)
        st.stop()

    # === クイズ本体の表示ロジック ===
    if not st.session_state.get("started", False):
        quiz_labels = {"sqrt": "平方根クイズ", "eng": "中3英語クイズ"}
        quiz_label = quiz_labels.get(st.session_state.quiz_type, "クイズ")
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
            if st.session_state.quiz_type == "eng": # 英語クイズの場合のみリセット
                st.session_state.asked_eng_indices_this_session = []
                st.session_state.incorrectly_answered_eng_questions = []

            st.session_state.current_problem = make_problem()
            if st.session_state.current_problem is None:
                st.session_state.current_problem_display_choices = []
            elif st.session_state.quiz_type == "eng":
                problem_data = st.session_state.current_problem
                if "choices" in problem_data and problem_data["choices"]:
                    shuffled_choices = random.sample(problem_data["choices"], len(problem_data["choices"]))
                    st.session_state.current_problem_display_choices = shuffled_choices
                else: st.session_state.current_problem_display_choices = []
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

    if remaining == 0:
        if not st.session_state.get("time_up_processed", False):
            st.warning("⏰ タイムアップ！")
            st.write(f"最終スコア: {st.session_state.score}点 ({st.session_state.total}問)")
            incorrect_questions = []
            if st.session_state.quiz_type == "eng" and "incorrectly_answered_eng_questions" in st.session_state:
                incorrect_questions = st.session_state.incorrectly_answered_eng_questions
            if incorrect_questions:
                st.markdown("---")
                st.subheader("📝 間違えた問題の復習 (英語)")
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
                else: is_in_top3 = True
                if is_in_top3: play_sound(RESULT1_URL)
                else: play_sound(RESULT2_URL)
                st.balloons()
            st.session_state.time_up_processed = True
        st.write("### 🏆 歴代ランキング（上位3名）")
        current_ranking_data = top3()
        if current_ranking_data:
            for i, r_data in enumerate(current_ranking_data, 1):
                name_display = r_data.get("name", "名無し")
                score_display = r_data.get("score", 0)
                st.write(f"{i}. {name_display} — {score_display}点")
        else: st.write("まだランキングデータがありません。")

        def restart_quiz_flow(): # クイズ専用のやり直し関数
            keys_to_remove = [
                "started", "start_time", "score", "total", "current_problem",
                "answered", "is_correct", "user_choice", "saved", "time_up_processed",
                "current_problem_display_choices",
                "nick_input", "nickname", # ニックネームから再入力
                # クイズ種別ごとの状態もクリア
                "asked_eng_indices_this_session", "incorrectly_answered_eng_questions",
            ]
            # class_selected, password_ok, agreed, content_type_selected, quiz_type は保持
            for key in keys_to_remove:
                if key in st.session_state: del st.session_state[key]
            init_quiz_state() # ニックネームなどが""で再初期化される
            st.rerun()
        st.button("🔁 もう一度挑戦", on_click=restart_quiz_flow)
        # ホームに戻るボタン
        if st.button("最初の選択に戻る", key="quiz_back_to_home"):
            keys_to_clear_for_home = [
                "started", "start_time", "score", "total", "current_problem",
                "answered", "is_correct", "user_choice", "saved", "time_up_processed",
                "current_problem_display_choices",
                "nick_input", "nickname",
                "asked_eng_indices_this_session", "incorrectly_answered_eng_questions",
                "class_selected", "password_ok", "agreed",
                "quiz_type", "content_type_selected"
            ]
            for key in keys_to_clear_for_home:
                 if key in st.session_state: del st.session_state[key]
            st.rerun()
        st.stop()

    # --- 問題表示と解答プロセス (クイズ用) ---
    problem_data = st.session_state.current_problem
    if problem_data is None: # 全問解いた場合など
        st.warning("全ての問題を解きました！お疲れ様でした。")
        # 強制的にタイムアップ処理に移行させるか、結果表示ボタンを出す
        st.session_state.start_time = time.time() - 61 # 経過時間を60秒超にする
        st.rerun() # タイムアップ処理が走るようにする
        st.stop()

    question_text_to_display = ""
    correct_answer_string = ""
    if st.session_state.quiz_type == "sqrt":
        q_display_value, correct_answer_string_local, _ = problem_data
        question_text_to_display = f"√{q_display_value} を簡約すると？"
        correct_answer_string = correct_answer_string_local
    elif st.session_state.quiz_type == "eng":
        q_dict = problem_data
        question_text_to_display = q_dict["q"]
        correct_answer_string = q_dict["correct"]

    st.subheader(question_text_to_display)
    choices_for_radio = st.session_state.current_problem_display_choices
    if not st.session_state.answered:
        if not choices_for_radio:
            st.error("選択肢が読み込めませんでした。ページを更新するか、やり直してください。")
        else:
            user_choice = st.radio("選択肢を選んでください", choices_for_radio, key=f"radio_choice_{st.session_state.total}")
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
                    if st.session_state.quiz_type == "eng":
                        current_q_data = st.session_state.current_problem
                        # incorrectly_answered_eng_questions が初期化されていることを確認
                        if "incorrectly_answered_eng_questions" not in st.session_state:
                             st.session_state.incorrectly_answered_eng_questions = []
                        st.session_state.incorrectly_answered_eng_questions.append({
                            "question_text": current_q_data["q"],
                            "user_answer": st.session_state.user_choice,
                            "correct_answer": correct_answer_string,
                            "explanation": current_q_data["explanation"]
                        })
                st.rerun()

    # --- 結果表示と次の問題へのボタン (クイズ用) ---
    if st.session_state.answered:
        if st.session_state.is_correct: st.success("🎉 正解！ +1点")
        else: st.error(f"😡 不正解！ 正解は {correct_answer_string} でした —1点")
        def next_q():
            st.session_state.current_problem = make_problem()
            st.session_state.answered = False
            st.session_state.is_correct = None
            st.session_state.user_choice = ""
            if st.session_state.current_problem is None: # 次の問題がない場合
                st.session_state.current_problem_display_choices = []
                # 全問解いたのでタイムアップ処理へ
                st.session_state.start_time = time.time() - 61 # 経過時間を60秒超にする
            elif st.session_state.quiz_type == "eng":
                eng_problem_data = st.session_state.current_problem
                if "choices" in eng_problem_data and eng_problem_data["choices"]:
                    shuffled_choices = random.sample(eng_problem_data["choices"], len(eng_problem_data["choices"]))
                    st.session_state.current_problem_display_choices = shuffled_choices
                else: st.session_state.current_problem_display_choices = []
            elif st.session_state.quiz_type == "sqrt":
                _, _, sqrt_choices = st.session_state.current_problem
                st.session_state.current_problem_display_choices = sqrt_choices
            st.rerun()
        st.button("次の問題へ", on_click=next_q, key=f"next_q_button_{st.session_state.total}")
        st.stop()
