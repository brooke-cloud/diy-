import json, os, string, tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

TITLE="6-Key Macro Studio"; KEYS=[f"SW{i}" for i in range(1,7)]; PINS=["GP2","GP3","GP8","GP5","GP6","GP7"]
TYPES=["单键","组合键","文本"]; TO_CODE={"单键":"key","组合键":"hotkey","文本":"text"}; FROM_CODE={v:k for k,v in TO_CODE.items()}
DEFAULTS=[("组合键","CTRL+C"),("组合键","CTRL+V"),("组合键","CTRL+Z"),("组合键","ALT+TAB"),("组合键","WIN+SHIFT+S"),("单键","F5")]
# PCB 实际位置：上排 SW2、SW3、SW1；下排 SW6、SW5、SW4。
PCB_POSITIONS={0:(0,2),1:(0,0),2:(0,1),3:(1,2),4:(1,1),5:(1,0)}
BG="#F4F6FA"; CARD="#FFFFFF"; TEXT="#172033"; MUTED="#667085"; BORDER="#E4E7EC"; PRIMARY="#5B5CE2"; SOFT="#EEF0FF"; GREEN="#14804A"; AMBER="#8A6116"
MODS=["CTRL","SHIFT","ALT","WIN"]
MOD_KEYS={"Control_L":"CTRL","Control_R":"CTRL","Shift_L":"SHIFT","Shift_R":"SHIFT","Alt_L":"ALT","Alt_R":"ALT","Meta_L":"WIN","Meta_R":"WIN","Super_L":"WIN","Super_R":"WIN","Win_L":"WIN","Win_R":"WIN"}
ALIASES={"Escape":"ESC","Return":"ENTER","KP_Enter":"ENTER","BackSpace":"BACKSPACE","Delete":"DELETE","Insert":"INSERT","Tab":"TAB","space":"SPACE","Caps_Lock":"CAPS_LOCK","Up":"UP","Down":"DOWN","Left":"LEFT","Right":"RIGHT","Prior":"PGUP","Next":"PGDN","Home":"HOME","End":"END","Print":"PRINT_SCREEN","minus":"MINUS","equal":"EQUALS","bracketleft":"LEFT_BRACKET","bracketright":"RIGHT_BRACKET","backslash":"BACKSLASH","semicolon":"SEMICOLON","apostrophe":"QUOTE","grave":"GRAVE_ACCENT","comma":"COMMA","period":"PERIOD","slash":"FORWARD_SLASH"}

def detect_drive():
    if os.name=="nt":
        for letter in string.ascii_uppercase:
            p=Path(letter+":\\")
            if (p/"code.py").exists() and (p/"lib"/"adafruit_hid").exists(): return str(p)
    return ""

def event_token(e):
    if e.keysym in MOD_KEYS: return MOD_KEYS[e.keysym]
    if e.keysym in ALIASES: return ALIASES[e.keysym]
    if e.keysym.startswith("KP_"):
        m={"Add":"KEYPAD_PLUS","Subtract":"KEYPAD_MINUS","Multiply":"KEYPAD_ASTERISK","Divide":"KEYPAD_FORWARD_SLASH","Decimal":"KEYPAD_PERIOD"}
        return m.get(e.keysym[3:],"KEYPAD_"+e.keysym[3:].upper())
    if len(e.keysym)==1 and e.keysym.isalnum(): return e.keysym.upper()
    if e.keysym.upper().startswith("F") and e.keysym[1:].isdigit(): return e.keysym.upper()

class MacroRow:
    def __init__(self,app,parent,i,default):
        self.app=app; self.i=i; self.kind=tk.StringVar(value=default[0]); self.value=tk.StringVar(value=default[1]); self.recording=False; self.pressed=[]
        f=self.frame=tk.Frame(parent,bg=CARD,highlightbackground=BORDER,highlightthickness=1,padx=14,pady=11)
        pcb_row,pcb_column=PCB_POSITIONS[i]
        left=0 if pcb_column==0 else 7; right=0 if pcb_column==2 else 7
        f.grid(row=pcb_row,column=pcb_column,sticky="nsew",padx=(left,right),pady=7); f.grid_columnconfigure(1,weight=1)
        tk.Label(f,text=KEYS[i],bg=SOFT,fg=PRIMARY,font=("Segoe UI",10,"bold"),padx=9,pady=4).grid(row=0,column=0,sticky="w")
        tk.Label(f,text=PINS[i],bg=CARD,fg=MUTED,font=("Segoe UI",9)).grid(row=0,column=1,sticky="w",padx=8)
        b=tk.Menubutton(f,textvariable=self.kind,relief="flat",bg="#F7F8FA",fg=TEXT,font=("Segoe UI",9),padx=9,pady=5,cursor="hand2")
        m=tk.Menu(b,tearoff=False)
        for item in TYPES: m.add_radiobutton(label=item,variable=self.kind,value=item,command=self.type_changed)
        b["menu"]=m; b.grid(row=0,column=2)
        box=tk.Frame(f,bg=CARD); box.grid(row=1,column=0,columnspan=3,sticky="ew",pady=(10,0)); box.grid_columnconfigure(0,weight=1)
        self.entry=tk.Entry(box,textvariable=self.value,relief="flat",bg="#F7F8FA",fg=TEXT,readonlybackground="#F7F8FA",font=("Segoe UI",10),highlightbackground=BORDER,highlightcolor=PRIMARY,highlightthickness=1)
        self.entry.grid(row=0,column=0,sticky="ew",ipady=8); self.entry.bind("<Button-1>",self.clicked); self.entry.bind("<KeyPress>",self.down); self.entry.bind("<KeyRelease>",self.up)
        self.button=tk.Button(box,text="录制",command=self.start,relief="flat",bg=SOFT,fg=PRIMARY,font=("Segoe UI",9,"bold"),cursor="hand2",padx=12,pady=7)
        self.button.grid(row=0,column=1,padx=(8,0)); self.type_changed()
    def type_changed(self):
        self.stop(); text=self.kind.get()=="文本"; self.entry.config(state="normal" if text else "readonly"); self.button.config(state="disabled" if text else "normal",bg="#F2F4F7" if text else SOFT,fg="#98A2B3" if text else PRIMARY)
    def clicked(self,e):
        if self.kind.get()!="文本": self.start(); return "break"
    def start(self):
        if self.kind.get()=="文本": return
        self.app.stop_others(self); self.recording=True; self.pressed=[]; self.value.set("请按下按键…"); self.entry.config(readonlybackground="#FFF8E7",highlightbackground="#F5C451"); self.button.config(text="录制中",bg="#FFF0C2",fg=AMBER); self.entry.focus_set()
    def stop(self):
        self.recording=False; self.pressed=[]; self.entry.config(readonlybackground="#F7F8FA",highlightbackground=BORDER); self.button.config(text="录制")
    def down(self,e):
        if not self.recording: return "break" if self.kind.get()!="文本" else None
        token=event_token(e)
        if token and token not in self.pressed: self.pressed.append(token); self.show()
        return "break"
    def up(self,e):
        if not self.recording:return
        token=event_token(e)
        if token and self.pressed:
            ordered=[x for x in MODS if x in self.pressed]+[x for x in self.pressed if x not in MODS]
            self.value.set("+".join(ordered)); self.kind.set("组合键" if len(ordered)>1 else "单键"); self.stop(); self.app.set_status(f"{KEYS[self.i]} 已录入：{self.value.get()}",GREEN)
        return "break"
    def show(self):
        ordered=[x for x in MODS if x in self.pressed]+[x for x in self.pressed if x not in MODS]; self.value.set(" + ".join(ordered))

class App:
    def __init__(self,root):
        self.root=root; root.title(TITLE); root.geometry("1120x650"); root.minsize(980,610); root.configure(bg=BG)
        self.drive=tk.StringVar(value=detect_drive()); self.status=tk.StringVar(value="准备就绪"); self.rows=[]; self.build(); self.load_config()
    def build(self):
        s=tk.Frame(self.root,bg=BG,padx=28,pady=24); s.pack(fill="both",expand=True); s.grid_columnconfigure(0,weight=1); s.grid_rowconfigure(3,weight=1)
        h=tk.Frame(s,bg=BG); h.grid(row=0,column=0,sticky="ew"); tk.Label(h,text="Macro Studio",bg=BG,fg=TEXT,font=("Segoe UI",22,"bold")).pack(anchor="w"); tk.Label(h,text="为 6 键宏键盘快速设置单键、组合键和文本",bg=BG,fg=MUTED,font=("Segoe UI",10)).pack(anchor="w")
        d=tk.Frame(s,bg=CARD,highlightbackground=BORDER,highlightthickness=1,padx=16,pady=13); d.grid(row=1,column=0,sticky="ew",pady=(18,7)); d.grid_columnconfigure(1,weight=1)
        tk.Label(d,text="设备位置",bg=CARD,fg=TEXT,font=("Segoe UI",10,"bold")).grid(row=0,column=0)
        tk.Entry(d,textvariable=self.drive,relief="flat",bg="#F7F8FA",fg=TEXT,font=("Segoe UI",10),highlightbackground=BORDER,highlightcolor=PRIMARY,highlightthickness=1).grid(row=0,column=1,sticky="ew",padx=14,ipady=7)
        tk.Button(d,text="选择目录",command=self.browse,relief="flat",bg=SOFT,fg=PRIMARY,font=("Segoe UI",9,"bold"),cursor="hand2",padx=12,pady=7).grid(row=0,column=2)
        tk.Label(d,text="请选择含 code.py 的 CIRCUITPY 根目录",bg=CARD,fg=MUTED,font=("Segoe UI",9)).grid(row=1,column=1,sticky="w",padx=14,pady=(6,0))
        t=tk.Frame(s,bg=BG); t.grid(row=2,column=0,sticky="ew",pady=(10,0)); tk.Label(t,text="按键功能 · PCB 布局",bg=BG,fg=TEXT,font=("Segoe UI",12,"bold")).pack(side="left"); tk.Label(t,text="点击“录制”，再按下实体键盘上的按键",bg=BG,fg=MUTED,font=("Segoe UI",9)).pack(side="right")
        g=tk.Frame(s,bg=BG); g.grid(row=3,column=0,sticky="nsew")
        for i in range(3):g.grid_columnconfigure(i,weight=1,uniform="c")
        for i in range(2):g.grid_rowconfigure(i,weight=1)
        for i,x in enumerate(DEFAULTS):self.rows.append(MacroRow(self,g,i,x))
        f=tk.Frame(s,bg=BG); f.grid(row=4,column=0,sticky="ew",pady=(14,0)); self.status_label=tk.Label(f,textvariable=self.status,bg=BG,fg=MUTED,font=("Segoe UI",9)); self.status_label.pack(side="left")
        tk.Button(f,text="恢复默认",command=self.restore,relief="flat",bg="#EAECF0",fg=TEXT,cursor="hand2",padx=14,pady=9).pack(side="right",padx=(8,0)); tk.Button(f,text="保存到设备",command=self.save,relief="flat",bg=PRIMARY,fg="white",font=("Segoe UI",9,"bold"),cursor="hand2",padx=18,pady=9).pack(side="right")
        tk.Label(s,text="设备通电连接电脑即可使用；保存后配置会自动生效，无需按 RESET 或重新插拔 USB。",bg="#ECFDF3",fg=GREEN,anchor="w",padx=12,pady=8,font=("Segoe UI",9)).grid(row=5,column=0,sticky="ew",pady=(14,0))
    def stop_others(self,current):
        for r in self.rows:
            if r is not current and r.recording:r.stop()
    def set_status(self,text,color=MUTED):self.status.set(text); self.status_label.config(fg=color)
    def browse(self):
        folder=filedialog.askdirectory(title="选择 CIRCUITPY 根目录")
        if folder:self.drive.set(folder); self.load_config()
    def load_config(self):
        p=Path(self.drive.get().strip())/"config.json" if self.drive.get().strip() else None
        if not p or not p.exists():return
        try:
            keys=json.loads(p.read_text(encoding="utf-8")).get("keys",[])
            if len(keys)!=6:return
            for r,a in zip(self.rows,keys):r.kind.set(FROM_CODE.get(a.get("type"),"单键")); r.value.set(str(a.get("value",""))); r.type_changed()
            self.set_status("已载入设备中的 config.json",GREEN)
        except Exception:self.set_status("未能读取现有配置",AMBER)
    def restore(self):
        for r,x in zip(self.rows,DEFAULTS):r.kind.set(x[0]);r.value.set(x[1]);r.type_changed()
        self.set_status("已恢复默认配置（尚未保存）",AMBER)
    def save(self):
        root=Path(self.drive.get().strip())
        if not root.exists() or not (root/"code.py").exists():messagebox.showerror("路径错误","请选择包含 code.py 的 CIRCUITPY 根目录。");return
        actions=[]
        for i,r in enumerate(self.rows):
            kind=r.kind.get(); value=r.value.get() if kind=="文本" else r.value.get().replace(" ",""); parts=[x for x in value.split("+") if x]
            if not value or value=="请按下按键…":messagebox.showerror("配置错误",f"{KEYS[i]} 的内容不能为空。");return
            if kind=="组合键" and len(parts)<2:messagebox.showerror("配置错误",f"{KEYS[i]} 请录入至少两个按键。");return
            if kind=="单键" and len(parts)!=1:messagebox.showerror("配置错误",f"{KEYS[i]} 只能包含一个按键。");return
            if kind=="文本" and len(value)>500:messagebox.showerror("配置错误",f"{KEYS[i]} 文本最多 500 个字符。");return
            actions.append({"type":TO_CODE[kind],"value":value})
        target=root/"config.json"; temp=root/"config.tmp"
        try:
            with open(temp,"w",encoding="utf-8",newline="\n") as file:json.dump({"version":1,"keys":actions},file,ensure_ascii=True,indent=2);file.flush();os.fsync(file.fileno())
            os.replace(temp,target)
        except Exception as e:
            try:temp.unlink(missing_ok=True)
            except Exception:pass
            messagebox.showerror("保存失败","无法写入 CIRCUITPY。\n\n"+str(e));return
        self.set_status("配置已保存，设备将在约 0.5 秒内自动应用",GREEN);messagebox.showinfo("保存成功","config.json 已写入。\n\n新配置将在约 0.5 秒内自动生效，无需按 RESET 或重新插拔 USB。")

if __name__=="__main__":
    window=tk.Tk();App(window);window.mainloop()
