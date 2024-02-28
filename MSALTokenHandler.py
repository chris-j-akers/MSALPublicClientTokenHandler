from msal import PublicClientApplication
import sqlite3
import logging

logger = logging.getLogger(__name__)

class MSALTokenHandler:
    
    def __init__(self, app_name, client_id, authority, scopes=['User.Read'], db_filepath='./tokens.db') -> None:
        """
        Handles retrieving tokens from MSAL and persists the 
        associated refresh token to a `SqLite` db for future use.

        Args:
            `app_name` (`string`)   : Name of your application (used to pull the 
            token from storage, does not have to match the name in Azure)
            `client_id` (`string`)  : The app_id/client_id of your registered app 
            taken from the Azure portal
            `authority` (`string`)  : The URL end-point of the Azure authority provides tokens for your app (see [Azure documentation](https://learn.microsoft.com/en-us/entra/identity-platform/msal-client-application-configuration))
            `scopes` (`[string]`)   : List of scopes required, defaults to 'User.Read' (see [Azure documentation](https://learn.microsoft.com/en-us/graph/permissions-reference))
            `db_filepath` (`string`): The path and name of the `SQLite3` database 
            used to store refresh tokens (defaults to './tokens.db')

        Returns:
            `MSALTokenHandler`      : A new `MSALTokenHandler` object
        """
        self._logger = logger.getChild(__class__.__name__)
        self._app_name = app_name
        self._scopes = scopes
        self._account = ''
        self._pca = PublicClientApplication(client_id=client_id, authority=authority, client_credential=None)
        self._initialise_token_db(db_filepath=db_filepath)

    def _initialise_token_db(self, db_filepath):
        self._logger.debug('Initialising token_db')
        self._connection = sqlite3.connect(db_filepath)
        self._connection.autocommit = True
        cursor = self._connection.cursor()
        cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name="token"')
        if len(cursor.fetchall()) == 0:
            self._logger.debug('token table not found, creating')
            self._create_token_db()
            return
        self._logger.debug('token table found in db')
        cursor.close()

    def _create_token_db(self):
        cursor = self._connection.cursor()
        cursor.execute('CREATE TABLE token (app_name TEXT, refresh_token TEXT, PRIMARY KEY (app_name))')
        self._logger.debug('Created token table')
        cursor.close()

    def _get_refresh_token_from_db(self):
        cursor = self._connection.cursor()
        rows = cursor.execute('SELECT refresh_token FROM token where app_name = ?', (self._app_name,)).fetchall()
        if len(rows) == 0:
            self._logger.debug('No refresh_tokens found in token_db, setting empty')
            return ''
        else:
            self._logger.debug(f'Refresh token found in db')
            cursor.close()
            return rows[0][0]

    def _upsert_refresh_token_in_db(self, refresh_token):
        self._logger.debug('Updating refresh token in token_db')
        cursor = self._connection.cursor()
        cursor.execute('INSERT INTO token (app_name, refresh_token) VALUES (?, ?) ON CONFLICT (app_name) DO UPDATE SET refresh_token = ?;', (self._app_name, refresh_token, refresh_token))
        cursor.close()

    def get_token(self):
        """
        Return a new token fetched using the MSAL `PublicClientApplication`
        class.

        Attempts are made in the following order:

        1. Silently, using the `MSAL` built-in token cache
        2. With a refresh token loaded from storage
        3. Interactively by presenting a browser with the MSFT login page 
        (assumes a default browser is set)

        If none of these methods succeed, the function will fail fast with an 
        assert error.

        Once a token is retrieved, its associated refresh token is persisted 
        to the Sqlite DB for future use. Subsequent attempts will always try 
        this token if the MSAL cache is empty, avoiding the need to 
        re-authenticate. This is even if the program has been stopped entirely
        and restarted at a later time.

        Returns:
            `string` : An `MSAL` access token
        """
        self._logger.debug('get_token() called, running waterfall')

        # MSAL Cache
        if self._pca.get_accounts() != []:
            account = self._pca.get_accounts()[0]
            self._logger.debug(f'Found cached account for {account["username"]}, acquiring silently')    
            token_data = self._pca.acquire_token_silent(account=self._pca.get_accounts()[0], scopes=self._scopes)
            if 'error' not in token_data:
                # There is no refresh token sent back with this one as it's the same as the previous token, anyway
                return token_data['access_token']
            else:
                self._logger.debug(f'error from acquire_token_silent():  {token_data["error"]} | {token_data["error_description"]}')

        # Refresh Token
        refresh_token = self._get_refresh_token_from_db()
        if refresh_token != '':
            self._logger.debug('trying refresh token')
            token_data = self._pca.acquire_token_by_refresh_token(refresh_token=refresh_token, scopes=self._scopes)
            if 'error' not in token_data:
                self._upsert_refresh_token_in_db(token_data['refresh_token'])
                return token_data['access_token']
            else:
                self._logger.debug('error from acquire_token_by_refresh_token():  {token_data["error"]} | {token_data["error_description"]}')

        # Interactive
        token_data = self._pca.acquire_token_interactive(scopes=self._scopes)

        # We should fail-fast if there's an error at this point. It's over, man.
        assert 'error' not in token_data, f'unable to get token, error from acquire_token_by_refresh_token():  {token_data["error"]} | {token_data["error_description"]}'
        
        # We good.
        self._upsert_refresh_token_in_db(token_data['refresh_token'])
        return token_data['access_token']
