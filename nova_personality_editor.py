
from tkinter import Tk, Label, Text, Button, END, messagebox
import json
import os

def save_personality():
    try:
        data = {
            "default": default_box.get("1.0", END).strip().splitlines(),
            "greeting": greeting_box.get("1.0", END).strip().splitlines(),
            "weird_fact_intro": weird_box.get("1.0", END).strip().splitlines()
        }
        with open("nova_personality.json", "w") as f:
            json.dump(data, f, indent=2)
        messagebox.showinfo("Saved", "NOVA personality updated!")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def load_existing():
    if os.path.exists("nova_personality.json"):
        with open("nova_personality.json", "r") as f:
            data = json.load(f)
            default_box.insert("1.0", "\n".join(data.get("default", [])))
            greeting_box.insert("1.0", "\n".join(data.get("greeting", [])))
            weird_box.insert("1.0", "\n".join(data.get("weird_fact_intro", [])))

app = Tk()
app.title("NOVA Personality Editor")
app.geometry("500x600")

Label(app, text="Default Responses").pack()
default_box = Text(app, height=6, width=60)
default_box.pack()

Label(app, text="Greeting Responses").pack()
greeting_box = Text(app, height=6, width=60)
greeting_box.pack()

Label(app, text="Weird Fact Intros").pack()
weird_box = Text(app, height=6, width=60)
weird_box.pack()

Button(app, text="💾 Save Personality", command=save_personality).pack(pady=10)

load_existing()
app.mainloop()
