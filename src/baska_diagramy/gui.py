"""Proste okno do generowania diagramów Baśki (bez konsoli)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk

from .table import save_state, state_from_dict


def project_root() -> Path:
    """Katalog projektu (obok examples/ i output/)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    # .../src/baska_diagramy/gui.py → parents[2] = diagramy/
    return Path(__file__).resolve().parents[2]


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Baśka — generator diagramów")
        self.geometry("980x720")
        self.minsize(800, 560)

        self.root_dir = project_root()
        self.examples_dir = self.root_dir / "examples"
        self.output_dir = self.root_dir / "output"
        self.output_dir.mkdir(exist_ok=True)
        self.examples_dir.mkdir(exist_ok=True)

        self.current_path: Path | None = None
        self.preview_imgtk: ImageTk.PhotoImage | None = None

        self._build()
        self._refresh_file_list()
        if self.file_list.size():
            self.file_list.selection_set(0)
            self._on_select()

    def _build(self) -> None:
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        left = ttk.Frame(self, padding=8)
        left.grid(row=0, column=0, sticky="nsw")
        left.rowconfigure(1, weight=1)

        ttk.Label(left, text="Pliki JSON").grid(row=0, column=0, sticky="w")
        self.file_list = tk.Listbox(left, width=28, height=18, exportselection=False)
        self.file_list.grid(row=1, column=0, sticky="nsw")
        self.file_list.bind("<<ListboxSelect>>", lambda _e: self._on_select())

        btns = ttk.Frame(left)
        btns.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(btns, text="Odśwież listę", command=self._refresh_file_list).pack(fill="x", pady=2)
        ttk.Button(btns, text="Otwórz JSON…", command=self._open_json).pack(fill="x", pady=2)
        ttk.Button(btns, text="Nowy z szablonu", command=self._new_from_template).pack(fill="x", pady=2)

        right = ttk.Frame(self, padding=8)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        right.rowconfigure(3, weight=1)

        self.path_var = tk.StringVar(value="")
        ttk.Label(right, textvariable=self.path_var).grid(row=0, column=0, sticky="w")

        self.editor = tk.Text(right, wrap="none", font=("Consolas", 11), undo=True)
        self.editor.grid(row=1, column=0, sticky="nsew")
        yscroll = ttk.Scrollbar(right, orient="vertical", command=self.editor.yview)
        yscroll.grid(row=1, column=1, sticky="ns")
        self.editor.configure(yscrollcommand=yscroll.set)

        actions = ttk.Frame(right)
        actions.grid(row=2, column=0, columnspan=2, sticky="ew", pady=8)
        ttk.Button(actions, text="Zapisz JSON", command=self._save_json).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Generuj PNG", command=self._generate).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Generuj wszystkie z examples/", command=self._generate_all).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(actions, text="Otwórz folder output", command=self._open_output).pack(side="left")

        prev_frame = ttk.LabelFrame(right, text="Podgląd", padding=6)
        prev_frame.grid(row=3, column=0, columnspan=2, sticky="nsew")
        prev_frame.columnconfigure(0, weight=1)
        prev_frame.rowconfigure(0, weight=1)
        self.preview = ttk.Label(prev_frame, anchor="center")
        self.preview.grid(row=0, column=0, sticky="nsew")

        self.status = tk.StringVar(value=f"Katalog: {self.root_dir}")
        ttk.Label(self, textvariable=self.status, padding=(8, 4)).grid(
            row=1, column=0, columnspan=2, sticky="ew"
        )

    def _refresh_file_list(self) -> None:
        self.file_list.delete(0, tk.END)
        for path in sorted(self.examples_dir.glob("*.json")):
            self.file_list.insert(tk.END, path.name)

    def _selected_name(self) -> str | None:
        sel = self.file_list.curselection()
        if not sel:
            return None
        return self.file_list.get(sel[0])

    def _on_select(self) -> None:
        name = self._selected_name()
        if not name:
            return
        path = self.examples_dir / name
        self._load_path(path)

    def _load_path(self, path: Path) -> None:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as e:
            messagebox.showerror("Błąd", f"Nie mogę odczytać pliku:\n{e}")
            return
        self.current_path = path
        self.path_var.set(str(path))
        self.editor.delete("1.0", tk.END)
        self.editor.insert("1.0", text)
        out_name = None
        try:
            out_name = json.loads(text).get("output")
        except json.JSONDecodeError:
            pass
        preview = self.output_dir / (out_name or f"{path.stem}.png")
        if preview.is_file():
            self._show_preview(preview)

    def _open_json(self) -> None:
        path = filedialog.askopenfilename(
            title="Wybierz plik JSON",
            initialdir=str(self.examples_dir),
            filetypes=[("JSON", "*.json"), ("Wszystkie", "*.*")],
        )
        if path:
            self._load_path(Path(path))

    def _new_from_template(self) -> None:
        template = {
            "output": "nowy_diagram.png",
            "players": [
                {
                    "name": "S",
                    "position": "south",
                    "cards": ["Ah", "10h", "Qc"],
                    "highlight": [0, 2],
                },
                {"name": "W", "position": "west", "face_up": False, "cards": 2},
                {"name": "N", "position": "north", "face_up": False, "cards": 2},
                {"name": "E", "position": "east", "cards": ["Qs"]},
            ],
            "trick": ["Jd"],
        }
        name = "nowy_diagram.json"
        i = 1
        while (self.examples_dir / name).exists():
            name = f"nowy_diagram_{i}.json"
            i += 1
        path = self.examples_dir / name
        path.write_text(json.dumps(template, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self._refresh_file_list()
        names = list(self.file_list.get(0, tk.END))
        if name in names:
            self.file_list.selection_clear(0, tk.END)
            self.file_list.selection_set(names.index(name))
        self._load_path(path)
        self.status.set(f"Utworzono {path.name}")

    def _editor_json(self) -> dict:
        raw = self.editor.get("1.0", tk.END)
        return json.loads(raw)

    def _save_json(self) -> None:
        if self.current_path is None:
            path = filedialog.asksaveasfilename(
                title="Zapisz JSON",
                initialdir=str(self.examples_dir),
                defaultextension=".json",
                filetypes=[("JSON", "*.json")],
            )
            if not path:
                return
            self.current_path = Path(path)
        try:
            data = self._editor_json()
        except json.JSONDecodeError as e:
            messagebox.showerror("JSON", f"Niepoprawny JSON:\n{e}")
            return
        self.current_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        self.path_var.set(str(self.current_path))
        self._refresh_file_list()
        self.status.set(f"Zapisano {self.current_path.name}")

    def _generate(self) -> None:
        try:
            data = self._editor_json()
            state = state_from_dict(data)
        except (json.JSONDecodeError, ValueError) as e:
            messagebox.showerror("Błąd", str(e))
            return

        if self.current_path is None:
            self._save_json()
            if self.current_path is None:
                return
        else:
            # auto-zapis przed generowaniem
            try:
                self.current_path.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
            except OSError as e:
                messagebox.showerror("Zapis", str(e))
                return

        out_name = data.get("output") or f"{self.current_path.stem}.png"
        out_path = self.output_dir / out_name
        try:
            save_state(state, out_path)
        except Exception as e:
            messagebox.showerror("Generowanie", str(e))
            return
        self._show_preview(out_path)
        self.status.set(f"Wygenerowano: {out_path}")

    def _generate_all(self) -> None:
        files = sorted(self.examples_dir.glob("*.json"))
        if not files:
            messagebox.showinfo("Info", "Brak plików w examples/.")
            return
        ok = 0
        errors: list[str] = []
        last: Path | None = None
        for path in files:
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                state = state_from_dict(data)
                out_name = data.get("output") or f"{path.stem}.png"
                last = self.output_dir / out_name
                save_state(state, last)
                ok += 1
            except Exception as e:
                errors.append(f"{path.name}: {e}")
        if last and last.is_file():
            self._show_preview(last)
        msg = f"Wygenerowano {ok}/{len(files)}."
        if errors:
            msg += "\n\n" + "\n".join(errors[:8])
            messagebox.showwarning("Gotowe (z błędami)", msg)
        else:
            messagebox.showinfo("Gotowe", msg)
        self.status.set(msg.split(".", 1)[0] + ".")

    def _show_preview(self, path: Path) -> None:
        try:
            im = Image.open(path)
        except OSError:
            return
        max_w, max_h = 520, 320
        im = im.copy()
        im.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        self.preview_imgtk = ImageTk.PhotoImage(im)
        self.preview.configure(image=self.preview_imgtk)

    def _open_output(self) -> None:
        self.output_dir.mkdir(exist_ok=True)
        if sys.platform == "win32":
            os.startfile(self.output_dir)  # type: ignore[attr-defined]
        else:
            subprocess.run(["xdg-open", str(self.output_dir)], check=False)


def main() -> int:
    app = App()
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
