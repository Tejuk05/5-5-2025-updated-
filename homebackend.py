import http.server
import mysql.connector
import io
import json
from urllib.parse import urlparse
import os

# MySQL connection config
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'V@r$ha#123',
    'database': 'Desi'
}
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)
query = "SELECT id, name, description, price FROM products"
cursor.execute(query)
products = cursor.fetchall()

for row in products:
    print(row)


'''# Function to fetch product data
def get_products():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    cursor.close()
    conn.close()
    return products

# Handler for HTTP server
class ProductHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)

        # API endpoint to fetch products as JSON
        if parsed_path.path == '/api/products':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            products = get_products()
            self.wfile.write(json.dumps(products).encode('utf-8'))

        else:
            # Handle other paths (like images)
            super().do_GET()

# Run the HTTP server
def run(server_class=http.server.HTTPServer, handler_class=ProductHandler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    print("Server started on http://localhost:8000")
    httpd.serve_forever()

if __name__ == '__main__':
    run()'''


