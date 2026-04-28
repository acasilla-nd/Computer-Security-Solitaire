import tkinter as tk
from tkinter import ttk, messagebox
import threading
import solitaire_reader
import Improved_Solver
import autoSolver

class SolitaireAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("Computer Security: Solitaire GUI")
        self.root.geometry("1000x800")
        #self.root.attributes("-topmost", True)  # Keep on top of game

        self.solution_moves = []
        self.current_move_idx = 0

        self.setup_ui()

    def setup_ui(self):
        # Header
        header = tk.Label(self.root, text="Solitaire Game Solver", font=("Arial", 16, "bold"))
        header.pack(pady=10)

        # Status Frame
        status_frame = tk.LabelFrame(self.root, text="Game Status", padx=10, pady=10)
        status_frame.pack(fill="x", padx=20)
        
        self.status_label = tk.Label(status_frame, text="Not Connected", fg="red")
        self.status_label.pack()

        # Control Buttons
        btn_frame = tk.Frame(self.root, pady=10)
        btn_frame.pack()

        tk.Button(btn_frame, text="Scan Game Memory", command=self.scan_game, width=20).grid(row=0, column=0, padx=5)
        
        self.solve_btn = tk.Button(btn_frame, text="Solve Board", command=self.solve_board, width=20, state="disabled")
        self.solve_btn.grid(row=0, column=1, padx=5)

        # Moves Display
        moves_frame = tk.LabelFrame(self.root, text="Suggested Moves", padx=10, pady=10)
        moves_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.moves_listbox = tk.Listbox(moves_frame, font=("Courier", 10))
        self.moves_listbox.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(moves_frame)
        scrollbar.pack(side="right", fill="y")
        self.moves_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.moves_listbox.yview)

        # Automation Frame
        auto_frame = tk.Frame(self.root, pady=10)
        auto_frame.pack()

        self.auto_btn = tk.Button(auto_frame, text="Execute All Moves (Bonus)", 
                                  command=self.run_automation, bg="#2ecc71", state="disabled")
        self.auto_btn.pack(side="left", padx=10)
        
        tk.Button(auto_frame, text="Clear", command=self.clear_all).pack(side="left")

    def scan_game(self):
        try:
            deck, piles = solitaire_reader.main()
            if deck is not None:
                self.status_label.config(text="CONNECTED: Game Data Read", fg="green")
                self.current_deck = deck
                self.current_piles = piles
                self.solve_btn.config(state="normal")
                messagebox.showinfo("Success", "Memory scan complete. Cards identified.")
            else:
                self.status_label.config(text="ERROR: sol.exe not found", fg="red")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read memory: {e}")

    def solve_board(self):
        if not hasattr(self, 'current_deck'):
            messagebox.showwarning("Warning", "Scan the game memory first!")
            return

        self.status_label.config(text="Calculating Solution...", fg="orange")
        self.root.update()

        # Run solver in a thread to keep GUI responsive
        def solve_thread():
            top = [[], [], [], []]
            # Solve returns (moves, success)
            sol, success = Improved_Solver.solve(self.current_deck, self.current_piles, top)
            
            if success:
                # Expand moves to include deck shuffles
                self.solution_moves = Improved_Solver.expand_moves(sol, self.current_deck, self.current_piles, top)
                self.root.after(0, self.display_moves)
            else:
                self.root.after(0, lambda: messagebox.showinfo("Solver", "No solution found for this state."))

        threading.Thread(target=solve_thread).start()

    def display_moves(self):
        self.moves_listbox.delete(0, tk.END)
        for i, move in enumerate(self.solution_moves):
            # Formats the internal move tuples into human-readable text
            # e.g. (('p0', 0), ('p1', 1)) -> "Pile 0 -> Pile 1"

            location1 = move[0][0]
            offset1 = move[0][1]
            location2 = move[1][0]
            offset2 = move[1][1]

            if location1 == "d" and location2 == "d":
                #Click Deck instruction
                location1 = "Deck"
                location2 = "Waste"
            elif location1 == "d":
                #Move from waste to pile instruction
                location1 = "Waste"

            try:
                num1 = f" {int(location1[-1])+1}"
            except Exception as e:
                num1 = ""

            try:
                num2 = f" {int(location2[-1])+1}"
            except Exception as e:
                num2 = ""

            cardsGrabbed = 1

            indexStr = ""

            if "t" in location1 and len(location1) == 2:
                location1 = "Sorted Pile"
            elif "p" in location1 and len(location1) == 2:
                location1 = "Tableau"
                indexStr = f"at index {offset1+1}"

            if "t" in location2 and len(location2) == 2:
                location2 = "Sorted Pile"
            elif "p" in location2 and len(location2) == 2:
                location2 = "Tableau"

            self.moves_listbox.insert(tk.END, f"Step: {i+1}: {location1}{num1} {indexStr} -> {location2}{num2}")
        
        self.status_label.config(text=f"SOLVED: {len(self.solution_moves)} moves", fg="green")
        self.auto_btn.config(state="normal")

    def run_automation(self):
        if not self.solution_moves: return
        
        # Confirmation for safety
        if messagebox.askyesno("Automation", "Starting AutoSolver. Ensure Solitaire is visible and do not move the mouse. Start?"):
            self.root.iconify()
            # Create the thread
            auto_thread = threading.Thread(
                target=lambda: autoSolver.solveGame(self.solution_moves)
            )
            auto_thread.start()
            
            # Start checking if it's finished
            self.check_thread(auto_thread)

    def check_thread(self, thread):
        if thread.is_alive():
            # If still running, check again in 500ms
            self.root.after(500, lambda: self.check_thread(thread))
        else:
            # IT IS DONE!
            self.on_automation_complete()

    def on_automation_complete(self):
        self.root.deiconify()  # Bring GUI back
        self.root.attributes("-topmost", True) # Briefly force it to front
        self.root.attributes("-topmost", False) # Release it so it's not annoying
        self.auto_btn.config(state="disabled")
        self.solve_btn.config(state="disabled")
        messagebox.showinfo("Done", "Automation complete! All moves executed.")

    def clear_all(self):
        self.moves_listbox.delete(0, tk.END)
        self.status_label.config(text="Not Connected", fg="red")
        self.auto_btn.config(state="disabled")
        self.solve_btn.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    app = SolitaireAssistant(root)
    root.mainloop()
