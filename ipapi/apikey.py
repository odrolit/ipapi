

tokens = {
  't': {
    'uid': 'ip.our.net',
    'provider_ipv4': ['10.0.0.0/22', '10.0.33.0/24'],
    'provider_ipv6': []
  }
}



def apikey_auth(token, required_scopes):
  return tokens.get(token, None)


