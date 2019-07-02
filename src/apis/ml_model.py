from flask import jsonify, current_app
from flask_restplus import Resource, Namespace, fields, abort
from src.apis.cache import cache
from src.ml import model, preprocessor
from src.infrastructure import blobhandler


api = Namespace('model', description="Namespace holding all methods related to the model.")

model_info_schema = api.model(name="Model information schema", model=
    {
        "model_type": fields.String(required=True),
        "last_trained": fields.String(required=True),
        "samples_used": fields.String(required=True)
    }
)

training_result_schema = api.model(name="Training result schema", model=
    {
        "training_result": fields.String(required=True),
        "trained_model": fields.String(required=True),
        "samples_used": fields.String(required=True)
    }
)


@api.route("/current/")
class Model(Resource):
    @api.response(200, 'Success', model_info_schema)
    @api.response(404, "Not found")
    def get(self):
        """Returns information about the current trained model."""

        if "trained_model" not in cache.keys():
            message = "No trained model found. Train model first."
            abort(404, custom=message)

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
    @api.response(200, 'Success', model_info_schema)
    @api.response(404, "Not found")
    def get(self):
        """Returns information about the activated pickled model."""

        if "pickled_model" not in cache.keys():
            message = "No activated model found. Activated pickled model first."
            abort(404, custom=message)
        
        if cache["pickled_model"]:
            return jsonify(
                {
                    "model_type": "{}".format(str(type(cache["pickled_model"]))),
                    "last_trained": "unknown",
                    "samples_used": "unknown"
                }
            )



@api.route("/train_current/<training_samples>/")
@api.param('training_samples', 'Number of samples to be used in training')
class CurrentTraining(Resource):
    @api.response(200, 'Success', training_result_schema)
    @api.response(500, "Internal server error")
    def put(self, training_samples):
        """Initiates and trains a random forest model that can be used to make predictions."""

        samples = int(training_samples)
        handler = blobhandler.BlobHandler()
        blobs = handler.download_blobs(current_app.config["CONTAINER_NAME_DATA"], number_of_blobs=samples)

        if blobs == None:
            message = "Failed to connect to azure blob."
            abort(500, custom=message)

        else:
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
    @api.response(200, 'Success', training_result_schema)
    @api.response(500, "Internal server error")
    def put(self, model_id):
        """Activates a pickled model from Azure blob storage that can be used to make predictions."""

        handler = blobhandler.BlobHandler()
        model = handler.azure_blob_to_model(model_id=model_id, container_name=current_app.config["CONTAINER_NAME_MODELS"])

        if model[0] == False:
            message = "Failed to download model from Azure blob. {}".format(str(model[1]))
            abort(500, custom=message)

        else:
            cache["pickled_model"] = model[1]
            return jsonify(
                {
                    "training_result": "Successfully activated model",
                    "trained_model": "{}".format(str(type(model[1]))),
                    "samples_used": "unknown"
                }
            )
