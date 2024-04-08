import os
from dotenv import load_dotenv
load_dotenv()
secret_key = os.getenv('SECRET_KEY').encode()
# secret_key=b'\x99\x97x\n]#\x8f\xcf\xfe\xaf\xc7!\xb388\xc8\x15:x\xbb\x17\xca\xf8\xbe'
salt='otp_verication'
salt2='reset_conirmation'
add_faculty_verify = 'verify_faculty_confirmation'
update_faculty_verify = 'update_faculty_confirmation'