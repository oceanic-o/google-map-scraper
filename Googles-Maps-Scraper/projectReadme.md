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

You can define your search targets in `input.csv` (under a `category` header) or pass them via arguments.

**Using `input.csv` (Default):**

Add your search queries to `input.csv` (e.g., `hair salon`), then run the main script:

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
- `--grid`: Enables Grid Search (spatial scraping) by providing a coordinate bounding box (`lat_start,lon_start,lat_end,lon_end`). 
- `--step`: Defines the increment for the grid points (default is `0.01`, which is roughly ~1km steps).

### Grid Search with `input.csv`

The real power of grid search is combining it with `input.csv`. If your `input.csv` file contains multiple desired business types (e.g., `restaurant`, `khaja ghar`, `spa`), you can simply run:

```bash
uv run python main.py --grid 28.209,83.985,28.220,83.995 --step 0.01
```

**How it works seamlessly together:**
The scraper reads the categories from your `.csv` file, processes the `--grid` rectangle, and loops through both lists. It will go to the first grid coordinate and search for "restaurant", then search for "khaja ghar", then "spa", before moving onto the next coordinate block. This guarantees that you capture practically 100% of all listed businesses for your desired categories in the designated area!
