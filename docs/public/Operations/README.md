# Operations Guide

This guide covers day-to-day operations: running simulations, managing them, and exporting data for analysis.

## Table of Contents

- [Running Simulations](#running-simulations)
- [Managing Running Simulations](#managing-running-simulations)
- [Viewing Current State](#viewing-current-state)
- [Exporting Data](#exporting-data)
- [Understanding Files and Directories](#understanding-files-and-directories)
- [Common Tasks](#common-tasks)

---

## Running Simulations

### Starting a New Simulation

**Basic command:**
```bash
make run
```

**What this does:**
- Starts a fresh simulation from the beginning
- Uses the default configuration (`configs/dev.yml`)
- Creates a new database and log files
- Runs until you stop it

**When to use:** Starting a new scenario, testing configurations, or when you want to overwrite previous results.

**To stop:** Press `Ctrl+C` in the terminal, or run `make run-stop` in another terminal.

### Resuming a Previous Simulation

**Basic command:**
```bash
make resume
```

**What this does:**
- Loads the last saved state from the database
- Continues from where it left off
- Appends to existing log files (doesn't overwrite)
- Preserves all previous data

**When to use:** Continuing a long-running simulation, or when you stopped a simulation and want to continue it.

**Why resume?** Simulations can run for days or weeks of simulated time. If you stop the simulation (to shut down your computer, for example), you can resume it later without losing any progress.

**To stop:** Press `Ctrl+C` or run `make resume-stop` (or `make run-stop` - both work).

### Running with Custom Configuration

**Command:**
```bash
python -m src --config path/to/your/config.yml
```

**Example:**
```bash
python -m src --config configs/my_scenario.yml
```

**What this does:** Runs the simulation using your custom configuration file instead of the default.

**When to use:** Testing different scenarios, using configurations you've customized, or running multiple different simulations.

### Limiting Simulation Duration

**Command:**
```bash
python -m src --config configs/dev.yml --max-ticks 100
```

**What this does:** Runs the simulation for a limited number of ticks (hours), then stops automatically.

**Useful for:**
- Quick testing of configurations
- Running short simulations
- Debugging without waiting for long runs

**Examples:**
- `--max-ticks 24` = Run for 1 simulated day
- `--max-ticks 720` = Run for 1 simulated month (30 days)
- `--max-ticks 8760` = Run for 1 simulated year

### Command Line Options

All available options when running simulations:

- **`--config PATH`**: Path to your configuration file (YAML or JSON format)
- **`--db PATH`**: Path to SQLite database file (default: `_running/simulation.db`)
- **`--resume`**: Resume from existing database instead of starting fresh
- **`--max-ticks N`**: Maximum number of ticks (hours) to run before stopping
- **`--log-level LEVEL`**: How much detail to log (DEBUG, INFO, WARNING, ERROR)

**Example with multiple options:**
```bash
python -m src --config configs/my_scenario.yml --max-ticks 1000 --log-level INFO
```

---

## Managing Running Simulations

### Stopping a Simulation

**If running in foreground** (you see output in terminal):
- Press `Ctrl+C` to stop gracefully

**If running in background** (using `make run` or `make resume`):
```bash
make run-stop
# or
make resume-stop
```

Both commands work for stopping any running simulation.

### Checking if Simulation is Running

**View running processes:**
```bash
ps aux | grep python
```

Look for processes running `src` or `simulation.py`.

### Viewing Live Logs

**Watch the log file as it updates:**
```bash
tail -f _running/logs/simulation.log
```

**What this does:** Shows the last few lines of the log file and updates automatically as new events occur.

**To stop watching:** Press `Ctrl+C`

**View last 50 lines:**
```bash
tail -n 50 _running/logs/simulation.log
```

**View entire log file:**
```bash
less _running/logs/simulation.log
```

(Press `q` to quit, `Space` to scroll down, `/` to search)

---

## Viewing Current State

### View World State Summary

**Command:**
```bash
make world-state-view
```

**What it shows:**
- Current simulation date and time
- Total ticks elapsed
- Number of registered systems
- Resource summary
- Active modifier count
- Entity count

**Useful for:** Quick check of simulation status without reading log files.

### View All Resources

**Command:**
```bash
make resources-view
```

**What it shows:**
- All resources and their current amounts
- Maximum capacity (if set)
- Replenishment rates
- Active modifiers affecting each resource
- Resource status (depleted, at_risk, moderate, sufficient, abundant)

**Useful for:** Checking if resources are running low or if production/consumption is balanced.

### View Modifiers

**List all modifiers:**
```bash
make modifier-list
```

**What it shows:**
- All active and inactive modifiers
- What resources/systems they affect
- When they start and end
- Repeat settings

**Useful for:** Understanding what events or effects are currently active in your simulation.

---

## Exporting Data

After running a simulation, you'll want to export the data to analyze it in spreadsheet programs, create graphs, or do further analysis.

### Export Resource History

**Basic export:**
```bash
make export-resources
```

**What this does:**
- Exports all resource history to a CSV file
- File is saved in `_running/exports/` directory
- Filename includes timestamp: `resources_YYYYMMDD_HHMMSS.csv`

**What's in the file:**
- One row per resource per timestamp
- Columns: `timestamp`, `tick`, `resource_id`, `amount`, `status_id`, `utilization_percent`
- Can be opened in Excel, Google Sheets, or any spreadsheet program

**Useful for:** Creating graphs of resource levels over time, analyzing trends, identifying shortages or surpluses.

### Export Entity/Population History

**Basic export:**
```bash
make export-entities
```

**What this does:**
- Exports population and entity statistics to a CSV file
- File is saved in `_running/exports/` directory
- Filename includes timestamp: `entities_YYYYMMDD_HHMMSS.csv`

**What's in the file:**
- One row per timestamp
- Columns include:
  - `total_entities`: Total population
  - `avg_hunger`, `avg_thirst`, `avg_rest`: Average needs levels
  - `avg_health`: Average health
  - `avg_age_years`: Average age
  - `avg_wealth`: Average wealth/money
  - `employed_count`: Number of employed people
  - And more...

**Useful for:** Analyzing population trends, health statistics, employment rates, and demographic changes over time.

### Advanced Export Options

#### Export Specific Resources Only

```bash
python -m src.cli.export_resources --resource-id food --resource-id water
```

**Useful when:** You only care about specific resources and want a smaller file.

#### Export by Time Range

**By tick range:**
```bash
python -m src.cli.export_resources --start-tick 100 --end-tick 200
```

**By date range:**
```bash
python -m src.cli.export_resources --start-date 2024-01-01T00:00:00 --end-date 2024-01-31T23:59:59
```

**Useful when:** You want to analyze a specific time period, not the entire simulation.

#### Export to Specific File

```bash
python -m src.cli.export_resources --output my_analysis.csv
```

**Useful when:** You want to control the filename or save to a specific location.

#### Pivot Format (Wider Table)

**For resources:**
```bash
python -m src.cli.export_resources --pivot
```

**For entities:**
```bash
python -m src.cli.export_entities --pivot
```

**What this does:** Creates a "wide" format where each resource/metric gets its own column, one row per timestamp.

**Useful when:** You want to create graphs comparing multiple resources side-by-side, or when working with pivot tables in Excel.

**Example:** Instead of multiple rows like:
```
timestamp, resource_id, amount
2024-01-01, food, 1000
2024-01-01, water, 2000
```

You get:
```
timestamp, food_amount, water_amount
2024-01-01, 1000, 2000
```

### Working with Exported Data

**Opening CSV files:**
- **Excel**: Double-click the file, or File → Open
- **Google Sheets**: Upload the file, or File → Import
- **Python/R**: Use pandas or similar libraries
- **Any spreadsheet program**: CSV is a universal format

**Creating graphs:**
- Select the data columns you want
- Insert a line chart or scatter plot
- X-axis: `timestamp` or `tick`
- Y-axis: `amount`, `total_entities`, `avg_health`, etc.

**Analyzing trends:**
- Look for increasing/decreasing trends
- Identify peaks and valleys
- Compare different resources or metrics
- Calculate averages, growth rates, etc.

---

## Understanding Files and Directories

### Directory Structure

**`_running/`** - Main directory for simulation files:
- `simulation.db` - SQLite database with all simulation data
- `logs/` - Directory containing log files
  - `simulation.log` - Main simulation log file
- `exports/` - Directory for exported CSV files (created automatically)

### Database File

**Location:** `_running/simulation.db`

**What it contains:**
- Complete simulation state (can resume from here)
- Resource history
- Entity/population history
- Job history
- Modifiers
- Configuration snapshot

**Important:** Don't delete this file if you want to resume the simulation! It contains all your simulation data.

**Backing up:** Copy this file to save a snapshot of your simulation at a specific point in time.

### Log Files

**Location:** `_running/logs/simulation.log`

**What it contains:**
- Text log of everything that happened
- Resource levels at logging intervals
- System status updates
- Errors and warnings
- Population changes
- And more...

**Size:** Can get large for long-running simulations. Consider adjusting logging frequency in configuration if files get too big.

**Viewing:** Use `tail`, `less`, or any text editor. See [Viewing Live Logs](#viewing-live-logs) above.

### Export Files

**Location:** `_running/exports/`

**Format:** CSV files with timestamps in filenames

**Naming:**
- `resources_YYYYMMDD_HHMMSS.csv` - Resource history exports
- `entities_YYYYMMDD_HHMMSS.csv` - Entity/population history exports

**Cleaning up:** Old export files can be deleted if you don't need them. They're just copies of data from the database.

---

## Common Tasks

### Task: Run a Simulation Overnight

1. **Start the simulation:**
   ```bash
   make run
   ```

2. **Let it run** (it will continue until you stop it)

3. **In the morning, stop it:**
   ```bash
   make run-stop
   ```

4. **Resume later if needed:**
   ```bash
   make resume
   ```

### Task: Test a Configuration Quickly

1. **Create or edit your configuration file**

2. **Run a short test:**
   ```bash
   python -m src --config configs/my_test.yml --max-ticks 100
   ```

3. **Check the results:**
   ```bash
   make resources-view
   make world-state-view
   ```

4. **If it looks good, run longer:**
   ```bash
   python -m src --config configs/my_test.yml --max-ticks 10000
   ```

### Task: Analyze Resource Trends

1. **Run your simulation**

2. **Export resource history:**
   ```bash
   make export-resources
   ```

3. **Open the CSV file** in Excel or Google Sheets

4. **Create a line chart:**
   - X-axis: `timestamp` or `tick`
   - Y-axis: `amount`
   - Filter by `resource_id` to see individual resources

5. **Analyze trends:**
   - Are resources increasing or decreasing?
   - Are there any sudden drops or spikes?
   - How do different resources compare?

### Task: Compare Two Scenarios

1. **Run first scenario:**
   ```bash
   python -m src --config configs/scenario1.yml --max-ticks 1000
   make export-resources --output scenario1_resources.csv
   ```

2. **Run second scenario:**
   ```bash
   python -m src --config configs/scenario2.yml --max-ticks 1000
   make export-resources --output scenario2_resources.csv
   ```

3. **Compare the CSV files** side-by-side or import both into a spreadsheet

### Task: Monitor a Long-Running Simulation

1. **Start the simulation:**
   ```bash
   make run
   ```

2. **In another terminal, watch the logs:**
   ```bash
   tail -f _running/logs/simulation.log
   ```

3. **Periodically check resources:**
   ```bash
   make resources-view
   ```

4. **If something looks wrong, stop and investigate:**
   ```bash
   make run-stop
   ```

### Task: Export Data for a Specific Time Period

1. **Find the tick numbers or dates** you're interested in (check the log file)

2. **Export with date range:**
   ```bash
   python -m src.cli.export_resources --start-date 2024-01-01T00:00:00 --end-date 2024-01-31T23:59:59
   ```

   Or with tick range:
   ```bash
   python -m src.cli.export_resources --start-tick 1000 --end-tick 2000
   ```

---

## Quick Reference: Make Commands

Common commands you'll use regularly:

- **`make setup`** - Initial setup (install dependencies)
- **`make run`** - Start a new simulation
- **`make run-stop`** - Stop a running simulation
- **`make resume`** - Resume a previous simulation
- **`make resume-stop`** - Stop a resumed simulation
- **`make world-state-view`** - View current simulation state
- **`make resources-view`** - View all resources
- **`make modifier-list`** - List all modifiers
- **`make export-resources`** - Export resource history to CSV
- **`make export-entities`** - Export entity/population history to CSV
- **`make test`** - Run tests (for developers)
- **`make docs`** - Build documentation
- **`make docs-serve`** - Serve documentation locally (view in browser)

---

## Troubleshooting

### Simulation Won't Start

**Check:**
- Is Python installed? (`python3 --version`)
- Is the virtual environment activated? (should see `(.venv)` in prompt)
- Are there errors in the terminal?
- Is the configuration file valid YAML?

### Can't Resume Simulation

**Check:**
- Does the database file exist? (`_running/simulation.db`)
- Are there errors in the log file?
- Was the previous simulation stopped cleanly?

### Exports Are Empty

**Check:**
- Did the simulation run long enough? (history systems need time to record data)
- Are history systems enabled in configuration?
- Check the log file for errors

### Log File Is Too Large

**Solution:**
- Adjust logging frequency in configuration (less frequent = smaller files)
- Use `--log-level WARNING` to reduce log detail
- Archive old log files and start fresh

---

## Next Steps

Now that you know how to operate simulations:

1. **[Configuration Guide](../Configuration/README.md)** - Learn how to customize simulations
2. **[Getting Started Guide](../Overview/getting-started.md)** - Review basics if needed
3. **[Systems Documentation](../Systems/README.md)** - Understand how systems work

**Ready to create your own scenarios?** Check out the [Configuration Guide](../Configuration/README.md)!
