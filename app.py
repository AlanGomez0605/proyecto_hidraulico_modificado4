from flask import Flask, render_template
import map_generator

app = Flask(__name__)
map_generator.generar_mapa_html()

@app.route('/')
def index():
    return render_template('index.html')

if __name__=='__main__':
    app.run(debug=True)
