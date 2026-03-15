# PyVault

A secure command-line password manager built with Python.

## Features

- Secure password storage using Fernet symmetric encryption
- SQLite database for persistence
- Command-line interface with Click
- Password generation
- CRUD operations: Add, Get, Update, Delete, List passwords

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pyvault.git
   cd pyvault
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. (Optional) Install for development:
   ```bash
   pip install -e .
   ```

## Usage

Initialize the database (first time only):
```bash
python -m pyvault.cli
```

Add a password:
```bash
pyvault add
```

Get a password:
```bash
pyvault get
```

Update a password:
```bash
pyvault update
```

Delete a password:
```bash
pyvault delete
```

List all services:
```bash
pyvault list
```

Generate a password:
```bash
pyvault generate --length 16
```

## Security

- Passwords are encrypted using Fernet (AES 128) before storage.
- The encryption key is stored in `secret.key` (keep this secure!).
- Uses `secrets` module for password generation.

## Testing

Run tests with pytest:
```bash
pytest
```

## Project Structure

```
pyvault/
├── src/pyvault/
│   ├── __init__.py
│   ├── cli.py
│   ├── database.py
│   ├── encryption.py
│   ├── models.py
│   └── utils.py
├── tests/
│   ├── __init__.py
│   ├── test_cli.py
│   ├── test_database.py
│   ├── test_encryption.py
│   ├── test_models.py
│   └── test_utils.py
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── setup.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.