import streamlit as st
import random
import json
import os
from pypinyin import pinyin, Style

# ===== 載入成語資料 =====
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

with open(os.path.join(DATA_DIR, "answer_pool.json"), encoding="utf-8") as f:
    ANSWER_POOL = json.load(f)

with open(os.path.join(DATA_DIR, "all_idioms.json"), encoding="utf-8") as f:
    ALL_IDIOMS = set(json.load(f))

with open(os.path.join(DATA_DIR, "hints.json"), encoding="utf-8") as f:
    IDIOM_HINTS = json.load(f)

st.set_page_config(page_title="成語 Wordle", page_icon="🀄", layout="wide")

# ===== 注音拆分 =====
INITIALS = set("ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙ")
TONE_MARKS = "ˊˇˋ˙"

def get_zhuyin(char):
    bpmf = pinyin(char, style=Style.BOPOMOFO)[0][0]
    clean = bpmf
    for t in TONE_MARKS:
        clean = clean.replace(t, "")
    if clean and clean[0] in INITIALS:
        initial = clean[0]
        final = clean[1:] if len(clean) > 1 else "∅"
    else:
        initial = "∅"
        final = clean if clean else "∅"
    return initial, final

def get_idiom_zhuyin(idiom):
    return [get_zhuyin(c) for c in idiom]

# ===== 樣式 =====
st.markdown("""
<style>
    /* ===== 共用 ===== */
    .grid-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 6px;
        margin: 10px auto 20px;
    }
    .grid-row {
        display: flex;
        justify-content: center;
        gap: 6px;
    }
    .cell-wrapper {
        width: 62px;
        height: 62px;
        overflow: hidden;
        position: relative;
        border-radius: 4px;
    }
    .cell-top { height: 50%; }
    .cell-bottom { height: 50%; }
    .cell-char {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        font-weight: 700;
        color: #ffffff;
        z-index: 2;
        pointer-events: none;
        font-family: 'Noto Sans TC', sans-serif;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
        line-height: 1;
    }
    .cell-empty {
        width: 62px;
        height: 62px;
        border: 2px solid #d3d6da;
        border-radius: 4px;
        background-color: #ffffff;
    }
    .bg-correct { background-color: #6aaa64; }
    .bg-present { background-color: #c9b458; }
    .bg-absent  { background-color: #787c7e; }

    /* 注音狀態表 */
    .zhuyin-table {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        justify-content: center;
        margin: 4px auto;
    }
    .zhuyin-tag {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-width: 28px;
        height: 28px;
        padding: 0 6px;
        border-radius: 3px;
        font-size: 1.05rem;
        font-weight: 600;
        color: #fff;
        font-family: 'Noto Sans TC', sans-serif;
        line-height: 1;
    }
    .zt-correct { background-color: #6aaa64; }
    .zt-present { background-color: #c9b458; }
    .zt-absent  { background-color: #787c7e; }
    .zt-unknown { background-color: transparent; color: #888; border: 1px solid #ccc; }

    /* ===== 手機版 (≤ 768px) ===== */
    @media (max-width: 768px) {
        /* 把 Streamlit 預設 padding 壓到最小 */
        .block-container {
            padding-top: 0.5rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
            max-width: 100% !important;
        }
        header[data-testid="stHeader"] {
            display: none !important;
        }

        h1 {
            font-size: 1.4rem !important;
            text-align: center;
            margin-bottom: 0.3rem !important;
        }

        /* 格子撐滿螢幕：(100vw - padding*2 - gap*3) / 4 */
        .cell-wrapper, .cell-empty {
            width: calc((100vw - 1rem - 18px) / 4);
            height: calc((100vw - 1rem - 18px) / 4);
            max-width: 72px;
            max-height: 72px;
        }
        .cell-char {
            font-size: clamp(1.4rem, 5vw, 2.2rem);
        }
        .grid-row {
            gap: 6px;
        }
        .grid-container {
            gap: 6px;
            margin: 8px auto 12px;
        }

        /* 按鈕 & 輸入框加大方便觸控 */
        .stButton > button {
            min-height: 48px !important;
            font-size: 1.1rem !important;
        }
        .stTextInput > div > div > input {
            font-size: 1.3rem !important;
            min-height: 48px !important;
        }

        /* 縮小 divider 間距 */
        hr {
            margin-top: 0.5rem !important;
            margin-bottom: 0.5rem !important;
        }

        /* 注音狀態表縮小 */
        .zhuyin-tag {
            min-width: 22px;
            height: 22px;
            padding: 0 4px;
            font-size: 0.85rem;
        }
        .zhuyin-table {
            gap: 3px;
        }

        /* 讓 columns 不要浪費空間 */
        [data-testid="stHorizontalBlock"] {
            gap: 0 !important;
        }
    }
</style>
""", unsafe_allow_html=True)

MAX_GUESSES = 6
IDIOM_SET = ALL_IDIOMS

# ===== 初始化 =====
if "answer" not in st.session_state:
    st.session_state.answer = random.choice(ANSWER_POOL)
    st.session_state.guesses = []
    st.session_state.results = []
    st.session_state.game_over = False
    st.session_state.won = False
    st.session_state.hints_used = 0

# ===== 檢查猜測（正確處理重複） =====
def _match(guess_list, answer_list):
    """Wordle 標準比對：綠色優先消耗，剩餘配黃色，多的灰色"""
    n = len(guess_list)
    status = ["absent"] * n
    remaining = list(answer_list)  # 可配對的池子

    # 第一輪：標記 correct，從池子移除
    for i in range(n):
        if guess_list[i] == answer_list[i]:
            status[i] = "correct"
            remaining[i] = None  # 已消耗

    # 第二輪：標記 present，每個只能配一次
    for i in range(n):
        if status[i] == "correct":
            continue
        for j in range(n):
            if remaining[j] is not None and guess_list[i] == remaining[j]:
                status[i] = "present"
                remaining[j] = None  # 消耗掉
                break

    return status

def check_guess(guess, answer):
    answer_zhuyin = get_idiom_zhuyin(answer)
    guess_zhuyin = get_idiom_zhuyin(guess)

    guess_initials = [z[0] for z in guess_zhuyin]
    answer_initials = [z[0] for z in answer_zhuyin]
    guess_finals = [z[1] for z in guess_zhuyin]
    answer_finals = [z[1] for z in answer_zhuyin]

    init_statuses = _match(guess_initials, answer_initials)
    final_statuses = _match(guess_finals, answer_finals)

    return list(zip(init_statuses, final_statuses))

# ===== 畫格子 =====
def render_grid():
    html = '<div class="grid-container">'
    for i in range(MAX_GUESSES):
        html += '<div class="grid-row">'
        if i < len(st.session_state.guesses):
            guess = st.session_state.guesses[i]
            result = st.session_state.results[i]
            for j in range(4):
                char = guess[j]
                init_s, final_s = result[j]
                html += f'''<div class="cell-wrapper">
                    <div class="cell-top bg-{init_s}"></div>
                    <div class="cell-char">{char}</div>
                    <div class="cell-bottom bg-{final_s}"></div>
                </div>'''
        else:
            for _ in range(4):
                html += '<div class="cell-empty"></div>'
        html += '</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ===== 注音狀態表 =====
PRIORITY = {"correct": 2, "present": 1, "absent": 0}

def render_zhuyin_status():
    init_status = {}
    final_status = {}
    for guess, result in zip(st.session_state.guesses, st.session_state.results):
        zhuyin = get_idiom_zhuyin(guess)
        for i in range(4):
            init, final = zhuyin[i]
            is_, fs_ = result[i]
            if PRIORITY.get(is_, 0) > PRIORITY.get(init_status.get(init, ""), -1):
                init_status[init] = is_
            if PRIORITY.get(fs_, 0) > PRIORITY.get(final_status.get(final, ""), -1):
                final_status[final] = fs_

    all_i = "ㄅㄆㄇㄈㄉㄊㄋㄌㄍㄎㄏㄐㄑㄒㄓㄔㄕㄖㄗㄘㄙ"
    all_f = ["ㄚ","ㄛ","ㄜ","ㄝ","ㄞ","ㄟ","ㄠ","ㄡ","ㄢ","ㄣ","ㄤ","ㄥ","ㄦ",
             "ㄧ","ㄧㄚ","ㄧㄝ","ㄧㄠ","ㄧㄡ","ㄧㄢ","ㄧㄣ","ㄧㄤ","ㄧㄥ",
             "ㄨ","ㄨㄚ","ㄨㄛ","ㄨㄞ","ㄨㄟ","ㄨㄢ","ㄨㄣ","ㄨㄤ","ㄨㄥ",
             "ㄩ","ㄩㄝ","ㄩㄢ","ㄩㄣ","ㄩㄥ"]

    html = '<div style="text-align:center;margin:8px 0;">'
    html += '<div class="zhuyin-table">'
    for c in all_i:
        cls = f"zt-{init_status[c]}" if c in init_status else "zt-unknown"
        html += f'<span class="zhuyin-tag {cls}">{c}</span>'
    cls_i = f"zt-{init_status['∅']}" if "∅" in init_status else "zt-unknown"
    html += f'<span class="zhuyin-tag {cls_i}">∅</span>'
    html += '</div>'

    html += '<div class="zhuyin-table" style="margin-top:4px;">'
    for c in all_f:
        cls = f"zt-{final_status[c]}" if c in final_status else "zt-unknown"
        sz = ' style="font-size:0.75rem;"' if len(c) > 1 else ""
        html += f'<span class="zhuyin-tag {cls}"{sz}>{c}</span>'
    cls_f = f"zt-{final_status['∅']}" if "∅" in final_status else "zt-unknown"
    html += f'<span class="zhuyin-tag {cls_f}">∅</span>'
    html += '</div></div>'
    st.markdown(html, unsafe_allow_html=True)

# ===== 置中容器 =====
col_l, col_c, col_r = st.columns([1, 2, 1])
with col_c:
    st.title("🀄 成語 Wordle")
    render_grid()
    render_zhuyin_status()

_l, _c, _r = st.columns([1, 2, 1])
with _c:
    # ===== 輸入區 =====
    if not st.session_state.game_over:
        raw_input = st.text_input(
            "輸入四字成語",
            placeholder="輸入成語...",
            key=f"input_{len(st.session_state.guesses)}",
            label_visibility="collapsed"
        )
        guess_input = raw_input.strip()[:4]

        # 按 Enter 自動送出
        if guess_input:
            if len(guess_input) != 4:
                st.warning("請輸入四個字")
            elif guess_input not in IDIOM_SET:
                st.warning("不在成語庫中")
            elif guess_input in st.session_state.guesses:
                st.warning("已經猜過了")
            else:
                result = check_guess(guess_input, st.session_state.answer)
                st.session_state.guesses.append(guess_input)
                st.session_state.results.append(result)
                if all(r[0] == "correct" and r[1] == "correct" for r in result):
                    st.session_state.won = True
                    st.session_state.game_over = True
                elif len(st.session_state.guesses) >= MAX_GUESSES:
                    st.session_state.game_over = True
                st.rerun()

    # ===== 遊戲結束 =====
    if st.session_state.game_over:
        if st.session_state.won:
            tries = len(st.session_state.guesses)
            if tries == 1:
                msg = "🤯 不可思議！"
            elif tries <= 3:
                msg = "🎉 成語大師！"
            elif tries <= 5:
                msg = "👏 猜中了！"
            else:
                msg = "😅 好險！"
            st.success(msg)
        else:
            st.error(f"答案：**{st.session_state.answer}**")

        hint = IDIOM_HINTS.get(st.session_state.answer, "")
        if hint:
            st.info(f"📖 **{st.session_state.answer}**：{hint}")

        if st.button("🔄 再來一局", use_container_width=True, type="primary"):
            st.session_state.answer = random.choice(ANSWER_POOL)
            st.session_state.guesses = []
            st.session_state.results = []
            st.session_state.game_over = False
            st.session_state.won = False
            st.session_state.hints_used = 0
            st.rerun()

_l2, _c2, _r2 = st.columns([1, 2, 1])
with _c2.expander("ℹ️ 說明 / 提示"):
    st.markdown(f"""
**玩法**：輸入四字成語，每格上半=聲母、下半=韻母。
🟩 正確位置 / 🟨 有但位置錯 / ⬛ 沒有，共 **6** 次機會。

出題 **{len(ANSWER_POOL):,}** 個 / 可猜 **{len(ALL_IDIOMS):,}** 個
    """)
    if not st.session_state.game_over:
        if st.button("💡 給我提示"):
            answer = st.session_state.answer
            h = st.session_state.hints_used
            if h == 0:
                st.info(f"第一個字：**{answer[0]}**")
            elif h == 1:
                st.info(f"最後一個字：**{answer[3]}**")
            elif h == 2:
                st.info(f"第二個字：**{answer[1]}**")
            else:
                st.info(f"**{answer[0]}＿{answer[2]}＿**")
            st.session_state.hints_used += 1
