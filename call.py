from flask import Flask, request, jsonify, send_from_directory, abort
import pandas as pd
from twilio.rest import Client
import os

app = Flask(__name__)

# Twilio configuration
account_sid = account_sid
auth_token = <auth_token>
twilio_phone_number = <twilio_number>
client = Client(account_sid, auth_token)

# Twilio Bin URL
twilio_bin_url = <twilio bin>

# Load data
data_path = <path to your dataset>
if os.path.exists(data_path):
    data = pd.read_csv(data_path)
else:
    print(f"CSV file not found at {data_path}. Please check the file path.")

@app.route('/')
def index():
    file_path = os.path.join(os.getcwd(), 'index.html')
    if os.path.exists(file_path):
        return send_from_directory(os.getcwd(), 'index.html')
    else:
        abort(404, description="Index file not found.")

@app.route('/send-calls', methods=['POST'])
def send_calls_to_male_heads():
    if data is None:
        return jsonify(["Data not loaded. Check CSV path."])

    results = []
    grouped_data = data.groupby('RationCardNumber')

    for ration_card_number, group in grouped_data:
        cardholder_row = group[group['RelationToCardHolder'] == 'Self']

        if not cardholder_row.empty:
            cardholder_gender = cardholder_row['Gender'].values[0].strip().lower()
            number_of_family_members = cardholder_row['NumberOfFamilyMembers'].values[0]
            phone_number = cardholder_row['PhoneNumber'].values[0]
            head_name = cardholder_row['MemberName'].values[0]

            if cardholder_gender == 'male' and number_of_family_members > 1:
                has_spouse = not group[(group['RelationToCardHolder'] == 'Spouse') &
                                       (group['Gender'].str.lower() == 'female')].empty

                if has_spouse:
                    try:
                        # Initiate the call with Twilio Bin URL for the custom message
                        call = client.calls.create(
                            to=phone_number,
                            from_=twilio_phone_number,
                            url=twilio_bin_url
                        )
                        results.append(f"Call initiated to {head_name} at {phone_number}")
                    except Exception as e:
                        results.append(f"Failed to call {head_name} at {phone_number}: {str(e)}")
                else:
                    results.append(f"No call made to {head_name} (no spouse available).")
            elif cardholder_gender == 'male' and number_of_family_members == 1:
                results.append(f"No call made to {head_name} (only 1 family member).")
            else:
                results.append(f"No action needed for {head_name} (already updated).")

    return jsonify(results)

@app.route('/send-messages', methods=['POST'])
def send_messages_to_update_spouse_name():
    if data is None:
        return jsonify(["Data not loaded. Check CSV path."])

    results = []
    grouped_data = data.groupby('RationCardNumber')

    for ration_card_number, group in grouped_data:
        cardholder_row = group[group['RelationToCardHolder'] == 'Self']

        if not cardholder_row.empty:
            cardholder_gender = cardholder_row['Gender'].values[0].strip().lower()
            number_of_family_members = cardholder_row['NumberOfFamilyMembers'].values[0]
            phone_number = cardholder_row['PhoneNumber'].values[0]
            head_name = cardholder_row['MemberName'].values[0]

            if cardholder_gender == 'male' and number_of_family_members > 1:
                has_spouse = not group[(group['RelationToCardHolder'] == 'Spouse') &
                                       (group['Gender'].str.lower() == 'female')].empty

                if has_spouse:
                    try:
                        # Send SMS to male cardholders to update their spouse's name
                        message = client.messages.create(
                            to=phone_number,
                            from_=twilio_phone_number,
                            body=f"Dear {head_name}, as per the new government regulation,please update the head of your household to your spouse.Visit the portal to update:https://tnpds.gov.in/"
                        )
                        results.append(f"Message sent to {head_name} at {phone_number}")
                    except Exception as e:
                        results.append(f"Failed to send message to {head_name} at {phone_number}: {str(e)}")
                else:
                    results.append(f"No message sent to {head_name} (no spouse available).")
            elif cardholder_gender == 'male' and number_of_family_members == 1:
                results.append(f"No message sent to {head_name} (only 1 family member).")
            else:
                results.append(f"No action needed for {head_name} (already updated).")

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)
