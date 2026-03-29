import sys  # Moduł do obsługi systemu (argumenty, wyjście)
import os   # Moduł do operacji na plikach i ścieżkach
import sqlite3  # Obsługa bazy danych SQLite
import pandas as pd  # Biblioteka do analizy danych
from typing import List, Dict, Any, Optional, Tuple  # Podpowiedzi typów

from PyQt6.QtCore import Qt  # Podstawowe flagi i stałe Qt
from PyQt6.QtWidgets import (  # Komponenty interfejsu graficznego
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QTabWidget,
    QPlainTextEdit, QSpinBox, QComboBox, QCheckBox,
    QGroupBox, QFormLayout
)

# Matplotlib (wykresy)
try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas  # Płótno wykresu dla Qt
    from matplotlib.figure import Figure  # Obiekt figury Matplotlib
    import matplotlib.pyplot as plt  # Interfejs do rysowania
    MATPLOTLIB_OK = True  # Oznaczenie dostępności biblioteki
except Exception:
    MATPLOTLIB_OK = False  # Oznaczenie braku biblioteki

# PDF (eksport)
try:
    from fpdf import FPDF  # Biblioteka do tworzenia plików PDF
    PDF_OK = True  # Oznaczenie dostępności
except Exception:
    PDF_OK = False  # Oznaczenie braku

# Lista wymaganych kolumn w danych wejściowych
REQUIRED_COLUMNS = [
    "id", "gender", "age", "hypertension", "heart_disease",
    "ever_married", "work_type", "Residence_type",
    "avg_glucose_level", "bmi", "smoking_status", "stroke"
]

# Kolumny, które powinny zawierać wartości liczbowe
NUMERIC_COLUMNS = ["age", "avg_glucose_level", "bmi"]


class PlotWidget(QWidget):  # Klasa widżetu odpowiedzialna za rysowanie wykresów
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)  # Pionowy układ elementów

        if not MATPLOTLIB_OK:  # Sprawdzenie czy matplotlib jest zainstalowany
            layout.addWidget(QLabel("Matplotlib nie jest dostępny. Zainstaluj: pip install matplotlib"))
            self.canvas = None
            self.figure = None
            return

        self.figure = Figure(figsize=(6, 4))  # Tworzenie obiektu figury
        self.canvas = FigureCanvas(self.figure)  # Tworzenie płótna do wyświetlania figury
        layout.addWidget(self.canvas)  # Dodanie płótna do układu

    def clear(self):  # Metoda czyszcząca aktualny wykres
        if self.figure is None:
            return
        self.figure.clear()  # Czyszczenie figury
        if self.canvas:
            self.canvas.draw()  # Odświeżenie widoku

    def plot_histogram(self, values: List[float], title: str, xlabel: str):  # Rysowanie histogramu
        if self.figure is None:
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)  # Dodanie osi wykresu
        ax.hist(values, bins=25, color='skyblue', edgecolor='black')  # Generowanie histogramu
        ax.set_title(title)  # Tytuł wykresu
        ax.set_xlabel(xlabel)  # Opis osi X
        ax.set_ylabel("Liczba rekordów")  # Opis osi Y
        ax.grid(True, axis='y', linestyle='--', alpha=0.6)  # Siatka pomocnicza
        self.figure.tight_layout()  # Dopasowanie marginesów
        self.canvas.draw()  # Narysowanie na płótnie

    def plot_scatter(self, x: List[float], y: List[float], title: str, xlabel: str, ylabel: str):  # Wykres punktowy
        if self.figure is None:
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.scatter(x, y, s=15, alpha=0.5, color='royalblue')  # Generowanie punktów
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, linestyle='--', alpha=0.7)
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_boxplot(self, groups_data: Dict[str, List[float]], title: str, ylabel: str):  # Wykres pudełkowy
        if self.figure is None:
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        labels = list(groups_data.keys())
        values = [groups_data[k] for k in labels]
        
        ax.boxplot(values, labels=labels)  # Generowanie wykresu pudełkowego dla grup
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.grid(True, axis='y', linestyle='--', alpha=0.7)
        self.figure.tight_layout()
        self.canvas.draw()

    def plot_bar(self, counts: Dict[str, int], title: str, xlabel: str, ylabel: str):
        """Rysuje wykres słupkowy (przydatny dla cech kategorycznych)."""
        if self.figure is None:
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        labels = list(counts.keys())
        values = list(counts.values())
        
        bars = ax.bar(labels, values, color='lightcoral', edgecolor='black', alpha=0.8)
        
        # Dodanie etykiet z wartościami nad słupkami
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 3,
                    f'{int(height)}', ha='center', va='bottom', fontweight='bold')

        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.grid(True, axis='y', linestyle='--', alpha=0.6)
        
        # Obrócenie etykiet jeśli jest ich dużo
        if len(labels) > 4:
            ax.tick_params(axis='x', rotation=45)
            
        self.figure.tight_layout()
        self.canvas.draw()


class MainWindow(QMainWindow):  # Główne okno aplikacji
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Analiza danych pacjentów (CSV/SQLite) – PyQt6 & Pandas")  # Tytuł okna
        self.resize(1100, 750)  # Rozmiar okna

        self.df_all: Optional[pd.DataFrame] = None  # Wszystkie wczytane dane
        self.df_filtered: Optional[pd.DataFrame] = None  # Dane po przefiltrowaniu

        # --- Główny layout ---
        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)

        # Górny pasek z przyciskami
        main_layout.addLayout(self._build_top_bar())

        # Zakładki
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Sekcja logów
        main_layout.addWidget(QLabel("Logi / komunikaty:"))
        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)  # Tylko do odczytu
        self.log_box.setMaximumHeight(140)
        main_layout.addWidget(self.log_box)

        # Inicjalizacja zakładek
        self._build_tabs()

        self.log("Gotowe. Wczytaj CSV lub połącz z SQLite.")

    # ---------------- UI ----------------
    def _build_top_bar(self) -> QHBoxLayout:  # Budowanie paska narzędzi
        layout = QHBoxLayout()

        self.btn_load_csv = QPushButton("Wczytaj CSV")
        self.btn_load_csv.clicked.connect(self.load_csv)  # Reakcja na kliknięcie

        self.btn_connect_sql = QPushButton("Połącz SQLite")
        self.btn_connect_sql.clicked.connect(self.load_sqlite)

        self.btn_apply_filters = QPushButton("Zastosuj filtry")
        self.btn_apply_filters.clicked.connect(self.apply_filters)

        self.btn_analyze = QPushButton("Analizuj")
        self.btn_analyze.clicked.connect(self.analyze_data)

        self.btn_plot = QPushButton("Wykresy")
        self.btn_plot.clicked.connect(self.show_plots)

        self.btn_export_csv = QPushButton("Eksport CSV")
        self.btn_export_csv.clicked.connect(self.export_csv)

        self.btn_export_pdf = QPushButton("Eksport PDF")
        self.btn_export_pdf.clicked.connect(self.export_pdf)

        # Dodawanie przycisków do układu
        layout.addWidget(self.btn_load_csv)
        layout.addWidget(self.btn_connect_sql)
        layout.addSpacing(12)
        layout.addWidget(self.btn_apply_filters)
        layout.addWidget(self.btn_analyze)
        layout.addWidget(self.btn_plot)
        layout.addSpacing(12)
        layout.addWidget(self.btn_export_csv)
        layout.addWidget(self.btn_export_pdf)
        layout.addStretch()  # Rozciągnięcie na końcu

        return layout

    def _build_tabs(self):  # Tworzenie zawartości zakładek
        # 1) Podgląd danych
        self.tab_preview = QWidget()
        v1 = QVBoxLayout(self.tab_preview)
        self.table = QTableWidget()  # Tabela danych
        v1.addWidget(self.table)
        self.tabs.addTab(self.tab_preview, "Podgląd danych")

        # 2) Filtry
        self.tab_filters = QWidget()
        v2 = QVBoxLayout(self.tab_filters)
        v2.addWidget(self._build_filters_panel())  # Dodanie panelu filtrów
        v2.addStretch()
        self.tabs.addTab(self.tab_filters, "Filtry")

        # 3) Statystyki
        self.tab_stats = QWidget()
        v3 = QVBoxLayout(self.tab_stats)
        
        # Opcje grupowania
        group_row = QHBoxLayout()
        self.cmb_group_by = QComboBox()
        self.cmb_group_by.addItems(["Brak", "gender", "hypertension", "heart_disease", "stroke"])
        btn_refresh_stats = QPushButton("Odśwież statystyki")
        btn_refresh_stats.clicked.connect(self.analyze_data)
        group_row.addWidget(QLabel("Grupuj według:"))
        group_row.addWidget(self.cmb_group_by)
        group_row.addWidget(btn_refresh_stats)
        group_row.addStretch()
        v3.addLayout(group_row)

        self.stats_box = QPlainTextEdit()
        self.stats_box.setReadOnly(True)
        v3.addWidget(self.stats_box)
        self.tabs.addTab(self.tab_stats, "Statystyki")

        # 4) Wykresy
        self.tab_plots = QWidget()
        v4 = QVBoxLayout(self.tab_plots)

        self.plot_widget = PlotWidget()
        v4.addWidget(self.plot_widget)

        # Kontrolki wyboru wykresu
        if MATPLOTLIB_OK:
            row = QHBoxLayout()
            self.cmb_plot_type = QComboBox()
            self.cmb_plot_type.addItems([
                "Histogram: wiek",
                "Histogram: avg_glucose_level",
                "Histogram: bmi",
                "Scatter: bmi vs avg_glucose_level",
                "Boxplot: wiek wg płci",
                "Boxplot: bmi wg stroke",
                "Boxplot: glucose wg hypertension",
                "--- Dowolna korelacja ---",
                "Korelacja: X vs Y"
            ])
            self.cmb_plot_type.currentIndexChanged.connect(self._toggle_axes_visibility)
            btn_draw = QPushButton("Rysuj")
            btn_draw.clicked.connect(self.show_plots)

            row.addWidget(QLabel("Typ wykresu:"))
            row.addWidget(self.cmb_plot_type)
            row.addWidget(btn_draw)
            row.addStretch()
            v4.addLayout(row)

            # Kontener dla wyboru osi (ukrywany/pokazywany)
            self.axes_container = QWidget()
            row_axes = QHBoxLayout(self.axes_container)
            row_axes.setContentsMargins(0, 0, 0, 0)
            self.cmb_col_x = QComboBox()
            self.cmb_col_y = QComboBox()
            row_axes.addWidget(QLabel("Oś X:"))
            row_axes.addWidget(self.cmb_col_x)
            row_axes.addWidget(QLabel("Oś Y:"))
            row_axes.addWidget(self.cmb_col_y)
            row_axes.addStretch()
            v4.addWidget(self.axes_container)
            self.axes_container.hide() # Domyślnie ukryte

        self.tabs.addTab(self.tab_plots, "Wizualizacja")

        # 5) Raport
        self.tab_report = QWidget()
        v5 = QVBoxLayout(self.tab_report)
        self.report_box = QPlainTextEdit()
        self.report_box.setReadOnly(True)
        v5.addWidget(self.report_box)
        self.tabs.addTab(self.tab_report, "Raport")

    def _build_filters_panel(self) -> QWidget:  # Budowanie interfejsu filtrów
        box = QGroupBox("Filtry (działają na dane po wczytaniu)")
        layout = QGridLayout(box)

        # Kontrolki wieku
        self.age_min = QSpinBox()
        self.age_min.setRange(0, 130)
        self.age_min.setValue(0)

        self.age_max = QSpinBox()
        self.age_max.setRange(0, 130)
        self.age_max.setValue(130)

        # Kontrolka płci
        self.gender = QComboBox()
        self.gender.addItems(["All", "Male", "Female", "Other"])

        # Kontrolki binarne
        self.chk_hyper = QCheckBox("Tylko hypertension = 1")
        self.chk_heart = QCheckBox("Tylko heart_disease = 1")
        self.chk_stroke = QCheckBox("Tylko stroke = 1")

        # Rozmieszczenie w siatce
        layout.addWidget(QLabel("Wiek min:"), 0, 0)
        layout.addWidget(self.age_min, 0, 1)
        layout.addWidget(QLabel("Wiek max:"), 0, 2)
        layout.addWidget(self.age_max, 0, 3)

        layout.addWidget(QLabel("Płeć:"), 1, 0)
        layout.addWidget(self.gender, 1, 1)

        layout.addWidget(self.chk_hyper, 2, 0, 1, 2)
        layout.addWidget(self.chk_heart, 2, 2, 1, 2)
        layout.addWidget(self.chk_stroke, 3, 0, 1, 2)

        btn_row = QHBoxLayout()
        btn_apply = QPushButton("Zastosuj filtry")
        btn_apply.clicked.connect(self.apply_filters)
        btn_reset = QPushButton("Reset filtrów")
        btn_reset.clicked.connect(self.reset_filters)
        btn_row.addWidget(btn_apply)
        btn_row.addWidget(btn_reset)
        btn_row.addStretch()

        layout.addLayout(btn_row, 4, 0, 1, 4)
        return box

    # ---------------- UI HELPERS ----------------
    def _format_val(self, col: str, val: Any) -> str:
        """Konwertuje techniczne wartości (np. 0/1) na czytelne etykiety."""
        if col == "stroke":
            return "Stroke" if str(val) == "1" else "No Stroke"
        if col == "hypertension":
            return "Hypertension" if str(val) == "1" else "No Hypertension"
        if col == "heart_disease":
            return "Heart Disease" if str(val) == "1" else "No Heart Disease"
        return str(val)

    def _toggle_axes_visibility(self):
        """Pokazuje lub ukrywa wybór osi X i Y w zależności od typu wykresu."""
        if hasattr(self, "axes_container"):
            is_custom = self.cmb_plot_type.currentText() == "Korelacja: X vs Y"
            self.axes_container.setVisible(is_custom)

    # ---------------- LOG ----------------
    def log(self, msg: str):  # Dodawanie wiadomości do pola logów
        self.log_box.appendPlainText(msg)

    def error(self, msg: str):  # Wyświetlanie błędu
        QMessageBox.critical(self, "Błąd", msg)
        self.log(f"ERROR: {msg}")

    def info(self, msg: str):  # Wyświetlanie informacji
        QMessageBox.information(self, "Informacja", msg)
        self.log(msg)

    # ---------------- DATA IO ----------------
    def load_csv(self):  # Wczytywanie pliku CSV
        path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz plik CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return

        try:
            df = pd.read_csv(path)  # Odczyt danych przez pandas
            self._process_and_load_df(df, f"Wczytano CSV: {path}")
        except Exception as e:
            self.error(f"Nie udało się wczytać CSV: {e}")

    def load_sqlite(self):  # Wczytywanie z bazy SQLite
        default_db = "healthcare.db" if os.path.exists("healthcare.db") else ""
        db_path, _ = QFileDialog.getOpenFileName(
            self, "Wybierz bazę SQLite (.db)", default_db, "SQLite DB (*.db *.sqlite *.sqlite3);;All Files (*)"
        )
        if not db_path:
            return

        try:
            conn = sqlite3.connect(db_path)
            # Pobranie nazw tabel
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cursor.fetchall()]
            
            if not tables:
                raise ValueError("Brak tabel w bazie danych.")
            
            table_name = "patients" if "patients" in tables else tables[0]
            df = pd.read_sql(f"SELECT * FROM {table_name}", conn)  # Pobranie tabeli do DataFrame
            conn.close()
            
            self._process_and_load_df(df, f"Połączono SQLite: {db_path} | tabela: {table_name}")
        except Exception as e:
            self.error(f"Nie udało się wczytać z SQLite: {e}")

    def _process_and_load_df(self, df: pd.DataFrame, log_msg: str):  # Walidacja i wstępne przetwarzanie
        # Sprawdzenie obecności wymaganych kolumn
        missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing:
            self.error(f"Brak wymaganych kolumn: {', '.join(missing)}")
            return

        # Konwersja na typy numeryczne
        for col in NUMERIC_COLUMNS:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Konwersja kolumn binarnych
        for col in ["hypertension", "heart_disease", "stroke"]:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

        self.df_all = df  # Zapisanie głównego zbioru
        self.df_filtered = df.copy()  # Kopia do filtrowania
        
        # Wypełnienie list wyboru kolumn dla wykresów korelacji
        if MATPLOTLIB_OK:
            cols = list(df.columns)
            self.cmb_col_x.clear()
            self.cmb_col_x.addItems(cols)
            self.cmb_col_y.clear()
            self.cmb_col_y.addItems(cols)
            # Domyślne ustawienie dla ciekawego porównania
            if "ever_married" in cols: self.cmb_col_x.setCurrentText("ever_married")
            if "stroke" in cols: self.cmb_col_y.setCurrentText("stroke")

        self.populate_table(self.df_filtered)  # Wypełnienie tabeli GUI
        self.log(f"{log_msg} | rekordów: {len(df)}")
        self.tabs.setCurrentWidget(self.tab_preview)

    # ---------------- TABLE ----------------
    def populate_table(self, df: pd.DataFrame):  # Wyświetlanie danych w widżecie tabeli
        self.table.clear()
        if df is None or df.empty:
            self.table.setColumnCount(0)
            self.table.setRowCount(0)
            return

        headers = list(df.columns)
        self.table.setColumnCount(len(headers))
        self.table.setRowCount(len(df))
        self.table.setHorizontalHeaderLabels(headers)

        # Ograniczenie do 500 wierszy dla płynności interfejsu
        display_df = df.head(5000)
        self.table.setRowCount(len(display_df))

        for r_i in range(len(display_df)):
            for c_i, col in enumerate(headers):
                val = str(display_df.iloc[r_i][col])
                if val == "nan": val = ""
                item = QTableWidgetItem(val)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Zablokowanie edycji komórki
                self.table.setItem(r_i, c_i, item)

        self.table.resizeColumnsToContents()  # Dopasowanie rozmiaru kolumn

    # ---------------- FILTERS ----------------
    def reset_filters(self):  # Resetowanie wszystkich filtrów do wartości domyślnych
        self.age_min.setValue(0)
        self.age_max.setValue(130)
        self.gender.setCurrentIndex(0)
        self.chk_hyper.setChecked(False)
        self.chk_heart.setChecked(False)
        self.chk_stroke.setChecked(False)
        self.log("Zresetowano filtry.")

    def apply_filters(self):  # Nakładanie filtrów na wczytany zbiór danych
        if self.df_all is None:
            self.error("Najpierw wczytaj dane.")
            return

        amin = self.age_min.value()
        amax = self.age_max.value()
        if amin > amax:
            self.error("Wiek min nie może być większy niż wiek max.")
            return

        g = self.gender.currentText()
        
        # Tworzenie maski filtrowania Pandas
        mask = (self.df_all["age"] >= amin) & (self.df_all["age"] <= amax)
        
        if g != "All":
            mask &= (self.df_all["gender"] == g)
            
        if self.chk_hyper.isChecked():
            mask &= (self.df_all["hypertension"] == 1)
        if self.chk_heart.isChecked():
            mask &= (self.df_all["heart_disease"] == 1)
        if self.chk_stroke.isChecked():
            mask &= (self.df_all["stroke"] == 1)

        self.df_filtered = self.df_all[mask].copy()  # Zastosowanie maski i utworzenie kopii
        self.populate_table(self.df_filtered)  # Odświeżenie tabeli

        self.log(
            f"Filtry: wiek {amin}-{amax}, płeć={g}, "
            f"hyper={int(self.chk_hyper.isChecked())}, stroke={int(self.chk_stroke.isChecked())} "
            f"=> wynik: {len(self.df_filtered)}"
        )
        self.tabs.setCurrentWidget(self.tab_preview)

    # ---------------- ANALYSIS ----------------
    def analyze_data(self):  # Przeprowadzanie analizy statystycznej
        if self.df_filtered is None or self.df_filtered.empty:
            self.error("Brak danych do analizy.")
            return

        group_by = self.cmb_group_by.currentText()
        stats_lines = []
        stats_lines.append("ANALIZA STATYSTYCZNA (Pandas)")
        stats_lines.append(f"Liczność całkowita (N): {len(self.df_filtered)}")
        stats_lines.append(f"Grupowanie: {group_by}")
        stats_lines.append("=" * 35)
        stats_lines.append("")

        if group_by == "Brak":
            self._append_stats_for_df(self.df_filtered, "Cały zbiór", stats_lines)
        else:
            # Grupowanie danych w Pandas
            grouped = self.df_filtered.groupby(group_by)
            for name, group in grouped:
                self._append_stats_for_df(group, f"Grupa: {group_by} = {name}", stats_lines)

        text = "\n".join(stats_lines)
        self.stats_box.setPlainText(text)  # Wyświetlenie statystyk
        self.report_box.setPlainText(
            "RAPORT ROZSZERZONY (PANDAS)\n\n"
            "1) Charakterystyka zbioru:\n"
            f"   - Liczba rekordów po filtracji: {len(self.df_filtered)}\n"
            f"   - Kryterium grupowania: {group_by}\n\n"
            "2) Statystyki opisowe zostały wygenerowane automatycznie.\n\n"
            "3) Analiza wizualna:\n"
            "   Dostępna w zakładce 'Wizualizacja'.\n"
        )
        self.log(f"Analiza Pandas zakończona (grupy: {group_by}).")
        self.tabs.setCurrentWidget(self.tab_stats)

    def _append_stats_for_df(self, df: pd.DataFrame, title: str, lines: List[str]):  # Pomocnicza metoda generująca opis statystyczny
        lines.append(f"--- {title} (N={len(df)}) ---")
        # Wykorzystujemy pandas describe() dla szybkich statystyk
        stats = df[NUMERIC_COLUMNS].describe()
        
        for col in NUMERIC_COLUMNS:
            if col in stats.columns:
                s = stats[col]
                lines.append(f"  {col.upper()}:")
                lines.append(f"    - średnia: {s['mean']:.2f}")
                lines.append(f"    - mediana: {df[col].median():.2f}")
                lines.append(f"    - min/max: {s['min']:.1f} / {s['max']:.1f}")
                lines.append(f"    - odch. std: {s['std']:.2f}")
        lines.append("")

    # ---------------- PLOTS ----------------
    def show_plots(self):  # Wyświetlanie wybranego typu wykresu
        if not MATPLOTLIB_OK:
            self.error("Brak Matplotlib. Zainstaluj: pip install matplotlib")
            return

        if self.df_filtered is None or self.df_filtered.empty:
            self.error("Brak danych do wyświetlenia. Wczytaj dane i zastosuj filtry.")
            return

        df = self.df_filtered
        plot_type = self.cmb_plot_type.currentText() if hasattr(self, "cmb_plot_type") else "Histogram: wiek"

        # Logika wyboru wykresu na podstawie tekstu z ComboBox
        if plot_type == "Histogram: wiek":
            self.plot_widget.plot_histogram(df["age"].dropna().tolist(), "Histogram wieku", "age")

        elif plot_type == "Histogram: avg_glucose_level":
            self.plot_widget.plot_histogram(df["avg_glucose_level"].dropna().tolist(), "Histogram poziomu glukozy", "avg_glucose_level")

        elif plot_type == "Histogram: bmi":
            self.plot_widget.plot_histogram(df["bmi"].dropna().tolist(), "Histogram BMI", "bmi")

        elif plot_type == "Scatter: bmi vs avg_glucose_level":
            temp_df = df[["bmi", "avg_glucose_level"]].dropna()
            self.plot_widget.plot_scatter(temp_df["bmi"].tolist(), temp_df["avg_glucose_level"].tolist(), "BMI vs Poziom glukozy", "BMI", "Avg Glucose")

        elif "Boxplot" in plot_type:
            col, group_col = "", ""
            if "wiek wg płci" in plot_type: col, group_col = "age", "gender"
            elif "bmi wg stroke" in plot_type: col, group_col = "bmi", "stroke"
            elif "glucose wg hypertension" in plot_type: col, group_col = "avg_glucose_level", "hypertension"
            
            # Przygotowanie danych pogrupowanych dla wykresu pudełkowego
            groups_data = {self._format_val(group_col, name): group[col].dropna().tolist() 
                           for name, group in df.groupby(group_col) if not group[col].dropna().empty}
            
            if groups_data:
                self.plot_widget.plot_boxplot(groups_data, f"Porównanie: {col} wg {group_col}", col)
            else:
                self.error("Brak danych do wykresu pudełkowego.")

            
            # Pobieramy dane i usuwamy puste wartości
            temp_df = df[[col_x, col_y]].dropna()
            if temp_df.empty:
                self.error("Brak danych po usunięciu wartości NaN.")
                return

            # Sprawdzamy typy danych, aby dobrać najlepszy wykres
            is_x_num = pd.api.types.is_numeric_dtype(temp_df[col_x])
            is_y_num = pd.api.types.is_numeric_dtype(temp_df[col_y])
            
            # Liczba unikalnych wartości (do odróżnienia ciągłych od dyskretnych/kategorii)
            x_unique = temp_df[col_x].nunique()
            y_unique = temp_df[col_y].nunique()

            # --- LOGIKA DOBORU WYKRESU ---
            
            # 1. Obie kolumny są kategoryczne (lub mają bardzo mało wartości, np. 0/1)
            if (not is_x_num or x_unique < 5) and (not is_y_num or y_unique < 5):
                # Robimy wykres słupkowy zliczeń kombinacji (np. ile osób hajtniętych ma udar)
                counts = temp_df.groupby([col_x, col_y]).size().reset_index(name='count')
                # Tworzymy czytelne etykiety "WartośćX | WartośćY" korzystając z mapowania
                bar_data = {
                    f"{self._format_val(col_x, r[col_x])} | {self._format_val(col_y, r[col_y])}": int(r['count']) 
                    for _, r in counts.iterrows()
                }
                self.plot_widget.plot_bar(bar_data, f"Rozkład: {col_x} oraz {col_y}", f"{col_x} | {col_y}", "Liczba osób")

            # 2. X jest kategorią, Y jest liczbą (klasyczny Boxplot)
            elif (not is_x_num or x_unique < 10) and is_y_num:
                groups = {self._format_val(col_x, n): g[col_y].tolist() for n, g in temp_df.groupby(col_x)}
                self.plot_widget.plot_boxplot(groups, f"{col_y} względem {col_x}", col_y)

            # 3. Y jest kategorią, X jest liczbą (odwracamy dla Boxplota)
            elif is_x_num and (not is_y_num or y_unique < 10):
                groups = {self._format_val(col_y, n): g[col_x].tolist() for n, g in temp_df.groupby(col_y)}
                self.plot_widget.plot_boxplot(groups, f"{col_x} względem {col_y}", col_x)

            # 4. Obie są liczbami (Scatter)
            else:
                self.plot_widget.plot_scatter(
                    temp_df[col_x].tolist(), temp_df[col_y].tolist(),
                    f"Korelacja: {col_x} vs {col_y}", col_x, col_y
                )

        self.log(f"Wygenerowano wykres: {plot_type}")
        self.tabs.setCurrentWidget(self.tab_plots)

    # ---------------- EXPORT ----------------
    def export_csv(self):  # Eksportowanie przefiltrowanych danych do CSV
        if self.df_filtered is None:
            self.error("Najpierw wczytaj dane.")
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Zapisz CSV", "filtered_csv.csv", "CSV Files (*.csv);;All Files (*)"
        )
        if not out_path:
            return

        try:
            self.df_filtered.to_csv(out_path, index=False, encoding="utf-8")  # Zapis do pliku
            self.log(f"Zapisano CSV: {out_path} | rekordów: {len(self.df_filtered)}")
            self.info("Eksport CSV zakończony.")
        except Exception as e:
            self.error(f"Nie udało się zapisać CSV: {e}")

    def export_pdf(self):  # Generowanie i eksport raportu do pliku PDF
        if not PDF_OK:
            self.error("Brak biblioteki fpdf2. Zainstaluj: pip install fpdf2")
            return
        if self.df_filtered is None:
            self.error("Najpierw wczytaj dane.")
            return

        report_content = self.report_box.toPlainText().strip()
        stats_content = self.stats_box.toPlainText().strip()
        
        if not report_content and not stats_content:
            self.error("Brak treści raportu. Najpierw kliknij 'Analizuj'.")
            return

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Zapisz Raport PDF", "raport_pacjenci.pdf", "PDF Files (*.pdf)"
        )
        if not out_path:
            return

        try:
            pdf = FPDF()  # Inicjalizacja obiektu PDF
            # Ścieżki do fontów systemowych na macOS
            font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
            font_path_bold = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
            font_name = "Arial"
            font_loaded = False
            
            # Próba załadowania fontów obsługujących polskie znaki
            if os.path.exists(font_path):
                try:
                    pdf.add_font("Arial", "", font_path)
                    if os.path.exists(font_path_bold):
                        pdf.add_font("Arial", "B", font_path_bold)
                    font_loaded = True
                except: pass

            def clean_polish(text: str) -> str:  # Funkcja usuwająca polskie znaki, jeśli font ich nie obsługuje
                if font_loaded: return text
                pol = "ąćęłńóśźżĄĆĘŁŃÓŚŹŻ"
                lat = "acelnoszzACELNOSZZ"
                table = str.maketrans(pol, lat)
                return text.translate(table).encode('ascii', 'ignore').decode('ascii')

            pdf.add_page()
            
            # Tytuł raportu
            if font_loaded:
                pdf.set_font(font_name, "B", 16)
            else:
                pdf.set_font("Helvetica", "B", 16)
            
            pdf.cell(0, 10, clean_polish("RAPORT MEDYCZNY (PANDAS)"), ln=True, align="C")
            pdf.ln(10)
            
            # Treść podsumowania
            if font_loaded:
                pdf.set_font(font_name, "", 12)
            else:
                pdf.set_font("Helvetica", "", 12)
            pdf.multi_cell(0, 8, clean_polish(report_content if report_content else "Brak podsumowania."))
            pdf.ln(5)
            
            # Szczegółowe statystyki
            if font_loaded:
                pdf.set_font(font_name, "B", 14)
            else:
                pdf.set_font("Helvetica", "B", 14)
            pdf.cell(0, 10, clean_polish("Szczegółowe statystyki:"), ln=True)
            
            if font_loaded:
                pdf.set_font(font_name, "", 9)
            else:
                pdf.set_font("Courier", "", 9)
            pdf.multi_cell(0, 5, clean_polish(stats_content if stats_content else "Brak danych."))
            
            # Dołączanie aktualnego wykresu do PDF
            if MATPLOTLIB_OK and self.plot_widget.figure:
                img_path = "temp_plot.png"
                self.plot_widget.figure.savefig(img_path, dpi=100)  # Zapis tymczasowego obrazu
                pdf.add_page()
                if font_loaded:
                    pdf.set_font(font_name, "B", 14)
                else:
                    pdf.set_font("Helvetica", "B", 14)
                pdf.cell(0, 10, clean_polish("Wizualizacja:"), ln=True)
                pdf.image(img_path, x=10, y=30, w=190)
                if os.path.exists(img_path): os.remove(img_path)  # Usunięcie pliku tymczasowego

            pdf.output(out_path)  # Finalny zapis PDF
            self.log(f"Zapisano PDF: {out_path}")
            self.info("Eksport PDF zakończony pomyślnie.")
        except Exception as e:
            self.error(f"Nie udało się wygenerować PDF: {e}")


def main():  # Główna funkcja startowa aplikacji
    app = QApplication(sys.argv)  # Inicjalizacja aplikacji Qt
    w = MainWindow()  # Utworzenie okna
    w.show()  # Wyświetlenie okna
    sys.exit(app.exec())  # Uruchomienie pętli zdarzeń


if __name__ == "__main__":  # Punkt wejścia skryptu
    main()
