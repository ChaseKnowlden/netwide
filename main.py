import socket
import ssl

class URL:
  def __init__(self, url_string=None):
    self.url_string = url_string
    self.scheme = None
    self.host = None
    self.port = None
    self.path = None
    self.query = None
    self.fragment = None
    
    if url_string:
      self.parse()
  
  def parse(self):
    """Parse the URL string into its components."""
    if not self.url_string:
      return
    
    # Parse the scheme
    self.scheme = self.parse_scheme()
    
    # Parse host and path
    self.host, self.path = self.parse_host_and_path()
    
  def parse_scheme(self):
    """Parse and validate the HTTP scheme from the URL."""
    if not self.url_string:
      return None
    
    # Find the scheme separator
    scheme_separator = "://"
    scheme_index = self.url_string.find(scheme_separator)
    
    if scheme_index == -1:
      # No scheme found, assume http
      return "http"
    
    scheme = self.url_string[:scheme_index].lower()
    
    # Validate that it's a supported HTTP scheme
    if scheme in ["http", "https"]:
      return scheme
    else:
      raise ValueError(f"Unsupported scheme: {scheme}. Only 'http' and 'https' are supported.")
  
  def parse_host_and_path(self):
    """Parse and separate the host from the path."""
    if not self.url_string:
      return None, None
    
    # Remove scheme if present
    url_without_scheme = self.url_string
    scheme_separator = "://"
    scheme_index = self.url_string.find(scheme_separator)
    
    if scheme_index != -1:
      url_without_scheme = self.url_string[scheme_index + len(scheme_separator):]
    
    # Find the first slash that separates host from path
    first_slash_index = url_without_scheme.find('/')
    
    if first_slash_index == -1:
      # No path found, entire string is the host
      host = url_without_scheme
      path = "/"  # Default path
    else:
      # Split at the first slash
      host = url_without_scheme[:first_slash_index]
      path = url_without_scheme[first_slash_index:]
    
    # Handle query parameters and fragments in the path
    # Remove query and fragment from host (in case there's no path)
    if '?' in host:
      host = host.split('?')[0]
    if '#' in host:
      host = host.split('#')[0]
    
    return host, path
  
  def is_secure(self):
    """Check if the URL uses HTTPS (secure) scheme."""
    return self.scheme == "https"
  
  def get_scheme(self):
    """Get the parsed scheme."""
    return self.scheme
  
  def get_host(self):
    """Get the parsed host."""
    return self.host
  
  def get_path(self):
    """Get the parsed path."""
    return self.path
  
  def download(self):
    """Download the web page content from the URL using raw sockets."""
    return self.request("GET")
  
  def send(self, data, content_type="application/x-www-form-urlencoded"):
    """Send data to the server using POST request."""
    return self.request("POST", data, content_type)
  
  def request(self, method="GET", data=None, content_type="application/x-www-form-urlencoded"):
    """Make an HTTP request to the server using raw sockets."""
    if not self.url_string:
      raise ValueError("No URL string provided")
    
    # Use parsed components
    host = self.host
    path = self.path if self.path else "/"
    port = 443 if self.scheme == "https" else 80
    
    # Handle port in host (e.g., localhost:8080)
    if ":" in host:
      host, port_str = host.split(":", 1)
      port = int(port_str)
    
    try:
      # Create socket connection
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      sock.settimeout(10)  # 10 second timeout
      
      # Wrap with SSL for HTTPS
      if self.scheme == "https":
        context = ssl.create_default_context()
        sock = context.wrap_socket(sock, server_hostname=host)
      
      # Connect to the server
      sock.connect((host, port))
      
      # Construct HTTP request
      request = f"{method} {path} HTTP/1.1\r\n"
      request += f"Host: {host}\r\n"
      request += "User-Agent: Mozilla/5.0 (Python Socket Browser) AppleWebKit/537.36\r\n"
      request += "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8\r\n"
      request += "Accept-Language: en-US,en;q=0.5\r\n"
      request += "Accept-Encoding: identity\r\n"  # Don't request compression
      request += "Connection: close\r\n"
      
      # Add data for POST requests
      if data and method == "POST":
        if isinstance(data, dict):
          # Convert dict to URL-encoded form data
          encoded_data = "&".join([f"{key}={value}" for key, value in data.items()])
        else:
          encoded_data = str(data)
        
        request += f"Content-Type: {content_type}\r\n"
        request += f"Content-Length: {len(encoded_data)}\r\n"
        request += "\r\n"
        request += encoded_data
      else:
        request += "\r\n"
      
      # Send request
      sock.send(request.encode('utf-8'))
      
      # Read response using makefile for better handling
      response_file = sock.makefile('rb')
      
      # Read status line
      status_line = response_file.readline().decode('utf-8', errors='ignore').strip()
      
      # Read headers
      headers = {}
      while True:
        header_line = response_file.readline().decode('utf-8', errors='ignore').strip()
        if not header_line:  # Empty line indicates end of headers
          break
        if ':' in header_line:
          key, value = header_line.split(':', 1)
          headers[key.strip()] = value.strip()
      
      # Read body based on Content-Length or until connection closes
      body = ""
      if 'Content-Length' in headers:
        content_length = int(headers['Content-Length'])
        body_bytes = response_file.read(content_length)
        body = body_bytes.decode('utf-8', errors='ignore')
      elif headers.get('Transfer-Encoding', '').lower() == 'chunked':
        # Handle chunked encoding
        body = self._read_chunked_response(response_file)
      else:
        # Read until connection closes
        body_bytes = response_file.read()
        body = body_bytes.decode('utf-8', errors='ignore')
      
      response_file.close()
      sock.close()
      
      # Extract status code
      status_parts = status_line.split()
      if len(status_parts) >= 2:
        status_code = int(status_parts[1])
      else:
        status_code = 0
      
      return {
        'content': body,
        'status_code': status_code,
        'headers': headers,
        'url': f"{self.scheme}://{self.host}{self.path}",
        'method': method
      }
      
    except socket.timeout:
      raise Exception("Connection timeout")
    except socket.gaierror as e:
      raise Exception(f"DNS resolution failed: {e}")
    except ConnectionRefusedError:
      raise Exception("Connection refused")
    except Exception as e:
      raise Exception(f"Download failed: {str(e)}")
  
  def _read_chunked_response(self, response_file):
    """Read chunked transfer encoding using makefile."""
    body = ""
    
    while True:
      # Read chunk size line
      size_line = response_file.readline().decode('utf-8', errors='ignore').strip()
      if not size_line:
        break
      
      # Parse chunk size (hexadecimal)
      try:
        chunk_size = int(size_line, 16)
      except ValueError:
        break
      
      if chunk_size == 0:
        # End of chunks
        break
      
      # Read chunk data
      chunk_data = response_file.read(chunk_size)
      body += chunk_data.decode('utf-8', errors='ignore')
      
      # Read the trailing CRLF after chunk data
      response_file.readline()
    
    return body
  
  def _decode_chunked(self, body):
    """Decode chunked transfer encoding."""
    decoded = ""
    lines = body.split('\r\n') if '\r\n' in body else body.split('\n')
    i = 0
    
    while i < len(lines):
      # Get chunk size
      try:
        chunk_size = int(lines[i], 16)
      except (ValueError, IndexError):
        break
      
      if chunk_size == 0:
        break
      
      # Get chunk data
      i += 1
      if i < len(lines):
        chunk_data = lines[i]
        decoded += chunk_data[:chunk_size]
      
      i += 1
    
    return decoded
  
  def __str__(self):
    """String representation of the URL."""
    return f"URL(scheme='{self.scheme}', host='{self.host}', path='{self.path}', url='{self.url_string}')"


# Example usage
if __name__ == "__main__":
  # Test GET requests
  print("=== Testing GET requests ===")
  get_test_urls = [
    "http://example.com",
    "https://httpbin.org/get",
  ]
  
  for url_str in get_test_urls:
    try:
      url = URL(url_str)
      print(f"URL: {url_str}")
      print(f"  Scheme: {url.get_scheme()}")
      print(f"  Host: {url.get_host()}")
      print(f"  Path: {url.get_path()}")
      
      # Download the content
      print(f"  Downloading...")
      result = url.download()
      print(f"  Method: {result['method']}")
      print(f"  Status: {result['status_code']}")
      print(f"  Content-Type: {result['headers'].get('Content-Type', 'Unknown')}")
      print(f"  Content Length: {len(result['content'])} characters")
      print(f"  First 200 characters: {result['content'][:200]}...")
      print()
      
    except Exception as e:
      print(f"Error with {url_str}: {e}")
      print()
  
  # Test POST requests
  print("=== Testing POST requests ===")
  post_test_urls = [
    "https://httpbin.org/post",
    "https://httpbin.org/anything",
  ]
  
  for url_str in post_test_urls:
    try:
      url = URL(url_str)
      print(f"URL: {url_str}")
      
      # Send form data
      form_data = {
        "name": "Python Browser",
        "version": "1.0",
        "message": "Hello from custom socket client!"
      }
      
      print(f"  Sending POST data: {form_data}")
      result = url.send(form_data)
      print(f"  Method: {result['method']}")
      print(f"  Status: {result['status_code']}")
      print(f"  Content-Type: {result['headers'].get('Content-Type', 'Unknown')}")
      print(f"  Content Length: {len(result['content'])} characters")
      print(f"  First 500 characters: {result['content'][:500]}...")
      print()
      
    except Exception as e:
      print(f"Error with {url_str}: {e}")
      print()
  
  # Test sending JSON data
  print("=== Testing JSON POST request ===")
  try:
    url = URL("https://httpbin.org/post")
    json_data = '{"user": "john", "age": 30, "active": true}'
    
    print(f"  Sending JSON data: {json_data}")
    result = url.send(json_data, content_type="application/json")
    print(f"  Method: {result['method']}")
    print(f"  Status: {result['status_code']}")
    print(f"  Content-Type: {result['headers'].get('Content-Type', 'Unknown')}")
    print(f"  Response: {result['content'][:800]}...")
    print()
    
  except Exception as e:
    print(f"Error with JSON POST: {e}")
    print()