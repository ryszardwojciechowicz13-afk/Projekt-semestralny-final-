# Projekt Semestralny: Analiza Danych Pacjentów (Stroke Data)

Aplikacja desktopowa napisana w **Pythonie** przy użyciu biblioteki **PyQt6**, służąca do eksploracyjnej analizy danych dotyczących udarów mózgu. Program umożliwia wczytywanie danych z plików **CSV** oraz baz **SQLite**, filtrowanie rekordów, generowanie statystyk opisowych oraz wizualizację danych za pomocą wykresów.

## Autor
- **Imię i Nazwisko**: [Twoje Imię i Nazwisko]
- **Kierunek**: [Nazwa Kierunku]
- **Grupa**: [Numer Grupy]

## Funkcjonalności
- Wczytywanie danych z pliku `healthcare-dataset-stroke-data.csv` lub bazy `healthcare.db`.
- Zaawansowane filtrowanie (wiek, płeć, nadciśnienie, choroby serca).
- Automatyczne generowanie statystyk (średnia, mediana, odchylenie standardowe).
- Wizualizacja danych: histogramy, wykresy punktowe i pudełkowe.
- Eksport przefiltrowanych danych do pliku **CSV**.
- Generowanie raportu końcowego w formacie **PDF** wraz z wykresem.

## Instrukcja uruchomienia

### Wymagania
- Python 3.8 lub nowszy.
- System operacyjny: Windows, macOS lub Linux.

### Kroki instalacji i uruchomienia

1. **Stworzenie środowiska wirtualnego (zalecane):**
   ```bash
   python -m venv venv
   ```

2. **Aktywacja środowiska wirtualnego:**
   - **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - **macOS / Linux:**
     ```bash
     source venv/bin/activate
     ```

3. **Instalacja wymaganych bibliotek:**
   Upewnij się, że plik `requirements.txt` znajduje się w katalogu projektu, a następnie wykonaj:
   ```bash
   pip install -r requirements.txt
   ```

4. **Uruchomienie aplikacji:**
   ```bash
   python main.py
   ```

### Uruchomienie w PyCharm
1. **Otwórz projekt**: `File -> Open` i wybierz folder projektu.
2. **Konfiguracja środowiska**: PyCharm powinien automatycznie wykryć plik `requirements.txt` i zaproponować stworzenie środowiska wirtualnego oraz instalację zależności.
3. **Ręczne ustawienie**: Jeśli tak się nie stało, wejdź w `Settings -> Project -> Python Interpreter` i dodaj nowy interpreter (venv).
4. **Uruchomienie**: Kliknij prawym przyciskiem myszy na plik `main.py` i wybierz `Run 'main'`.

## Struktura projektu
- `main.py` – główny kod źródłowy aplikacji (z komentarzami w języku polskim).
- `requirements.txt` – lista zależności projektowych.
- `healthcare-dataset-stroke-data.csv` – przykładowy zbiór danych.
- `healthcare.db` – baza danych SQLite z tabelą pacjentów.
- `README.md` – niniejsza dokumentacja.

---
*Projekt przygotowany na zaliczenie przedmiotu [Nazwa Przedmiotu].*
