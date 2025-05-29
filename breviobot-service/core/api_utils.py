from core.logger import logger
from flask import jsonify

def handle_general_error(error):
    logger.error(f"Unhandled unexpected error: {str(error)}", exc_info=True)
    return jsonify({"error": "An unexpected error occurred. Please check the service logs for details."}), 500

def handle_authentication_error(error):
    logger.warning(f"Authentication error: {str(error)}")
    return jsonify({"error": str(error)}), 401

def handle_validation_error(error):
    logger.error(f"Validation error: {str(error)}")
    return jsonify({"error": str(error)}), 400