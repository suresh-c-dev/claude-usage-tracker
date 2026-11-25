# Claude Usage Tracker (Free Plan)

A small command-line app to track my Claude free plan usage.

## Commands

```
python tracker.py log short    # also: long, file
python tracker.py status       # message count and reset time
python tracker.py limit        # record that Claude blocked you
python tracker.py history      # past blocks and typical cap
```

## Requirements

Python 3 (built-in libraries only)

## Limitations

- Estimate only: messages are logged manually
- Assumes a 5-hour window starting at the first logged message
- The typical cap counts all message types equally

## Built with

Python, SQLite. Code written with help from Claude.
