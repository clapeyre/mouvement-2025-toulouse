import os
import logging
from waitress import serve
from mouvement.app import app

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mouvement.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('mouvement')

if __name__ == '__main__':
    try:
        # Get port from environment variable or default to 8081
        port = int(os.environ.get('PORT', 8081))
        
        # Get host from environment variable or default to 0.0.0.0
        host = os.environ.get('HOST', '0.0.0.0')
        
        logger.info(f"Starting server on {host}:{port}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Environment variables: FLASK_SECRET_KEY={'*' * 32 if os.environ.get('FLASK_SECRET_KEY') else 'Not set'}")
        
        serve(app, host=host, port=port)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}", exc_info=True)
        raise 