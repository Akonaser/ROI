# Grocery coursework

Two project folders share this repository:

- [ROI](ROI/README.md): the existing grocery application, source code, tests, and user guide.
- **Final Project/**: reserved for future development. Only a `.gitkeep` placeholder is present so Git preserves the folder.

## Run the existing application

From the repository root:

```bash
cd ROI
python3 main.py
```

For the macOS interface, run `python3 gui.py` from the same folder.
To run tests: `python3 -m unittest discover -s tests -v`.

Open the repository root in VS Code to use the included tasks. They automatically run inside `ROI/`.
The existing expiry/waste prototype is retained in ROI; the separate final-project folder has no implementation yet.
