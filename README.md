
# Tprotocol

A Python desktop application for configurable network protocol testing.

Tprotocol provides a graphical interface for configuring protocol checks, selecting target ports, executing tests concurrently, reviewing results, and exporting reports.

The project was built to make repetitive protocol testing workflows easier to configure and review.

## Features

- **Graphical Interface:** Built with Python and Tkinter.
- **Configurable Protocols:** Select and manage protocol test definitions.
- **Flexible Targeting:** Configure a target IP address and one or more ports.
- **Custom Parameters:** Supply test parameters such as usernames and passwords where required.
- **Concurrent Execution:** Run multiple protocol checks using a thread pool.
- **Result Classification:** Interpret command output using configurable success and failure patterns.
- **HTML Reports:** Export collected results into an HTML report.
- **JSON Configuration:** Store protocol definitions and default test values locally.

## Screenshots

Add an application screenshot to the repository at:

`docs/images/tprotocol-main.png`

Then it will appear here:

![Tprotocol application interface](docs/images/tprotocol-main.png)

## Requirements

- Python 3
- Tkinter
- Local command-line clients required by the selected protocol definitions

Tprotocol uses Python standard-library modules for its desktop interface, concurrency, JSON handling, and subprocess execution.

The external programs required for individual protocol checks depend on the protocol definitions being used.

## Installation

Clone the repository:

```bash
git clone https://github.com/sudoxs/Tprotocol.git
cd Tprotocol
```

Run the application:

```bash
python protocol_tester.py
```

On some Linux distributions, Tkinter may need to be installed separately through the system package manager.

## Basic Workflow

1. Launch Tprotocol.
2. Enter the target IP address.
3. Specify the ports to test.
4. Select the protocols you want to check.
5. Configure the available test parameters.
6. Select the desired test mode and concurrency level.
7. Start the tests.
8. Review the collected results.
9. Export the results as an HTML report when needed.

## Configuration

Protocol definitions and default values are stored locally in JSON files.

The application loads the available protocol definitions and uses their configured command templates, parameters, and response patterns during testing.

Review custom protocol definitions before running them. They may invoke local command-line programs.

## Project Structure

```text
Tprotocol/
│
├── protocol_tester.py
├── README.md
├── protocols.json       # Generated or locally maintained
├── defaults.json        # Generated or locally maintained
└── docs/
    └── images/
        └── tprotocol-main.png
```

The JSON files may be created locally by the application and are not necessarily included in a fresh clone.

## Security Notice

Use Tprotocol only against systems you own or have explicit permission to test.

The application invokes local command-line programs through subprocess execution. Review protocol definitions and command templates before running them.

This tool is intended for authorized testing and educational use.

## Author

**Shayan Ghasemi**

GitHub: https://github.com/sudoxs

Portfolio: https://sudoxs.github.io/sudoxsweb/
