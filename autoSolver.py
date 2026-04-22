import pyautogui
import pygetwindow as gw
import win32gui
import win32con
import time
import sys
import ctypes

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass 

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05  # Cuts the "wait" between actions in half

# Used to determine the 'Fixed' card sizes and vertical anchors
width, height = pyautogui.size()
BASE_W = 1202
BASE_H = 886

#Other Resolution
#3840x2400

#My Resolution
#2940x1846

def force_focus(hwnd):
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    pyautogui.press('alt')
    win32gui.SetForegroundWindow(hwnd)

def get_dynamic_layout(title="Solitaire"):
    wins = gw.getWindowsWithTitle(title)
    if not wins: return None, None
    win = wins[0]
    
    hwnd = win32gui.FindWindow(None, win.title)
    force_focus(hwnd)
    time.sleep(0.5)

    return {
        "left": max(0, win.left),
        "top": win.top,
        "width": win.width,
        "height": win.height
    }, win

def get_coords(layout, zone, index=0, hiddenCardsHeight=0, visibleCardsHeight=0, cardsGrabbed=1):
    L, T = layout["left"], layout["top"]
    W, H = layout["width"], layout["height"]

    # This tells us: "The current window is X times larger than the original"
    scale_x = W / 1202
    scale_y = H / 886

    CARD_W = 140 * scale_x
    y_hidden_cards_height = 6.2 * scale_y
    y_visible_cards_height = y_hidden_cards_height * 5
    
    # 3. Horizontal Logic (Using the Scaled CARD_W)
    remaining_space = W - (CARD_W * 7)
    avg_margin = remaining_space / 8
    x_pos = L + (avg_margin * (index + 1)) + (CARD_W * index) + (CARD_W / 2)

    # 4. Vertical Logic (Using percentages of the current Window Height H)
    # We use the ratios (0.225, 0.357) because they scale perfectly with H
    y_top_row = T + (H * 0.225)
    y_tab_base = T + (H * 0.357) + (10 * scale_y)

    if zone == 'deck':
        return L + avg_margin + (CARD_W / 2), y_top_row
    
    elif zone == 'waste':
        return L + (avg_margin * 2) + CARD_W + (CARD_W / 2), y_top_row
    
    elif zone == 'sortedCol':
        slot_idx = 3 + index
        return L + (avg_margin * (slot_idx + 1)) + (CARD_W * slot_idx) + (CARD_W / 2), y_top_row
    
    elif zone == 'tableau':
        # Apply the scaled vertical offsets
        y_offset = (hiddenCardsHeight * y_hidden_cards_height) + \
                   ((visibleCardsHeight - cardsGrabbed) * y_visible_cards_height)
        return x_pos, y_tab_base + y_offset

    return x_pos, y_top_row

def solveGame(instructions=[]):
    layout, win = get_dynamic_layout("Solitaire")

    if win:
        win.resizeTo(1202, 886)
        time.sleep(1) # Let the UI catch up
        layout, win = get_dynamic_layout() # Re-get layout after resize

    if not layout: 
        sys.exit("[-] Solitaire not found.")

    tableauHiddenCardHeights = [0, 1, 2, 3, 4, 5, 6]
    tableauAllCardHeights = [1, 2, 3, 4, 5, 6, 7]

    #Calibrating mouse
    pyautogui.moveTo(0, 0, duration=0.2)
    time.sleep(0.5)

    if instructions == []:
        # 1. Deck and Waste Test
        for zone in ['deck', 'waste']:
            tx, ty = get_coords(layout, zone)
            print(f"Checking {zone}...")
            pyautogui.moveTo(tx, ty, duration=0.4)
            time.sleep(0.3)

        # 2. Foundation Test
        for i in range(4):
            tx, ty = get_coords(layout, 'sortedCol', index=i)
            print(f"Checking Foundation {i+1}...")
            pyautogui.moveTo(tx, ty, duration=0.4)
            time.sleep(0.3)

        # 3. All 7 Tableaus (Top and Bottom of stack)
        for i in range(7):
            # Move to top of stack
            tx, ty = get_coords(layout, 'tableau', index=i, hiddenCardsHeight = tableauHiddenCardHeights[i], visibleCardsHeight=tableauAllCardHeights[i] - tableauHiddenCardHeights[i])
            print(f"Checking Tableau {i+1}...")
            pyautogui.moveTo(tx, ty, duration=0.4)
            time.sleep(0.3)

        """tx, ty = get_coords(layout, 'tableau', index=2, hiddenCardsHeight = 2, visibleCardsHeight=2, cardsGrabbed = 2)
        pyautogui.moveTo(tx, ty, duration=0.4)
        time.sleep(0.3)
        #tx, ty = get_coords(layout, 'tableau', index=2, hiddenCardsHeight = 2, visibleCardsHeight=1)
        #pyautogui.moveTo(tx, ty, duration=0.4)"""

    else:
        for i in instructions:
            location1 = i[0][0]
            offset1 = i[0][1]
            location2 = i[1][0]
            offset2 = i[1][1]

            if location1 == "d" and location2 == "d":
                #Click Deck instruction
                location1 = "deck"
                location2 = "waste"
            elif location1 == "d":
                #Move from waste to pile instruction
                location1 = "waste"

            try:
                num1 = int(location1[-1])
            except Exception as e:
                num1 = ""

            try:
                num2 = int(location2[-1])
            except Exception as e:
                num2 = ""

            cardsGrabbed = 1

            if "t" in location1 and len(location1) == 2:
                location1 = "sortedCol"
            elif "p" in location1 and len(location1) == 2:
                location1 = "tableau"

                cardsGrabbed = tableauAllCardHeights[num1] - offset1

            if "t" in location2 and len(location2) == 2:
                location2 = "sortedCol"
            elif "p" in location2 and len(location2) == 2:
                location2 = "tableau"

            #print(f"{location1}{num1} to {location2}{num2}")
            #print(i, tableauHiddenCardHeights, tableauAllCardHeights)

            tx1, ty1 = get_coords(layout, location1, index = num1 if num1 != "" else 0, hiddenCardsHeight = tableauHiddenCardHeights[num1] if num1 != "" else 0, visibleCardsHeight = tableauAllCardHeights[num1] - tableauHiddenCardHeights[num1] if num1 != "" else 0, cardsGrabbed = cardsGrabbed)
            pyautogui.moveTo(tx1, ty1, duration=0.2)

            if location1 == "deck" and location2 == "waste":
                #left click
                time.sleep(0.15)
                pyautogui.click()
                time.sleep(0.1)
                continue

            tx2, ty2 = get_coords(layout, location2, index = num2 if num2 != "" else 0, hiddenCardsHeight = tableauHiddenCardHeights[num2] if num2 != "" else 0, visibleCardsHeight = tableauAllCardHeights[num2] - tableauHiddenCardHeights[num2] if num2 != "" else 0)
            #pyautogui.dragTo(tx2, ty2, duration=0.8)
            pyautogui.mouseDown()
            time.sleep(0.1) # Vital: Gives the game a moment to "grab" the card
            #pyautogui.moveTo(tx2, ty2, duration=0.4)
            pyautogui.moveTo(tx2, ty2, duration=0.1)
            pyautogui.mouseUp()

            if location1 == "tableau":
                pyautogui.moveTo(tx1, ty1, duration=0.2)
                pyautogui.click()
                time.sleep(0.1)

                tableauAllCardHeights[num1] -= cardsGrabbed

                if tableauHiddenCardHeights[num1] == tableauAllCardHeights[num1] and tableauHiddenCardHeights[num1] > 0:
                    tableauHiddenCardHeights[num1] -= 1

            if location2 == "tableau":
                tableauAllCardHeights[num2] += cardsGrabbed

#solveGame([])
