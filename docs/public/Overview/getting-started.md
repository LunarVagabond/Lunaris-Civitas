# Getting Started

Welcome! This guide will help you set up and run your first Lunaris Civitas simulation. No programming experience required—just follow these steps.

## What You'll Need

- A computer running Linux, macOS, or Windows (with WSL)
- Python 3.8 or higher installed
- Basic familiarity with using a terminal/command line

## Installation

### Step 1: Get the Code

If you haven't already, get the Lunaris Civitas code onto your computer. This might involve:
- Cloning a repository (if using Git)
- Downloading and extracting a ZIP file
- Or however you obtained the project files

### Step 2: Set Up the Environment

Open a terminal in the project directory and run:

```bash
make setup
```

**What this does:** Creates a virtual environment (an isolated Python environment) and installs all required dependencies.

**How long it takes:** Usually 1-2 minutes, depending on your internet connection.

**If you see errors:** Make sure Python 3.8+ is installed. Try `python3 --version` to check.

### Step 3: Activate the Virtual Environment

```bash
source .venv/bin/activate
```

**What this does:** Activates the virtual environment so you can use the installed packages.

**You'll know it worked when:** Your terminal prompt shows `(.venv)` at the beginning.

**Note:** You need to do this every time you open a new terminal window to work with the simulation.

---

## Running Your First Simulation

### Quick Start: Run with Default Settings

The easiest way to get started is to run the simulation with the default configuration:

```bash
make run
```

**What happens:**
1. The simulation starts from the beginning
2. It uses the default configuration file (`configs/dev.yml`)
3. It creates a new database and log files
4. The simulation runs continuously until you stop it

**To stop the simulation:** Press `Ctrl+C` in the terminal, or run `make run-stop` in another terminal.

**Where are the results?**
- Database: `_running/simulation.db` (contains all simulation data)
- Logs: `_running/simulation.log` (text file with what happened)

### Understanding What's Happening

When you run the simulation, you're creating a virtual world where:

1. **Time passes**: The simulation advances hour by hour (each hour = 1 "tick")
2. **People exist**: A population is created and lives their lives
3. **Resources change**: Food, water, money, and other resources are produced and consumed
4. **Events occur**: People work jobs, get hungry, fulfill needs, age, and eventually pass away
5. **Data is recorded**: Everything is saved to the database for later analysis

**You won't see a visual interface**—this is a background simulation. Check the log file to see what's happening, or export data to analyze later.

---

## Running Simulations

### Basic Run (Start Fresh)

```bash
make run
```

**Use this when:**
- You want to start a new simulation from scratch
- You're testing different configurations
- You want to overwrite previous results

**What it does:**
- Starts a new simulation
- Uses `configs/dev.yml` by default
- Creates new database and log files (overwrites old ones)

### Resume a Previous Simulation

```bash
make resume
```

**Use this when:**
- You want to continue a simulation that was stopped
- You want to run a simulation for longer
- You don't want to lose previous progress

**What it does:**
- Loads the last saved state from the database
- Continues from where it left off
- Appends to existing log files (doesn't overwrite)
- Preserves all previous data

**Why use resume?** Simulations can run for days, weeks, or months of simulated time. If you stop the simulation, you can resume it later without losing progress.

### Run with a Custom Configuration

```bash
python -m src --config path/to/your/config.yml
```

**Use this when:**
- You've created your own configuration file
- You want to test different scenarios
- You want to use a configuration other than the default

**Example:**
```bash
python -m src --config configs/my_scenario.yml
```

### Limit How Long the Simulation Runs

```bash
python -m src --config configs/dev.yml --max-ticks 100
```

**Use this when:**
- You want to test a configuration quickly
- You want to run a short simulation
- You're debugging and don't want to wait

**What it means:** `--max-ticks 100` means the simulation will stop after 100 ticks (100 hours of simulated time).

**Example scenarios:**
- `--max-ticks 24` = Run for 1 simulated day (24 hours)
- `--max-ticks 720` = Run for 1 simulated month (720 hours)
- `--max-ticks 8760` = Run for 1 simulated year (8760 hours)

---

## Understanding Your Simulation

### What Gets Created

When you run a simulation, several things are created:

1. **Database** (`_running/simulation.db`):
   - Contains all simulation state
   - Stores resource history, entity history, job history
   - Can be resumed from this file
   - Can be queried for analysis

2. **Log File** (`_running/simulation.log`):
   - Text file showing what happened
   - Includes resource levels, population changes, events
   - Useful for understanding what's happening
   - Can get large for long simulations

3. **Export Directory** (`_running/exports/`):
   - Created when you export data
   - Contains CSV files you can open in Excel or other tools

### Checking What's Happening

**View the log file:**
```bash
tail -f _running/logs/simulation.log
```

This shows the last few lines and updates as new events occur. Press `Ctrl+C` to stop watching.

**View world state:**
```bash
make world-state-view
```

Shows current resource levels, population, and active modifiers.

**View resources:**
```bash
make resources-view
```

Shows all resources and their current amounts.

### Exporting Data for Analysis

After running a simulation, you can export the data:

**Export resource history:**
```bash
make export-resources
```

Creates a CSV file with resource amounts over time. Open it in Excel, Google Sheets, or any spreadsheet program to create graphs and analyze trends.

**Export entity/population history:**
```bash
make export-entities
```

Creates a CSV file with population statistics over time (total people, average health, employment, etc.).

**Where are exports saved?** `_running/exports/` directory with timestamps in the filename.

For more export options, see the [Operations Guide](../Operations/README.md).

---

## Customizing Your Simulation

### Your First Custom Configuration

The default configuration (`configs/dev.yml`) is a good starting point, but you'll probably want to customize it. Here's how:

1. **Copy the default config:**
   ```bash
   cp configs/dev.yml configs/my_first_scenario.yml
   ```

2. **Edit the file** with any text editor:
   ```bash
   nano configs/my_first_scenario.yml
   # or
   code configs/my_first_scenario.yml  # if using VS Code
   ```

3. **Make some changes:**
   - Change `initial_population: 100` to `initial_population: 50` for a smaller starting population
   - Change `spawn_rate: 10` to `spawn_rate: 5` for slower population growth
   - Experiment with resource amounts and production rates

4. **Run with your config:**
   ```bash
   python -m src --config configs/my_first_scenario.yml --max-ticks 100
   ```

**Tip:** Start with small changes and test them. See the [Configuration Guide](../Configuration/README.md) for detailed explanations of all settings.

### Common First Customizations

**Smaller starting population:**
```yaml
systems_config:
  HumanSpawnSystem:
    initial_population: 50  # Instead of 100
```

**More food production:**
```yaml
systems_config:
  ResourceProductionSystem:
    production:
      food: 200.0  # Instead of 100.0
```

**Slower population growth:**
```yaml
systems_config:
  HumanSpawnSystem:
    spawn_rate: 5  # Instead of 10 (fewer new people per day)
```

---

## Next Steps

Now that you've run your first simulation, here's what to explore next:

1. **[Configuration Guide](../Configuration/README.md)** - Learn how to customize everything
   - Understand what each setting does
   - See examples of different scenarios
   - Learn how to balance resources and population

2. **[Operations Guide](../Operations/README.md)** - Learn how to manage simulations
   - Export data for analysis
   - Resume long-running simulations
   - View current simulation state

3. **[Systems Documentation](../Systems/README.md)** - Understand how systems work
   - Learn about each system's purpose
   - See how systems interact
   - Understand the simulation mechanics

4. **Experiment!** - Try different configurations
   - Create scenarios with abundant resources
   - Create scenarios with resource scarcity
   - Test different population sizes and growth rates
   - See how different settings affect outcomes

---

## Troubleshooting

### "Command not found" errors

**Problem:** `make` command doesn't work.

**Solution:** 
- On Linux/macOS: Install `make` (usually pre-installed)
- On Windows: Use WSL (Windows Subsystem for Linux) or install `make` for Windows

### "Python not found" errors

**Problem:** Python isn't installed or not in your PATH.

**Solution:**
- Install Python 3.8 or higher from [python.org](https://www.python.org/)
- Make sure `python3` or `python` works in your terminal
- Try `python3 --version` to verify

### Simulation stops immediately

**Problem:** Simulation starts but exits right away.

**Solution:**
- Check the log file for error messages
- Verify your configuration file is valid YAML
- Make sure all required systems are enabled
- Check that resources are properly configured

### Resources running out quickly

**Problem:** Food, water, or other resources deplete rapidly.

**Solution:**
- Increase `replenishment_rate` in resource configuration
- Increase production rates in `ResourceProductionSystem`
- Decrease consumption rates in `ResourceConsumptionSystem`
- See the [Configuration Guide](../Configuration/README.md) for balancing tips

### Population dying off

**Problem:** People are dying faster than new ones are being born.

**Solution:**
- Increase `spawn_rate` in `HumanSpawnSystem`
- Ensure resources are sufficient (people need food/water to survive)
- Check health system settings (lower damage rates = people survive longer)
- See the [Configuration Guide](../Configuration/README.md) for health and death settings

### Need More Help?

- Check the [Configuration Guide](../Configuration/README.md) for detailed setting explanations
- Review the [Operations Guide](../Operations/README.md) for managing simulations
- Look at example configuration files in the `configs/` directory
- Check log files for error messages and warnings

---

## Summary

You've learned how to:
- ✅ Install and set up Lunaris Civitas
- ✅ Run your first simulation
- ✅ Resume simulations
- ✅ Use custom configurations
- ✅ Export data for analysis
- ✅ Customize basic settings

**Ready to dive deeper?** Check out the [Configuration Guide](../Configuration/README.md) to learn how to create your own scenarios!
