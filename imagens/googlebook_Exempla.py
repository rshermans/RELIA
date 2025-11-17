from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

def fetch_book_cover(title, author):
    query = f"{title} {author}".replace(' ', '+')
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}"
    response = requests.get(url)
    data = response.json()
    
    if 'items' in data and len(data['items']) > 0:
        book_info = data['items'][0]['volumeInfo']
        if 'imageLinks' in book_info and 'thumbnail' in book_info['imageLinks']:
            return book_info['imageLinks']['thumbnail']
    return None

def save_image(image_url):
    return image_url

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        if not title or not author:
            return render_template_string(TEMPLATE, error="Title and author are required")
        img_url = fetch_book_cover(title, author)
        if img_url:
            image_url = save_image(img_url)
            return render_template_string(TEMPLATE, title=title, author=author, image_url=image_url)
        return render_template_string(TEMPLATE, error="Could not find book cover")
    return render_template_string(TEMPLATE)

TEMPLATE = '''
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Book Cover Finder</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        padding: 20px;
      }
      .container {
        max-width: 600px;
        margin: 0 auto;
      }
      h1 {
        text-align: center;
      }
      .form-group {
        margin-bottom: 15px;
      }
      .form-group label {
        display: block;
        margin-bottom: 5px;
      }
      .form-group input {
        width: 100%;
        padding: 8px;
        box-sizing: border-box;
      }
      .btn {
        display: block;
        width: 100%;
        padding: 10px;
        background-color: #007BFF;
        color: white;
        border: none;
        cursor: pointer;
      }
      .btn:hover {
        background-color: #0056b3;
      }
      .result img {
        max-width: 100%;
      }
      .error {
        color: red;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <h1 class="mt-5">Book Cover Finder</h1>
      <form method="post">
        <div class="form-group">
          <label for="title">Book Title</label>
          <input type="text" class="form-control" id="title" name="title" required>
        </div>
        <div class="form-group">
          <label for="author">Author</label>
          <input type="text" class="form-control" id="author" name="author" required>
        </div>
        <button type="submit" class="btn btn-primary">Search</button>
      </form>
      {% if image_url %}
      <div class="mt-5 result">
        <h2>Result for "{{ title }}" by "{{ author }}"</h2>
        <img src="{{ image_url }}" alt="Book Cover">
      </div>
      {% endif %}
      {% if error %}
      <div class="mt-5 error">
        <p>{{ error }}</p>
      </div>
      {% endif %}
    </div>
  </body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)