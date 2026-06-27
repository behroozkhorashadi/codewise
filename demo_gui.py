"""
CodeWise Demo GUI — interactive pipeline demo for master's presentation.
Run with: python demo_gui.py
"""

import os
import sys
from typing import Dict, Optional

from dotenv import load_dotenv
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSplitter,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

load_dotenv()

# ── Example code snippets ──────────────────────────────────────────────────────

EXAMPLES = {
    "Example 1 — Poor naming & no error handling": """\
def calc(x, y, z):
    r = x + y
    if r > z:
        f = r - z
    else:
        f = 0
    return f / z * 100
""",
    "Example 2 — God function with magic numbers": """\
def process(data):
    result = []
    for i in range(len(data)):
        if data[i] > 100:
            data[i] = 100
        if data[i] < 0:
            data[i] = 0
        result.append(data[i] * 1.5 + 10)
    total = 0
    for x in result:
        total = total + x
    avg = total / len(result)
    print("Average:", avg)
    print("Count:", len(result))
    return result
""",
    "Example 3 — O(n²) duplicate finder": """\
def find_dupes(lst):
    dupes = []
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            if lst[i] == lst[j]:
                if lst[i] not in dupes:
                    dupes.append(lst[i])
    return dupes
""",
    "Example 4 — Mixed concerns, no resource mgmt": """\
def parse_and_save(filename):
    f = open(filename)
    lines = f.readlines()
    f.close()
    data = []
    for l in lines:
        parts = l.split(",")
        if len(parts) >= 2:
            name = parts[0]
            val = int(parts[1])
            data.append({"name": name, "value": val})
    import json
    out = open("output.json", "w")
    json.dump(data, out)
    out.close()
    total = 0
    for d in data:
        total += d["value"]
    print(total / len(data))
""",
}

# (display label, JSON key in critique/recritique responses)
DIMENSIONS = [
    ("Separation of Concerns", "separation_of_concerns"),
    ("Documentation", "documentation"),
    ("Logic Clarity", "logic_clarity"),
    ("Understandability", "understandability"),
    ("Efficiency", "efficiency"),
    ("Error Handling", "error_handling"),
    ("Testability", "testability"),
    ("Reusability", "reusability"),
    ("Code Consistency", "code_consistency"),
    ("Dependency Management", "dependency_management"),
    ("Security Awareness", "security_awareness"),
    ("Side Effects", "side_effects"),
    ("Scalability", "scalability"),
    ("Resource Management", "resource_management"),
    ("Encapsulation", "encapsulation"),
    ("Complex Logic Readability", "complex_logic_readability"),
]


def score_color(score: float) -> str:
    if score >= 8:
        return "#a6e3a1"
    elif score >= 6:
        return "#fab387"
    else:
        return "#f38ba8"


def mono_font(size: int = 12) -> QFont:
    font = QFont("Menlo", size)
    font.setStyleHint(QFont.Monospace)
    return font


# ── Worker thread ──────────────────────────────────────────────────────────────


class PipelineWorker(QThread):
    phase_started = Signal(str)
    critique_ready = Signal(dict)
    improve_ready = Signal(dict)
    recritique_ready = Signal(dict)
    error_occurred = Signal(str, str)
    all_done = Signal()

    def __init__(self, code: str, model_choice: str):
        super().__init__()
        self.code = code
        self.model_choice = model_choice

    def run(self):
        try:
            model = self._build_model()
        except Exception as exc:
            self.error_occurred.emit("init", str(exc))
            self.all_done.emit()
            return

        self.phase_started.emit("critique")
        try:
            critique = model.critique(self.code)
        except Exception as exc:
            self.error_occurred.emit("critique", str(exc))
            self.all_done.emit()
            return
        self.critique_ready.emit(critique)

        self.phase_started.emit("improve")
        try:
            improve = model.improve(self.code, critique)
        except Exception as exc:
            self.error_occurred.emit("improve", str(exc))
            self.all_done.emit()
            return
        self.improve_ready.emit(improve)

        improved_code = improve.get("refactored_code", self.code)

        self.phase_started.emit("recritique")
        try:
            recritique = model.recritique(self.code, improved_code, critique)
        except Exception as exc:
            self.error_occurred.emit("recritique", str(exc))
            self.all_done.emit()
            return
        self.recritique_ready.emit(recritique)

        self.all_done.emit()

    def _build_model(self):
        from source.pipeline.model_api import ClaudeReviewer, GPT4Reviewer

        if self.model_choice == "Claude 3.5 Sonnet":
            key = os.environ.get("ANTHROPIC_API_KEY", "")
            if not key:
                raise RuntimeError("ANTHROPIC_API_KEY not set in .env")
            return ClaudeReviewer(api_key=key)
        else:
            key = os.environ.get("OPENAI_API_KEY", "")
            if not key:
                raise RuntimeError("OPENAI_API_KEY not set in .env")
            return GPT4Reviewer(api_key=key)


# ── Reusable sub-widgets ───────────────────────────────────────────────────────


class ScoreBar(QWidget):
    """Dimension label + colored progress bar + numeric score."""

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 1, 0, 1)
        layout.setSpacing(8)

        self._name = QLabel(label)
        self._name.setFixedWidth(200)
        self._name.setStyleSheet("color: #cdd6f4; font-size: 12px;")

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(14)

        self._value = QLabel("—")
        self._value.setFixedWidth(36)
        self._value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._value.setStyleSheet("font-size: 12px; font-weight: bold; color: #cdd6f4;")

        layout.addWidget(self._name)
        layout.addWidget(self._bar, 1)
        layout.addWidget(self._value)

    def set_score(self, score: float):
        color = score_color(score)
        self._bar.setValue(int(score * 10))
        self._bar.setStyleSheet(
            f"""
            QProgressBar {{ background: #313244; border-radius: 3px; }}
            QProgressBar::chunk {{ background: {color}; border-radius: 3px; }}
        """
        )
        self._value.setText(f"{score:.1f}")
        self._value.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {color};")


class ComparisonRow(QWidget):
    """Before → after scores for one dimension."""

    def __init__(self, label: str, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 1, 0, 1)
        layout.setSpacing(6)

        self._name = QLabel(label)
        self._name.setFixedWidth(200)
        self._name.setStyleSheet("color: #cdd6f4; font-size: 12px;")

        self._before = QLabel("—")
        self._before.setFixedWidth(30)
        self._before.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._before.setStyleSheet("font-size: 12px; font-weight: bold;")

        arrow = QLabel("→")
        arrow.setFixedWidth(18)
        arrow.setAlignment(Qt.AlignCenter)
        arrow.setStyleSheet("color: #6c7086; font-size: 12px;")

        self._after = QLabel("—")
        self._after.setFixedWidth(30)
        self._after.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._after.setStyleSheet("font-size: 12px; font-weight: bold;")

        self._delta = QLabel("")
        self._delta.setFixedWidth(42)
        self._delta.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._delta.setStyleSheet("font-size: 11px; font-weight: bold;")

        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(12)

        layout.addWidget(self._name)
        layout.addWidget(self._before)
        layout.addWidget(arrow)
        layout.addWidget(self._after)
        layout.addWidget(self._delta)
        layout.addWidget(self._bar, 1)

    def set_scores(self, before: float, after: float):
        bc = score_color(before)
        ac = score_color(after)
        self._before.setText(f"{before:.1f}")
        self._before.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {bc};")
        self._after.setText(f"{after:.1f}")
        self._after.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {ac};")

        diff = after - before
        sign = "+" if diff >= 0 else ""
        dc = "#a6e3a1" if diff > 0 else ("#f38ba8" if diff < 0 else "#6c7086")
        self._delta.setText(f"{sign}{diff:.1f}")
        self._delta.setStyleSheet(f"font-size: 11px; font-weight: bold; color: {dc};")

        self._bar.setValue(int(after * 10))
        self._bar.setStyleSheet(
            f"""
            QProgressBar {{ background: #313244; border-radius: 3px; }}
            QProgressBar::chunk {{ background: {ac}; border-radius: 3px; }}
        """
        )


# ── Main window ────────────────────────────────────────────────────────────────


class DemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CodeWise — AI Code Quality Analysis Pipeline")
        self.resize(1440, 880)
        self._worker: Optional[PipelineWorker] = None
        self._critique_data: Optional[dict] = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._make_left_panel())
        splitter.addWidget(self._make_right_panel())
        splitter.setSizes([440, 1000])
        splitter.setHandleWidth(1)
        root.addWidget(splitter)

        self._load_example(list(EXAMPLES.keys())[0])

    # ── Left panel ─────────────────────────────────────────────────────────────

    def _make_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: #1e1e2e;")
        panel.setMinimumWidth(380)
        panel.setMaximumWidth(480)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 24, 20, 20)
        layout.setSpacing(0)

        title = QLabel("CodeWise")
        title.setStyleSheet("color: #cdd6f4; font-size: 26px; font-weight: bold;")
        sub = QLabel("AI Code Quality Analysis Pipeline")
        sub.setStyleSheet("color: #a6adc8; font-size: 12px; margin-bottom: 16px;")
        layout.addWidget(title)
        layout.addWidget(sub)
        layout.addWidget(self._sep())

        # Example picker
        layout.addSpacing(12)
        layout.addWidget(self._field_label("Load example:"))
        self._example_combo = self._make_combo(list(EXAMPLES.keys()))
        self._example_combo.currentTextChanged.connect(self._load_example)
        layout.addWidget(self._example_combo)

        # Code editor
        layout.addSpacing(12)
        layout.addWidget(self._field_label("Python code:"))
        self._code_edit = QTextEdit()
        self._code_edit.setFont(mono_font(11))
        self._code_edit.setStyleSheet(
            """
            QTextEdit {
                background: #181825; color: #cdd6f4;
                border: 1px solid #313244; border-radius: 6px; padding: 8px;
            }
        """
        )
        self._code_edit.setMinimumHeight(260)
        layout.addWidget(self._code_edit)

        # Model selector
        layout.addSpacing(12)
        layout.addWidget(self._field_label("Model:"))
        self._model_combo = self._make_combo(["Claude 3.5 Sonnet", "GPT-4o"])
        layout.addWidget(self._model_combo)

        layout.addSpacing(16)
        layout.addWidget(self._sep())
        layout.addSpacing(12)

        # Run button
        self._run_btn = QPushButton("▶  Analyze Code")
        self._run_btn.setStyleSheet(
            """
            QPushButton {
                background: #a6e3a1; color: #1e1e2e;
                font-size: 14px; font-weight: bold;
                border-radius: 6px; padding: 11px;
                border: none;
            }
            QPushButton:hover { background: #94e2d5; }
            QPushButton:disabled { background: #45475a; color: #585b70; }
        """
        )
        self._run_btn.clicked.connect(self._start_pipeline)
        layout.addWidget(self._run_btn)

        layout.addSpacing(8)

        # Status + phase bar
        self._status_lbl = QLabel("Ready — select an example and click Analyze.")
        self._status_lbl.setStyleSheet("color: #6c7086; font-size: 11px;")
        self._status_lbl.setWordWrap(True)
        self._status_lbl.setAlignment(Qt.AlignCenter)

        self._phase_bar = QProgressBar()
        self._phase_bar.setRange(0, 3)
        self._phase_bar.setValue(0)
        self._phase_bar.setTextVisible(False)
        self._phase_bar.setFixedHeight(5)
        self._phase_bar.setStyleSheet(
            """
            QProgressBar { background: #313244; border-radius: 2px; }
            QProgressBar::chunk { background: #89b4fa; border-radius: 2px; }
        """
        )
        self._phase_bar.hide()

        layout.addWidget(self._status_lbl)
        layout.addWidget(self._phase_bar)

        layout.addStretch()

        # Pipeline legend
        legend = QFrame()
        legend.setStyleSheet("background: #181825; border-radius: 8px;")
        ll = QVBoxLayout(legend)
        ll.setContentsMargins(14, 12, 14, 12)
        ll.setSpacing(6)
        ll.addWidget(self._field_label("Pipeline stages"))
        for step, color in [
            ("① Critique     Score 16 quality dimensions", "#f38ba8"),
            ("② Improve      LLM rewrites the code", "#fab387"),
            ("③ Re-critique  Score the improved version", "#a6e3a1"),
        ]:
            lbl = QLabel(step)
            lbl.setStyleSheet(f"color: {color}; font-size: 11px; font-family: monospace;")
            ll.addWidget(lbl)
        layout.addWidget(legend)

        return panel

    # ── Right panel ────────────────────────────────────────────────────────────

    def _make_right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: #181825;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(
            """
            QTabWidget::pane { border: none; background: #181825; }
            QTabBar::tab {
                background: #1e1e2e; color: #585b70;
                padding: 10px 28px; font-size: 13px;
                border-bottom: 2px solid transparent;
            }
            QTabBar::tab:selected { color: #cdd6f4; border-bottom: 2px solid #89b4fa; }
            QTabBar::tab:hover { color: #a6adc8; }
        """
        )
        self._tabs.addTab(self._make_critique_tab(), "① Critique")
        self._tabs.addTab(self._make_improve_tab(), "② Improved Code")
        self._tabs.addTab(self._make_recritique_tab(), "③ Re-critique")
        layout.addWidget(self._tabs)

        return panel

    # ── Critique tab ───────────────────────────────────────────────────────────

    def _make_critique_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: #181825;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Hero row: overall score + summary
        hero = QHBoxLayout()
        hero.setSpacing(14)

        score_card = QFrame()
        score_card.setFixedWidth(160)
        score_card.setStyleSheet("background: #1e1e2e; border-radius: 10px;")
        sc_layout = QVBoxLayout(score_card)
        sc_layout.setAlignment(Qt.AlignCenter)
        sc_layout.setContentsMargins(16, 20, 16, 20)
        lbl_overall = QLabel("Overall Score")
        lbl_overall.setStyleSheet("color: #a6adc8; font-size: 11px;")
        lbl_overall.setAlignment(Qt.AlignCenter)
        self._overall_score = QLabel("—")
        self._overall_score.setStyleSheet("color: #cdd6f4; font-size: 44px; font-weight: bold;")
        self._overall_score.setAlignment(Qt.AlignCenter)
        lbl_outof = QLabel("out of 10")
        lbl_outof.setStyleSheet("color: #585b70; font-size: 11px;")
        lbl_outof.setAlignment(Qt.AlignCenter)
        sc_layout.addWidget(lbl_overall)
        sc_layout.addWidget(self._overall_score)
        sc_layout.addWidget(lbl_outof)
        hero.addWidget(score_card)

        summary_card = QFrame()
        summary_card.setStyleSheet("background: #1e1e2e; border-radius: 10px;")
        sm_layout = QVBoxLayout(summary_card)
        sm_layout.setContentsMargins(16, 14, 16, 14)
        sm_layout.setSpacing(8)
        lbl_assessment = QLabel("Assessment")
        lbl_assessment.setStyleSheet("color: #a6adc8; font-size: 11px; font-weight: bold;")
        self._critique_summary = QLabel("Run the pipeline to see results.")
        self._critique_summary.setStyleSheet("color: #cdd6f4; font-size: 12px;")
        self._critique_summary.setWordWrap(True)
        self._critique_priority = QLabel("")
        self._critique_priority.setStyleSheet("color: #f38ba8; font-size: 11px;")
        self._critique_priority.setWordWrap(True)
        sm_layout.addWidget(lbl_assessment)
        sm_layout.addWidget(self._critique_summary)
        sm_layout.addWidget(self._critique_priority)
        sm_layout.addStretch()
        hero.addWidget(summary_card, 1)
        layout.addLayout(hero)

        # Dimension bars
        lbl_dims = QLabel("Quality Dimensions")
        lbl_dims.setStyleSheet("color: #a6adc8; font-size: 12px; font-weight: bold;")
        layout.addWidget(lbl_dims)

        scroll = self._scrollable()
        dims_container = QWidget()
        dims_container.setStyleSheet("background: transparent;")
        dims_layout = QVBoxLayout(dims_container)
        dims_layout.setContentsMargins(0, 0, 0, 0)
        dims_layout.setSpacing(2)

        self._score_bars: Dict[str, ScoreBar] = {}
        for label, key in DIMENSIONS:
            bar = ScoreBar(label)
            bar.setStyleSheet("background: transparent;")
            dims_layout.addWidget(bar)
            self._score_bars[key] = bar

        scroll.setWidget(dims_container)
        layout.addWidget(scroll)

        return w

    # ── Improve tab ────────────────────────────────────────────────────────────

    def _make_improve_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: #181825;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        self._improve_summary = QLabel("Waiting for pipeline to run...")
        self._improve_summary.setStyleSheet("color: #fab387; font-size: 13px; font-weight: bold;")
        layout.addWidget(self._improve_summary)

        # Side-by-side code panes
        code_split = QSplitter(Qt.Horizontal)
        code_split.setHandleWidth(4)
        code_split.setStyleSheet("QSplitter::handle { background: #313244; }")

        orig_panel = QWidget()
        orig_layout = QVBoxLayout(orig_panel)
        orig_layout.setContentsMargins(0, 0, 0, 0)
        orig_layout.setSpacing(4)
        orig_title = QLabel("Original Code")
        orig_title.setStyleSheet("color: #f38ba8; font-size: 12px; font-weight: bold;")
        self._orig_code = QTextEdit()
        self._orig_code.setReadOnly(True)
        self._orig_code.setFont(mono_font(11))
        self._orig_code.setStyleSheet(self._code_pane_style())
        orig_layout.addWidget(orig_title)
        orig_layout.addWidget(self._orig_code)
        code_split.addWidget(orig_panel)

        impr_panel = QWidget()
        impr_layout = QVBoxLayout(impr_panel)
        impr_layout.setContentsMargins(0, 0, 0, 0)
        impr_layout.setSpacing(4)
        impr_title = QLabel("Improved Code")
        impr_title.setStyleSheet("color: #a6e3a1; font-size: 12px; font-weight: bold;")
        self._impr_code = QTextEdit()
        self._impr_code.setReadOnly(True)
        self._impr_code.setFont(mono_font(11))
        self._impr_code.setStyleSheet(self._code_pane_style())
        impr_layout.addWidget(impr_title)
        impr_layout.addWidget(self._impr_code)
        code_split.addWidget(impr_panel)

        layout.addWidget(code_split, 1)

        lbl_changes = QLabel("Changes Made")
        lbl_changes.setStyleSheet("color: #a6adc8; font-size: 12px; font-weight: bold;")
        layout.addWidget(lbl_changes)

        self._changes_text = QTextEdit()
        self._changes_text.setReadOnly(True)
        self._changes_text.setMaximumHeight(130)
        self._changes_text.setStyleSheet(self._code_pane_style())
        layout.addWidget(self._changes_text)

        return w

    # ── Re-critique tab ────────────────────────────────────────────────────────

    def _make_recritique_tab(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet("background: #181825;")
        layout = QVBoxLayout(w)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Hero: Before / After / Δ
        hero = QHBoxLayout()
        hero.setSpacing(12)
        self._before_lbl = self._score_hero_card("Before", "#f38ba8")
        self._after_lbl = self._score_hero_card("After", "#a6e3a1")
        self._delta_lbl = self._score_hero_card("Improvement", "#89b4fa")
        for card, _ in [self._before_lbl, self._after_lbl, self._delta_lbl]:
            hero.addWidget(card)
        layout.addLayout(hero)

        lbl_comp = QLabel("Dimension Comparison  (before → after)")
        lbl_comp.setStyleSheet("color: #a6adc8; font-size: 12px; font-weight: bold;")
        layout.addWidget(lbl_comp)

        scroll = self._scrollable()
        comp_container = QWidget()
        comp_container.setStyleSheet("background: transparent;")
        comp_layout = QVBoxLayout(comp_container)
        comp_layout.setContentsMargins(0, 0, 0, 0)
        comp_layout.setSpacing(2)

        self._comp_rows: Dict[str, ComparisonRow] = {}
        for label, key in DIMENSIONS:
            row = ComparisonRow(label)
            row.setStyleSheet("background: transparent;")
            comp_layout.addWidget(row)
            self._comp_rows[key] = row

        scroll.setWidget(comp_container)
        layout.addWidget(scroll, 1)

        self._recritique_assessment = QTextEdit()
        self._recritique_assessment.setReadOnly(True)
        self._recritique_assessment.setMaximumHeight(100)
        self._recritique_assessment.setStyleSheet(self._code_pane_style())
        layout.addWidget(self._recritique_assessment)

        return w

    # ── Pipeline control ───────────────────────────────────────────────────────

    def _start_pipeline(self):
        code = self._code_edit.toPlainText().strip()
        if not code:
            return

        self._run_btn.setEnabled(False)
        self._run_btn.setText("Running pipeline...")
        self._phase_bar.setValue(0)
        self._phase_bar.show()
        self._status("Initializing...", "#a6adc8")
        self._tabs.setCurrentIndex(0)

        self._worker = PipelineWorker(code, self._model_combo.currentText())
        self._worker.phase_started.connect(self._on_phase_started)
        self._worker.critique_ready.connect(self._on_critique)
        self._worker.improve_ready.connect(self._on_improve)
        self._worker.recritique_ready.connect(self._on_recritique)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.all_done.connect(self._on_done)
        self._worker.start()

    def _on_phase_started(self, phase: str):
        msgs = {
            "critique": "Phase 1 / 3 — Analyzing code quality...",
            "improve": "Phase 2 / 3 — Generating improved version...",
            "recritique": "Phase 3 / 3 — Scoring the improved code...",
        }
        self._status(msgs.get(phase, phase), "#a6adc8")

    def _on_critique(self, data: dict):
        self._critique_data = data
        self._phase_bar.setValue(1)
        self._tabs.setCurrentIndex(0)

        overall = float(data.get("overall_score", 0))
        color = score_color(overall)
        self._overall_score.setText(f"{overall:.1f}")
        self._overall_score.setStyleSheet(f"color: {color}; font-size: 44px; font-weight: bold;")

        fb = data.get("feedback", {})
        self._critique_summary.setText(fb.get("general_comments", ""))
        priorities = fb.get("priority_improvements", [])
        if priorities:
            self._critique_priority.setText(
                "Priority: " + " · ".join(f"({i+1}) {p}" for i, p in enumerate(priorities[:3]))
            )

        scores = data.get("scores", {})
        for _, key in DIMENSIONS:
            self._score_bars[key].set_score(float(scores.get(key, 0)))

        self._orig_code.setPlainText(self._code_edit.toPlainText())

    def _on_improve(self, data: dict):
        self._phase_bar.setValue(2)
        self._tabs.setCurrentIndex(1)

        self._impr_code.setPlainText(data.get("refactored_code", "# No code returned"))

        changes = data.get("changes_made", {})
        summary = changes.get("summary", "")
        self._improve_summary.setText(f"✓ {summary}" if summary else "✓ Code improved")

        lines = []
        for item in changes.get("detailed_changes", []):
            dim = item.get("dimension", "")
            fix = item.get("how_fixed", "")
            if dim and fix:
                lines.append(f"• [{dim}] {fix}")
        self._changes_text.setPlainText("\n".join(lines))

    def _on_recritique(self, data: dict):
        self._phase_bar.setValue(3)
        self._tabs.setCurrentIndex(2)

        new_block = data.get("improved_code_scores", {})
        new_overall = float(new_block.get("overall_score", 0))
        new_scores = new_block.get("scores", {})

        old_overall = float(self._critique_data.get("overall_score", 0)) if self._critique_data else 0.0
        old_scores = self._critique_data.get("scores", {}) if self._critique_data else {}

        _, before_val_lbl = self._before_lbl
        _, after_val_lbl = self._after_lbl
        _, delta_val_lbl = self._delta_lbl

        before_val_lbl.setText(f"{old_overall:.1f}")
        after_val_lbl.setText(f"{new_overall:.1f}")

        diff = new_overall - old_overall
        delta_val_lbl.setText(f"+{diff:.1f}" if diff >= 0 else f"{diff:.1f}")
        delta_color = "#a6e3a1" if diff >= 0 else "#f38ba8"
        delta_val_lbl.setStyleSheet(f"color: {delta_color}; font-size: 38px; font-weight: bold;")

        for _, key in DIMENSIONS:
            old_s = float(old_scores.get(key, 0))
            new_s = float(new_scores.get(key, 0))
            self._comp_rows[key].set_scores(old_s, new_s)

        fb = data.get("feedback", {})
        parts = []
        assessment = fb.get("overall_assessment", "")
        if assessment:
            parts.append(assessment)
        validated = fb.get("improvements_validated", [])
        if validated:
            parts.append("\nValidated: " + "; ".join(validated[:3]))
        remaining = fb.get("remaining_issues", [])
        if remaining:
            parts.append("Remaining: " + "; ".join(remaining[:2]))
        self._recritique_assessment.setPlainText("\n".join(parts))

    def _on_error(self, phase: str, msg: str):
        self._status(f"Error in {phase}: {msg}", "#f38ba8")

    def _on_done(self):
        self._run_btn.setEnabled(True)
        self._run_btn.setText("▶  Analyze Code")
        if "Error" not in self._status_lbl.text():
            self._status("✓ Pipeline complete", "#a6e3a1")

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _load_example(self, name: str):
        self._code_edit.setPlainText(EXAMPLES.get(name, ""))

    def _status(self, text: str, color: str = "#6c7086"):
        self._status_lbl.setText(text)
        self._status_lbl.setStyleSheet(f"color: {color}; font-size: 11px;")

    def _sep(self) -> QFrame:
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #313244; border: none;")
        return sep

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("color: #a6adc8; font-size: 11px; font-weight: bold; margin-bottom: 3px;")
        return lbl

    def _make_combo(self, items: list) -> QComboBox:
        cb = QComboBox()
        cb.addItems(items)
        cb.setStyleSheet(
            """
            QComboBox {
                background: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 4px;
                padding: 5px 10px; font-size: 12px;
            }
            QComboBox::drop-down { border: none; width: 20px; }
            QComboBox QAbstractItemView {
                background: #313244; color: #cdd6f4;
                selection-background-color: #45475a; border: none;
            }
        """
        )
        return cb

    def _scrollable(self) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        return scroll

    def _code_pane_style(self) -> str:
        return (
            "QTextEdit { background: #1e1e2e; color: #cdd6f4; "
            "border: 1px solid #313244; border-radius: 6px; padding: 8px; font-size: 12px; }"
        )

    def _score_hero_card(self, title: str, color: str):
        """Returns (card_widget, value_label) tuple."""
        card = QFrame()
        card.setStyleSheet("background: #1e1e2e; border-radius: 10px;")
        cl = QVBoxLayout(card)
        cl.setAlignment(Qt.AlignCenter)
        cl.setContentsMargins(20, 16, 20, 16)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color: #a6adc8; font-size: 11px;")
        title_lbl.setAlignment(Qt.AlignCenter)
        val_lbl = QLabel("—")
        val_lbl.setStyleSheet(f"color: {color}; font-size: 38px; font-weight: bold;")
        val_lbl.setAlignment(Qt.AlignCenter)
        cl.addWidget(title_lbl)
        cl.addWidget(val_lbl)
        return card, val_lbl


# ── Entry point ────────────────────────────────────────────────────────────────


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#181825"))
    palette.setColor(QPalette.WindowText, QColor("#cdd6f4"))
    palette.setColor(QPalette.Base, QColor("#1e1e2e"))
    palette.setColor(QPalette.AlternateBase, QColor("#313244"))
    palette.setColor(QPalette.Button, QColor("#313244"))
    palette.setColor(QPalette.ButtonText, QColor("#cdd6f4"))
    app.setPalette(palette)

    win = DemoWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
