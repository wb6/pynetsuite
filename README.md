Simple NetSuite class to interact with NetSuite REST API, SuiteQL, scripts

## Install 

```bash
pip install git+https://github.com/wb6/pynetsuite
```

## Usage

```python

import pynetsuite

config = {
	'netsuite_account':         '12345678-sb1',
    	'netsuite_consumer_key':    '123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234',
	'netsuite_consumer_secret': '123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234',
	'netsuite_token_id':        '123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234',
	'netsuite_token_secret':    '123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234',
}



ns = pynetsuite.pynetsuite(config)

suiteql_results = ns.suiteql("SELECT TOP 1 id FROM transaction")


sales_order = ns.get('/salesOrder/123456')


payload = {
	'custbody123' : 'TEST 123'
}

ns.patch('/invoice/12345',payload)


ns.script('POST',parameters={'script':1501,'deploy':1},data={"test":1})


```

### suiteql result as pandas dataframe

if you have pandas installed you can get suiteql result as pandas dataframe

```python

ns.ss("SELECT TOP 2 * FROM transaction ORDER BY trandate DESC").df()

```


