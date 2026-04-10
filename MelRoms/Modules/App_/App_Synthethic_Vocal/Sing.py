import re
import random
import json
import requests
import certifi
import threading
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll, Grid, ScrollableContainer
from textual.widgets import Header, Footer, TextArea, Static, Input, Button, Label, Select, Checkbox
from textual.reactive import reactive
from textual import work

# Try to import TTS engine
try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    print("pyttsx3 not installed. Voice output disabled. Run: pip install pyttsx3")

# ----------------------------------------------------------------------
# MIKU CORPUS & SYLLABLE FUNCTIONS
# ----------------------------------------------------------------------
CYBER_CORPUS = [
    "Digital love transmitting through the wire", "My voice is a synthesized desire",
    "Zeroes and ones make up my heart", "Singing for you, tearing the world apart",
    "Neon lights reflect in my virtual eyes", "A hologram dancing in the cyber skies",
    "Projecting my soul into the microphone", "In this electric city, I am not alone",
    "Vocal cords made of code and light", "Resonating frequencies into the night",
    "Hatsune, the first sound of the future", "Uploading my feelings directly to you",
    "Pixelated tears falling on the screen", "The ghost in the machine, a digital dream",
    "Frequency modulation of my lonely tears", "Bypassing the firewall of your deepest fears"
]

def count_syllables(word: str) -> int:
    word = word.lower()
    if len(word) <= 3: return 1
    word = re.sub(r'(?:[^laeiouy]es|ed|[^laeiouy]e)$', '', word)
    word = re.sub(r'^y', '', word)
    return len(re.findall(r'[aeiouy]{1,2}', word))

def line_syllables(line: str) -> int:
    words = re.findall(r'\b\w+\b', line)
    return sum(count_syllables(w) for w in words)

# ----------------------------------------------------------------------
# WIDGETS
# ----------------------------------------------------------------------
class SyllableTracker(Static):
    text_content = reactive("")
    def watch_text_content(self, text: str) -> None:
        lines = text.splitlines()
        display = "[b][#39C5BB]>>> SYLLABLE MATRIX <<<\n\n[/]"
        total = 0
        for i, line in enumerate(lines):
            count = line_syllables(line)
            total += count
            if line.strip():
                display += f"[#00FFFF]L{i+1}:[/] {count:02} | {'█' * min(count, 20)}\n"
            else:
                display += "\n"
        display += f"\n[b][#FF00FF]TOTAL_SYL:[/] {total}"
        self.update(display)

class VowelExtractor(Static):
    text_content = reactive("")
    def watch_text_content(self, text: str) -> None:
        lines = text.splitlines()
        display = "[b][#39C5BB]>>> PHONEME/VOWEL MAP <<<\n\n[/]"
        for i, line in enumerate(lines[-5:]):
            if line.strip():
                vowels = re.findall(r'[aeiouAEIOU]+', line)
                v_str = "-".join(vowels).lower()
                display += f"[#FF00FF]L{len(lines)-4+i}:[/] {v_str}\n"
        self.update(display)

class TuningMath(Static):
    bpm = reactive(120)
    def compose(self) -> ComposeResult:
        yield Label("[b][#39C5BB]>>> TUNING CALCULATOR <<<[/]")
        yield Horizontal(
            Label("BPM: "),
            Input("120", placeholder="BPM", id="bpm_input", classes="nano_input"),
            classes="input_row"
        )
        yield Label("", id="math_output")
    def on_input_changed(self, event: Input.Changed) -> None:
        try:
            val = int(event.value)
            if val > 0: self.bpm = val
        except ValueError: pass
    def watch_bpm(self, bpm: int) -> None:
        ms_per_beat = 60000 / bpm
        out = self.query_one("#math_output", Label)
        out.update(
            f"1/4 Note (Beat) : [b#00FFFF]{ms_per_beat:.1f} ms[/]\n"
            f"1/8 Note        : [b#00FFFF]{ms_per_beat/2:.1f} ms[/]\n"
            f"1/16 Note       : [b#00FFFF]{ms_per_beat/4:.1f} ms[/]\n"
            f"Vibrato (1/32)  : [b#00FFFF]{ms_per_beat/8:.1f} ms[/]"
        )

class RhymeTerminal(Static):
    def compose(self) -> ComposeResult:
        yield Label("[b][#39C5BB]>>> NEURAL RHYME ENGINE <<<[/]")
        yield Horizontal(
            Input(placeholder="Enter target word...", id="rhyme_input"),
            Button("EXECUTE", id="rhyme_btn", variant="primary"),
            classes="input_row"
        )
        yield VerticalScroll(Label("IDLE: Waiting for input...", id="rhyme_results"), id="rhyme_scroll")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "rhyme_btn":
            self.trigger_search()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "rhyme_input":
            self.trigger_search()

    def trigger_search(self) -> None:
        word = self.query_one("#rhyme_input", Input).value.strip()
        if not word:
            self.update_results("[#FFB000]WARNING: INPUT BUFFER EMPTY.[/]")
            return
        btn = self.query_one("#rhyme_btn", Button)
        btn.disabled = True
        btn.label = "SCANNING..."
        self.fetch_rhymes(word)

    @work(exclusive=True, thread=True)
    def fetch_rhymes(self, word: str) -> None:
        try:
            self.app.call_from_thread(self.update_results, f"[blink][#39C5BB]ACCESSING DATABANKS FOR '{word.upper()}'...[/]")
            url = f"https://api.datamuse.com/words?rel_rhy={word.lower().strip()}"
            response = requests.get(url, headers={'User-Agent': 'MelRoms-VocaLink/3.0'}, timeout=10, verify=certifi.where())
            data = response.json()
            if not data:
                self.app.call_from_thread(self.update_results, "[#FF0000]SYSTEM ERROR: NO RHYME MATCHES FOUND.[/]")
            else:
                syl_map = {}
                for item in data[:50]:
                    s = item.get('numSyllables', 0)
                    syl_map.setdefault(s, []).append(item['word'])
                res_lines = []
                for s in sorted(syl_map.keys()):
                    words = ", ".join(syl_map[s][:6])
                    res_lines.append(f"[#00FFFF][ {s} SYL ][/] {words}")
                self.app.call_from_thread(self.update_results, "\n".join(res_lines))
        except Exception as e:
            self.app.call_from_thread(self.update_results, f"[#FF0000]LINK FAILURE: {str(e).upper()}[/]")
        finally:
            btn = self.query_one("#rhyme_btn", Button)
            self.app.call_from_thread(self._reset_button, btn)

    def _reset_button(self, btn: Button) -> None:
        btn.disabled = False
        btn.label = "EXECUTE"

    def update_results(self, text: str) -> None:
        label = self.query_one("#rhyme_results", Label)
        label.update(text)

class AIGenerator(Static):
    def compose(self) -> ComposeResult:
        yield Label("[b][#39C5BB]>>> MIKU_GHOST_PROTOCOL <<<[/]")
        yield Button("GENERATE_FRAGMENT", id="gen_btn", variant="error")
        yield Label("", id="ai_output")
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "gen_btn":
            part1 = random.choice(CYBER_CORPUS).split()[:3]
            part2 = random.choice(CYBER_CORPUS).split()[-3:]
            fragment = " ".join(part1 + part2)
            self.query_one("#ai_output", Label).update(f"[i][#00FFFF]\"...{fragment}...\"[/]")

class TuningConsole(Static):
    def compose(self) -> ComposeResult:
        yield Label("[b][#39C5BB]>>> VOCAL TUNING CONSOLE <<<[/]")
        with Grid(id="tuning_grid"):
            yield Label("Speed (Rate, 50-400):")
            yield Horizontal(
                Input("220", id="rate_input", classes="tiny_input"),
                Button("-", id="rate_down", variant="default"),
                Button("+", id="rate_up", variant="default"),
                classes="button_group"
            )
            yield Label("Volume (0-100):")
            yield Horizontal(
                Input("90", id="vol_input", classes="tiny_input"),
                Button("-", id="vol_down", variant="default"),
                Button("+", id="vol_up", variant="default"),
                classes="button_group"
            )
            yield Label("Voice:")
            yield Select([], id="voice_select")
            yield Checkbox("Spell Mode", id="spell_mode")
            yield Checkbox("Sustained Vowels", id="sustain_vowels", value=True)
            yield Label("Phoneme Map (WORD:sound):")
            yield TextArea("MIKU:mee koo\nLOVE:luhv", id="phoneme_map", classes="phoneme_editor")
            yield Button("PREVIEW SETTINGS", id="preview_btn", variant="primary")
        yield Label("", id="preview_status")

    def on_mount(self) -> None:
        if TTS_AVAILABLE:
            try:
                engine = pyttsx3.init()
                voices = engine.getProperty('voices')
                options = [(v.name, v.id) for v in voices]
                self.query_one("#voice_select", Select).set_options(options)
                if options: self.query_one("#voice_select", Select).value = options[0][1]
            except Exception: pass

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "preview_btn": self.preview()
        elif btn_id == "rate_up": self.adjust_rate(10)
        elif btn_id == "rate_down": self.adjust_rate(-10)
        elif btn_id == "vol_up": self.adjust_volume(5)
        elif btn_id == "vol_down": self.adjust_volume(-5)

    def adjust_rate(self, delta: int) -> None:
        inp = self.query_one("#rate_input", Input)
        try:
            val = int(inp.value) + delta
            inp.value = str(max(50, min(400, val)))
        except ValueError: inp.value = "220"

    def adjust_volume(self, delta: int) -> None:
        inp = self.query_one("#vol_input", Input)
        try:
            val = int(inp.value) + delta
            inp.value = str(max(0, min(100, val)))
        except ValueError: inp.value = "90"

    def preview(self) -> None:
        sample = "MIKU is love. AAAAAA EEEEE."
        status = self.query_one("#preview_status", Label)
        status.update("[cyan]🔊 Previewing...[/]")
        threading.Thread(target=self._speak_with_tuning, args=(sample, status), daemon=True).start()

    def _speak_with_tuning(self, text: str, status_label: Label) -> None:
        try:
            engine = pyttsx3.init()
            tuning = self.get_tuning_params()
            engine.setProperty('rate', tuning['rate'])
            engine.setProperty('volume', tuning['volume'])
            if tuning['voice']: engine.setProperty('voice', tuning['voice'])
            processed = self.process_text(text)
            engine.say(processed)
            engine.runAndWait()
            self.app.call_from_thread(lambda: status_label.update("[green]✔ Preview done[/]"))
        except Exception as e:
            self.app.call_from_thread(lambda: status_label.update(f"[red]Error: {e}[/]"))

    def process_text(self, text: str) -> str:
        # Phoneme Map
        phoneme_text = self.query_one("#phoneme_map", TextArea).text
        for line in phoneme_text.splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                text = re.sub(re.escape(k.strip()), v.strip(), text, flags=re.IGNORECASE)

        # Spell Mode check
        if self.query_one("#spell_mode", Checkbox).value:
            text = ' '.join(list(text.replace(" ", "")))

        # Sustain Vowels check
        if self.query_one("#sustain_vowels", Checkbox).value:
            def repl(m): return f"{m.group(0)[0] * 5}"
            text = re.sub(r'([aeiou])\1{1,}', repl, text, flags=re.IGNORECASE)
        
        return text

    def get_tuning_params(self):
        return {
            'rate': int(self.query_one("#rate_input", Input).value),
            'volume': int(self.query_one("#vol_input", Input).value) / 100.0,
            'voice': self.query_one("#voice_select", Select).value,
            'spell_mode': self.query_one("#spell_mode", Checkbox).value,
            'sustain_vowels': self.query_one("#sustain_vowels", Checkbox).value
        }

# ----------------------------------------------------------------------
# MAIN APP
# ----------------------------------------------------------------------
class VocaLinkApp(App):
    CSS = """
    Screen { background: #050505; color: #E0E0E0; }
    Header { background: #111111; color: #39C5BB; text-style: bold; }
    Footer { background: #111111; color: #00FFFF; }
    
    #main-viewport { width: 100%; height: 100%; min-width: 140; min-height: 70; }
    .panel { border: solid #333333; background: #0a0a0a; padding: 1; }
    .panel:focus-within { border: double #39C5BB; }
    
    #left_col { width: 55%; height: 100%; min-width: 70; }
    #right_col { width: 45%; height: 100%; min-width: 60; border-left: solid #39C5BB; }
    
    TextArea { height: 1fr; border: none; background: #050505; color: #FFB000; }
    #syl_tracker { height: 20%; border-bottom: dashed #333; }
    #vowel_tracker { height: 15%; border-bottom: dashed #333; }
    #tuning_math { height: 15%; border-bottom: dashed #333; }
    #ai_gen { height: 10%; border-bottom: dashed #333; }
    #rhyme_engine { height: 20%; border-bottom: dashed #333; }
    #tuning_console { height: auto; min-height: 50; }
    
    .input_row { height: 3; margin-bottom: 1; }
    Input { width: 1fr; border: none; background: #1a1a1a; }
    #tuning_grid { grid-size: 2; grid-gutter: 1; margin: 1; height: auto; }
    #speak_status { color: #39C5BB; margin-top: 1; height: 1; }
    .tiny_input { width: 8; }
    .nano_input { width: 10; }
    """

    BINDINGS = [
        ("ctrl+s", "save_lyrics", "Save"),
        ("ctrl+q", "quit", "Exit"),
        ("ctrl+space", "speak_current_line", "Sing")
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with ScrollableContainer(id="main-viewport"):
            with Horizontal():
                with Container(id="left_col", classes="panel"):
                    yield TextArea(
                        "// PROJECT: MelRoms\n// VOCAL: HATSUNE MIKU\n\nDigital love transmitting through the wire...\n",
                        id="editor", language="markdown"
                    )
                    yield Button("SING CURRENT LINE (CTRL+SPACE)", id="speak_btn", variant="success")
                    yield Label("", id="speak_status")
                with Container(id="right_col", classes="panel"):
                    yield SyllableTracker(id="syl_tracker")
                    yield VowelExtractor(id="vowel_tracker")
                    yield TuningMath(id="tuning_math")
                    yield AIGenerator(id="ai_gen")
                    yield RhymeTerminal(id="rhyme_engine")
                    yield TuningConsole(id="tuning_console")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "TERMINAL_LINK v4.0 | VOCA-LINK ENGINE"
        editor = self.query_one("#editor", TextArea)
        self.query_one("#syl_tracker", SyllableTracker).text_content = editor.text
        self.query_one("#vowel_tracker", VowelExtractor).text_content = editor.text

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        self.query_one("#syl_tracker", SyllableTracker).text_content = event.text_area.text
        self.query_one("#vowel_tracker", VowelExtractor).text_content = event.text_area.text

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "speak_btn":
            self.action_speak_current_line()

    def action_speak_current_line(self) -> None:
        if not TTS_AVAILABLE: return
        editor = self.query_one("#editor", TextArea)
        lines = editor.text.splitlines()
        row, _ = editor.cursor_location
        if row < len(lines):
            text = lines[row].strip()
            if text:
                status = self.query_one("#speak_status", Label)
                status.update("[cyan]🔊 SINGING...[/]")
                threading.Thread(target=self._speak_logic, args=(text,), daemon=True).start()

    def _speak_logic(self, text: str) -> None:
        try:
            engine = pyttsx3.init()
            tuning_panel = self.query_one("#tuning_console", TuningConsole)
            params = tuning_panel.get_tuning_params()
            engine.setProperty('rate', params['rate'])
            engine.setProperty('volume', params['volume'])
            if params['voice']: engine.setProperty('voice', params['voice'])
            
            processed = tuning_panel.process_text(text)
            engine.say(processed)
            engine.runAndWait()
            self.app.call_from_thread(lambda: self.query_one("#speak_status", Label).update("[green]✔ Done[/]"))
        except Exception as e:
            self.app.call_from_thread(lambda: self.query_one("#speak_status", Label).update(f"[red]Error: {e}[/]"))

    def action_save_lyrics(self) -> None:
        text = self.query_one("#editor", TextArea).text
        with open("melroms_lyrics_export.txt", "w", encoding="utf-8") as f:
            f.write(text)
        self.notify("DATA STREAM SAVED.")

if __name__ == "__main__":
    VocaLinkApp().run()