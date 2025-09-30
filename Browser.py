import socket
import ssl
import sys
import os
import base64
import time
import gzip
import tkinter

# py Browser.py https://example.org

# Global dictionary to store open sockets
open_sockets = {}

# Global dictionary to store responses
cached_responses = {}

# Global variables for the GUI
HSTEP, VSTEP = 13, 18
SCROLL_STEP = 100
SCROLLBAR_WIDTH = 12
EMOJI_SIZE = 18
EMOJI_FOLDER = "openmoji-72x72-color"

# Global variables to control redirects
redirects_number=0
redirects_limit=10

class URL:
    def __init__(self, url):
        self.view_source = False
        self.right_to_left_text = False
        if url.startswith("view-source:"):
            self.view_source = True
            url = url[12:]  # Remove "view-source:"
            # Parse the inner URL as a new instance of the URL
            inner_url = URL(url)
            self.scheme = inner_url.scheme
            self.host = inner_url.host
            self.port = inner_url.port
            self.path = inner_url.path
            self.mime_type = getattr(inner_url, 'mime_type', None)
            self.is_base64 = getattr(inner_url, 'is_base64', False)
            self.data = getattr(inner_url, 'data', None)
        # If url starts with "rlt:" then show text right to left
        elif url.startswith("rlt:"):
            self.right_to_left_text = True
            url = url[4:] # Remove "rlt:"
            inner_url = URL(url)
            self.scheme = inner_url.scheme
            self.host = inner_url.host
            self.port = inner_url.port
            self.path = inner_url.path
        else:
            if url.startswith("data:"):
                self.scheme = "data"
                url = url[5:]  # Remove "data:"
            else:
                if "://" not in url or url == "about:blank":
                    self.host = ""
                    self.port = None
                    self.path = "about:blank"
                    return
                self.scheme, url = url.split("://", 1)
                # Changes to about blank or fallback
            assert self.scheme in ["http", "https", "file", "data"]
            if self.scheme in ["http", "https"]:
                if self.scheme == "http":
                    self.port = 80
                elif self.scheme == "https":
                    self.port = 443
                if "/" not in url:
                    url = url + "/"
                self.host, url = url.split("/", 1)
                self.path = "/" + url
                if ":" in self.host:
                    self.host, port = self.host.split(":", 1)
                    self.port = int(port)
            elif self.scheme == "file":
                self.host = ""
                self.port = None
                self.path = url
            elif self.scheme == "data":
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

        # Global variables
        global redirects_limit
        global redirects_number

        # If about:blank URL
        if self.path == "about:blank":
            return "<>"

        # Open local files
        if self.scheme == "file":
            file_path = self.path
            if os.name == "nt" and file_path.startswith("/"): # Removes initial "/" if running on Windows
                file_path = file_path[1:]
            try:
                with open(file_path, "r", encoding="utf8") as f:
                    return f.read()
            except FileNotFoundError:
                raise ValueError(f"File not found: {file_path}")
            except Exception as e:
                raise ValueError(f"Error while reading file {file_path}: {e}")
            
        # Support for data scheme
        if self.scheme == "data": 
            return self.data
        
        # Verify cache before request
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
                
        
        # Reutilize existing sockets
        socket_key = (self.host, self.port)
        s = open_sockets.get(socket_key)
        if s is None:
            s = socket.socket(
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
            proto=socket.IPPROTO_TCP,
            )
            s.settimeout(20)
            try:
                print(f"Connecting to '{self.scheme + "://" + self.host + self.path}' in port {self.port}...")
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

        # Support to add headers easily
        headers = [
             "Host: {}\r\n".format(self.host),
             "Connection: {}\r\n".format("keep-alive"),
             "User-Agent: {}\r\n".format(user_agent),
             "Accept-Encoding: {}\r\n".format("gzip"),
             "\r\n" # \r\n to end headers
        ]
        request = "GET {} HTTP/1.1\r\n".format(self.path)
        for header in headers:
            request += header
        #print(f"Request sent to server: [\n{request}]")
        s.send(request.encode("utf8"))

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

        response_headers = {}
        while True:
            line = response.readline().decode("utf8").strip()
            if line == "": break
            try:
                header, value = line.split(":", 1)
                response_headers[header.casefold()] = value.strip()
            except ValueError:
                print(f"Invalid header ignored: '{line}'")
                continue

        # Support to redirects
        if redirects_number <= redirects_limit and status in (301, 302, 303, 307, 308):
            redirects_number += 1
            new_url = response_headers.get("location", "").strip()
            if not new_url:
                s.close()
                open_sockets.pop(socket_key, None)
                raise ValueError(f"Redirect response missing 'Location' header")
            # Resolve URL
            if "://" in new_url:
                new_url = new_url
            elif new_url[:1] == "/":
                new_url = self.scheme + "://" + self.host + new_url
            else:
                new_url = self.scheme + "://" + self.host + "/" + new_url
            # Close socket if the server has close
            if response_headers.get("Connection", "").lower() == "close":
                s.close()
                open_sockets.pop(socket_key, None)
            print(f"Redirecting to: '{new_url}'...")
            return URL(new_url).request(user_agent)

        # Check if redirects limit was reached
        if redirects_number >= redirects_limit:
            s.close()
            open_sockets.pop(socket_key, None)
            raise ValueError("Redirects limit reached")

        # Turn str into bytes
        content = b""

        # Support to Transfer-Encoding: chunked
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

        # Support to Content-Ecoding: gzip
        if response_headers.get("content-encoding", "").lower() == "gzip":
            print("Gzip compression detected")
            try:
                content = gzip.decompress(content)
            except gzip.BadGzipFile as e:
                s.close()
                open_sockets.pop(socket_key, None)
                raise ValueError(f"Error decompressing gzip content: {e}")
        
        # Support to Transfer-Encoding: gzip
        if response_headers.get("transfer-encoding", "").lower() == "gzip":
            print("Gzip transfer-encoding detected")
            try:
                content = gzip.decompress(content)
            except gzip.BadGzipFile as e:
                s.close()
                open_sockets.pop(socket_key, None)
                raise ValueError(f"Error decompressing gzip transfer-encoding: {e}")
        
        # Close the socket only if the server says so
        if response_headers.get("connection", "").lower() == "close":
            s.close()
            open_sockets.pop(socket_key, None)

        # Support for caching
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
                # Only store if max-age is present or Cache-Control is absent
                if max_age is None or not cache_control:
                    expiry = time.time() + max_age if max_age is not None else None
                    cached_responses[cache_key] = (content, expiry)
                    print(f"Caching response for {self.scheme}://{self.host}{self.path}")

        return content.decode("utf8")
    
def lex(body, view_source=False, right_to_left=False):
    # Handle view-source mode by escaping HTML tags
    if view_source:
        body = body.replace("<", "&lt;").replace(">", "&gt;")

    text = ""
    in_tag = False
    entity = ""
    entities = {"&lt;": "<", "&gt;": ">"}
    i = 0

    # Process body character by character
    while i < len(body):
        c = body[i]
        if c == "<":
            in_tag = True
            if entity:
                text += entity
                entity = ""
            i += 1
        elif c == ">":
            in_tag = False
            if entity:
                text += entity
                entity = ""
            i += 1
        elif not in_tag:
            if c == "&":
                entity = "&"
                i += 1
                # Read until next ';' or limit to 5 characters
                while i < len(body) and body[i] != ";" and len(entity) < 5:
                    entity += body[i]
                    i += 1
                if i < len(body) and body[i] == ";":
                    entity += ";"
                    i += 1
                    if entity in entities:
                        text += entities[entity]
                    else:
                        text += entity
                    entity = ""
                else:
                    text += entity
                    entity = ""
            else:
                if entity:
                    text += entity
                    entity = ""
                text += c
                i += 1
        else:
            if entity:
                text += entity
                entity = ""
            i += 1

    # If RTL mode is enabled, reverse the order of words
    if right_to_left:
        # Split text into lines
        lines = text.split("\n")
        reversed_lines = []
        for line in lines:
            # Reverse their order
            reversed_line = line[::-1]
            # Join words back into a line
            reversed_lines.append(reversed_line)
        # Join lines back into text
        text = "\n".join(reversed_lines)

    return text

def layout(text, width, text_right_to_left):
    # Initialize display list and cursor position
    display_list = []
    cursor_x, cursor_y = HSTEP, VSTEP
    biggest_y = 0
    
    # Set initial x position to the right edge for RTL mode
    if text_right_to_left:
        cursor_x = width - HSTEP
    
    # Process each character in the text
    for c in text:
        # Handle newline characters
        if c == "\n":
            cursor_y += VSTEP + 10
            cursor_x = width - HSTEP if text_right_to_left else HSTEP
            continue

        # Check for emoji support using Unicode code point
        code = f"{ord(c):X}"
        path = os.path.join(os.path.dirname(__file__), EMOJI_FOLDER, code + ".png")
        w = EMOJI_SIZE if os.path.exists(path) else HSTEP

        # Check for line break
        if text_right_to_left:
            # Break line when cursor approaches the left edge
            if cursor_x - w < HSTEP:
                cursor_y += VSTEP
                cursor_x = width - HSTEP
        else:
            # Break line when cursor approaches the right edge
            if cursor_x + w >= width - HSTEP:
                cursor_y += VSTEP
                cursor_x = HSTEP

        # Add character or emoji to display list
        if os.path.exists(path):
            display_list.append(("image", cursor_x, cursor_y, path))
        else:
            display_list.append(("text", cursor_x, cursor_y, c))

        # Update cursor position: move left for RTL, right for LTR
        cursor_x += -w if text_right_to_left else w
        if cursor_y > biggest_y:
            biggest_y = cursor_y

    return display_list, biggest_y


class Browser:
    def __init__(self, text_left_to_right):
        self.text_left_to_right = text_left_to_right
        self.window = tkinter.Tk()
        self.scroll = 0
        self.content_height = 0
        self.width = 800
        self.height = 600
        self.emoji_images = {}
        self.canvas = tkinter.Canvas(
            self.window,
            width=self.width,
            height=self.height
        )
        self.canvas.pack(fill=tkinter.BOTH, expand=True)
        self.window.bind("<Configure>", self.resize)

    # Scroll through the page
        self.window.bind("<Down>", self.scrolldown)
        self.window.bind("<Up>", self.scrollup)
        self.window.bind("<Button-4>", self.scrollup) # Linux Support
        self.window.bind("<Button-5>", self.scrolldown) # Linux Support
        self.window.bind("<MouseWheel>", self.mouseWheelScroll)
        
    def mouseWheelScroll(self, e):
        if os.name == 'nt':  # Windows
            scroll_amount = -int(e.delta / 120) * SCROLL_STEP
        elif os.name == 'posix':  # Linux / Mac
            scroll_amount = int(e.delta) * SCROLL_STEP
        else:
            scroll_amount = 0  # fallback if another OS

        # Calculates new scroll position
        new_scroll = self.scroll + scroll_amount
            
        max_scroll = max(0, (self.biggest_y + VSTEP) - self.height)
        self.scroll = max(0, min(new_scroll, max_scroll))
        self.draw()
        
    def scrolldown(self, e):
        max_scroll = max(0, (self.biggest_y + VSTEP) - self.height)
        if self.scroll + SCROLL_STEP > max_scroll: return
        self.scroll += SCROLL_STEP
        self.draw()
    
    def scrollup(self, e):
        if self.scroll - SCROLL_STEP < 0: return
        self.scroll -= SCROLL_STEP
        self.draw()

    # Support to resize screen
    def resize(self, event):
        self.width = event.width
        self.height = event.height
        if hasattr(self, 'text'):
            # First pass: layout with full width to check if scrollbar is needed
            _, temp_biggest_y = layout(self.text, self.width, self.text_left_to_right)
            temp_content_height = temp_biggest_y + VSTEP
            if temp_content_height > self.height:
                self.display_list, self.biggest_y = layout(self.text, self.width - SCROLLBAR_WIDTH, self.text_left_to_right)
            else:
                self.display_list, self.biggest_y = layout(self.text, self.width, self.text_left_to_right)
            self.draw()

    def draw(self):
        self.canvas.delete("all")
        for item in self.display_list:
            typ, x, y, val = item
            if y > self.scroll + self.height: continue
            if y + VSTEP < self.scroll: continue
            if typ == "text":
                self.canvas.create_text(x, y - self.scroll, text=val)
            elif typ == "image":
                code = os.path.splitext(os.path.basename(val))[0]
                if code not in self.emoji_images:
                    try:
                        img = tkinter.PhotoImage(file=val).subsample(3, 3)
                        self.emoji_images[code] = img
                    except Exception as e:
                        print(f"Error loading emoji {code}: {e}")
                        continue
                self.canvas.create_image(x, y - self.scroll, image=self.emoji_images[code], anchor="center")

        # Draw scrollbar
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
        global redirects_number
        redirects_number = 0 # Restart redirects counter everytime loads a URL
        body = url.request()
        self.text = lex(body, url.view_source, self.text_left_to_right)
        # First pass: layout with full width to check if scrollbar is needed
        _, temp_biggest_y = layout(self.text, self.width, self.text_left_to_right)
        temp_content_height = temp_biggest_y + VSTEP
        if temp_content_height > self.height:
            self.display_list, self.biggest_y = layout(self.text, self.width - SCROLLBAR_WIDTH, self.text_left_to_right)
        else:
            self.display_list, self.biggest_y = layout(self.text, self.width, self.text_left_to_right)
        self.draw()



if __name__ == "__main__":
    if len(sys.argv) <= 1:
        default_file = os.path.join(os.path.dirname(__file__), "Default.html")
        Browser().load(URL(f"file:///{default_file}"))
        tkinter.mainloop()
    else:
        url = URL(sys.argv[1])
        Browser(url.right_to_left_text).load(url)
        tkinter.mainloop()