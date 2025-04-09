import boto3
from flask import Flask, request, jsonify
from flasgger import Swagger
from kafka import KafkaProducer
import json
import os
from datetime import datetime

# חיבור ל-S3
s3 = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name='eu-north-1'
)

bucket_name = 'your-bucket-name'  # שם ה-bucket שבו תשמור את ההודעות

app = Flask(__name__)
swagger = Swagger(app)

# יצרנו Producer שיחבר אותנו ל-Kafka
producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

@app.route('/messages', methods=['POST'])
def send_message():
    """
    שולח הודעה ל-Kafka ושומר אותה ב-S3
    ---
    parameters:
      - name: message
        in: body
        required: true
        schema:
          type: object
          properties:
            message:
              type: string
    responses:
      200:
        description: ההודעה נשלחה ונותרה ב-S3
    """
    data = request.get_json()
    message = data.get('message')

    if not message:
        return jsonify({'error': 'Missing message'}), 400

    # שלח את ההודעה ל-Kafka
    producer.send('message_topic', {'message': message})

    # שמירת ההודעה ב-S3 בקובץ חדש
    file_name = f"message_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
    s3.put_object(
        Bucket=bucket_name,
        Key=file_name,
        Body=json.dumps({'message': message}),
        ContentType='application/json'
    )

    return jsonify({'status': 'sent', 'message': message}), 200

if __name__ == '__main__':
    app.run(debug=True)
