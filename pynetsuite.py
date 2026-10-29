import json, urllib, random, math, time, base64, hmac, re, os
from urllib import parse, request
from urllib.parse import quote, urlencode


class pynetsuite:
	def __init__(self,config={}):
		self._version = '1.0'
		self._signature_method = 'HMAC-SHA256'
		self._netsuite_account = os.getenv('NETSUITE_ACCOUNT') or config.get('netsuite_account')
		if not self._netsuite_account:
			raise ValueError("NETSUITE_ACCOUNT missing.")

		self._netsuite_consumer_key = 		os.getenv('NETSUITE_CONSUMER_KEY') 		or config.get('netsuite_consumer_key','')     # Consumer Key / Client ID
		self._netsuite_consumer_secret = 	os.getenv('NETSUITE_CONSUMER_SECRET') 	or config.get('netsuite_consumer_secret','')  # Consumer Secret / Client Secret

		self._netsuite_token_id = 			os.getenv('NETSUITE_TOKEN_ID') 			or config.get('netsuite_token_id','') 
		self._netsuite_token_secret = 		os.getenv('NETSUITE_TOKEN_SECRET') 		or config.get('netsuite_token_secret','')
		# OR
		self.certificate_id = 				os.getenv('NETSUITE_CERTIFICATE_ID')	or config.get('netsuite_certificate_id','')
		self.private_key_path = 			os.getenv('NETSUITE_PRIVATE_KEY_PATH')	or config.get('netsuite_private_key_path','')


		self._base_url = f"https://{self._netsuite_account}.suitetalk.api.netsuite.com/services/rest/record/v1"
		self._base_url_suiteql = f"https://{self._netsuite_account}.suitetalk.api.netsuite.com/services/rest/query/v1"
		self._base_url_script = f"https://{self._netsuite_account}.restlets.api.netsuite.com/app/site/hosting/restlet.nl"
		self._base_url_job = f"https://{self._netsuite_account}.suitetalk.api.netsuite.com/services/rest/async/v1"
		
		self._realm = self._netsuite_account.replace("-","_").upper()
		self.token_url = f"https://{self._realm}.suitetalk.api.netsuite.com/services/rest/auth/oauth2/v1/token"


		self.scope = os.getenv("NETSUITE_SCOPE", "rest_webservices")
		self._access_token = None
		self._expires_at = 0

	def _new_access_token(self):
		# python3 -m pip install PyJWT cryptography
		import jwt
		now = int(time.time())

		with open(self.private_key_path, "rb") as key_file:
			private_key = key_file.read()

		assertion = jwt.encode(
			{
				"iss": self._netsuite_consumer_key,
				"aud": self.token_url,
				"iat": now,
				"exp": now + 300,
				"scope": self.scope.split(","),
			},
			private_key,
			algorithm="PS256",
			headers={"typ": "JWT", "kid": self.certificate_id},
		)


		data = urlencode({
			"grant_type": "client_credentials",
			"client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
			"client_assertion": assertion,
		}).encode("utf-8")

		req = urllib.request.Request(
			self.token_url,
			data=data,
			method="POST",
		)

		with urllib.request.urlopen(req, timeout=30) as response:
			payload = json.loads(response.read().decode("utf-8"))


		self._access_token = payload["access_token"]
		# Refresh a little early rather than waiting for expiry.
		self._expires_at = now + int(payload.get("expires_in", 3600)) - 60

	def access_token(self):
		if not self._access_token or time.time() >= self._expires_at:
			self._new_access_token()
		return self._access_token

	def _b64url(self,data):
		return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

	def _sign(self, http_method, path='', parameters={}):
		base_url = self._base_url
		if(path == '/suiteql'): base_url = self._base_url_suiteql
		if(path == '/script'): 
			base_url = self._base_url_script
			path = ''

		# print(path)
		if( len(path) > 3 and len(path.split("/")) > 1 and path.split("/")[1] == 'job'):
			# if(parameters.get('jobid') == None):
				# return {'error':'Missing jobid'}
			# base_url = self._base_url_job + "/" + str(parameters.get('jobid'))
			base_url = self._base_url_job
			if(parameters.get('jobid') != None):
				base_url = self._base_url_job + "/job/" + str(parameters.get('jobid'))
				del(parameters['jobid'])
				path = ''
		# print(base_url)
				
		http_method = http_method.upper()
		nonce = "".join(random.sample("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",20))
		timestamp = math.floor(time.time())

		oauth_params = {
			"oauth_consumer_key"			: self._netsuite_consumer_key,
			"oauth_nonce" 	 			    : nonce,
			"oauth_signature_method"		: self._signature_method,
			"oauth_timestamp"				: timestamp,
			"oauth_token" 	 			    : self._netsuite_token_id,
			"oauth_version" 	 		    : self._version,
		}

		parameters_sorted = {key:parameters[key] for key in sorted(parameters.keys())}
		url = base_url + path + "?" + urllib.parse.urlencode(parameters_sorted)

		all_parameters = parameters_sorted
		all_parameters.update(oauth_params)

		all_parameters_sorted = {key:all_parameters[key] for key in sorted(all_parameters.keys())}
		all_parameters_string = urllib.parse.urlencode(all_parameters_sorted,quote_via=urllib.parse.quote)

		# print(all_parameters_string)

		# base_string = http_method + '&' + urllib.parse.quote(base_url + path, safe='') + "&" + urllib.parse.quote(all_parameters_string)
		base_string = (http_method + '&' + urllib.parse.quote(base_url + path, safe='') + '&' + urllib.parse.quote(all_parameters_string, safe='') )

		# key = self._netsuite_consumer_secret + '&' + self._netsuite_token_secret
		key = ( urllib.parse.quote(self._netsuite_consumer_secret, safe='') + '&'+ urllib.parse.quote(self._netsuite_token_secret, safe='') )

		signature = urllib.parse.quote( base64.b64encode( (hmac.new(bytes(key,'utf-8'), bytes(base_string,'utf-8'), 'sha256').digest() )).decode() )

		headers = {
			"Authorization": f'OAuth realm="{self._realm}",oauth_consumer_key="{self._netsuite_consumer_key}",oauth_token="{self._netsuite_token_id}",oauth_signature_method="HMAC-SHA256",oauth_timestamp="{timestamp}",oauth_nonce="{nonce}",oauth_version="{self._version}",oauth_signature="{signature}"',
			"Cookie": "NS_ROUTING_VERSION=LAGGING",
			"Content-Type" : "application/json"
		}

		# print(base_string)
		# print

		return (url,headers)

	def rest(self, http_method='GET', path=None, parameters={}, data=None, run_async=False):

		if path == None:
			return path
		if http_method == 'POST' and data == None:
			return data

		if type(data) is dict:
			post_data = bytes(json.dumps(data),'utf-8')  
		elif type(data) is list:
			data = {'items': data }
			post_data = bytes(json.dumps(data),'utf-8')  
		elif data == None:
			post_data = None
		else:
			post_data = bytes(data,'utf-8')

		url=''
		headers={}

		if self.certificate_id != '' and self.private_key_path != '':
			base_url = self._base_url
			if(path == '/suiteql'): base_url = self._base_url_suiteql
			if(path == '/script'): 
				base_url = self._base_url_script
				path = ''
			url = base_url + path + "?" + urllib.parse.urlencode(parameters)
			headers['Authorization'] = f"Bearer {self.access_token()}"
		else:
			(url,headers) = self._sign(http_method, path, parameters)

		if http_method == 'POST' and type(data) is dict and len(data) == 1 and type(data.get('items')) is list:
			headers['content-type'] = 'application/vnd.oracle.resource+json; type=collection'
			headers['Prefer'] = 'respond-async'
		
		if run_async: headers['Prefer'] = 'respond-async'

		req = urllib.request.Request(url, data=post_data, headers=headers, method=http_method)

		try :
			with urllib.request.urlopen(req) as response:
				response_body = response.read().decode('utf-8')

				if len(response_body) == 0:
					return {'Location': response.getheader('Location')}

				return json.loads(response_body)
		except urllib.error.HTTPError as e :
				response = e.fp.read()
				return json.loads(response)
		except:
			return {}

		return {}


	def rest_old(self, http_method='GET', path=None, parameters={}, data=None, run_async=False):

		if path == None:
			return path
		if http_method == 'POST' and data == None:
			return data

		if type(data) is dict:
			post_data = bytes(json.dumps(data),'utf-8')  
		elif type(data) is list:
			data = {'items': data }
			post_data = bytes(json.dumps(data),'utf-8')  
		elif data == None:
			post_data = None
		else:
			post_data = bytes(data,'utf-8')

		(url,headers) = self._sign(http_method, path, parameters)

		if http_method == 'POST' and type(data) is dict and len(data) == 1 and type(data.get('items')) is list:
			headers['content-type'] = 'application/vnd.oracle.resource+json; type=collection'
			headers['Prefer'] = 'respond-async'
		
		if run_async: headers['Prefer'] = 'respond-async'

		req = urllib.request.Request(url, data=post_data, headers=headers, method=http_method)

		try :
			with urllib.request.urlopen(req) as response:
				response_body = response.read().decode('utf-8')

				if len(response_body) == 0:
					return {'Location': response.getheader('Location')}

				return json.loads(response_body)
		except urllib.error.HTTPError as e :
				response = e.fp.read()
				return json.loads(response)
		except:
			return {}

		return {}

	def suiteql(self,q=None,parameters={}):
		if q== None:
			return q

		url=''
		headers={}

		if self.certificate_id != '' and self.private_key_path != '':
			print("new auth")
			base_url = self._base_url_suiteql
			path='/suiteql'

			url = base_url + path + "?" + urllib.parse.urlencode(parameters)
			headers['Authorization'] = f"Bearer {self.access_token()}"
		else:
			(url,headers) = self._sign(http_method='POST', path='/suiteql', parameters=parameters)


		data = bytes( '{"q":"' + re.sub(r'\r?\n|\r|\t', " ",re.sub(r"\-\-.*","",q,flags=re.M) ).strip() + '"}','utf-8')

		req = urllib.request.Request(url,method='POST')
		for header in headers:
			req.add_header(header, headers[header])
		req.add_header("Content-Type", "application/json")
		req.add_header('Prefer', 'transient')

		with urllib.request.urlopen(req,data=data) as f:
			headers = f.headers
			response = f.read().decode("utf-8") # May be empty
			if response == '':
				return headers

		result = json.loads(response)

		if(result.get('hasMore') == True):
			for link in result.get('links'):
				if(link['rel'] == 'next'):
					params = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(link['href']).query))
			response_sub = self.suiteql(q=q,parameters=params)
			if response_sub.get('items') is not None:
				result['items'] +=  response_sub['items'] 
						
				
		return result

	def script(self,http_method='GET',path='/script',parameters={},data=None):
		return self.rest(http_method,path,parameters=parameters,data=data)

	def get(self,path=None,parameters={},data=None):
		return self.rest('GET',path,parameters,data)

	def post(self,path=None,data=None,run_async=False,batch=False):
		return self.rest('POST',path,{},data,run_async=run_async)

	def patch(self,path=None,data=None,parameters={},run_async=False):
		return self.rest(http_method='PATCH',path=path,parameters=parameters,data=data,run_async=run_async)

	def put(self,path=None,data=None,run_async=False):
		return self.rest('PUT',path,{},data,run_async=run_async)

	def delete(self,path=None,data=None,run_async=False):
		return self.rest('DELETE',path,{},data,run_async=run_async)

	def getJobStatus(self,jobid):
		return self.rest('GET',path='/job',parameters={'jobid':jobid})

	def ss(self,sql):
		if sql[0:1] == "/":
			return self.Result(self.get(sql))
		return self.Result(self.suiteql(sql))

	class Result:
		def __init__(self, data):
			self.data = data

		def json(self):
			return self.data

		def df(self):
			import pandas as pd
			return pd.DataFrame(self.data.get('items') or self.data.get('o:errorDetails')).drop(columns=['links'], errors='ignore')

		def get(self,param):
			return self.data.get(param)

		def __repr__(self):
			return repr(self.json())

		def __call__(self):
			return self.json()

