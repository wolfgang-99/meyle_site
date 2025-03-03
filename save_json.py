import json

# Your dictionary
text_to_translate = {
    "heading": "Welcome Back",
    "sub_heading":"Sign in to your account to continue",
    "email_label": "Email Address",
    "password_label": "Password",
    "remember": "Remember me",
    "sign_up": "Sign Up",
    "forgot": "Forgot password?",
    "log_in": "Sign In",
    "no_account": "Don't have an account?"

}

# Save the dictionary to a JSON file
with open('translate/login_translate.json', 'w', encoding='utf-8') as json_file:
    json.dump(text_to_translate, json_file, ensure_ascii=False, indent=4)

print(f"Dictionary saved to {json_file}")