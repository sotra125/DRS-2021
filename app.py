from application_data import app


@app.route('/')
def home():
    return None


if __name__ == '__main__':
    app.run()
