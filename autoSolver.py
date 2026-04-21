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

# Used to determine the 'Fixed' card sizes and vertical anchors
BASE_W = 1202
BASE_H = 886

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

def get_coords(layout, zone, index=0, depth=0):
    L, T = layout["left"], layout["top"]

    if (L < 0):
        L = 0

    W = layout["width"]
    H = BASE_H

    # --- ELASTIC X-LOGIC ---
    # Based on 1202px width, we assume a card + gap takes up 
    # roughly 1/7.5 of the width.
    # Estimated Card Width (in pixels) that stays constant:
    CARD_W = 140
    
    # Calculate the remaining space
    # There are 7 columns. We subtract the card widths from the total window.
    remaining_space = W - (CARD_W * 7)
    
    # Distribute the space into 8 margins (Outer left, 6 gaps, Outer right)
    avg_margin = remaining_space / 8
    
    # Calculate the center of the target column
    # (Margin * (index + 1)) + (CardWidth * index) + (Half a card to hit center)
    x_pos = L + (avg_margin * (index + 1)) + (CARD_W * index) + (CARD_W / 2)

    y_top_row = T + (H * 0.225)
    y_tab_base = T + (H * 0.37)
    y_depth_step = H * 0.006

    if zone == 'deck':
        # The deck is the top left place to click to see new cards
        return L + avg_margin + (CARD_W / 2), y_top_row
    
    elif zone == 'waste':
        # The waste is where the cards clicked from the deck go to 
        return L + (avg_margin * 2) + CARD_W + (CARD_W / 2), y_top_row
    
    elif zone == 'sortedCol':
        # sortedCol is just the solutions for each col
        slot_idx = 3 + index
        return L + (avg_margin * (slot_idx + 1)) + (CARD_W * slot_idx) + (CARD_W / 2), y_top_row
    
    elif zone == 'tableau':
        #tableau is the playing area where cards are stacked
        return x_pos, y_tab_base + (depth * y_depth_step)

    return x_pos, y_top_row

def solveGame(instructions=[]):
    layout, win = get_dynamic_layout("Solitaire")
    if not layout: 
        sys.exit("[-] Solitaire not found.")


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
            tx, ty = get_coords(layout, 'tableau', index=i, depth=i)
            print(f"Checking Tableau {i+1}...")
            pyautogui.moveTo(tx, ty, duration=0.4)
            
            # Move to 5th card deep
            dx, dy = get_coords(layout, 'tableau', index=i, depth=i+30)
            pyautogui.moveTo(dx, dy, duration=0.2)
            time.sleep(0.3)
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

            if "t" in location1 and len(location1) == 2:
                location1 = "sortedCol"
            elif "p" in location1 and len(location1) == 2:
                location1 = "tableau"

            if "t" in location2 and len(location2) == 2:
                location2 = "sortedCol"
            elif "p" in location2 and len(location2) == 2:
                location2 = "tableau"

            #print(f"{location1}{num1} to {location2}{num2}")
            #print(i)

            tx1, ty1 = get_coords(layout, location1, num1 if num1 != "" else 0, (num1 if num1 != "" else 0) + offset1*5)
            pyautogui.moveTo(tx1, ty1, duration=0.2)
            time.sleep(0.2)

            if location1 == "deck" and location2 == "waste":
                #left click
                pyautogui.click()
                continue

            tx2, ty2 = get_coords(layout, location2, num2 if num2 != "" else 0, (num2 if num2 != "" else 0) + offset2*5)
            #pyautogui.moveTo(tx2, ty2, duration=0.4)
            pyautogui.dragTo(tx2, ty2, duration=0.8)
            time.sleep(0.2)

            if (location1 == "tableau"):
                pyautogui.moveTo(tx1, ty1, duration=0.2)
                time.sleep(0.2)
                pyautogui.click()