## MSALPublicClientTokenHandler Class

The `MSALPublicClientTokenHandler` class handles re-authentication using persisted refresh tokens so that authentication is only required the first time a Python script runs. You should only be asked to re-authenticate if it can't receive a token from the MSAL cache or if it doesn't have a working refresh token in storage.

**This class requires MSAL. For a token handler that doesn't require MSAL, see here: https://github.com/chris-j-akers/OneDriveTokenHandler/tree/master**

It's a pretty simple wrapper class that attempts to retrieve tokens, using methods provided by `MSAL` in this order:

1. Directly from the `MSAL` cache
2. Using a refresh-token stored locally in a SQLite3 table
3. Interactively (requires a default browser to be configured on your system)

If step 3 fails, an `assert` error should end the program.

Once a token is received, it's accompanying refresh-token is 'upserted' into a SQLite database.

SQLIte reasons:

* Yes, Python has the `dbm` module, but I kept ending up with `dumbdbm` as the implementation, and the plaintext file-clutter annoyed me.
* For `Shelve`, see above 
* [sqlitedict](https://pypi.org/project/sqlitedict/) looks promising but doesn't seem to have been updated for a couple of years.

...So, direct to SQLite3 it was. It may seem a bit fiddly to update a refresh token using SQL, but the whole thing felt more robust. Besides, there's a promising new update on the way to add SQLite3 as a backend to the `DBM` module (see details [here](https://discuss.python.org/t/new-default-preferred-dbm-backend/44228/26)). Plus, if I really wanted to, it doesn't seem like much effort to put a Python `dictionary` style adapter over the SQLite3 module, anyway, much like the top answer to this [Stack Overflow question](https://stackoverflow.com/questions/47237807/use-sqlite-as-a-keyvalue-store).

## GitHub Link

Source can be found on GitHub, here: [https://github.com/chris-j-akers/MSALPublicClientTokenHandler](https://github.com/chris-j-akers/MSALPublicClientTokenHandler)

## Example

Create a new instance of the MSALPublicClientTokenHandler and call `get_token()`.


```python
from MSALPublicClientTokenHandler import MSALPublicClientTokenHandler as TokenHandler

token_handler = TokenHandler(app_name='my-app',
                             client_id="12345678-abcd-9123-dcba-abcdef123456",
                             authority='https://login.microsoftonline.com/consumers',
                             db_filepath='./token.db')

token = token_handler.get_token()
```
### Parameters

| Parameter     | Req | Type     | Description                                                                                                                                                                                                                                                                                                                    |
|---------------|-----|----------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| app_name    | Y   | string | A name for your app. This is unique to `MSALPublicClientTokenHandler` and really just used when the refresh-token is persisted, so can actually be anything. It doesn't need to match the name of your app as it's registered in Azure, for instance.                                                                                      |
| client_id   | Y   | string | ClientId (also called AppId) of your app. This is generated once you've registered your App in Azure and can be retrieved by logging onto the Azure Portal and selecting *App Registrations*. Clicking on your registered app will show the *Application (client) Id* field in the *Essentials* section. Just copy this value. |
| authority   | Y   | string | URL end-point of the authority that will process credentials. This depends on the way your app is configured in Azure. The example, above, uses the `/consumers` end-point which means the app is configured for accounts registered under someone's personal email address.                                                   |
| db_filepath | N   | string | (*optional*) Specifies the location/name of the SQLite3 db database that stores the refresh token. Defaults to `./token.db`.                                                                                                                                                                                                   |                                                                                                                                                                   |
