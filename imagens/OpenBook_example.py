from flask import Flask, request, render_template_string
import requests

app = Flask(__name__)

def fetch_book_cover(title, author):
    query = f"{title} {author}".replace(' ', '+')
    url = f"https://openlibrary.org/search.json?q={query}"
    response = requests.get(url)
    data = response.json()
    
    if 'docs' in data and len(data['docs']) > 0:
        cover_id = data['docs'][0].get('cover_i')
        if cover_id:
            return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        if not title or not author:
            return render_template_string(TEMPLATE, error="Title and author are required")
        img_url = fetch_book_cover(title, author)
        if img_url:
            return render_template_string(TEMPLATE, title=title, author=author, image_url=img_url)
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
        background-color: #f0f0f0;
      }
      .container {
        max-width: 600px;
        margin: 0 auto;
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
      }
      h1 {
        text-align: center;
        color: #333;
      }
      .form-group {
        margin-bottom: 15px;
      }
      .form-group label {
        display: block;
        margin-bottom: 5px;
        color: #666;
      }
      .form-group input {
        width: 100%;
        padding: 8px;
        box-sizing: border-box;
        border: 1px solid #ddd;
        border-radius: 4px;
      }
      .btn {
        display: block;
        width: 100%;
        padding: 10px;
        background-color: #007BFF;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
        transition: background-color 0.3s;
      }
      .btn:hover {
        background-color: #0056b3;
      }
      .result img {
        max-width: 100%;
        border-radius: 4px;
        transition: transform 0.3s;
        cursor: pointer;
      }
      .result img:hover {
        transform: scale(1.05);
      }
      .error {
        color: red;
        text-align: center;
      }
      .modal {
        display: none;
        position: fixed;
        z-index: 1;
        left: 0;
        top: 0;
        width: 100%;
        height: 100%;
        overflow: auto;
        background-color: rgba(0,0,0,0.9);
      }
      .modal-content {
        margin: auto;
        display: block;
        width: 80%;
        max-width: 700px;
      }
      .close {
        position: absolute;
        top: 15px;
        right: 35px;
        color: #f1f1f1;
        font-size: 40px;
        font-weight: bold;
        transition: 0.3s;
      }
      .close:hover,
      .close:focus {
        color: #bbb;
        text-decoration: none;
        cursor: pointer;
      }
    </style>
  </head>
  <body>
    <div class="container">
      <h1>Book Cover Finder</h1>
      <form method="post">
        <div class="form-group">
          <label for="title">Book Title</label>
          <input type="text" id="title" name="title" required>
        </div>
        <div class="form-group">
          <label for="author">Author</label>
          <input type="text" id="author" name="author" required>
        </div>
        <button type="submit" class="btn">Search</button>
      </form>
      {% if image_url %}
      <div class="result">
        <h2>Result for "{{ title }}" by "{{ author }}"</h2>
        <img src="{{ image_url }}" alt="Book Cover" id="bookCover">
      </div>
      {% endif %}
      {% if error %}
      <div class="error">
        <p>{{ error }}</p>
      </div>
      {% endif %}
    </div>

    <div id="imageModal" class="modal">
      <span class="close">&times;</span>
      <img class="modal-content" id="modalImage">
    </div>

    <script>
      var modal = document.getElementById("imageModal");
      var img = document.getElementById("bookCover");
      var modalImg = document.getElementById("modalImage");
      var span = document.getElementsByClassName("close")[0];

      if (img) {
        img.onclick = function(){
          modal.style.display = "block";
          modalImg.src = this.src;
        }
      }

      span.onclick = function() {
        modal.style.display = "none";
      }

      window.onclick = function(event) {
        if (event.target == modal) {
          modal.style.display = "none";
        }
      }
    </script>
  </body>
</html>
'''

if __name__ == '__main__':
    app.run(debug=True)