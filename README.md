Simple NetSuite class to interact with NetSuite REST API, SuiteQL, scripts

## Install 

```bash
pip install git+https://github.com/wb6/pynetsuite
```

### for OAuth 2.0 Client Credentials (M2M)

```bash
pip install PyJWT cryptography
```

## Usage

```python

import pynetsuite

config = {
	'netsuite_account':				'12345678-sb1',
	'netsuite_consumer_key':		'123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234',
	'netsuite_consumer_secret': 	'123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234',

	# for TBA
	'netsuite_token_id':			'123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234',
	'netsuite_token_secret':		'123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234',

	# or for OAuth 2.0 Client Credentials (M2M)
	'netsuite_certificate_id':		'1234567890abcdef',
	'netsuite_private_key_path':	'/path/to/netsuite/private/key.pem',
}



ns = pynetsuite.pynetsuite(config)

# set these env variables
# NETSUITE_ACCOUNT, NETSUITE_CONSUMER_KEY, NETSUITE_CONSUMER_SECRET
# for TBA: NETSUITE_TOKEN_ID, NETSUITE_TOKEN_SECRET 
# for OAuth 2.0 Client Credentials (M2M): NETSUITE_CERTIFICATE_ID, NETSUITE_PRIVATE_KEY_PATH
# then config parameter can be ommited
# ns = pynetsuite.pynetsuite()


suiteql_results = ns.suiteql("SELECT TOP 1 id FROM transaction")


sales_order = ns.get('/salesOrder/123456')


payload = {
	'custbody123' : 'TEST 123'
}

ns.patch('/invoice/12345',payload)


ns.script('POST',parameters={'script':1501,'deploy':1},data={"test":1})



### if you have pandas installed you can get suiteql result as pandas dataframe

ns.ss("SELECT TOP 2 * FROM transaction ORDER BY trandate DESC").df()


### if you need to batch update records

payload = [
	{
		'id': 1,
		'custbody123' : 'TEST 123'
	},
	{
		'id': 2,
		'custbody123' : 'TEST 123-2'
	},
]

ns.patch('/invoice/12345',payload)



```


