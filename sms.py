import africastalking

# TODO: Initialize Africa's Talking

africastalking.initialize(
    username='[YOUR_USERNAME_GOES_HERE]',
    api_key='[YOUR_API_KEY_GOES_HERE]'
)

sms = africastalking.SMS

class SMS():

    def send(self):
        
        # Set the numbers in international format
        recipients = ["+254722123123"]
        # Set your message
        message = "Hey AT Ninja!";
        # Set your shortCode or senderId
        sender = "XXYYZZ"
        try:
            response = self.sms.send(message, recipients, sender)
            print (response)
        except Exception as e:
            print (f'Houston, we have a problem: {e}')

    