# Standard library imports
import os
from pathlib import Path
import platform
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox

# Third-party imports
import customtkinter as ctk
from loguru import logger

# Local imports
from config import CONFIG, BUNDLE_DIR

class DataProcessorApp(ctk.CTk):
    def __init__(self, start_callback=None, edit_callback=None, fetch_models_callback=None) -> None:
        """Initializes the main application window and its widgets."""

        super().__init__()

        self.title("TOBot - The Belgian Stock-Exchange Tax Toolbox")
        self.geometry("450x650")
        self.minsize(450, 650)
        self.maxsize(5000, 5000) #to make it consisten in Mac OS X (26.4.1)
        self.resizable(True, True)

        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        self.set_app_icon() # Apply Cross-Platform Icon

        self.start_callback = start_callback
        self.edit_callback = edit_callback
        self.fetch_models_callback = fetch_models_callback

        self.selected_folder = ctk.StringVar(value=CONFIG.get("last_folder_path", ""))
        self.api_choice = ctk.StringVar(value="Mistral Cloud")
        self.model_choice = ctk.StringVar(value=CONFIG.get("model_choice", "mistral-medium-latest"))

        self.create_widgets()

    def create_widgets(self) -> None:
        """Sets up all the UI components in the main application window."""

        # Folder Selection
        ctk.CTkLabel(self, text="Folder for Processing", font=("Arial", 14, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        folder_frame = ctk.CTkFrame(self, fg_color="transparent")
        folder_frame.pack(fill="x", padx=20)


        # Browse Button
        self.entry_folder = ctk.CTkEntry(folder_frame, textvariable=self.selected_folder, width=280, justify="right")
        self.entry_folder.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Bind the Enter key to trigger the folder validation (same as clicking Browse)
        self.entry_folder.bind("<Return>", self.validate_folder_path)

        self.btn_browse = ctk.CTkButton(folder_frame, text="🔍 Browse...", width=100, command=self.browse_folder)
        self.btn_browse.pack(side="right")


        # Maping and Open Folder Buttons
        utils_frame = ctk.CTkFrame(self, fg_color="transparent")
        utils_frame.pack(fill="x", padx=20, pady=(15, 5))

        self.btn_edit = ctk.CTkButton(
            utils_frame,
            text="🧩 Mapping Rules",
            height=32,
            font=("Arial", 12, "bold"),
            fg_color="gray",
            hover_color="darkgray",
            command=self.edit_mapping
        )
        self.btn_edit.pack(side="left", fill="x", expand=True, padx=(0, 5)) # padx=(0, 5) gives a little 5px gap between the two buttons

        self.btn_open_folder = ctk.CTkButton(
            utils_frame,
            text="🗂️ Open Folder",
            height=32,
            font=("Arial", 12, "bold"),
            fg_color="gray",
            hover_color="darkgray",
            command=self.open_selected_folder
        )
        self.btn_open_folder.pack(side="right", fill="x", expand=True, padx=(5, 0)) # padx=(5, 0) mirrors the gap on the right button

        # Progress Bar
        self.lbl_progress = ctk.CTkLabel(self, text="Waiting to start...", text_color="gray")
        self.lbl_progress.pack(anchor="w", padx=20, pady=(20, 0))

        self.progress_bar = ctk.CTkProgressBar(self, width=410)
        self.progress_bar.set(0.0)
        self.progress_bar.pack(fill="x", padx=20, pady=(5, 10))

        # Run Mode Checkboxes
        ctk.CTkLabel(self, text="Processing Steps", font=("Arial", 14, "bold")).pack(anchor="w", padx=20, pady=(15, 0))

        checkbox_frame = ctk.CTkFrame(self, fg_color="transparent")
        checkbox_frame.pack(fill="x", padx=20, pady=(5, 10))

        # Variables holding the True/False state
        self.var_full = ctk.BooleanVar(value=True)
        self.var_extract = ctk.BooleanVar(value=True)
        self.var_calc = ctk.BooleanVar(value=True)

        # Interlocking commands
        def on_full_toggle():
            is_checked = self.var_full.get()
            self.var_extract.set(is_checked)
            self.var_calc.set(is_checked)

        def on_single_toggle():
            if self.var_extract.get() and self.var_calc.get():
                self.var_full.set(True)
            else:
                self.var_full.set(False)

        # Creating the checkboxes
        self.chk_full = ctk.CTkCheckBox(checkbox_frame, text="Full Processing", variable=self.var_full, command=on_full_toggle)
        self.chk_full.pack(side="left", padx=(0, 15))

        self.chk_extract = ctk.CTkCheckBox(checkbox_frame, text="Extraction", variable=self.var_extract, command=on_single_toggle)
        self.chk_extract.pack(side="left", padx=(0, 15))

        self.chk_calc = ctk.CTkCheckBox(checkbox_frame, text="Calculation", variable=self.var_calc, command=on_single_toggle)
        self.chk_calc.pack(side="left")


        # Start Button
        self.btn_start = ctk.CTkButton(self, text="🚀 Start Processing", height=40, font=("Arial", 14, "bold"), command=self.start_processing)
        self.btn_start.pack(fill="x", padx=20, pady=(10, 5))

        # API & Model Choice Section
        ctk.CTkLabel(self, text="API & Model Choice", font=("Arial", 14, "bold")).pack(anchor="w", padx=20, pady=(20, 5))

        mode_frame = ctk.CTkFrame(self, fg_color="transparent")
        mode_frame.pack(fill="x", padx=20)

        self.seg_btn_mode = ctk.CTkSegmentedButton(
            mode_frame,
            values=["Mistral Cloud", "Custom Endpoint"],
            variable=self.api_choice,
            command=self.toggle_slider_state
        )
        self.seg_btn_mode.pack(side="left")

        self.entry_custom = ctk.CTkEntry(mode_frame, textvariable=self.model_choice, justify="left")
        self.entry_custom.pack(side="left", fill="x", expand=True, padx=(15, 0))

        self.dropdown_custom = ctk.CTkOptionMenu(
            mode_frame,
            variable=self.model_choice,
            values=["Loading..."]
        )

        # Mistral Model Size Slider
        # A static container to maintain layout order
        self.slider_container = ctk.CTkFrame(self, fg_color="transparent")
        self.slider_container.pack(fill="x")

        self.slider_inner_frame = ctk.CTkFrame(self.slider_container, fg_color="transparent")
        self.slider_inner_frame.pack(fill="x")

        # Parent everything to slider_inner_frame instead of self
        ctk.CTkLabel(self.slider_inner_frame, text="Mistral Model Size", font=("Arial", 14, "bold")).pack(anchor="w", padx=20, pady=(20, 5))

        self.slider_var = ctk.IntVar()

        self.slider = ctk.CTkSlider(
            self.slider_inner_frame, # Changed parent
            from_=0,
            to=2,
            number_of_steps=2,
            variable=self.slider_var,
            command=self.update_model_choice_from_slider
        )
        self.slider.pack(fill="x", padx=20)

        # Store default colors so we can restore them when un-masking
        self.default_progress_color = self.slider.cget("progress_color")
        self.default_button_color = self.slider.cget("button_color")
        self.default_fg_color = self.slider.cget("fg_color")

        slider_labels_frame = ctk.CTkFrame(self.slider_inner_frame, fg_color="transparent") # Changed parent
        slider_labels_frame.pack(fill="x", padx=20)

        ctk.CTkLabel(slider_labels_frame, text="Small").pack(side="left")
        ctk.CTkLabel(slider_labels_frame, text="Medium").pack(side="left", expand=True)
        ctk.CTkLabel(slider_labels_frame, text="Large").pack(side="right")

        # Custom Model Section
        self.custom_explanation = ctk.CTkLabel(
            self.slider_container,
            text="Allows to use custom local models via OpenAI API.\nMake sure you choose a multimodal model with sufficient context window size.",
            text_color="gray",
            font=("Arial", 12, "italic")
        )

        # Initially hide the custom model UI since Mistral is the default selection
        if self.api_choice.get() == "Custom Endpoint":
            self.slider_inner_frame.pack_forget()
            self.custom_explanation.pack(pady=30) # Show Ollama text
        # Mistral is default, so we don't need an 'else' because the slider is already packed

        # Scrollable Log Output
        ctk.CTkLabel(self, text="Output", font=("Arial", 14, "bold")).pack(anchor="w", padx=20, pady=(20, 5))
        self.log_textbox = ctk.CTkTextbox(
            self,
            height=150,
            state="disabled",
            font=("Courier", 11),
            wrap="word",
            fg_color=("white", "gray17")
        )

        # Set up color tags for different log levels
        self.log_textbox.tag_config("WARNING", foreground="olive")
        self.log_textbox.tag_config("ERROR", foreground="red")
        self.log_textbox.tag_config("CRITICAL", foreground="red", background="black")

        self.log_textbox.pack(fill="both", expand=True, padx=20, pady=(5, 15))

        # Attach a trace to model_choice to update the slider whenever the text changes
        self.model_choice.trace_add("write", self.sync_slider_to_model)

        # Trigger it once at startup to set the initial slider state based on the loaded model
        self.sync_slider_to_model()

        if self.selected_folder.get():
            self.after(50, lambda: self.entry_folder.xview_moveto(1))

    def set_app_icon(self) -> None:
        """Handles cross-platform icon loading for the application window."""
        current_os = platform.system()

        try:
            if current_os == "Windows":
                # Windows uses .ico and iconbitmap
                icon_path = BUNDLE_DIR / "assets" / "icon.ico"
                if icon_path.exists():
                    self.iconbitmap(icon_path)

            elif current_os in ["Linux", "Darwin"]:
                # Linux and macOS use .png and iconphoto
                icon_path = BUNDLE_DIR / "assets" / "icon.png"
                if icon_path.exists():
                    img = tk.PhotoImage(file=icon_path)
                    self.iconphoto(True, img)

        except Exception as e:
            # Silently fail if the icon doesn't load so we don't crash the app
            print(f"Warning: Failed to load icon for {current_os}: {e}")

    def browse_folder(self) -> None:
        """Opens a folder selection dialog and updates the entry field with the chosen path."""
        current_path = self.selected_folder.get().strip()
        folder = filedialog.askdirectory(
            title="Select Folder for Processing",
            initialdir=current_path if current_path else None
        )
        if folder:
            self.selected_folder.set(folder)
            self.entry_folder.xview_moveto(1)

            # Delegate the file inspection to the helper
            self._check_folder_contents(Path(folder))

    def validate_folder_path(self, event=None) -> None:
        """Validates the manually entered or pasted folder path when the user presses Enter."""
        folder_string = self.selected_folder.get().strip()
        if not folder_string:
            return

        target_folder = Path(folder_string)
        if not target_folder.is_dir():
            messagebox.showerror("Invalid Path", f"The path does not exist or is not a folder:\n{folder_string}")
            return

        self.entry_folder.xview_moveto(1)

        # Delegate the file inspection to the helper
        self._check_folder_contents(target_folder)

    def _check_folder_contents(self, target_folder: Path) -> None:
        """Helper method to check for PDFs and warn about file limits in a given folder."""
        try:
            # Gather all PDF files (case-insensitive extension check)
            pdf_files = [
                f for f in target_folder.iterdir()
                if f.is_file() and f.suffix.lower() == ".pdf"
            ]

            if not pdf_files:
                logger.warning("No PDF files found in the selected folder!")
            else:
                logger.info(f"Found {len(pdf_files)} PDF file(s) in the selected folder")

            # Check if any PDF exceeds the 50 MB limit
            limit_bytes = 50 * 1024 * 1024
            for pdf in pdf_files:
                file_size = pdf.stat().st_size
                if file_size > limit_bytes:
                    size_mb = file_size / (1024 * 1024)
                    logger.warning(
                        f"File '{pdf.name}' is {size_mb:.2f} MB, which exceeds the 50 MB limit for Mistral OCR!"
                    )
        except PermissionError:
            logger.error(f"Permission denied accessing folder: {target_folder}")
            messagebox.showerror("Permission Denied", f"Cannot access the folder:\n{target_folder}")

    def edit_mapping(self) -> None:
        """Triggers the edit callback to open the system's default .CSV editor."""
        if self.edit_callback:
            self.edit_callback()

    def open_selected_folder(self) -> None:
        """Open the currently selected folder in the system's file manager."""
        folder_path = self.selected_folder.get().strip()

        # Quick sanity check
        if not folder_path or not Path(folder_path).is_dir():
            messagebox.showwarning("Warning", "Please select a valid folder first.")
            return

        try:
            current_os = platform.system()
            if current_os == "Windows":
                getattr(os, 'startfile')(folder_path)
            elif current_os == "Darwin":  # macOS
                subprocess.call(["open", folder_path])
            else:  # Linux variants
                subprocess.call(["xdg-open", folder_path])
        except Exception as e:
            logger.error(f"Failed to open folder: {e}")

    def sync_slider_to_model(self, *args) -> None:
        """Evaluates the current model_choice text and updates the slider's state and position."""
        current_model = self.model_choice.get().strip()

        if current_model == "mistral-small-latest":
            self.slider_var.set(0)
            self._unmask_slider()
        elif current_model == "mistral-medium-latest":
            self.slider_var.set(1)
            self._unmask_slider()
        elif current_model == "mistral-large-latest":
            self.slider_var.set(2)
            self._unmask_slider()
        else:
            # If it's anything else (custom typing), visually hide the choice
            self._mask_slider()

    def _unmask_slider(self) -> None:
        """Visually umasks the slider button and its progress bar."""
        self.slider.configure(
            #state="normal",
            progress_color=self.default_progress_color,
            button_color=self.default_button_color
        )

    def _mask_slider(self) -> None:
        """Visually masks the slider button and its progress bar."""
        self.slider.configure(
            #state="disabled",
            progress_color=self.default_fg_color, # Match track background
            button_color="gray"                   # Dull out the thumb
        )

    def toggle_slider_state(self, selected_mode) -> None:
        """Shows or hides UI elements based on the selected API mode."""
        if selected_mode == "Custom Endpoint":
            # Hide the Mistral slider UI
            self.slider_inner_frame.pack_forget()

            # Ask the Controller to fetch the models
            models = None
            if self.fetch_models_callback:
                models = self.fetch_models_callback()

            # Handle the result
            if models: # Success
                # Hide the text input, show the dropdown, and load the models
                self.entry_custom.pack_forget()
                self.dropdown_custom.configure(values=models)
                self.model_choice.set(models[0]) # Auto-select the first model

                self.dropdown_custom.pack(side="left", fill="x", expand=True, padx=(15, 0))
                self.custom_explanation.pack(pady=30)
            else: # Fetch failed (offline or empty).
                # Revert the segmented button back to Mistral automatically.
                self.api_choice.set("Mistral Cloud")
                self.toggle_slider_state("Mistral Cloud") # Recursive call to reset UI

        else:
            # Hide the Custom Endpoint UI
            self.custom_explanation.pack_forget()
            self.dropdown_custom.pack_forget()

            # Show the Mistral UI
            self.entry_custom.pack(side="left", fill="x", expand=True, padx=(15, 0))
            self.slider_inner_frame.pack(fill="x")

            # Reset the Mistral text based on where the slider currently is
            self.update_model_choice_from_slider(self.slider_var.get())

    def update_model_choice_from_slider(self, value) -> None:
        """Updates the model choice based on the slider position."""
        position = int(round(float(value)))
        if position == 0:
            self.model_choice.set("mistral-small-latest")
        elif position == 1:
            self.model_choice.set("mistral-medium-latest")
        elif position == 2:
            self.model_choice.set("mistral-large-latest")

    def start_processing(self) -> None:
        """Gathers user selections and triggers the start callback to begin processing."""
        folder_string = self.selected_folder.get().strip()
        api_choice = self.api_choice.get()
        model_choice = self.model_choice.get().strip()
        slider_value = self.slider_var.get()
        run_extract = self.var_extract.get()
        run_calc = self.var_calc.get()

        if not run_extract and not run_calc:
            messagebox.showwarning("Warning", "Please select at least one processing step.")
            return

        logger.debug(f"User selected slider position: {slider_value}")

        if not folder_string:
            messagebox.showwarning("Missing Information", "Please select or paste a folder path first.")
            return

        target_folder = Path(folder_string)
        if not target_folder.is_dir():
            messagebox.showerror("Invalid Path", f"The path does not exist or is not a folder:\n{folder_string}")
            return

        logger.debug("Sending Job to Controller...")

        self.btn_start.configure(state="disabled", text="Processing...")
        self.btn_browse.configure(state="disabled")
        self.lbl_progress.configure(text="Initializing...")
        self.progress_bar.set(0.0)

        #clear the log textbox
        self.log_textbox.configure(state="normal") # Unlock it
        self.log_textbox.delete("1.0", "end")      # Erase old logs
        self.log_textbox.configure(state="disabled") # Lock it again

        if self.start_callback:
            # Update the callback to include our new boolean flags
            self.start_callback(folder_string, api_choice, model_choice, run_extract, run_calc)

    def update_progress(self, current_file_name, current_step, total_steps) -> None:
        """Updates the progress bar and status text based on the current processing step."""
        # Subtracting 0.5 places the bar in the middle of the current step's chunk
        progress_value = (current_step - 0.5) / total_steps

        status_text = f"Processing ({current_step}/{total_steps}): {current_file_name}"
        self.after(0, self._apply_progress, progress_value, status_text)

    def _apply_progress(self, value, text) -> None:
        """Applies the progress update to the UI components."""
        self.progress_bar.set(value)
        self.lbl_progress.configure(text=text)

    def show_error_dialog(self, title, message) -> None:
        """A public method for the Controller to trigger error pop-ups."""
        messagebox.showerror(title, message)

    def show_summary(self, summary_text) -> None:
        """Displays the final summary in a new window with options to copy or close."""
        summary_window = ctk.CTkToplevel(self)
        summary_window.title("Processing Summary")
        summary_window.geometry("500x650")
        summary_window.attributes("-topmost", True)
        summary_window.focus()

        textbox = ctk.CTkTextbox(summary_window, font=("Courier", 13), wrap="none")
        textbox.pack(expand=True, fill="both", padx=15, pady=(15, 10))
        textbox.insert("0.0", summary_text)
        textbox.configure(state="disabled")

        def copy_to_clipboard():
            summary_window.clipboard_clear()
            summary_window.clipboard_append(summary_text)
            copy_button.configure(text="Copied!")
            summary_window.after(2000, lambda: copy_button.configure(text="Copy to Clipboard"))

        def close_window(event=None):
            summary_window.destroy()

        button_frame = ctk.CTkFrame(summary_window, fg_color="transparent")
        button_frame.pack(pady=(0, 15))

        copy_button = ctk.CTkButton(
            button_frame,
            text="Copy to Clipboard",
            command=copy_to_clipboard,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "#DCE4EE")
        )
        copy_button.pack(side="left", padx=10)

        close_button = ctk.CTkButton(button_frame, text="Close", command=close_window)
        close_button.pack(side="left", padx=10)

        close_button.focus_set()
        summary_window.bind('<Return>', close_window)

    def handle_log_message(self, message, level) -> None:
        """Thread-safe method called by the Loguru sink."""
        # Route it back to the main GUI thread
        self.after(0, self._apply_log_message, message, level)

    def _apply_log_message(self, message, level) -> None:
        """Appends log messages to the scrollable textbox."""
        # Unlock the textbox so we can write to it
        self.log_textbox.configure(state="normal")

        # Assign an emoji symbol for visual scanning
        symbol = ""
        if level == "WARNING":
            symbol = "⚠️ "
        elif level in ["ERROR", "CRITICAL"]:
            symbol = "❌ "

        # Split the string on the date closing bracket to make the emoji an infix
        if "] " in message:
            timestamp, rest_of_message = message.split("] ", 1)
            formatted_text = f"{timestamp}] {symbol}{rest_of_message}\n"
        else:
            # Fallback just in case a log message doesn't have the standard timestamp format
            formatted_text = f"{symbol}{message}\n"

        # Insert the text at the very end, applying the color tag based on the level
        self.log_textbox.insert("end", formatted_text, level)

        # Auto-scroll to the bottom
        self.log_textbox.yview("end")

        # Lock the textbox again
        self.log_textbox.configure(state="disabled")

        self.update_idletasks() # Force UI refresh

    def reset_ui(self) -> None:
        """Resets the UI to its initial state after processing is complete."""

        self.after(0, self._apply_reset)

    def _apply_reset(self) -> None:
        """Applies the UI reset, re-enabling buttons and updating status text."""

        self.btn_start.configure(state="normal", text="Start Processing")
        self.btn_browse.configure(state="normal")
        self.lbl_progress.configure(text="Finished!", text_color="green")
        self.progress_bar.set(1.0)
        self.update_idletasks()