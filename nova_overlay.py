import tkinter as tk
from PIL import Image, ImageTk

class NovaOverlay:
    def __init__(self, image_path="resized_overlay.png"):
        self.root = tk.Tk()
        self.root.title("Nova Overlay")
        self.root.overrideredirect(True)  # No window borders
        self.root.wm_attributes("-topmost", True)  # Always on top
        self.root.configure(bg="white")
        
        # Create a canvas for the image
        self.canvas = tk.Canvas(self.root, bg="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Load and display the image
        self.image = Image.open(image_path)
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        
        # Make the window draggable by binding mouse events to the canvas.
        self.offset_x = 0
        self.offset_y = 0
        self.canvas.bind("<Button-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.do_move)
        
        # Set initial geometry; adjust width and height as needed.
        self.root.geometry(f"{self.image.width()}x{self.image.height()}+100+100")
    
    def start_move(self, event):
        self.offset_x = event.x
        self.offset_y = event.y

    def do_move(self, event):
        x = self.root.winfo_pointerx() - self.offset_x
        y = self.root.winfo_pointery() - self.offset_y
        self.root.geometry(f"+{x}+{y}")

    def update_image(self, image_path):
        # Reload image and update the canvas
        self.image = Image.open(image_path)
        self.tk_image = ImageTk.PhotoImage(self.image)
        self.canvas.itemconfig(self.image_id, image=self.tk_image)
        # Update geometry if image size has changed
        self.root.geometry(f"{self.image.width()}x{self.image.height()}")

    def set_speaking(self, state):
        # Optionally change the background color when speaking
        if state:
            self.canvas.config(bg="lightblue")
        else:
            self.canvas.config(bg="white")
        print("Overlay set speaking:", state)

    def launch_overlay(self):
        self.root.mainloop()

# Global instance for external access
_overlay_instance = None

def launch_overlay():
    global _overlay_instance
    _overlay_instance = NovaOverlay("resized_overlay.png")
    _overlay_instance.launch_overlay()

def set_speaking(state):
    if _overlay_instance:
        _overlay_instance.set_speaking(state)
    else:
        print("No overlay instance available to set speaking state.")

def get_overlay_instance():
    return _overlay_instance
