import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mysite.settings')
django.setup()

from api.models.auth import OTPRecord, User

def check_otps():
    print("--- Users ---")
    for u in User.objects.all():
        print(f"User: {u.email}, Role: {u.role}")
    
    print("\n--- OTP Records ---")
    for otp in OTPRecord.objects.all().order_by('-created_at')[:5]:
        print(f"Email: {otp.email}, Created: {otp.created_at}, Used: {otp.is_used}, Expired: {not otp.is_valid()}")

if __name__ == "__main__":
    check_otps()
