# Mouvement

A visualization tool for school positions in France. This tool displays schools on an interactive map with information about vacant positions.

## Installation

### Using pip

```bash
pip install -e .
```

### Building a wheel

To build a wheel for Python 3.11:

```bash
pip install hatch
hatch build
```

The wheel will be created in the `dist/` directory.

## Usage

1. Place your CSV files in the project directory:
   - `mouvement_complet_clean.csv` - Contains the list of schools and positions
   - `schools_with_addresses.csv` - Contains school addresses and coordinates

2. Run the application:
```bash
mouvement
```

3. Open your web browser and navigate to `http://localhost:5000`

## Production Deployment

1. Install the package:
```bash
pip install .
```

2. Set up environment variables:
```bash
# Generate a secure secret key
python -c "import secrets; print(secrets.token_hex(32))"
# Copy the output and set it as FLASK_SECRET_KEY
export FLASK_SECRET_KEY="your-generated-secret-key"

# Optionally set port and host
export PORT=8081
export HOST=0.0.0.0
```

3. Run the production server:
```bash
python -m mouvement.server
```

For running as a service, create a systemd service file `/etc/systemd/system/mouvement.service`:
```ini
[Unit]
Description=Mouvement Web Application
After=network.target

[Service]
User=your-user
WorkingDirectory=/path/to/your/data
Environment=FLASK_SECRET_KEY=your-generated-secret-key
Environment=PORT=8081
Environment=HOST=0.0.0.0
ExecStart=/path/to/python -m mouvement.server
Restart=always

[Install]
WantedBy=multi-user.target
```

Then enable and start the service:
```bash
sudo systemctl enable mouvement
sudo systemctl start mouvement
```

## Development

To set up a development environment:

```bash
pip install -e .
```

## License

[Your chosen license] 
