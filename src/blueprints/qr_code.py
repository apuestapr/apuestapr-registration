from flask import Blueprint, request, send_file, jsonify, render_template, session, redirect
import json
from bson.objectid import ObjectId
from datetime import datetime
from functools import wraps
import qrcode
import io
import os

qr_code_bp = Blueprint('qr_code', __name__)

@qr_code_bp.route('/generate/<string:registration_id>', methods=['GET'])
def generate_qr(registration_id):
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    
    domain = os.getenv('RENDER_EXTERNAL_URL')
    url = f'{domain}/registration/review/{registration_id}'
    
    print('QR Registration URL/Value:', url)
    
    qr.add_data(url)
    qr.make(fit=True)

    # Create an image from the QR Code instance
    img = qr.make_image(fill_color="black", back_color="white")

    # Save the image to a bytes buffer
    img_bytes = io.BytesIO()
    img.save(img_bytes)
    img_bytes.seek(0)

    return send_file(img_bytes, mimetype='image/png')

