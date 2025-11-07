import tkinter as tk
import threading
import time
import random
from queue import Queue, Empty
from datetime import datetime

class ARPChatSimulator(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#f8fafc")
        self.master = master
        self.pack(fill="both", expand=True)
        self.devices = []
        self.sender = None
        self.msg_queue = Queue()
        self.animation_speed = 80  # ms per step
        self.create_widgets()
        self.reset_display()
        self.master.after(100, self._process_queue)

    def create_widgets(self):
        header = tk.Label(self, text="🔗 ARP Protocol Chat — Simulation",
                          font=("Segoe UI", 18, "bold"), bg="#1e293b", fg="white", pady=10)
        header.pack(fill="x")

        main = tk.Frame(self, bg="#f8fafc")
        main.pack(fill="both", expand=True, padx=10, pady=8)

        # Canvas
        self.canvas = tk.Canvas(main, width=740, height=480, bg="white",
                                highlightthickness=2, highlightbackground="#94a3b8")
        self.canvas.pack(side="left", fill="both", expand=False, padx=(0,8))

        # Chat panel
        chat_frame = tk.Frame(main, bg="#f1f5f9", width=320)
        chat_frame.pack(side="left", fill="y")

        title = tk.Label(chat_frame, text="💬 Chat Panel", bg="#1e293b", fg="white",
                         font=("Segoe UI", 13, "bold"), pady=6)
        title.pack(fill="x")

        self.chat_display = tk.Text(chat_frame, width=40, height=20, state="disabled",
                                    wrap="word", font=("Consolas",10), bg="white", fg="#111")
        self.chat_display.pack(padx=8, pady=6)

        entry_frame = tk.Frame(chat_frame, bg="#f1f5f9")
        entry_frame.pack(fill="x", padx=8, pady=(6,8))

        tk.Label(entry_frame, text="Destination:", bg="#f1f5f9").grid(row=0, column=0, sticky="w")
        self.device_var = tk.StringVar(value="Select device")
        # create OptionMenu with placeholder initial value
        self.device_menu = tk.OptionMenu(entry_frame, self.device_var, "Select device")
        self.device_menu.config(width=18, font=("Segoe UI",9))
        self.device_menu.grid(row=0, column=1, padx=4, pady=2)

        tk.Label(entry_frame, text="Message:", bg="#f1f5f9").grid(row=1, column=0, sticky="w")
        self.msg_entry = tk.Entry(entry_frame, width=24, font=("Segoe UI",10))
        self.msg_entry.grid(row=1, column=1, padx=4, pady=2)

        btn_frame = tk.Frame(chat_frame, bg="#f1f5f9")
        btn_frame.pack(fill="x", padx=8, pady=(0,8))

        send_btn = tk.Button(btn_frame, text="Send", bg="#2563eb", fg="white",
                             font=("Segoe UI",10,"bold"), command=self.send_message)
        send_btn.pack(side="left", padx=(0,6))

        replay_btn = tk.Button(btn_frame, text="Replay", bg="#0ea5e9", fg="white",
                               font=("Segoe UI",10,"bold"), command=self.replay_demo)
        replay_btn.pack(side="left", padx=4)

        speed_frame = tk.Frame(chat_frame, bg="#f1f5f9")
        speed_frame.pack(fill="x", padx=8, pady=(0,8))
        tk.Label(speed_frame, text="Animation Speed:", bg="#f1f5f9").pack(side="left")
        self.speed_slider = tk.Scale(speed_frame, from_=20, to=200, orient="horizontal",
                                     command=self.update_speed, bg="#f1f5f9", highlightthickness=0)
        self.speed_slider.set(self.animation_speed)
        self.speed_slider.pack(side="left")

        self.arp_table_label = tk.Label(chat_frame, text="ARP Table:\n", font=("Consolas", 10),
                                        justify="left", bg="white", relief="solid", bd=1,
                                        width=40, anchor="nw")
        self.arp_table_label.pack(padx=8, pady=(6,8))

        self.step_label = tk.Label(chat_frame, text="Step: Ready", bg="#f1f5f9",
                                   fg="#1e293b", anchor="w", font=("Segoe UI",10,"italic"))
        self.step_label.pack(fill="x", padx=8, pady=(0,8))

    # -------------------------
    # Device setup
    # -------------------------
    def reset_display(self):
        self.canvas.delete("all")
        self.devices = []

        sender = {
            "ip": "192.168.1.10",
            "mac": self.generate_mac(),
            "x": 80, "y": 220,
            "color": "#2563eb",  # blue sender
            "label": "Sender"
        }
        self.draw_device(sender)
        self.sender = sender

        # 5 vertical devices
        base_x = 500
        top_y = 40
        spacing = 80
        palette = ["#10b981", "#f59e0b", "#f43f5e", "#6366f1", "#14b8a6"]
        for i in range(5):
            x, y = base_x, top_y + i * spacing
            dev = {
                "ip": f"192.168.1.{20+i}",
                "mac": self.generate_mac(),
                "x": x, "y": y,
                "color": palette[i],
                "label": f"Device {i+1}"
            }
            self.draw_device(dev)
            self.devices.append(dev)

        # Update dropdown
        menu = self.device_menu["menu"]
        menu.delete(0, "end")
        for dev in self.devices:
            label = f"{dev['label']} ({dev['ip']})"
            # command sets the variable to the ip string
            menu.add_command(label=label,
                             command=lambda v=dev['ip']: self.device_var.set(v))
        if self.devices:
            self.device_var.set(self.devices[0]['ip'])

        self.arp_table_label.config(text="ARP Table:\n")
        self.step_label.config(text="Step: Devices initialized")

    def draw_device(self, device):
        x, y = device["x"], device["y"]
        width, height = 140, 60
        rect = self.canvas.create_rectangle(x, y, x+width, y+height,
                                            fill=device["color"], outline="#1e293b",
                                            width=2, tags=device["ip"])
        text = self.canvas.create_text(x+width/2, y+height/2,
                                       text=f"{device['label']}\n{device['ip']}\n{device['mac']}",
                                       font=("Segoe UI",9,"bold"), justify="center",
                                       fill="white", tags=device["ip"])

    def generate_mac(self):
        return ":".join(f"{random.randint(0,255):02X}" for _ in range(6))

    # -------------------------
    # Chat behavior
    # -------------------------
    def send_message(self):
        dest = self.device_var.get()
        msg = self.msg_entry.get().strip()
        if not dest or not msg or dest == "Select device":
            return
        self._append_chat(msg, sender="You")
        threading.Thread(target=self._simulate_arp_exchange, args=(dest, msg), daemon=True).start()
        self.msg_entry.delete(0, "end")

    def replay_demo(self):
        dev = random.choice(self.devices)
        sample = f"Hi_{random.randint(1,99)}"
        self.device_var.set(dev["ip"])
        self.msg_entry.delete(0, "end"); self.msg_entry.insert(0, sample)
        self.send_message()

    def _simulate_arp_exchange(self, dest_ip, message):
        self._queue_step(f"Step 1: Broadcasting ARP request for {dest_ip}")
        # broadcast visually to all devices (schedule animations on main thread; thread will sleep to space them)
        for dev in self.devices:
            # schedule a non-blocking animation
            self.master.after(0, lambda d=dev: self._animate_arrow(
                self.sender["x"]+70, self.sender["y"]+30,
                d["x"]+70, d["y"]+30, text=f"Who has {dest_ip}?", color="#ef4444"))
            # give a small gap between broadcast arrows
            time.sleep(0.12)

        matched = next((d for d in self.devices if d["ip"] == dest_ip), None)
        if matched:
            self._queue_step(f"Step 2: {matched['ip']} replies with MAC")
            self.master.after(0, lambda d=matched: self._animate_arrow(
                d["x"]+70, d["y"]+30,
                self.sender["x"]+70, self.sender["y"]+30,
                text=f"{d['ip']} → MAC", color="#3b82f6"))
            # allow animation to run (duration is ~steps * animation_speed ms)
            time.sleep((30 * self.animation_speed)/1000.0 + 0.12)

            self._queue_arp_update(matched["ip"], matched["mac"])
            # highlight device (non-blocking)
            self.master.after(0, lambda d=matched: self._highlight_device(d["ip"]))
            self._queue_msg(message, sender=matched["ip"])

            # Automatic reply from device with custom text
            device_replies = {
                "Device 1": "Hello! I got your message.",
                "Device 2": "Acknowledged, thank you.",
                "Device 3": "Message received.",
                "Device 4": "Copy that!",
                "Device 5": "Roger, over and out."
            }
            reply_msg = device_replies.get(matched["label"], "Got your message.")
            time.sleep(0.5)
            self._queue_msg(f"{matched['label']} replies: {reply_msg}", sender=matched["label"])
            self.master.after(0, lambda d=matched: self._animate_arrow(
                d["x"]+70, d["y"]+30,
                self.sender["x"]+70, self.sender["y"]+30,
                text=reply_msg, color="#10b981"))
        else:
            self._queue_step("Step 2: No device responded")
            self._queue_arp_update(dest_ip, "No Response")
            self._queue_msg(f"Destination {dest_ip} is unavailable.", sender="System")

        self._queue_step("Step: Done")

    # -------------------------
    # UI Queue + Animations
    # -------------------------
    def _queue_step(self, text): self.msg_queue.put(("step", text))
    def _queue_arp_update(self, ip, mac): self.msg_queue.put(("arp", (ip, mac)))
    def _queue_msg(self, text, sender=""): self.msg_queue.put(("msg", (text, sender)))

    def _process_queue(self):
        try:
            while True:
                typ, payload = self.msg_queue.get_nowait()
                if typ == "step":
                    self.step_label.config(text=payload)
                elif typ == "arp":
                    ip, mac = payload
                    cur = self.arp_table_label.cget("text")
                    self.arp_table_label.config(text=cur + f"{ip:<16} -> {mac}\n")
                elif typ == "msg":
                    text, sender = payload
                    self._append_chat(text, sender=sender)
        except Empty:
            pass
        except Exception:
            # unexpected; don't crash the mainloop
            pass
        self.master.after(100, self._process_queue)

    def _append_chat(self, text, sender="System"):
        now = datetime.now().strftime("%H:%M:%S")
        self.chat_display.config(state="normal")
        self.chat_display.insert("end", f"[{now}] {sender}: {text}\n")
        self.chat_display.config(state="disabled")
        self.chat_display.see("end")

    def _animate_arrow(self, x1, y1, x2, y2, text="", color="#ef4444"):
        """
        Non-blocking arrow animation: schedules small updates via after().
        The function returns immediately; the animation runs on the Tk mainloop.
        """
        steps = 30
        dx, dy = (x2 - x1) / steps, (y2 - y1) / steps
        line = self.canvas.create_line(x1, y1, x1, y1, arrow=tk.LAST, fill=color, width=2)
        txt = self.canvas.create_text((x1+x2)/2, (y1+y2)/2 - 18, text=text, fill=color,
                                      font=("Segoe UI", 9, "bold"))

        def step(i, curx, cury):
            if i >= steps:
                # final coords
                self.canvas.coords(line, x1, y1, x2, y2)
                # leave text for a short moment then remove
                self.master.after(300, lambda: (self.canvas.delete(line), self.canvas.delete(txt)))
                return
            curx += dx
            cury += dy
            self.canvas.coords(line, x1, y1, curx, cury)
            # move text to remain near middle of current line
            midx = (x1 + curx) / 2
            midy = (y1 + cury) / 2 - 18
            self.canvas.coords(txt, midx, midy)
            # schedule next step
            self.master.after(self.animation_speed, lambda: step(i+1, curx, cury))

        # start animation
        step(0, x1, y1)

    def _highlight_device(self, ip):
        """
        Non-blocking highlight: toggles device fill a couple of times using after().
        """
        items = self.canvas.find_withtag(ip)
        # find original color from self.devices
        orig_color = None
        for dev in self.devices:
            if dev["ip"] == ip:
                orig_color = dev["color"]
                break
        if orig_color is None:
            orig_color = "#ffffff"

        flash_color = "#22c55e"
        cycles = 2
        delay = 400

        def toggle(count):
            if count <= 0:
                # restore original
                for it in items:
                    try:
                        self.canvas.itemconfig(it, fill=orig_color)
                    except Exception:
                        pass
                return
            # set to flash color
            for it in items:
                try:
                    self.canvas.itemconfig(it, fill=flash_color)
                except Exception:
                    pass
            self.master.after(delay, lambda: restore(count))

        def restore(count):
            for it in items:
                try:
                    self.canvas.itemconfig(it, fill=orig_color)
                except Exception:
                    pass
            self.master.after(delay, lambda: toggle(count-1))

        toggle(cycles)

    def update_speed(self, val):
        self.animation_speed = int(val)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("ARP Protocol Chat — Professional UI")
    root.geometry("1100x600")
    app = ARPChatSimulator(root)
    root.mainloop()
