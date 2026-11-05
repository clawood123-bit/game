# ==================================================
#  🐙 바탕화면 픽셀 문어
#
#  [실행]  이 파일을 더블클릭하면 문어가 나타나요.
#  [놀기]  왼쪽 클릭      : 쓰다듬기 (점프 + 하트)
#          누른 채로 끌기 : 문어 옮기기
#          오른쪽 클릭    : 메뉴 (따라오기, 재우기, 끝내기)
# ==================================================

import tkinter as tk   # 창을 만드는 도구 (파이썬에 기본으로 들어 있어요)
import random          # 무작위로 고르는 도구
import math            # 계산 도구 (통통 튀는 움직임에 써요)

# ----- 1. 바꿔볼 수 있는 설정 -----
SPEED = 2      # 걷는 속도 (숫자가 크면 빨라요)
WORDS = ["심심해~", "뭐 해?", "♪ 룰루~", "놀아줘!", "오늘도 화이팅!", "배고파..."]

# 문어 그림 (그림 파일을 글자로 바꿔서 넣어둔 거예요. 건드리지 마세요!)
OCTO_PICTURE = "iVBORw0KGgoAAAANSUhEUgAAADAAAAAjCAYAAADSQImyAAAAfklEQVR42mNkwAEeVIf8ZxhEQKF1DSM2cSaGIQ6GvAcYB3OyISY5jSahAU9CQyXZDNsYGPXAqAdGugdYSNXgvfwOVvGtkSoDYs5oEhr1wKgHRj0w6oHR5vRoc3rUA6MeGPXA6LgQw+i40LBIQsQkJ1yjxAOldzQJjXpgpHsAAPHZI59m00cgAAAAAElFTkSuQmCC"

KEY = "#ff00fe"   # 이 색은 투명하게 보여요 (문어에 없는 색)


# ----- 2. 화면이 흐려지지 않게 하는 윈도우 설정 -----
try:
    import ctypes
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass


# ----- 3. 투명한 창을 만드는 도우미 -----
def make_window(parent=None):
    if parent is None:
        w = tk.Tk()
    else:
        w = tk.Toplevel(parent)
    w.overrideredirect(True)            # 테두리, 제목줄 없애기
    w.attributes("-topmost", True)      # 항상 다른 창보다 위에
    w.config(bg=KEY)
    try:
        w.attributes("-transparentcolor", KEY)   # KEY 색을 투명하게
    except tk.TclError:
        pass
    return w


# ----- 4. 문어 창 만들기 -----
root = make_window()

# 화면 선명도에 맞춰서 문어 크기 정하기
ZOOM = max(2, round(2.5 * root.winfo_fpixels("1i") / 96))
picture = tk.PhotoImage(data=OCTO_PICTURE).zoom(ZOOM)
W, H = picture.width(), picture.height()

canvas = tk.Canvas(root, width=W, height=H, bg=KEY, highlightthickness=0)
canvas.pack()
canvas.create_image(0, 0, image=picture, anchor="nw")


# ----- 5. 문어가 다닐 수 있는 공간 (작업표시줄은 빼고) -----
def get_screen():
    try:
        import ctypes.wintypes
        r = ctypes.wintypes.RECT()
        ctypes.windll.user32.SystemParametersInfoW(48, 0, ctypes.byref(r), 0)
        return r.left, r.top, r.right, r.bottom
    except Exception:
        return 0, 0, root.winfo_screenwidth(), root.winfo_screenheight()

LEFT, TOP, RIGHT, BOTTOM = get_screen()


# ----- 6. 문어의 상태 -----
octo = {
    "x": (LEFT + RIGHT) / 2,   # 지금 위치 (가로)
    "y": (TOP + BOTTOM) / 2,   # 지금 위치 (세로)
    "goal_x": 0,               # 가고 싶은 곳 (가로)
    "goal_y": 0,               # 가고 싶은 곳 (세로)
    "mode": "rest",            # walk 걷기, rest 쉬기, sleep 자기, follow 따라오기, drag 들려 있기
    "rest_time": 80,           # 쉬는 시간이 얼마나 남았는지
    "steps": 0,                # 걸은 거리 (통통 튀는 데 써요)
    "jump": 0,                 # 점프 높이
    "jump_speed": 0,           # 점프 속도
}


# ----- 7. 말풍선 (문어 머리 위에 뜨는 하얀 창) -----
bubble = tk.Toplevel(root)
bubble.overrideredirect(True)
bubble.attributes("-topmost", True)
bubble_text = tk.Label(bubble, text="", bg="white", fg="#333",
                       font=("Malgun Gothic", 11), padx=10, pady=4,
                       relief="solid", bd=2)
bubble_text.pack()
bubble.withdraw()   # 처음엔 숨겨두기
bubble_timer = [None]

def say(text, seconds=2):
    bubble_text.config(text=text)
    bubble.deiconify()
    if bubble_timer[0]:
        root.after_cancel(bubble_timer[0])
    bubble_timer[0] = root.after(seconds * 1000, bubble.withdraw)


# ----- 8. 하트와 Z (픽셀 그림으로 그려요) -----
# 1 = 색칠, 0 = 빈칸
HEART = ["0110110",
         "1111111",
         "1111111",
         "0111110",
         "0011100",
         "0001000"]
ZZZ = ["11111",
       "00010",
       "00100",
       "01000",
       "11111"]

def float_up(shape, color):
    dot = ZOOM * 2                      # 픽셀 한 칸의 크기
    w = make_window(root)
    c = tk.Canvas(w, width=len(shape[0]) * dot, height=len(shape) * dot,
                  bg=KEY, highlightthickness=0)
    c.pack()
    for row, line in enumerate(shape):
        for col, cell in enumerate(line):
            if cell == "1":
                c.create_rectangle(col * dot, row * dot, (col + 1) * dot, (row + 1) * dot,
                                   fill=color, outline="")

    start_x = int(octo["x"] + W * 0.6 + random.randint(0, W // 4))
    start_y = int(octo["y"])

    # 0.04초마다 조금씩 위로 올라가다가 사라져요
    def rise(count=0):
        if count > 25:
            w.destroy()
            return
        w.geometry(f"+{start_x}+{start_y - count * 3}")
        w.after(40, rise, count + 1)
    rise()


# ----- 9. 새로 갈 곳 정하기 (화면 안의 아무 곳) -----
def pick_new_goal():
    octo["goal_x"] = random.randint(LEFT, RIGHT - W)
    octo["goal_y"] = random.randint(TOP + 60, BOTTOM - H)
    octo["mode"] = "walk"


# ----- 10. 메뉴 (오른쪽 클릭) -----
def follow_me():
    octo["mode"] = "follow"
    say("따라갈게! ♥")

def go_sleep():
    octo["mode"] = "sleep"
    say("잘 자~ 쿨쿨...", 3)

def free_walk():
    say("자유다~!")
    pick_new_goal()

def bye():
    say("또 놀자! 안녕~")
    root.after(1000, root.destroy)

menu = tk.Menu(root, tearoff=0)
menu.add_command(label="🐾 나 따라와!", command=follow_me)
menu.add_command(label="🚶 자유롭게 놀기", command=free_walk)
menu.add_command(label="😴 재우기", command=go_sleep)
menu.add_separator()
menu.add_command(label="👋 끝내기", command=bye)


# ----- 11. 마우스로 하는 일 -----
drag = {"ox": 0, "oy": 0, "moved": False, "before": "rest"}

def mouse_down(e):
    drag["ox"], drag["oy"] = e.x, e.y
    drag["moved"] = False

def mouse_move(e):
    # 손이 살짝 떨린 건 무시 (조금 넘게 움직여야 끌기)
    if not drag["moved"]:
        if abs(e.x - drag["ox"]) + abs(e.y - drag["oy"]) < 5:
            return
        drag["moved"] = True
        octo["mode"] = "drag"
        say("우와앗!", 1)
    octo["x"] = e.x_root - drag["ox"]
    octo["y"] = e.y_root - drag["oy"]

def mouse_up(e):
    if drag["moved"]:
        # 다 옮겼으면 거기서 잠깐 쉬기
        octo["mode"] = "rest"
        octo["rest_time"] = 100
        say("여기 좋다!")
        return

    # 그냥 클릭 : 쓰다듬기
    if octo["mode"] == "sleep":
        octo["mode"] = "rest"
        octo["rest_time"] = 60
        say("으앗, 깼다!")
    else:
        say("헤헤 ♥")
    octo["jump_speed"] = 12      # 점프!
    float_up(HEART, "#ff5c8a")

canvas.bind("<Button-1>", mouse_down)
canvas.bind("<B1-Motion>", mouse_move)
canvas.bind("<ButtonRelease-1>", mouse_up)
canvas.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))


# ----- 12. 매 순간 반복 : 문어 움직이기 (0.02초마다) -----
def walk_to(goal_x, goal_y):
    """목표 쪽으로 한 걸음. 도착하면 True 를 알려줘요."""
    dx = goal_x - octo["x"]
    dy = goal_y - octo["y"]
    distance = math.sqrt(dx * dx + dy * dy)
    if distance < SPEED:
        return True
    octo["x"] += dx / distance * SPEED
    octo["y"] += dy / distance * SPEED
    octo["steps"] += SPEED
    return False

def update():
    mode = octo["mode"]

    if mode == "walk":
        if walk_to(octo["goal_x"], octo["goal_y"]):
            # 도착! 잠깐 쉬기
            octo["mode"] = "rest"
            octo["rest_time"] = random.randint(100, 300)

    elif mode == "follow":
        # 마우스 커서 옆으로 따라가기
        mx, my = root.winfo_pointerxy()
        walk_to(mx - W / 2, my + 20)

    elif mode == "rest":
        octo["rest_time"] -= 1
        if octo["rest_time"] <= 0:
            dice = random.random()          # 0 ~ 1 사이의 무작위 숫자
            if dice < 0.15:                 # 15% : 잠자기
                octo["mode"] = "sleep"
                say("졸려...")
            else:                           # 나머지 : 다른 곳으로 가기
                if dice < 0.4:
                    say(random.choice(WORDS))
                pick_new_goal()

    elif mode == "sleep":
        if random.random() < 0.01:
            float_up(ZZZ, "#5b6cff")
        if random.random() < 0.0007:        # 가끔 스스로 일어나요
            say("잘 잤다!")
            pick_new_goal()

    # 걸을 때 통통 튀기
    hop = 0
    if octo["mode"] in ("walk", "follow"):
        hop = abs(math.sin(octo["steps"] / 10)) * 8

    # 점프 (위로 솟았다가 다시 내려와요)
    if octo["jump_speed"] != 0 or octo["jump"] > 0:
        octo["jump"] += octo["jump_speed"]
        octo["jump_speed"] -= 1
        if octo["jump"] <= 0:
            octo["jump"] = 0
            octo["jump_speed"] = 0

    # 화면 밖으로 나가지 않게
    octo["x"] = max(LEFT, min(RIGHT - W, octo["x"]))
    octo["y"] = max(TOP, min(BOTTOM - H, octo["y"]))

    # 문어 창을 새 위치로 옮기기
    x = int(octo["x"])
    y = int(octo["y"] - hop - octo["jump"])
    root.geometry(f"+{x}+{y}")

    # 말풍선도 문어 머리 위로 따라오기
    bw = bubble_text.winfo_reqwidth()
    bh = bubble_text.winfo_reqheight()
    bubble.geometry(f"+{x + W // 2 - bw // 2}+{y - bh - 6}")

    root.after(20, update)


# ----- 13. 시작! -----
say("안녕! 나는 픽셀 문어야!", 3)
update()
root.mainloop()
