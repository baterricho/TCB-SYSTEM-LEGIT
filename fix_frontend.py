import re
import os

app_js_path = r'..\TCB-prototype\main\app.js'

if not os.path.exists(app_js_path):
    print(f"File not found: {app_js_path}")
    exit(1)

with open(app_js_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix TCB_API_BASE_URL
content = re.sub(
    r'const TCB_API_BASE_URL = \(.*?\)\.replace\(.*?\", \"\"\);',
    'const TCB_API_BASE_URL = "http://127.0.0.1:8000/api";',
    content,
    flags=re.DOTALL
)

# Fix endpoints
replacements = {
    'accounts/register/': 'auth/register-applicant/',
    'accounts/login/': 'auth/login/',
    'accounts/verify-email/': 'auth/verify-otp/',
    'accounts/verify-login-otp/': 'auth/verify-otp/',
    'accounts/resend-otp/': 'auth/resend-otp/'
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open(app_js_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully updated app.js")
