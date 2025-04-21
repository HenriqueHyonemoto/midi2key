import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from mido import get_input_names, open_input
from pynput.keyboard import Controller, Key
import threading
import json

keyboard = Controller()
midi_mappings = {}

listening_for_key = False
current_midi_note = None
pressed_keys = {}  # armazena as teclas pressionadas por nota MIDI

def on_midi(msg):
    global listening_for_key, current_midi_note, pressed_keys
    if msg.type == 'note_on' and msg.velocity > 0:
        note = msg.note
        if listening_for_key:
            current_midi_note = note
            status_label.config(text=f"Pressione uma tecla do teclado para mapear a nota MIDI {note}")
        elif note in midi_mappings:
            key_str = midi_mappings[note]
            if note not in pressed_keys:
                try:
                    if len(key_str) == 1:
                        keyboard.press(key_str)
                        pressed_keys[note] = key_str
                    else:
                        key = getattr(Key, key_str, None)
                        if key:
                            keyboard.press(key)
                            pressed_keys[note] = key
                except Exception as e:
                    print(f"Erro ao pressionar tecla: {e}")

    elif (msg.type == 'note_off') or (msg.type == 'note_on' and msg.velocity == 0):
        note = msg.note
        if note in pressed_keys:
            try:
                keyboard.release(pressed_keys[note])
                del pressed_keys[note]
            except Exception as e:
                print(f"Erro ao soltar tecla: {e}")

def listen_to_midi(port_name):
    try:
        with open_input(port_name) as inport:
            for msg in inport:
                on_midi(msg)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao abrir dispositivo MIDI: {e}")

def start_listening():
    port = midi_device_var.get()
    if not port:
        messagebox.showwarning("Aviso", "Selecione um dispositivo MIDI.")
        return
    threading.Thread(target=listen_to_midi, args=(port,), daemon=True).start()
    status_label.config(text=f"Escutando dispositivo: {port}")

def start_mapping():
    global listening_for_key
    listening_for_key = True
    status_label.config(text="Toque uma nota MIDI para iniciar o mapeamento...")

def on_key_press(event):
    global listening_for_key, current_midi_note
    if listening_for_key and current_midi_note is not None:
        midi_mappings[current_midi_note] = event.keysym
        mappings_list.insert(tk.END, f"Nota MIDI {current_midi_note} → Tecla '{event.keysym}'")
        status_label.config(text="Mapeamento salvo. Clique em mapear para outro ou toque uma nota.")
        listening_for_key = False
        current_midi_note = None

def save_mappings():
    try:
        file_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Arquivos JSON", "*.json")])
        if not file_path:
            return
        with open(file_path, "w") as f:
            json.dump(midi_mappings, f, indent=2)
        status_label.config(text="Mapeamento salvo com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao salvar: {e}")

def load_mappings():
    global midi_mappings
    try:
        file_path = filedialog.askopenfilename(filetypes=[("Arquivos JSON", "*.json")])
        if not file_path:
            return
        with open(file_path, "r") as f:
            midi_mappings = {int(k): v for k, v in json.load(f).items()}
        mappings_list.delete(0, tk.END)
        for note, key in midi_mappings.items():
            mappings_list.insert(tk.END, f"Nota MIDI {note} → Tecla '{key}'")
        status_label.config(text="Mapeamento carregado com sucesso!")
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar: {e}")

# UI setup
root = tk.Tk()
root.title("MIDI to Keyboard Mapper")
root.geometry("450x500")

tk.Label(root, text="Dispositivo MIDI:").pack(pady=5)
midi_device_var = tk.StringVar()
midi_devices = get_input_names()
device_menu = ttk.Combobox(root, textvariable=midi_device_var, values=midi_devices, state="readonly")
device_menu.pack(pady=5)

start_button = tk.Button(root, text="Iniciar Escuta", command=start_listening)
start_button.pack(pady=10)

map_button = tk.Button(root, text="Mapear Nota", command=start_mapping)
map_button.pack(pady=10)

save_button = tk.Button(root, text="Salvar Mapeamento", command=save_mappings)
save_button.pack(pady=5)

load_button = tk.Button(root, text="Carregar Mapeamento", command=load_mappings)
load_button.pack(pady=5)

mappings_list = tk.Listbox(root)
mappings_list.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

status_label = tk.Label(root, text="Aguardando ação...", fg="blue")
status_label.pack(pady=5)

root.bind("<Key>", on_key_press)

root.mainloop()
