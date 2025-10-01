import socket
import ssl
import sys
import os
import base64
import time
import gzip
import tkinter
import tkinter.font

# Command to run: python Browser.py https://example.org

# Global dictionaries to manage open sockets and cached responses
open_sockets = {}  # Stores active socket connections for reuse
cached_responses = {}  # Stores HTTP responses with their expiry times

# GUI constants for layout and rendering
HSTEP, VSTEP = 13, 18  # Horizontal and vertical spacing for text
SCROLL_STEP = 100  # Pixels to scroll per step
SCROLLBAR_WIDTH = 12  # Width of the scrollbar

# Redirect control variables
redirects_number = 0  # Tracks number of redirects
redirects_limit = 10  # Maximum allowed redirects to prevent loops

class URL:
    def __init__(self, url):
        # Initialize URL parsing with default flags
        self.view_source = False  # Flag to display source code
        self.right_to_left_text = False  # Flag for right-to-left text rendering
        if url.startswith("view-source:"):
            # Handle view-source scheme by parsing inner URL
            self.view_source = True
            url = url[12:]  # Remove "view-source:" prefix
            inner_url = URL(url)  # Recursively parse inner URL
            self.scheme = inner_url.scheme
            self.host = inner_url.host
            self.port = inner_url.port
            self.path = inner_url.path
            self.mime_type = getattr(inner_url, 'mime_type', None)
            self.is_base64 = getattr(inner_url, 'is_base64', False)
            self.data = getattr(inner_url, 'data', None)
        elif url.startswith("rlt:"):
            # Handle right-to-left text scheme
            self.right_to_left_text = True
            url = url[4:]  # Remove "rlt:" prefix
            inner_url = URL(url)  # Recursively parse inner URL
            self.scheme = inner_url.scheme
            self.host = inner_url.host
            self.port = inner_url.port
            self.path = inner_url.path
        else:
            if url.startswith("data:"):
                # Handle data scheme for inline content
                self.scheme = "data"
                self.host = ""
                self.port = None
                self.path = ""
                url = url[5:]  # Remove "data:" prefix
            else:
                # Handle standard URLs or about:blank
                if "://" not in url or url == "about:blank":
                    self.host = ""
                    self.port = None
                    self.path = "about:blank"
                    return
                self.scheme, url = url.split("://", 1)  # Split scheme and rest of URL
            # Validate supported schemes
            assert self.scheme in ["http", "https", "file", "data"]
            if self.scheme in ["http", "https"]:
                # Set default ports for HTTP/HTTPS
                self.port = 80 if self.scheme == "http" else 443
                if "/" not in url:
                    url = url + "/"  # Ensure path exists
                self.host, url = url.split("/", 1)  # Split host and path
                self.path = "/" + url
                if ":" in self.host:
                    # Handle custom port if specified
                    self.host, port = self.host.split(":", 1)
                    self.port = int(port)
            elif self.scheme == "file":
                # Handle file scheme for local files
                self.host = ""
                self.port = None
                self.path = url
            elif self.scheme == "data":
                # Handle data scheme with MIME type and content
                self.host = ""
                self.port = None
                if "," not in url:
                    raise ValueError("URL data inválida: falta vírgula")
                mime_type, data = url.split(",", 1)
                self.mime_type = mime_type or "text/plain"
                self.is_base64 = ";base64" in mime_type
                if self.is_base64:
                    self.mime_type = self.mime_type.replace(";base64", "")
                    try:
                        self.data = base64.b64decode(data).decode("utf8")
                    except Exception as e:
                        raise ValueError(f"Erro ao decodificar Base64: {e}")
                else:
                    self.data = data

    def request(self, user_agent="Vares Browser"):
        # Access global redirect variables
        global redirects_limit, redirects_number
        # Handle about:blank URL
        if self.path == "about:blank":
            return "<>"
        # Read local files for file scheme
        if self.scheme == "file":
            file_path = self.path
            if os.name == "nt" and file_path.startswith("/"):
                file_path = file_path[1:]  # Fix path for Windows
            try:
                with open(file_path, "r", encoding="utf8") as f:
                    return f.read()
            except FileNotFoundError:
                raise ValueError(f"File not found: {file_path}")
            except Exception as e:
                raise ValueError(f"Error while reading file {file_path}: {e}")
        # Return inline data for data scheme
        if self.scheme == "data":
            return self.data
        # Check cache for existing response
        cache_key = (self.scheme, self.host, self.port, self.path)
        cached = cached_responses.get(cache_key)
        if cached:
            content, expiry = cached
            if expiry is None or time.time() < expiry:
                print(f"Using cached response for {self.scheme}://{self.host}{self.path}")
                return content.decode("utf8")
            else:
                print(f"Cache expired for {self.scheme}://{self.host}{self.path}")
                del cached_responses[cache_key]
        # Reuse or create new socket connection
        socket_key = (self.host, self.port)
        s = open_sockets.get(socket_key)
        if s is None:
            s = socket.socket(
                family=socket.AF_INET,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
            )
            s.settimeout(20)  # Set connection timeout
            try:
                print(f"Connecting to '{self.scheme + '://' + self.host + self.path}' in port {self.port}...")
                s.connect((self.host, self.port))
            except socket.timeout:
                s.close()
                raise ConnectionError("Error connecting: Timeout")
            except socket.gaierror as e:
                raise ConnectionError(f"Error resolving host {self.host}: {e}")
            except Exception as e:
                raise ConnectionError(f"Error connecting: {e}")
            if self.scheme == "https":
                ctx = ssl.create_default_context()
                try:
                    print("Initiating SSL handshake...")
                    s = ctx.wrap_socket(s, server_hostname=self.host)
                except ssl.SSLError as e:
                    s.close()
                    raise ConnectionError(f"SSL Error: {e}")
            open_sockets[socket_key] = s
        # Build HTTP request with headers
        headers = [
            f"Host: {self.host}\r\n",
            "Connection: keep-alive\r\n",
            f"User-Agent: {user_agent}\r\n",
            "Accept-Encoding: gzip\r\n",
            "\r\n"
        ]
        request = f"GET {self.path} HTTP/1.1\r\n"
        for header in headers:
            request += header
        s.send(request.encode("utf8"))  # Send request to server
        # Read response
        response = s.makefile("rb", newline=b"\r\n")
        statusline = response.readline().decode("utf8").strip()
        if not statusline:
            s.close()
            open_sockets.pop(socket_key, None)
            raise ValueError("No server answer")
        try:
            version, status, explanation = statusline.split(" ", 2)
            status = int(status)
        except ValueError:
            s.close()
            open_sockets.pop(socket_key, None)
            raise ValueError(f"Status line invalid: {statusline}")
        # Parse response headers
        response_headers = {}
        while True:
            line = response.readline().decode("utf8").strip()
            if line == "":
                break
            try:
                header, value = line.split(":", 1)
                response_headers[header.casefold()] = value.strip()
            except ValueError:
                print(f"Invalid header ignored: '{line}'")
                continue
        # Handle redirects
        if redirects_number <= redirects_limit and status in (301, 302, 303, 307, 308):
            redirects_number += 1
            new_url = response_headers.get("location", "").strip()
            if not new_url:
                s.close()
                open_sockets.pop(socket_key, None)
                raise ValueError(f"Redirect response missing 'Location' header")
            if "://" in new_url:
                new_url = new_url
            elif new_url[:1] == "/":
                new_url = self.scheme + "://" + self.host + new_url
            else:
                new_url = self.scheme + "://" + self.host + "/" + new_url
            if response_headers.get("Connection", "").lower() == "close":
                s.close()
                open_sockets.pop(socket_key, None)
            print(f"Redirecting to: '{new_url}'...")
            return URL(new_url).request(user_agent)
        if redirects_number >= redirects_limit:
            s.close()
            open_sockets.pop(socket_key, None)
            raise ValueError("Redirects limit reached")
        # Read response body
        content = b""
        if "transfer-encoding" in response_headers and response_headers["transfer-encoding"].strip().lower() == "chunked":
            print("Chunked encoding detected")
            while True:
                chunk_size = response.readline().decode("utf8").strip()
                if not chunk_size:
                    break
                try:
                    chunk_size = int(chunk_size, 16)
                except ValueError:
                    s.close()
                    open_sockets.pop(socket_key, None)
                    raise ValueError(f"Chunk size invalid: '{chunk_size}'")
                if chunk_size == 0:
                    response.readline()
                    break
                content += response.read(chunk_size)
                response.readline()
        elif "content-length" in response_headers:
            content_length = int(response_headers["content-length"])
            content = response.read(content_length)
        else:
            content = response.read()
        # Handle gzip compression
        if response_headers.get("content-encoding", "").lower() == "gzip":
            print("Gzip compression detected")
            try:
                content = gzip.decompress(content)
            except gzip.BadGzipFile as e:
                s.close()
                open_sockets.pop(socket_key, None)
                raise ValueError(f"Error decompressing gzip content: {e}")
        if response_headers.get("transfer-encoding", "").lower() == "gzip":
            print("Gzip transfer-encoding detected")
            try:
                content = gzip.decompress(content)
            except gzip.BadGzipFile as e:
                s.close()
                open_sockets.pop(socket_key, None)
                raise ValueError(f"Error decompressing gzip transfer-encoding: {e}")
        # Close socket if server requests
        if response_headers.get("connection", "").lower() == "close":
            s.close()
            open_sockets.pop(socket_key, None)
        # Cache response if applicable
        if status in [200, 301, 404]:
            cache_control = response_headers.get("cache-control", "").lower()
            cache_key = (self.scheme, self.host, self.port, self.path)
            if "no-store" not in cache_control:
                max_age = None
                for directive in cache_control.split(","):
                    directive = directive.strip()
                    if directive.startswith("max-age="):
                        try:
                            max_age = int(directive.split("=")[1])
                            break
                        except (IndexError, ValueError):
                            continue
                if max_age is None or not cache_control:
                    expiry = time.time() + max_age if max_age is not None else None
                    cached_responses[cache_key] = (content, expiry)
                    print(f"Caching response for {self.scheme}://{self.host}{self.path}")
        return content.decode("utf8")

class Text:
    def __init__(self, text):
        # Store text content for rendering
        self.text = text

class Tag:
    def __init__(self, tag):
        # Store HTML tag for styling (e.g., <b>, <i>)
        self.tag = tag

def lex(body, view_source=False, right_to_left=False):
    # Escape HTML tags for view-source mode
    if view_source:
        body = body.replace("<", "&lt;").replace(">", "&gt;")
    out = []  # List to store Text and Tag objects
    buffer = ""  # Buffer for accumulating characters
    in_tag = False  # Flag to track if inside an HTML tag
    entity = ""  # Buffer for HTML entities
    entities = {"&lt;": "<", "&gt;": ">"}  # Supported HTML entities
    i = 0
    while i < len(body):
        c = body[i]
        if c == "<":
            # Start of an HTML tag
            in_tag = True
            if buffer:
                out.append(Text(buffer))  # Save accumulated text
                buffer = ""
            if entity:
                out.append(Text(entity))  # Save accumulated entity
                entity = ""
            i += 1
        elif c == ">":
            # End of an HTML tag
            in_tag = False
            out.append(Tag(buffer))  # Save tag
            buffer = ""
            if entity:
                out.append(Text(entity))  # Save accumulated entity
                entity = ""
            i += 1
        elif not in_tag:
            if c == "&":
                # Start of an HTML entity
                entity = "&"
                i += 1
                while i < len(body) and body[i] != ";" and len(entity) < 5:
                    entity += body[i]
                    i += 1
                if i < len(body) and body[i] == ";":
                    entity += ";"
                    i += 1
                    if entity in entities:
                        buffer += entities[entity]  # Decode known entity
                    else:
                        buffer += entity  # Keep unknown entity as-is
                    entity = ""
                else:
                    buffer += entity  # Append invalid entity
                    entity = ""
            else:
                if entity:
                    buffer += entity  # Append any accumulated entity
                    entity = ""
                buffer += c  # Add character to buffer
                i += 1
        else:
            if entity:
                buffer += entity  # Append entity inside tag
                entity = ""
            buffer += c  # Add character to tag buffer
            i += 1
    if not in_tag and buffer:
        out.append(Text(buffer))  # Save final text buffer
    if entity:
        out.append(Text(entity))  # Save final entity
    # Handle right-to-left text by reversing lines
    if right_to_left:
        reversed_out = []
        for item in out:
            if isinstance(item, Text):
                lines = item.text.split("\n")
                reversed_lines = [line[::-1] for line in lines]
                item.text = "\n".join(reversed_lines)
            reversed_out.append(item)
        out = reversed_out
    return out

class Layout:
    def __init__(self, tokens, width, text_right_to_left):
        self.display_list = []
        self.cursor_x = HSTEP
        self.cursor_y = VSTEP
        self.biggest_y = 0
        self.weight = "normal"
        self.style = "roman"
        self.size = 12  # Default font size
        self.width = width
        self.text_right_to_left = text_right_to_left
        if text_right_to_left:
            self.cursor_x = width - HSTEP  # Start from right for RTL
        for tok in tokens:
            self.token(tok)

    def token(self, tok):
        if isinstance(tok, Text):
            lines = tok.text.split("\n")  # Split text into lines
            for i, line in enumerate(lines):
                words = line.split()  # Split line into words
                if not words:
                    # Handle empty lines (explicit newline)
                    font = tkinter.font.Font(size=self.size, weight=self.weight, slant=self.style)
                    self.cursor_y += font.metrics("linespace") * 1.25
                    self.cursor_x = self.width - HSTEP if self.text_right_to_left else HSTEP
                    continue
                for word in words:
                    self.word(word)
                # Only advance to a new line for explicit newlines, not after every text node
                if i < len(lines) - 1:  # If not the last line
                    font = tkinter.font.Font(size=self.size, weight=self.weight, slant=self.style)
                    self.cursor_y += font.metrics("linespace") * 1.25
                    self.cursor_x = self.width - HSTEP if self.text_right_to_left else HSTEP
        elif tok.tag == "i":
            self.style = "italic"  # Set italic style
        elif tok.tag == "/i":
            self.style = "roman"  # Reset to normal style
        elif tok.tag == "b":
            self.weight = "bold"  # Set bold weight
        elif tok.tag == "/b":
            self.weight = "normal"  # Reset to normal weight
        elif tok.tag == "small":
            self.size = 10  # Decrease size
        elif tok.tag == "/small":
            self.size = 12  # Restore size
        elif tok.tag == "big":
            self.size = 18  # Increase size
        elif tok.tag == "/big":
            self.size = 12  # Restore size
        if self.cursor_y > self.biggest_y:
            self.biggest_y = self.cursor_y  # Update maximum height

    def word(self, word):
        font = tkinter.font.Font(size=self.size, weight=self.weight, slant=self.style)
        w = font.measure(word)  # Measure word width
        if self.text_right_to_left:
            # Check for line break in RTL mode
            if self.cursor_x - w < HSTEP:
                self.cursor_y += font.metrics("linespace") * 1.25
                self.cursor_x = self.width - HSTEP
        else:
            # Check for line break in LTR mode
            if self.cursor_x + w > self.width - HSTEP:
                self.cursor_y += font.metrics("linespace") * 1.25
                self.cursor_x = HSTEP
        # Add text to display list
        self.display_list.append(("text", self.cursor_x, self.cursor_y, word, font))
        # Update cursor position
        self.cursor_x += (-w - font.measure(" ") if self.text_right_to_left else w + font.measure(" "))

class Browser:
    def __init__(self, text_left_to_right):
        # Initialize browser with text direction
        self.text_left_to_right = text_left_to_right
        self.window = tkinter.Tk()  # Create Tkinter window
        self.scroll = 0  # Current scroll position
        self.content_height = 0  # Total content height
        self.width = 800  # Default window width
        self.height = 600  # Default window height
        self.canvas = tkinter.Canvas(
            self.window,
            width=self.width,
            height=self.height
        )
        self.canvas.pack(fill=tkinter.BOTH, expand=True)  # Expand canvas to fill window
        # Bind window events
        self.window.bind("<Configure>", self.resize)
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<Button-4>", self.scrollup)
        self.window.bind("<Button-5>", self.scrolldown)
        self.window.bind("<MouseWheel>", self.mouseWheelScroll)

    def mouseWheelScroll(self, e):
        # Handle mouse wheel scrolling
        if os.name == 'nt':
            scroll_amount = -int(e.delta / 120) * SCROLL_STEP
        elif os.name == 'posix':
            scroll_amount = int(e.delta) * SCROLL_STEP
        else:
            scroll_amount = 0
        new_scroll = self.scroll + scroll_amount
        max_scroll = max(0, (self.biggest_y + VSTEP) - self.height)
        self.scroll = max(0, min(new_scroll, max_scroll))  # Clamp scroll position
        self.draw()

    def scrolldown(self, e):
        # Scroll down by fixed step
        max_scroll = max(0, (self.biggest_y + VSTEP) - self.height)
        if self.scroll + SCROLL_STEP > max_scroll:
            return
        self.scroll += SCROLL_STEP
        self.draw()

    def scrollup(self, e):
        # Scroll up by fixed step
        if self.scroll - SCROLL_STEP < 0:
            return
        self.scroll -= SCROLL_STEP
        self.draw()

    def resize(self, event):
        # Handle window resize
        self.width = event.width
        self.height = event.height
        if hasattr(self, 'text'):
            # Recalculate layout to check if scrollbar is needed
            temp_biggest_y = Layout(self.text, self.width, self.text_left_to_right).biggest_y
            temp_content_height = temp_biggest_y + VSTEP
            if temp_content_height > self.height:
                layout = Layout(self.text, self.width - SCROLLBAR_WIDTH, self.text_left_to_right)
                self.display_list = layout.display_list
                self.biggest_y = layout.biggest_y
            else:
                layout = Layout(self.text, self.width, self.text_left_to_right)
                self.display_list = layout.display_list
                self.biggest_y = layout.biggest_y
            self.draw()

    def draw(self):
        # Clear and redraw canvas
        self.canvas.delete("all")
        for item in self.display_list:
            typ, x, y, val, font = item
            # Skip items outside visible area
            if y > self.scroll + self.height:
                continue
            if y + font.metrics("linespace") < self.scroll:
                continue
            if typ == "text":
                # Draw text with specified font
                self.canvas.create_text(x, y - self.scroll, text=val, font=font, anchor="nw" if not self.text_left_to_right else "nw")
        # Draw scrollbar if content exceeds window height
        self.content_height = self.biggest_y + VSTEP
        if self.content_height > self.height:
            track_x = self.width - SCROLLBAR_WIDTH
            track_y = 0
            track_height = self.height
            viewport_height = self.height
            max_scroll = self.content_height - viewport_height
            thumb_height = (viewport_height / self.content_height) * track_height
            fraction = self.scroll / max_scroll if max_scroll > 0 else 0
            thumb_y = fraction * (track_height - thumb_height)
            self.canvas.create_rectangle(track_x, thumb_y, track_x + SCROLLBAR_WIDTH, thumb_y + thumb_height, fill='black')

    def load(self, url):
        # Load and render URL content
        global redirects_number
        redirects_number = 0  # Reset redirect counter
        body = url.request()  # Fetch content
        self.text = lex(body, url.view_source, self.text_left_to_right)  # Parse content
        # Calculate layout to determine scrollbar need
        temp_biggest_y = Layout(self.text, self.width, self.text_left_to_right).biggest_y
        temp_content_height = temp_biggest_y + VSTEP
        if temp_content_height > self.height:
            layout = Layout(self.text, self.width - SCROLLBAR_WIDTH, self.text_left_to_right)
            self.display_list = layout.display_list
            self.biggest_y = layout.biggest_y
        else:
            layout = Layout(self.text, self.width, self.text_left_to_right)
            self.display_list = layout.display_list
            self.biggest_y = layout.biggest_y
        self.draw()

if __name__ == "__main__":
    # Main entry point
    if len(sys.argv) <= 1:
        # Load default HTML file if no URL provided
        default_file = os.path.join(os.path.dirname(__file__), "Default.html")
        Browser(False).load(URL(f"file:///{default_file}"))
        tkinter.mainloop()
    else:
        # Load URL from command-line argument
        url = URL(sys.argv[1])
        Browser(url.right_to_left_text).load(url)
        tkinter.mainloop()