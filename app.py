"""
Flask app for Railway deployment
"""

from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
import io
import zipfile
from lib.pdf_converter import PDFToFlipbook

app = Flask(__name__, static_folder='public', static_url_path='')
CORS(app)


@app.route('/')
def index():
    """Serve frontend"""
    return app.send_static_file('index.html')


@app.route('/api/convert', methods=['POST'])
def convert():
    """Convert PDF to flipbook ZIP"""
    try:
        # Get PDF file
        if 'pdf' not in request.files:
            return jsonify({'error': 'PDF file is required'}), 400

        pdf_file = request.files['pdf']
        title = request.form.get('title', 'Zpravodaj')
        account = request.form.get('account', 'default')

        # Read PDF bytes
        pdf_bytes = pdf_file.read()

        # Convert PDF to flipbook
        converter = PDFToFlipbook(pdf_bytes, title)
        result = converter.convert()

        # Create ZIP file in memory
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add HTML
            zip_file.writestr('index.html', result['html'])

            # Add CSS
            zip_file.writestr('css/style.css', result['css'])

            # Add JS
            zip_file.writestr('js/flipbook.js', result['js'])

            # Add page images
            for i, page_bytes in enumerate(result['pages'], start=1):
                zip_file.writestr(f'files/pages/{i}.jpg', page_bytes)

            # Add thumbnails
            for i, thumb_bytes in enumerate(result['thumbs'], start=1):
                zip_file.writestr(f'files/thumb/{i}.jpg', thumb_bytes)

        # Get ZIP bytes
        zip_buffer.seek(0)

        # Generate filename
        safe_title = title.replace(' ', '-').replace('/', '-').lower()
        filename = f"{safe_title}-flipbook.zip"

        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error: {error_trace}")

        return jsonify({
            'error': str(e),
            'trace': error_trace
        }), 500


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
