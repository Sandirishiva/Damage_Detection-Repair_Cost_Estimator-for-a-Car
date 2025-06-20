from flask import Blueprint, jsonify, request

repair_shops_bp = Blueprint('repair_shops', __name__)

@repair_shops_bp.route('/api/repair_shops', methods=['GET'])
def get_nearby_repair_shops():
    user_location = request.args.get('location')
    if not user_location:
        return jsonify({"error": "Location parameter is required."}), 400

    # Mock response with latitude and longitude
    repair_shops = [
        {"name": "Quick Fix Garage", "address": "123 Main St, Cityville", "distance": "1.2 miles", "lat": 37.7749, "lng": -122.4194},
        {"name": "Auto Repair Experts", "address": "456 Elm St, Cityville", "distance": "2.5 miles", "lat": 37.7849, "lng": -122.4094},
        {"name": "City Auto Service", "address": "789 Oak St, Cityville", "distance": "0.8 miles", "lat": 37.7949, "lng": -122.4294}
    ]

    return jsonify(repair_shops)