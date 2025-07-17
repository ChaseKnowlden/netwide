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
  
  def __str__(self):
    """String representation of the URL."""
    return f"URL(scheme='{self.scheme}', host='{self.host}', path='{self.path}', url='{self.url_string}')"


# Example usage
if __name__ == "__main__":
  # Test HTTP scheme parsing and host/path separation
  test_urls = [
    "http://example.com",
    "https://secure.example.com",
    "https://www.google.com/search?q=python",
    "https://api.github.com/repos/owner/repo",
    "http://localhost:8080/app/dashboard",
    "example.com",  # No scheme, should default to http
    "example.com/path/to/resource",
    "https://subdomain.example.com/path/to/file.html?param=value#section",
  ]
  
  for url_str in test_urls:
    try:
      url = URL(url_str)
      print(f"URL: {url_str}")
      print(f"  Scheme: {url.get_scheme()}")
      print(f"  Host: {url.get_host()}")
      print(f"  Path: {url.get_path()}")
      print(f"  Is Secure: {url.is_secure()}")
      print(f"  Parsed: {url}")
      print()
    except ValueError as e:
      print(f"Error parsing {url_str}: {e}")
      print()