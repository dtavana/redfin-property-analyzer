from flask import Flask, jsonify, request
from datetime import datetime
import logging
from redfin import Redfin
from urllib.parse import urlparse

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

redfin_client = Redfin()

# Basic error handling
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({'error': 'Internal server error'}), 500

# Basic health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

# Example POST endpoint
@app.route('/api/property', methods=['POST'])
def insert_property():
    data = request.get_json()
    if not data or 'redfin_url' not in data:
        return jsonify({'error': 'redfin_url is required'}), 400
    
    logger.info(f"Received redfin_url: {data['redfin_url']}")
    parsed_url = urlparse(data['redfin_url']).path
    initial_info = redfin_client.initial_info(parsed_url)
    property_id = initial_info['payload']['propertyId']
    mls_data = redfin_client.below_the_fold(property_id)

    return jsonify({
        'status': 'success',
        'data': parse_mls_data(mls_data)
    }), 201

class AddressInfo:
    def __init__(self, street, city, state, zip_code):
        self.street = street
        self.city = city
        self.state = state
        self.zip_code = zip_code

    def to_json(self):
        return {
            'street': self.street,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code
        }

    def __str__(self):
        return f"{self.address}, {self.city}, {self.state} {self.zip_code}"

def parse_mls_data(mls_data):
    address_info_raw = mls_data['payload']['amenitiesInfo']['addressInfo']
    street, city, state, zip_code = address_info_raw['street'], address_info_raw['city'], address_info_raw['state'], address_info_raw['zip']
    address_info = AddressInfo(street, city, state, zip_code)

    return {
        'address_info': address_info.to_json(),
        'other': mls_data['payload']
    }

def parse_amenity_groups(amenity_groups):
    group_reference_name_to_amenity = {
        'Bathroom Information': '*',
        'Room Information': '*',
        'PropertyInformation': ['LIVING_SQUARE_FEET', 'GROSS_SQUARE_FEET', 'NUMBER_OF_UNITS']
    }

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)