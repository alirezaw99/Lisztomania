from decouple import config

Token = config('token')

print(Token)