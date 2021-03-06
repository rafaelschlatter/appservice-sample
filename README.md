# Pipedesign-api
[![Build Status](https://travis-ci.org/rafaelschlatter/pipedesign-api.svg?branch=master)](https://travis-ci.org/rafaelschlatter/pipedesign-api)
[![codecov](https://codecov.io/gh/rafaelschlatter/pipedesign-api/branch/master/graph/badge.svg)](https://codecov.io/gh/rafaelschlatter/pipedesign-api)
[![Requirements Status](https://requires.io/github/rafaelschlatter/pipedesign-api/requirements.svg?branch=master)](https://requires.io/github/rafaelschlatter/pipedesign-api/requirements/?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/6f28fe09f64e4eaaa866498be841fa84)](https://app.codacy.com/app/rafaelschlatter/pipedesign-api?utm_source=github.com&utm_medium=referral&utm_content=rafaelschlatter/pipedesign-api&utm_campaign=Badge_Grade_Settings)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

## About
This is a python flask API that is hosted on Microsoft Azure app service. The API allows to activate pickled machine learning models from an Azure blob storage and request predictions on new data. The API can be tested using the Swagger ui here: <http://pipedesign.azurewebsites.net/>.

## Setup
Azure app service on linux needs a **requirements.txt** file for all dependencies except flask. A pipenv workflow probably fails (not tested).

Clone the repo and create a virtual environment with `virutalenv`:
````bash
git clone https://github.com/rafaelschlatter/pipedesign-api.git
cd pipedesign-api
virtualenv pipedesign-api
````

Activate it and install dependencies:
````bash
source pipedesign-api/bin/activate
pip install -r requirements.txt
````

You need to set the following environment variables:
````bash
STORAGE_ACC_NAME=<your-storage-account-name>
BLOB_KEY1=<your-storage-account-key>
CONTAINER_NAME_DATA=<container-name-containing-training-data>
CONTAINER_NAME_MODELS=<container-name-containing-models>
APPINSIGHTS_INSTRUMENTATIONKEY=<application-insights-instrumentation-key>
````

Run tests locally and produce coverage report (all or a specific file):
````bash
python -m pytest -v --cov=src
python -m pytest tests/infrastructure/blobhandler.py -v --cov=src
````

## Usage
Run the app locally with the following command at the root folder:
````bash
python application.py
````

You can also try the app hosted on Azure. The following code demonstrates usage with valid json data in python 3. Start a terminal at the root folder and run the following code:

````python
import requests, json

# Activate pickled model from Azure blob storage
activate_url = "http://pipedesign.azurewebsites.net/model/activate_pickled/test_model_1_do_not_delete/"
requests.put(url=activate_url)

# Retrieve prediction on pipedesign
predict_url = "http://pipedesign.azurewebsites.net/prediction/predict_pickled/"
with open("data/json/0a234fea9682454facab730c0a7f83f0.json") as f:
    json_data=json.load(f)

response = requests.post(predict_url, json=json_data)
print(response.json())
````

If there is a trained model available, you should get the following response:
````javascript
{
    "confidence": "0.00985992289985627",
    "label": "1",
    "pipedesign_id": "0a234fea9682454facab730c0a7f83f0",
    "prediction": "Viable"
}
````
