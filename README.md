# Traffic MQTT Monitor & Traffic Volume Prediction

A small end-to-end demo that replays historical traffic observations over MQTT, predicts traffic volume with a Random Forest regression model, and displays actual-versus-predicted values in a Flask dashboard.

> **Important:** This is a learning/demo project. The sender replays historical CSV rows; it is not a live traffic sensor or a production forecasting service.

## Features

- Publishes CSV rows as JSON messages over MQTT.
- Trains a scikit-learn `RandomForestRegressor` pipeline.
- Saves the fitted preprocessing and model to `traffic_model.pkl`.
- Subscribes to MQTT messages in a Flask receiver.
- Displays the latest messages in a table and plots actual versus predicted traffic volume.

## Architecture

```text
TrafficVolumeData.csv
        |
        v
    sender.py ---- JSON over MQTT ----> Mosquitto broker
                                            |
                                            v
                                      receiver.py
                                      |          |
                                model predicts   Flask dashboard
                                      |          |
                                      +------> templates/index.html
```

## Repository contents

```text
.
├── sender.py                 # Replays CSV rows to MQTT
├── receiver.py               # MQTT subscriber, prediction and Flask server
├── ml_model.py               # Trains and saves the model pipeline
├── test_prediction.py        # Tests the saved model on a dataset row
├── features.py               # Shared feature preparation for training/inference
├── requirements.txt
├── .env.example              # Safe configuration template (no credentials)
├── .gitignore
├── mosquitto/
│   └── mosquitto.conf        # Local-demo broker configuration
└── templates/
    └── index.html            # Table and Chart.js graph
```

The CSV dataset and generated `.pkl` model are intentionally **not included**. This avoids accidentally redistributing a dataset without checking its licence and avoids committing a generated binary that can be rebuilt.

## Requirements

- Python 3.9 or newer
- A running MQTT broker (Mosquitto is one option)
- The traffic CSV dataset described below
- Internet access in the browser if you want Chart.js to load from its CDN

## 1. Get the dataset

This project uses the traffic-volume dataset hosted on Kaggle:

**Dataset:** [TrafficVolumeDataCSV on Kaggle](https://www.kaggle.com/datasets/bobaaayoung/trafficvolumedatacsv/data)

1. Open the Kaggle dataset page and review its **License** and dataset description.
2. Download the CSV file from Kaggle.
3. Place it at the project root and rename it to:

```text
TrafficVolumeData.csv
```

The code expects these columns:

- `date_time`
- `is_holiday`
- `air_pollution_index`
- `humidity`
- `wind_speed`
- `wind_direction`
- `visibility_in_miles`
- `dew_point`
- `temperature`
- `rain_p_h`
- `snow_p_h`
- `clouds_all`
- `weather_type`
- `weather_description`
- `traffic_volume`

### Dataset licensing and attribution

The fact that a dataset is publicly visible or downloadable on Kaggle does **not automatically mean that anyone may re-host or redistribute the file**. Kaggle supports multiple licence types, and the permissions depend on the licence attached to this specific dataset and any applicable source terms. See [Kaggle's documentation on dataset licences](https://www.kaggle.com/docs/datasets).

For this repository, the safest default is to **link to the original Kaggle page and have users download the dataset themselves**, rather than committing a copy of the CSV. This keeps the repository smaller and avoids unintentionally redistributing data under terms that may require attribution, restrict commercial use, or impose other conditions.

If the dataset's displayed licence explicitly permits redistribution, you can choose to include it later, following all attribution and licence requirements. If you do include it, retain the original attribution/licence information and do not imply that you created the dataset. The project code and the dataset may have different licences.

## 2. Set up Python

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

## 3. Configure MQTT

Copy `.env.example` to `.env` and adjust values for your environment. The Python scripts read environment variables directly; they do not automatically load `.env`. To use `.env`, either export the variables in your shell or install `python-dotenv` and load it in your own environment.

For a local broker running on the same machine as the Python scripts, the defaults are:

```text
MQTT_HOST=127.0.0.1
MQTT_PORT=1883
MQTT_TOPIC=traffic/data
```

### Optional: run a local Mosquitto broker with Docker

From the project root:

```bash
docker run --rm --name traffic-mosquitto \
  -p 127.0.0.1:1883:1883 \
  -v "$PWD/mosquitto/mosquitto.conf:/mosquitto/config/mosquitto.conf:ro" \
  eclipse-mosquitto:2
```

The included broker configuration allows anonymous access for a **local-only demo**. The port is bound to `127.0.0.1`, not all network interfaces. Do not expose this configuration to an untrusted network or the public internet.

If the broker runs in a different container, `127.0.0.1` usually refers to the Python container itself, not the broker. Set `MQTT_HOST` to the broker's reachable hostname on the shared Docker network, or to the host address reachable from that container. Do not copy private LAN IP addresses into source code.

## 4. Train the model

With the dataset in the project root:

```bash
python ml_model.py
```

This trains a Random Forest regression pipeline and writes `traffic_model.pkl` to the project root. The pipeline includes missing-value imputation and one-hot encoding for categorical fields.

The script prints a holdout Mean Absolute Error (MAE) and R² score. The original development run reported **MAE 239.90** and **R² 0.9562** on a random train/test split. Results may differ by dataset version and library versions. A random split is not a rigorous test of future-time forecasting because nearby observations can be correlated; use a chronological split for a more realistic forecasting evaluation.

## 5. Run the receiver/dashboard

Start the Flask receiver in one terminal:

```bash
python receiver.py
```

By default, it listens on `http://127.0.0.1:5018`. Open that URL in your browser. If you are running it in Docker, publish the container port you configured; the host port may be different.

## 6. Start replaying the dataset

In another terminal, run:

```bash
python sender.py
```

The sender publishes one CSV row per second to `traffic/data` by default. The dashboard refreshes periodically and displays the most recent records.

You can change the broker address, port, topic, CSV path, publish interval, Flask host, and Flask port with environment variables. See `.env.example`.

## 7. Test the saved model separately

```bash
python test_prediction.py
```

This loads `traffic_model.pkl`, prepares one row using the same feature logic as training, and prints the actual and predicted traffic volume.

## How the model works

- **Target (`y`):** `traffic_volume`
- **Inputs (`X`):** weather/environment fields and holiday/weather categories, plus time features derived from `date_time` (`hour`, `day_of_week`, `month`, and `day`).
- **Preprocessing:** numeric missing values are filled with the training-set median; missing categorical values are filled with `Unknown`; categorical values are one-hot encoded.
- **Estimator:** `RandomForestRegressor` with 200 trees in the default training script.
- **Inference:** each incoming message is transformed by the same fitted pipeline and gets a `predicted_traffic` value.

The dashboard compares the prediction with the actual `traffic_volume` contained in each historical message. Because the actual value is sent along with the row, this graph is a comparison against known historical observations—not a prediction of an unknown future value.

## Security and public-repository checklist

Before pushing to GitHub:

- Keep `.env`, local logs, virtual environments, and local configuration out of Git.
- Do not commit API keys, passwords, tokens, private certificates, private IP addresses, usernames, machine paths, or internal hostnames.
- Do not commit your generated model or the CSV unless you have a reason to publish them and the dataset licence permits it.
- Review Git history as well as the current files. Removing a secret from the latest commit does not remove it from earlier commits.
- The bundled Mosquitto config is for a local demonstration only; do not expose anonymous MQTT access publicly.
- If a credential was ever committed, revoke/rotate it rather than merely deleting it from the file.

## Limitations and possible improvements

- Historical CSV replay is not live sensor data.
- The random train/test split can give an optimistic score for time-dependent data; evaluate with a chronological split before making forecasting claims.
- The model currently predicts the traffic volume in a row from that row's weather/time features. It does not forecast future traffic from a sequence of past traffic volumes.
- Chart.js is loaded from a CDN; an internet connection is needed for the graph unless the library is served locally.

## License

No project licence has been selected. Add a licence file before inviting reuse. Do not assume the dataset has the same licence as your code.
