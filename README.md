# Traffic MQTT Monitor & Traffic Volume Prediction

A small Python project that sends historical traffic data over MQTT, predicts traffic volume with a Random Forest model, and displays the actual and predicted values in a Flask dashboard.

## Features

- Publishes traffic records from a CSV file to an MQTT broker.
- Trains a Random Forest regression model with scikit-learn.
- Predicts traffic volume for incoming MQTT messages.
- Displays recent records and an actual-versus-predicted graph in a web dashboard.

## How it works

```text
Traffic CSV → sender.py → MQTT broker → receiver.py → Flask dashboard
                                         |
                                         └── Random Forest model
```

The sender replays historical rows from the dataset, one row at a time. The receiver uses the saved model to generate a prediction for each message, then the dashboard compares that prediction with the actual traffic volume in the same row.

## Project structure

```text
.
├── .env.example
├── .gitignore
├── features.py
├── ml_model.py
├── receiver.py
├── requirements.txt
├── sender.py
├── test_prediction.py
├── mosquitto/
│   └── mosquitto.conf
└── templates/
    └── index.html
```

## Dataset

This project uses the **[TrafficVolumeDataCSV dataset on Kaggle](https://www.kaggle.com/datasets/bobaaayoung/trafficvolumedatacsv/data)**.

Download the CSV from Kaggle and place it in the project root as `TrafficVolumeData.csv`. The training and sender scripts expect that filename. Please refer to the Kaggle dataset page for the source and any terms that apply to the data.

## Requirements

- Python 3.9 or newer
- An MQTT broker, such as Mosquitto
- The dataset described above

Install the Python dependencies:

```bash
python -m venv .venv
```

Activate the environment:

**Windows PowerShell**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux/macOS**
```bash
source .venv/bin/activate
```

Then install the packages:

```bash
python -m pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and adjust the values for your environment. The scripts load settings from `.env`.

The main settings are:

| Variable | Purpose | Default |
|---|---|---|
| `MQTT_HOST` | MQTT broker hostname or address | `127.0.0.1` |
| `MQTT_PORT` | MQTT broker port | `1883` |
| `MQTT_TOPIC` | Topic used for traffic messages | `traffic/data` |
| `CSV_PATH` | Path to the CSV dataset | `TrafficVolumeData.csv` |
| `PUBLISH_INTERVAL` | Seconds between published rows | `1` |
| `REPLAY_LOOP` | Replay the CSV continuously when `true` | `false` |
| `FLASK_HOST` | Address the dashboard listens on | `127.0.0.1` |
| `FLASK_PORT` | Dashboard port | `5018` |
| `MODEL_PATH` | Saved model path | `traffic_model.pkl` |
| `MAX_MESSAGES` | Number of recent messages shown | `10` |

### Start Mosquitto with Docker (optional)

From the project root, run:

```bash
docker run --rm --name traffic-mosquitto \
  -p 127.0.0.1:1883:1883 \
  -v "$PWD/mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf:ro" \
  eclipse-mosquitto:2
```

This example is intended for a local demo. If your broker runs elsewhere, set `MQTT_HOST` and `MQTT_PORT` to the address and port reachable from the Python scripts.

## Train the model

After placing the dataset in the project root, run:

```bash
python ml_model.py
```

The script trains a Random Forest regression pipeline, evaluates it on a held-out random split, then trains the pipeline on the full dataset and saves it as `traffic_model.pkl`.

In the original development run, the holdout results were:

- Mean Absolute Error (MAE): `239.90`
- R² score: `0.9562`

Your results may vary depending on the dataset and library versions. Because the data is time-based, a random split may give an optimistic view of performance on future dates; a chronological evaluation would be a stronger test for forecasting.

## Run the dashboard

Start the receiver:

```bash
python receiver.py
```

By default, the dashboard is available at [http://127.0.0.1:5018](http://127.0.0.1:5018).

In another terminal, start the CSV sender:

```bash
python sender.py
```

As the messages arrive, the dashboard updates its table and graph. Chart.js is loaded from a CDN, so the browser needs internet access to display the graph.

## Test a prediction

To compare the saved model's prediction with the actual value from the first dataset row, run:

```bash
python test_prediction.py
```

## Model overview

The target is `traffic_volume`. The model uses weather and environmental fields, holiday and weather categories, and time features derived from `date_time`:

- Hour
- Day of the week
- Month
- Day of the month

Missing numeric values are imputed with the median, and categorical values are imputed and one-hot encoded. The Random Forest model uses 200 trees by default.

This dashboard compares predictions with known historical values carried in the incoming CSV rows. It is a demonstration of an MQTT-to-ML pipeline, not a live traffic sensor or a future-traffic forecasting service.

## License

This repository's code is released under the **MIT License**. See [`LICENSE`](LICENSE). The Kaggle dataset is a separate work; refer to its source page for applicable terms.
