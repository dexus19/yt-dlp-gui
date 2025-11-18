 
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import threading
import os
import re
from pathlib import Path


class YTDLPDownloader:
    """Main application class for yt-dlp GUI"""

    def __init__(self, root):
        self.root = root
        self.root.title("yt-dlp Advanced GUI")
        self.root.geometry("700x580")
        self.download_process = None

        self._set_dark_theme()
        self._create_widgets()
        self._load_default_folder()

    def _set_dark_theme(self):
        """Apply dark theme to the application"""
        style = ttk.Style(self.root)
        alt_theme_path = "/usr/share/tk8.6/ttk/altTheme/alt.tcl"
        if os.path.exists(alt_theme_path):
            try:
                self.root.tk.call("source", alt_theme_path)
            except tk.TclError:
                pass

        self.root.configure(bg="#222222")
        style.configure(".", background="#222222", foreground="#ffffff")
        style.configure("TLabel", background="#222222", foreground="#ffffff")
        style.configure("TButton", background="#444444", foreground="#ffffff")
        style.configure("TEntry", fieldbackground="#333333", foreground="#ffffff")
        style.configure("TCombobox", fieldbackground="#333333", foreground="#ffffff")
        style.map("TButton", background=[("active", "#555555")])

    def _create_widgets(self):
        """Create all GUI widgets"""
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)

        # URL Entry
        ttk.Label(main, text="Video URL:").pack(anchor="w")
        self.url_entry = ttk.Entry(main, width=70)
        self.url_entry.pack(fill="x", pady=5)

        # Output folder
        ttk.Label(main, text="Download Folder:").pack(anchor="w")
        folder_frame = ttk.Frame(main)
        folder_frame.pack(fill="x", pady=5)

        self.output_var = tk.StringVar()
        output_entry = ttk.Entry(folder_frame, textvariable=self.output_var)
        output_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(folder_frame, text="Browse", command=self._choose_folder).pack(side="left", padx=(5, 0))

        # Format selection
        ttk.Label(main, text="Format:").pack(anchor="w", pady=(10, 0))
        self.format_var = tk.StringVar(value="MP4 (video)")
        format_box = ttk.Combobox(
            main,
            textvariable=self.format_var,
            values=["MP4 (video)", "MP3 (audio)", "Best Quality"],
            state="readonly"
        )
        format_box.pack(fill="x")
        format_box.bind("<<ComboboxSelected>>", self._on_format_change)

        # Resolution selection
        ttk.Label(main, text="Resolution:").pack(anchor="w", pady=(10, 0))
        self.resolution_var = tk.StringVar(value="Best")
        self.resolution_box = ttk.Combobox(
            main,
            textvariable=self.resolution_var,
            values=["Best", "144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p"],
            state="readonly"
        )
        self.resolution_box.pack(fill="x")

        # Options
        ttk.Label(main, text="Options:").pack(anchor="w", pady=(10, 0))
        self.aria_var = tk.BooleanVar()
        self.thumb_var = tk.BooleanVar()
        self.subtitles_var = tk.BooleanVar()

        ttk.Checkbutton(main, text="Use Aria2 (faster downloads)", variable=self.aria_var).pack(anchor="w")
        ttk.Checkbutton(main, text="Download Thumbnail", variable=self.thumb_var).pack(anchor="w")
        ttk.Checkbutton(main, text="Download Subtitles", variable=self.subtitles_var).pack(anchor="w")

        # Progress bar
        ttk.Label(main, text="Progress:").pack(anchor="w", pady=(10, 0))
        self.progress_var = tk.IntVar()
        self.progress = ttk.Progressbar(main, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x", pady=5)

        # Download/Cancel buttons
        button_frame = ttk.Frame(main)
        button_frame.pack(pady=10)
        self.download_btn = ttk.Button(button_frame, text="Start Download", command=self._start_download)
        self.download_btn.pack(side="left", padx=5)
        self.cancel_btn = ttk.Button(button_frame, text="Cancel", command=self._cancel_download, state="disabled")
        self.cancel_btn.pack(side="left", padx=5)

        # Log window
        ttk.Label(main, text="Log:").pack(anchor="w")
        log_frame = ttk.Frame(main)
        log_frame.pack(fill="both", expand=True, pady=5)

        self.log_text = tk.Text(log_frame, height=12, bg="#111111", fg="#00ff66", wrap="word")
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self.log_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def _load_default_folder(self):
        """Set default download folder to Downloads or home directory"""
        downloads_folder = Path.home() / "Downloads"
        if downloads_folder.exists():
            self.output_var.set(str(downloads_folder))
        else:
            self.output_var.set(str(Path.home()))

    def _on_format_change(self, event=None):
        """Disable resolution selection for audio format"""
        if self.format_var.get() == "MP3 (audio)":
            self.resolution_box.configure(state="disabled")
        else:
            self.resolution_box.configure(state="readonly")

    def _choose_folder(self):
        """Open folder selection dialog"""
        folder = filedialog.askdirectory(initialdir=self.output_var.get())
        if folder:
            self.output_var.set(folder)

    def _log(self, message):
        """Add message to log window"""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def _update_progress(self, text):
        """Parse and update progress bar from yt-dlp output"""
        # Match percentage in various formats
        percent_match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
        if percent_match:
            try:
                percent = float(percent_match.group(1))
                self.progress_var.set(int(percent))
            except (ValueError, IndexError):
                pass

    def _validate_inputs(self):
        """Validate user inputs before download"""
        url = self.url_entry.get().strip()
        output_folder = self.output_var.get()

        if not url:
            messagebox.showerror("Error", "Please enter a URL.")
            return False

        if not output_folder:
            messagebox.showerror("Error", "Please choose a download folder.")
            return False

        if not os.path.exists(output_folder):
            messagebox.showerror("Error", "Selected download folder does not exist.")
            return False

        return True

    def _build_command(self):
        """Build yt-dlp command with selected options"""
        url = self.url_entry.get().strip()
        format_choice = self.format_var.get()
        resolution_choice = self.resolution_var.get()
        output_folder = self.output_var.get()

        cmd = ["yt-dlp"]

        # Output template
        cmd += ["-o", os.path.join(output_folder, "%(title)s.%(ext)s")]

        # Thumbnail
        if self.thumb_var.get():
            cmd += ["--write-thumbnail", "--embed-thumbnail"]

        # Subtitles
        if self.subtitles_var.get():
            cmd += ["--write-subs", "--write-auto-subs", "--embed-subs", "--sub-lang", "en"]

        # Format selection
        if format_choice == "MP3 (audio)":
            cmd += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
        elif format_choice == "Best Quality":
            cmd += ["-f", "bestvideo+bestaudio/best", "--merge-output-format", "mp4"]
        else:  # MP4 (video)
            if resolution_choice == "Best":
                cmd += ["-f", "bestvideo+bestaudio/best", "--merge-output-format", "mp4"]
            else:
                height = resolution_choice.replace('p', '')
                cmd += ["-f", f"bestvideo[height<={height}]+bestaudio/best", "--merge-output-format", "mp4"]

        # Aria2 external downloader
        if self.aria_var.get():
            cmd += ["--external-downloader", "aria2c"]
            cmd += ["--external-downloader-args", "-x 16 -k 1M"]

        # Add metadata
        cmd += ["--add-metadata"]

        cmd.append(url)
        return cmd

    def _start_download(self):
        """Start the download process in a separate thread"""
        if not self._validate_inputs():
            return

        self._log("Starting download...\n")
        self.progress_var.set(0)
        self.download_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")

        def run():
            try:
                cmd = self._build_command()
                self._log(f"Command: {' '.join(cmd)}\n\n")

                self.download_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                for line in self.download_process.stdout:
                    if line.strip():
                        self._log(line)
                        self._update_progress(line)

                return_code = self.download_process.wait()

                if return_code == 0:
                    self._log("\n✓ Download completed successfully!\n\n")
                    self.progress_var.set(100)
                else:
                    self._log(f"\n✗ Download failed with error code {return_code}\n\n")

            except FileNotFoundError:
                self._log("\n✗ Error: yt-dlp not found. Please install it first.\n")
                messagebox.showerror("Error", "yt-dlp is not installed or not in PATH.")
            except Exception as e:
                self._log(f"\n✗ Error: {str(e)}\n\n")
                messagebox.showerror("Error", f"An error occurred: {str(e)}")
            finally:
                self.download_process = None
                self.download_btn.configure(state="normal")
                self.cancel_btn.configure(state="disabled")

        threading.Thread(target=run, daemon=True).start()

    def _cancel_download(self):
        """Cancel the current download"""
        if self.download_process:
            self.download_process.terminate()
            self._log("\n⚠ Download cancelled by user.\n\n")
            self.progress_var.set(0)
            self.download_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")


def main():
    root = tk.Tk()
    app = YTDLPDownloader(root)
    root.mainloop()


if __name__ == "__main__":
    main()
