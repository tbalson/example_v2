import connexion

# Initialize the Connexion app
connexion_app = connexion.FlaskApp(__name__, specification_dir='./')
connexion_app.add_api('openapi.yaml', strict_validation=True)

# Expose the underlying Flask app for the Gunicorn WSGI server
app = connexion_app.app

if __name__ == '__main__':
    connexion_app.run(host='0.0.0.0', port=5000)
