# Google Maps Scraper

## Setup Project with `uv`

This project uses `uv` for extremely fast Python package and virtual environment management.

### 1. Create a Virtual Environment

Initialize a virtual environment in the project directory using `uv`:

```bash
uv venv
```

### 2. Activate the Virtual Environment

Activate the newly created `.venv` virtual environment:

- On **Linux/macOS** (bash/zsh):
  ```bash
  source .venv/bin/activate
  ```
- On **Linux/macOS** (fish):
  ```fish
  source .venv/bin/activate.fish
  ```
- On **Windows**:
  ```cmd
  .venv\Scripts\activate
  ```

### 3. Install Dependencies

Install the required packages listed in `requirements.txt`:

```bash
uv pip install -r requirements.txt
```

### 4. Install Playwright Browsers

Since this scraper uses Playwright to navigate Google Maps, you'll need to install the Chromium browser binary used by the script:

```bash
uv run playwright install chromium
```

### 5. Running the Project

You can define your search targets in `input.txt` (one per line) or pass them via arguments.

**Using `input.txt` (Default):**

Add your search queries to `input.txt` (e.g., `hair salon`), then run the main script:

```bash
uv run python main.py
```
*(Or simply `python main.py` if the virtual environment is already activated.)*

**Using Command-Line Arguments:**

```bash
uv run python main.py -s "hair salon in pokhara nepal" -t 10
```

- `-s` or `--search`: Specifies the actual search string.
- `-t` or `--total`: Specifies the maximum number of listings to scrape per search.
