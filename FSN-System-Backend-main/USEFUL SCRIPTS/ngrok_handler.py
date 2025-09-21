import os
import http.server
import socketserver
import threading
import socket
from pyngrok import ngrok, conf
import time
import logging
import json

def get_ngrok_token(token_name="default"):
    """
    Retrieves an ngrok token from the 'ngrok_tokens.json' file.
    """
    try:
        with open("ngrok_tokens.json", "r") as f:
            tokens = json.load(f)
        return tokens.get(token_name)
    except FileNotFoundError:
        logging.error("'ngrok_tokens.json' not found. Please create it.")
        return None
    except json.JSONDecodeError:
        logging.error("'ngrok_tokens.json' is not a valid JSON file.")
        return None


class NgrokHandler:
    def __init__(self, directory, token_name="default"):
        self.directory = directory
        self.token_name = token_name
        self.server_thread = None
        self.server_instance = None
        self.public_url = None
        self.port = self._get_free_port()
        self.handler = self._create_handler(self.directory)

    def _get_free_port(self):
        """Finds and returns an available port."""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("", 0))
        port = s.getsockname()[1]
        s.close()
        return port

    def _create_handler(self, directory):
        """Creates a request handler that serves files from a specific directory."""
        class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=directory, **kwargs)
            
            def log_message(self, format, *args):
                pass
        return QuietHTTPRequestHandler

    def start_server_and_tunnel(self):
        """Starts the HTTP server and an ngrok tunnel."""
        try:
            authtoken = get_ngrok_token(self.token_name)
            if not authtoken or authtoken == "YOUR_DEFAULT_NGROK_TOKEN":
                logging.error(f"Valid ngrok token for '{self.token_name}' not found. Please check 'ngrok_tokens.json'.")
                raise Exception(f"Missing or invalid ngrok token for '{self.token_name}'")

            # Kill any existing ngrok processes first - be more aggressive
            try:
                import subprocess
                import time
                
                # Kill system ngrok processes
                subprocess.run(['pkill', '-f', 'ngrok'], check=False)
                time.sleep(1)
                
                # Also kill pyngrok sessions
                from pyngrok import ngrok
                ngrok.kill()
                time.sleep(1)
                
                logging.info("🧹 Killed all existing ngrok processes and sessions")
            except Exception as e:
                logging.info(f"🔍 No existing ngrok processes to kill: {e}")

            # Create a unique ngrok configuration for this instance
            pyngrok_config = conf.PyngrokConfig(
                auth_token=authtoken
            )

            socketserver.TCPServer.allow_reuse_address = True
            self.server_instance = socketserver.TCPServer(("", self.port), self.handler)

            self.server_thread = threading.Thread(target=self.server_instance.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            logging.info(f"HTTP server started on port {self.port}")

            # Pass the instance-specific configuration to the connect method
            tunnel = ngrok.connect(self.port, "http", pyngrok_config=pyngrok_config)
            self.public_url = tunnel.public_url
            logging.info(f"ngrok tunnel opened at: {self.public_url}")

        except Exception as e:
            logging.error(f"Failed to start server or ngrok tunnel: {e}", exc_info=True)
            if self.server_instance:
                self.server_instance.shutdown()
                self.server_instance.server_close()
            raise

    def stop_server_and_tunnel(self):
        """Stops the HTTP server and the ngrok tunnel."""
        if self.public_url:
            try:
                ngrok.disconnect(self.public_url)
                logging.info(f"ngrok tunnel {self.public_url} closed.")
            except Exception as e:
                logging.warning(f"Could not close ngrok tunnel {self.public_url}: {e}")
            finally:
                self.public_url = None
        
        # The ngrok.kill() command is removed. pyngrok will manage the process lifecycle.
        # Disconnecting the tunnel is sufficient.

        if self.server_instance:
            self.server_instance.shutdown()
            self.server_instance.server_close()
            if self.server_thread:
                self.server_thread.join()
            self.server_instance = None
            self.server_thread = None
            logging.info("HTTP server stopped.")

    def get_public_url(self):
        """Returns the current public URL."""
        return self.public_url

if __name__ == '__main__':
    # This block is for testing the NgrokHandler class independently.
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Create a dummy directory and file for testing
    test_dir = "test_www"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    with open(os.path.join(test_dir, "index.html"), "w") as f:
        f.write("<h1>Ngrok test successful!</h1>")

    handler = None
    try:
        # Replace "default" with your actual token name from ngrok_tokens.json
        handler = NgrokHandler(test_dir, token_name="default")
        handler.start_server_and_tunnel()
        
        public_url = handler.get_public_url()
        if public_url:
            logging.info(f"Tunnel is live at: {public_url}")
            logging.info("Test by opening the URL in your browser.")
            logging.info("Press Ctrl+C to stop the server and tunnel.")
            # Keep the server running for a while to allow for manual testing
            time.sleep(60)
        else:
            logging.error("Failed to get public URL.")

    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received. Shutting down.")
    except Exception as e:
        logging.error(f"An error occurred during the test: {e}")
    finally:
        if handler:
            handler.stop_server_and_tunnel()
        logging.info("Test finished.")
