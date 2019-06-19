import os
import traceback
from flask import jsonify
from flask_restplus import Resource, Namespace, fields
from src.apis.cache import cache
from src.ml import model
from src.ml import preprocessor
from src.infrastructure import blobhandler


api = Namespace('model', description="Namespace holding all methods related to the model.")


@api.route("/current/")
class Model(Resource):
    def get(self):
        """Returns information about the current trained model."""

        if "trained_model" not in cache.keys():
            return jsonify(
                {
                    "Error": "Model has not been trained yet. Train model first."
                }
            )

        if cache["trained_model"]:
            return jsonify(
                {
                    "model_type": "{}".format(str(type(cache["trained_model"].classifier))),
                    "last_trained": "{}".format(str(cache["trained_model"].last_train_time_utc)),
                    "samples_used": "{}".format(str(cache["trained_model"].samples_used))
                }
            )


@api.route("/pickled/")
class PickledModel(Resource):
    def get(self):
        """Returns information about the latest pickled model."""

        return jsonify({"Error": "Not implemented yet"})


@api.route("/train_current/<training_samples>")
@api.param('training_samples', 'Number of samples to be used in training')
class CurrentTraining(Resource):
    def put(self, training_samples):
        """Initiates and trains a random forest model that can be used to make predictions."""

        samples = int(training_samples)
        handler = blobhandler.BlobHandler()
        try:
            blobs = handler.download_blobs(os.environ["CONTAINER_NAME_DATA"], number_of_blobs=samples)
        except Exception:
            return jsonify(
                {
                    "Error": "Failed to connect to azure blob.",
                    "Exception": str(traceback.format_exc())
                }
            )

        proc = preprocessor.Preprocessor()
        training_data = proc.create_training_data(blobs)
        classifier = model.Model()
        classifier.train(training_data=training_data)
        cache["trained_model"] = classifier

        return jsonify({
            "training_result": "Successfully trained model",
            "trained_model": "{}".format(str(type(classifier.classifier))),
            "samples_used": "{}".format(len(blobs))
            }
        )


@api.route("/activate_pickled/<model_id>/")
@api.param("model_id", "The Id (blob name) of the model.")
class PickledTraining(Resource):
    def put(self, model_id):
        """Activates a pickled model from Azure blob storage that can be used to make predictions."""

        handler = blobhandler.BlobHandler()
        model = handler.azure_blob_to_model(model_id=model_id, container_name=os.environ["CONTAINER_NAME_MODELS"])

        if model[0] == True:
            cache["pickled_model"] = model
            return jsonify(
                {
                    "training_result": "Successfully activated model",
                    "trained_model": "{}".format(str(type(model[1]))),
                    "samples_used": "unknown"
                }
            )

        else:
            return jsonify(
                {
                    "Error": "Failed to download model from Azure blob.",
                    "Exception": str(model[1])
                }
            )
