import tkinter as tk
import mian
import ast
import subprocess
class LineNumberCanvas(tk.Canvas):
    def __init__(self, master, text_widget, **kwargs):
        super().__init__(master, **kwargs)
        self.text_widget = text_widget

    def redraw(self, *args):
        self.delete("all")

        i = self.text_widget.index("@0,0")
        while True:
            dline = self.text_widget.dlineinfo(i)
            if dline is None:
                break

            y = dline[1]
            line_number = str(i).split(".")[0]
            self.create_text(2, y, anchor="nw", text=line_number)

            i = self.text_widget.index(f"{i}+1line")


class IDE(tk.Tk):
    def __init__(self):
        super().__init__()
        self.output = ""
        self.title("IDE for Py2Ino")
        self.output_label = tk.Label(self, text="",anchor='w')
        self.output_label.pack(side=tk.BOTTOM, fill='x')
        run_button = tk.Button(self, text="Run Code", command=self.run_code)
        run_button.pack(side="right", fill="none")
        self.text = tk.Text(self, wrap="none")
        self.text.pack(side="right", fill="both", expand=True)
        self.line_numbers = LineNumberCanvas(self, self.text, width=40, bg="black")
        self.line_numbers.pack(side="left", fill="y")
        self.compbut = tk.Button(self, text="Compile", command=self.compile)
        self.compbut.pack(side="right", fill="none")
        self.compbut.pack_forget()
        # Bind events to update line numbers
        self.text.bind("<KeyRelease>", self.update_line_numbers)
        self.text.bind("<MouseWheel>", self.update_line_numbers)
        self.text.bind("<Button-1>", self.update_line_numbers)
        
        self.update_line_numbers()

    def update_line_numbers(self, event=None):
        self.line_numbers.redraw()
        self.text.config(yscrollcommand=self.on_scroll)

    def on_scroll(self, *args):
        self.line_numbers.yview_moveto(args[0])
        self.text.bind("<Configure>", self.update_line_numbers)
        self.text.bind("<FocusIn>", self.update_line_numbers)
    def run_code(self):
        code = self.text.get("1.0", tk.END)
        try:
            tree = ast.parse(code)
            self.output = mian.start(tree)
            self.output_label.config(text=self.output)
        except Exception as e:
            self.output_label.config(text="Error: "+str(e))
            self.compbut.pack_forget()
        else:
            self.compbut.pack()

    def compile(self):
        subprocess.run(['mkdir', '-p', 'py2ino'])
        subprocess.run(['rm', '-r', 'py2ino'])
        subprocess.run(['mkdir', 'py2ino'])
        out = open('py2ino/py2ino.ino', 'w')
        out.write(self.output)
        out.close()
        subprocess.run(['arduino-cli', 'compile', '-b', 'arduino:avr:uno', 'py2ino/py2ino.ino'])
if __name__ == "__main__":
    app = IDE()
    app.mainloop()