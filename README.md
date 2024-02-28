Example:

```python
from MSALTokenHandler import MSALTokenHandler

token_handler = MSALTokenHandler(app_name="my-app",
                                 client_id="12345678-abcd-9123-dcba-abcdef123456",
                                 authority='https://login.microsoftonline.com/consumers')

# If this is the first time the program is being run, or the persistence db has been deleted, you will be prompted to login to your MSFT account. You must ensure a default browser is enabled on your system.
# 
# Subsequent run's should simply retrieve a token, even after a restart.
token = token_handler.get_token()
```
